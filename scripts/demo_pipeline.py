"""
Demo Pipeline — runs the full pipeline end-to-end using real APIs.

Steps:
  1. Generate ideas (Claude)
  2. Generate script for top idea (Claude)
  3. Fetch B-roll (Pexels)
  4. Generate audio (ElevenLabs or synthetic fallback)
  5. Render video (FFmpeg/MoviePy)
  6. Generate metadata (Claude)

No upload happens — video lands in output/ for your review.

Usage:
    python scripts/demo_pipeline.py
    python scripts/demo_pipeline.py --topic "cognitive bias"
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from loguru import logger

from db.connection import execute, fetchone, fetchall, initialize_db


@click.command()
@click.option("--topic", default=None, help="Optional topic hint to seed idea generation")
@click.option("--idea-id", default=None, type=int, help="Skip idea gen, use existing idea ID")
@click.option("--script-id", default=None, type=int, help="Skip idea+script gen, use existing script ID")
def demo(topic, idea_id, script_id):
    """Run a full demo pipeline pass and produce one rendered video."""
    logger.info("=== Demo Pipeline Starting ===")
    start = time.time()

    # ── Step 1: Generate ideas ────────────────────────────────────────────
    if not idea_id and not script_id:
        logger.info("Step 1/6: Generating ideas with Claude...")
        from modules.ideas.idea_generator import IdeaGenerator
        gen = IdeaGenerator()
        ideas = gen.run(count=5)
        if not ideas:
            logger.error("Idea generation failed.")
            sys.exit(1)

        # Pick the highest-scoring idea
        idea = max(ideas, key=lambda x: x.get("predicted_score", 0))
        idea_id = idea["id"]
        logger.info(f"Selected idea [{idea['predicted_score']:.2f}]: {idea['title']}")
    else:
        if idea_id:
            row = fetchone("SELECT * FROM ideas WHERE id = ?", (idea_id,))
            logger.info(f"Using existing idea {idea_id}: {row['title']}")

    # ── Step 2: Generate script ───────────────────────────────────────────
    if not script_id:
        # Auto-approve the idea
        execute("UPDATE ideas SET status = 'approved' WHERE id = ?", (idea_id,))

        logger.info("Step 2/6: Generating script with Claude...")
        from modules.scripts.script_generator import ScriptGenerator
        script_gen = ScriptGenerator()
        result = script_gen.run(idea_id)
        if not result:
            logger.error("Script generation failed.")
            sys.exit(1)
        script_id = result["script_id"]
        logger.info(f"Script {script_id} generated ({result['word_count']} words, ~{result['estimated_duration']}s)")
        logger.info(f"Hook: {result['hook_text'][:80]}...")

        # Auto-approve the script
        execute("UPDATE scripts SET status = 'approved' WHERE id = ?", (script_id,))
    else:
        row = fetchone("SELECT * FROM scripts WHERE id = ?", (script_id,))
        logger.info(f"Using existing script {script_id}")

    # ── Step 3: Create production record ─────────────────────────────────
    existing_prod = fetchone(
        "SELECT * FROM productions WHERE script_id = ? AND status != 'failed'", (script_id,)
    )
    if existing_prod:
        prod_id = existing_prod["id"]
        logger.info(f"Reusing existing production {prod_id}")
    else:
        prod_id = execute(
            "INSERT INTO productions (script_id, status) VALUES (?, 'pending')",
            (script_id,),
        )
        logger.info(f"Created production {prod_id}")

    # ── Step 4: Generate audio ────────────────────────────────────────────
    production = dict(fetchone("SELECT * FROM productions WHERE id = ?", (prod_id,)))
    if production["status"] == "pending" or not production.get("audio_path"):
        logger.info("Step 3/6: Generating audio...")
        from modules.production.tts_generator import TTSGenerator
        tts = TTSGenerator()
        audio_path = tts.run(prod_id)
        if not audio_path:
            logger.error("Audio generation failed.")
            sys.exit(1)
        logger.info(f"Audio ready: {audio_path}")
    else:
        logger.info(f"Audio already exists: {production['audio_path']}")

    # ── Step 5: Fetch B-roll ──────────────────────────────────────────────
    production = fetchone("SELECT * FROM productions WHERE id = ?", (prod_id,))
    production = dict(production)
    broll_paths = json.loads(production.get("broll_paths") or "[]")
    if not broll_paths:
        logger.info("Step 4/6: Fetching B-roll from Pexels...")
        from modules.production.broll_fetcher import BrollFetcher, extract_broll_queries
        script = fetchone("SELECT visual_notes FROM scripts WHERE id = ?", (script_id,))
        queries = extract_broll_queries(script["visual_notes"] if script else "")
        logger.info(f"B-roll queries: {queries}")
        fetcher = BrollFetcher()
        broll_paths = fetcher.fetch_for_production(prod_id, queries)
        logger.info(f"Got {len(broll_paths)} B-roll asset(s)")
    else:
        logger.info(f"B-roll already fetched: {len(broll_paths)} asset(s)")

    # ── Step 6: Render video ──────────────────────────────────────────────
    production = dict(fetchone("SELECT * FROM productions WHERE id = ?", (prod_id,)))
    if production["status"] in ("audio_ready", "pending") or not production.get("video_path"):
        logger.info("Step 5/6: Rendering video...")
        from modules.render.renderer import Renderer
        renderer = Renderer()
        video_path = renderer.run(prod_id)
        if not video_path:
            logger.error("Render failed.")
            sys.exit(1)
        logger.info(f"Video rendered: {video_path}")
    else:
        video_path = production["video_path"]
        logger.info(f"Video already rendered: {video_path}")

    # ── Step 7: Generate metadata ─────────────────────────────────────────
    existing_queue = fetchone(
        "SELECT * FROM publish_queue WHERE production_id = ?", (prod_id,)
    )
    if not existing_queue:
        logger.info("Step 6/6: Generating metadata...")
        # Ensure production is in right state for metadata gen
        execute(
            "UPDATE productions SET status = 'rendered' WHERE id = ?", (prod_id,)
        )
        from modules.publish.metadata_generator import MetadataGenerator
        meta_gen = MetadataGenerator()
        metadata = meta_gen.run(prod_id)
        if not metadata:
            logger.error("Metadata generation failed.")
            sys.exit(1)
        queue_id = metadata["queue_id"]
        logger.info(f"Metadata generated. Title: {metadata['titles'][0]}")
    else:
        queue_id = existing_queue["id"]
        logger.info(f"Metadata already generated (queue entry {queue_id})")

    # ── Done ──────────────────────────────────────────────────────────────
    elapsed = time.time() - start
    queue_entry = fetchone("SELECT * FROM publish_queue WHERE id = ?", (queue_id,))
    script_row = fetchone("SELECT hook_text FROM scripts WHERE id = ?", (script_id,))

    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print(f"Time: {elapsed:.1f}s")
    print(f"Video: {video_path}")
    print(f"Title: {queue_entry['title']}")
    print(f"Hook: {script_row['hook_text'][:80]}...")
    print(f"Status: {queue_entry['upload_status']}")
    print()
    print("Next steps:")
    print("  1. Review the video in output/")
    print("  2. Open the dashboard to approve:")
    print("     streamlit run modules/dashboard/app.py")
    print("  3. Once approved, upload:")
    print("     python scripts/run_pipeline.py upload")
    print()


if __name__ == "__main__":
    demo()
