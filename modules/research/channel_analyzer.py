"""
Channel Analyzer — fetches competitor channel and video data via YouTube Data API.
Populates competitor_channels and competitor_videos tables.
"""

from __future__ import annotations

import json
from datetime import datetime

import httpx
from loguru import logger

from config.settings import settings
from db.connection import execute, fetchall, fetchone
from modules.publish.uploader import get_youtube_service


class ChannelAnalyzer:
    def __init__(self):
        self.service = get_youtube_service()

    def add_competitor(self, channel_handle: str) -> int | None:
        """
        Add a channel to the competitor list by handle (e.g. '@BrainScience').
        Returns channel DB id.
        """
        logger.info(f"Adding competitor channel: {channel_handle}")

        # Resolve handle to channel ID
        response = self.service.search().list(
            part="snippet",
            q=channel_handle,
            type="channel",
            maxResults=1,
        ).execute()

        items = response.get("items", [])
        if not items:
            logger.warning(f"Channel not found: {channel_handle}")
            return None

        snippet = items[0]["snippet"]
        channel_id = items[0]["id"]["channelId"]

        # Get subscriber count
        details = self.service.channels().list(
            part="statistics",
            id=channel_id,
        ).execute()

        stats = details["items"][0]["statistics"] if details.get("items") else {}
        sub_count = int(stats.get("subscriberCount", 0))

        db_id = execute(
            """
            INSERT OR REPLACE INTO competitor_channels
                (youtube_channel_id, handle, display_name, subscriber_count, niche_tags)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                channel_id,
                channel_handle,
                snippet.get("channelTitle", channel_handle),
                sub_count,
                json.dumps(["psychology", "human_behavior"]),
            ),
        )
        logger.info(f"Added channel {channel_handle} (db id: {db_id}, subs: {sub_count:,})")
        return db_id

    def scrape_channel_shorts(self, channel_db_id: int, max_videos: int = 50) -> int:
        """
        Fetch recent Shorts from a competitor channel.
        Returns count of new videos saved.
        """
        channel = fetchone(
            "SELECT * FROM competitor_channels WHERE id = ?", (channel_db_id,)
        )
        if not channel:
            return 0

        channel = dict(channel)
        logger.info(f"Scraping Shorts from {channel['display_name']}...")

        # Search for Shorts (duration <= 60s filter applied post-fetch)
        response = self.service.search().list(
            part="id,snippet",
            channelId=channel["youtube_channel_id"],
            type="video",
            videoDuration="short",   # under 4 minutes — we filter to 60s below
            order="viewCount",
            maxResults=min(max_videos, 50),
        ).execute()

        video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
        if not video_ids:
            return 0

        # Get full video details
        details = self.service.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids),
        ).execute()

        saved = 0
        for item in details.get("items", []):
            duration_sec = self._parse_duration(item["contentDetails"]["duration"])
            if duration_sec > 65:  # Only keep Shorts
                continue

            stats = item.get("statistics", {})
            snippet = item["snippet"]

            try:
                execute(
                    """
                    INSERT OR IGNORE INTO competitor_videos
                        (competitor_channel_id, youtube_video_id, title, description,
                         duration_seconds, view_count, like_count, comment_count, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        channel_db_id,
                        item["id"],
                        snippet.get("title", ""),
                        snippet.get("description", "")[:1000],
                        duration_sec,
                        int(stats.get("viewCount", 0)),
                        int(stats.get("likeCount", 0)),
                        int(stats.get("commentCount", 0)),
                        snippet.get("publishedAt", ""),
                    ),
                )
                saved += 1
            except Exception as e:
                logger.warning(f"Failed to save video {item['id']}: {e}")

        # Update last_scraped_at
        execute(
            "UPDATE competitor_channels SET last_scraped_at = datetime('now') WHERE id = ?",
            (channel_db_id,),
        )

        logger.info(f"Saved {saved} Shorts from {channel['display_name']}.")
        return saved

    def _parse_duration(self, iso_duration: str) -> int:
        """Parse ISO 8601 duration to seconds. e.g. PT1M30S -> 90"""
        import re
        pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
        match = re.match(pattern, iso_duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds


# Pre-curated list of psychology Shorts channels to seed the research engine
SEED_CHANNELS = [
    "@BrainScienceFacts",
    "@PsychologyFacts",
    "@DarkPsychologySecrets",
    "@MindMatters",
    "@CognitivePsychShorts",
]
