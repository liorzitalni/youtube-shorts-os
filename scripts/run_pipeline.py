"""
Pipeline CLI — manually trigger any pipeline step.

Usage:
    python scripts/run_pipeline.py research          # Scrape channels, extract patterns
    python scripts/run_pipeline.py produce           # Run daily production
    python scripts/run_pipeline.py analytics         # Run analytics ingestion + analysis
    python scripts/run_pipeline.py upload            # Upload approved videos
    python scripts/run_pipeline.py generate-ideas    # Generate idea batch only
    python scripts/run_pipeline.py scheduler         # Start the APScheduler daemon
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from loguru import logger
from config.settings import settings


@click.group()
def cli():
    """YouTube Shorts OS pipeline runner."""
    pass


@cli.command()
def research():
    """Scrape competitor channels and extract content patterns."""
    from jobs.daily_research import run_research
    report = run_research()
    logger.info(f"Research report: {report}")


@cli.command()
def produce():
    """Run daily production pipeline (ideas → scripts → TTS → render → metadata)."""
    from jobs.daily_production import run_daily_production
    report = run_daily_production()
    logger.info(f"Production report: {report}")


@cli.command()
def analytics():
    """Ingest YouTube Analytics data and run performance analysis."""
    from jobs.daily_analytics import run_daily_analytics
    report = run_daily_analytics()
    logger.info(f"Analytics report: {report}")


@cli.command()
def upload():
    """Upload all approved videos in the publish queue, then cross-post to TikTok + Instagram."""
    from db.connection import fetchall
    from modules.publish.uploader import YouTubeUploader
    from modules.publish.tiktok_uploader import TikTokUploader
    from modules.publish.instagram_uploader import InstagramUploader

    approved = fetchall(
        "SELECT id FROM publish_queue WHERE upload_status = 'approved' ORDER BY scheduled_for ASC"
    )

    if not approved:
        logger.info("No approved videos to upload.")
        return

    yt_uploader = YouTubeUploader()
    tt_uploader = TikTokUploader()
    ig_uploader = InstagramUploader()

    for entry in approved:
        queue_id = entry["id"]
        result = yt_uploader.upload(queue_id)
        if result:
            logger.info(f"Uploaded: {result['url']}")
            # Cross-post to TikTok
            tt_result = tt_uploader.upload(queue_id)
            if tt_result:
                logger.info(f"TikTok cross-posted: {tt_result.get('url') or tt_result.get('publish_id')}")
            # Cross-post to Instagram
            ig_result = ig_uploader.upload(queue_id)
            if ig_result:
                logger.info(f"Instagram cross-posted: {ig_result.get('post_id')}")
        else:
            logger.error(f"Upload failed for queue entry {queue_id}")


@cli.command(name="respond-comments")
@click.option("--max", "max_comments", default=50, help="Max comments to process per video")
def respond_comments(max_comments):
    """Fetch new YouTube comments and reply with Claude-generated empathetic responses."""
    from modules.publish.comment_responder import CommentResponder
    responder = CommentResponder()
    stats = responder.run(max_comments=max_comments)
    logger.info(f"Done: {stats}")


@cli.command(name="generate-ideas")
@click.option("--count", default=15, help="Number of ideas to generate")
def generate_ideas(count):
    """Generate a batch of video ideas."""
    from modules.ideas.idea_generator import IdeaGenerator
    gen = IdeaGenerator()
    ideas = gen.run(count=count)
    logger.info(f"Generated {len(ideas)} ideas.")
    for idea in ideas:
        logger.info(f"  [{idea.get('predicted_score', 0):.2f}] {idea.get('title')}")


@cli.command(name="generate-script")
@click.argument("idea_id", type=int)
def generate_script(idea_id):
    """Generate a script for a specific idea ID."""
    from modules.scripts.script_generator import ScriptGenerator
    gen = ScriptGenerator()
    result = gen.run(idea_id)
    if result:
        logger.info(f"Script {result['script_id']} created.")
        logger.info(f"Hook: {result['hook_text']}")
    else:
        logger.error("Script generation failed.")


@cli.command()
def verify():
    """Check all API connections."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "scripts/verify_apis.py"],
        cwd=str(Path(__file__).parent.parent),
    )
    sys.exit(result.returncode)


@cli.command()
@click.option("--topic", default=None, help="Optional topic hint")
@click.option("--idea-id", default=None, type=int, help="Use existing idea ID")
@click.option("--script-id", default=None, type=int, help="Use existing script ID")
def demo(topic, idea_id, script_id):
    """Run a full demo pipeline: idea -> script -> TTS -> render -> metadata."""
    from scripts.demo_pipeline import demo as _demo
    from click.testing import CliRunner
    # Invoke directly so we stay in the same venv
    import subprocess, sys
    args = ["scripts/demo_pipeline.py"]
    if topic:
        args += ["--topic", topic]
    if idea_id:
        args += ["--idea-id", str(idea_id)]
    if script_id:
        args += ["--script-id", str(script_id)]
    result = subprocess.run([sys.executable] + args)
    sys.exit(result.returncode)


@cli.command(name="youtube-auth")
def youtube_auth():
    """Run YouTube OAuth2 browser flow to create youtube_token.json."""
    import subprocess, sys
    result = subprocess.run([sys.executable, "scripts/setup_youtube_auth.py"])
    sys.exit(result.returncode)


@cli.command()
def scheduler():
    """Start the APScheduler daemon (runs all jobs on cron schedule)."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    sched = BlockingScheduler()

    from jobs.daily_research import run_research
    from jobs.daily_production import run_daily_production
    from jobs.daily_analytics import run_daily_analytics

    # Parse cron expressions from settings
    def _add_cron(func, cron_str, name):
        parts = cron_str.split()
        sched.add_job(
            func,
            CronTrigger(
                minute=parts[0], hour=parts[1],
                day=parts[2], month=parts[3], day_of_week=parts[4],
            ),
            id=name,
            name=name,
            misfire_grace_time=3600,
        )
        logger.info(f"Scheduled {name}: {cron_str}")

    _add_cron(run_research, settings.research_cron, "research")
    _add_cron(run_daily_production, settings.production_cron, "production")
    _add_cron(run_daily_analytics, settings.analytics_cron, "analytics")

    logger.info("Scheduler started. Press Ctrl+C to stop.")
    try:
        sched.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    cli()
