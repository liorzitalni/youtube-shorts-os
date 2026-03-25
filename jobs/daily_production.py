"""
Daily Production Job — runs the full content pipeline for the day.

Steps:
  1. Check idea backlog — refill if below threshold
  2. For each approved idea (up to daily target): generate script
  3. For each approved script: generate TTS audio
  4. For each audio-ready production: render video
  5. For each rendered video: generate metadata → add to publish queue

Each step respects the HUMAN_REVIEW_SCRIPTS and HUMAN_REVIEW_VIDEOS flags.
When human review is enabled, the pipeline pauses at review checkpoints
and waits for dashboard approval before proceeding.
"""

from loguru import logger

from config.settings import settings
from db.connection import execute, fetchall, fetchone, enqueue_job
from modules.ideas.idea_generator import IdeaGenerator, needs_refill
from modules.scripts.script_generator import ScriptGenerator
from modules.production.tts_generator import TTSGenerator
from modules.production.broll_fetcher import BrollFetcher, extract_broll_queries
from modules.render.renderer import Renderer
from modules.publish.metadata_generator import MetadataGenerator


def run_daily_production() -> dict:
    logger.info("=== Daily Production Run Starting ===")
    report = {
        "ideas_generated": 0,
        "scripts_generated": 0,
        "audio_generated": 0,
        "broll_fetched": 0,
        "videos_rendered": 0,
        "metadata_generated": 0,
    }

    # ── Step 1: Refill idea backlog ────────────────────────────────────────
    if needs_refill():
        logger.info("Backlog below threshold — generating new ideas...")
        gen = IdeaGenerator()
        new_ideas = gen.run(count=15)
        report["ideas_generated"] = len(new_ideas)
        logger.info(f"Generated {len(new_ideas)} new ideas.")

    # ── Step 2: Generate scripts for approved ideas ────────────────────────
    if not settings.human_review_scripts:
        # Auto-approve backlog ideas when review is disabled
        execute(
            "UPDATE ideas SET status = 'approved' WHERE status = 'backlog'"
        )

    approved_ideas = fetchall(
        """
        SELECT i.id FROM ideas i
        WHERE i.status = 'approved'
          AND NOT EXISTS (SELECT 1 FROM scripts s WHERE s.idea_id = i.id AND s.status != 'rejected')
        ORDER BY i.predicted_score DESC
        LIMIT ?
        """,
        (settings.daily_video_target * 2,),  # Generate 2x buffer
    )

    script_gen = ScriptGenerator()
    for idea_row in approved_ideas:
        result = script_gen.run(idea_row["id"])
        if result:
            report["scripts_generated"] += 1

    # ── Step 3: Generate TTS for approved scripts ──────────────────────────
    if not settings.human_review_scripts:
        execute(
            "UPDATE scripts SET status = 'approved' WHERE status = 'draft'"
        )

    approved_scripts = fetchall(
        """
        SELECT s.id FROM scripts s
        WHERE s.status = 'approved'
          AND NOT EXISTS (
            SELECT 1 FROM productions p WHERE p.script_id = s.id AND p.status != 'failed'
          )
        LIMIT ?
        """,
        (settings.daily_video_target * 2,),
    )

    tts = TTSGenerator()
    for script_row in approved_scripts:
        # Create production record
        prod_id = execute(
            "INSERT INTO productions (script_id, status) VALUES (?, 'pending')",
            (script_row["id"],),
        )
        execute(
            "UPDATE scripts SET status = 'in_production' WHERE id = ?",
            (script_row["id"],),
        )
        result = tts.run(prod_id)
        if result:
            report["audio_generated"] += 1

    # ── Step 3b: Fetch B-roll for audio-ready productions ─────────────────
    audio_ready_for_broll = fetchall(
        """
        SELECT pr.id, s.visual_notes FROM productions pr
        JOIN scripts s ON s.id = pr.script_id
        WHERE pr.status = 'audio_ready'
          AND (pr.broll_paths IS NULL OR pr.broll_paths = '[]')
        """,
    )
    fetcher = BrollFetcher()
    for prod_row in audio_ready_for_broll:
        queries = extract_broll_queries(prod_row["visual_notes"] or "")
        paths = fetcher.fetch_for_production(prod_row["id"], queries)
        if paths:
            report["broll_fetched"] += len(paths)

    # ── Step 4: Render videos from audio-ready productions ─────────────────
    audio_ready = fetchall(
        "SELECT id FROM productions WHERE status = 'audio_ready' LIMIT ?",
        (settings.daily_video_target * 2,),
    )

    renderer = Renderer()
    for prod_row in audio_ready:
        result = renderer.run(prod_row["id"])
        if result:
            report["videos_rendered"] += 1

    # ── Step 5: Generate metadata for rendered videos ──────────────────────
    if not settings.human_review_videos:
        execute(
            "UPDATE productions SET status = 'approved' WHERE status = 'rendered'"
        )

    rendered = fetchall(
        """
        SELECT pr.id FROM productions pr
        WHERE pr.status IN ('rendered', 'approved')
          AND NOT EXISTS (
            SELECT 1 FROM publish_queue pq WHERE pq.production_id = pr.id
          )
        LIMIT ?
        """,
        (settings.daily_video_target,),
    )

    meta_gen = MetadataGenerator()
    for prod_row in rendered:
        result = meta_gen.run(prod_row["id"])
        if result:
            report["metadata_generated"] += 1

    logger.info(f"=== Daily Production Complete: {report} ===")
    return report
