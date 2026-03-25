"""
Weekly Research Job — scrapes competitor channels and extracts patterns.
Runs once per week by default (Monday 6am via scheduler).
"""

from loguru import logger

from db.connection import fetchall
from modules.research.channel_analyzer import ChannelAnalyzer, SEED_CHANNELS
from modules.research.pattern_extractor import PatternExtractor


def run_research() -> dict:
    logger.info("=== Research Run Starting ===")

    analyzer = ChannelAnalyzer()

    # Seed channels on first run
    existing = fetchall("SELECT handle FROM competitor_channels")
    existing_handles = {r["handle"] for r in existing}

    channels_added = 0
    for handle in SEED_CHANNELS:
        if handle not in existing_handles:
            db_id = analyzer.add_competitor(handle)
            if db_id:
                channels_added += 1

    # Scrape all active channels
    channels = fetchall(
        "SELECT id, display_name FROM competitor_channels WHERE is_active = 1"
    )
    videos_scraped = 0
    for ch in channels:
        count = analyzer.scrape_channel_shorts(ch["id"], max_videos=50)
        videos_scraped += count

    # Extract patterns from unprocessed videos
    extractor = PatternExtractor()
    patterns_extracted = extractor.run(batch_size=50)

    report = {
        "channels_added": channels_added,
        "videos_scraped": videos_scraped,
        "patterns_extracted": patterns_extracted,
    }
    logger.info(f"=== Research Complete: {report} ===")
    return report
