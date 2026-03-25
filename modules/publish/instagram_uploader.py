"""
Instagram Uploader — cross-posts rendered videos to Instagram Reels
via the Instagram Graph API (Meta).

Setup:
    1. Create a Facebook Developer App at developers.facebook.com
    2. Add Instagram Graph API product
    3. Connect an Instagram Business/Creator account
    4. Run: python scripts/setup_instagram_auth.py
    5. Add INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID to .env
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests
from loguru import logger

from config.settings import settings
from db.connection import execute, fetchone


GRAPH_URL = "https://graph.instagram.com/v21.0"


class InstagramUploader:
    def __init__(self):
        self._access_token = settings.instagram_access_token
        self._account_id = settings.instagram_account_id

    def upload(self, queue_id: int) -> dict | None:
        """Upload video as Instagram Reel. Returns dict with post_id or None."""
        if not self._access_token or not self._account_id:
            logger.warning("Instagram credentials not set — skipping cross-post.")
            logger.warning("Add INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID to .env")
            return None

        entry = fetchone(
            """SELECT pq.title, pq.description, pq.hashtags,
                      pr.video_path
               FROM publish_queue pq
               JOIN productions pr ON pr.id = pq.production_id
               WHERE pq.id = ?""",
            (queue_id,),
        )
        if not entry:
            logger.error(f"Queue entry {queue_id} not found.")
            return None

        video_path = Path(entry["video_path"])
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return None

        # Instagram Graph API requires a publicly accessible video URL.
        # The video must be hosted somewhere accessible (not local file).
        # For now, log a clear message — this requires a hosting step.
        logger.warning(
            "Instagram Reels upload requires a publicly accessible video URL. "
            "Local file upload is not supported by the Instagram Graph API. "
            "To enable: host videos on S3/Cloudflare R2 and update this uploader."
        )
        return None

        # --- Implementation ready once hosting is configured ---
        # caption = self._build_caption(entry)
        # container_id = self._create_container(video_url, caption)
        # if not container_id:
        #     return None
        # post_id = self._publish_container(container_id)
        # if post_id:
        #     execute(
        #         "UPDATE publish_queue SET instagram_url = ?, updated_at = datetime('now') WHERE id = ?",
        #         (f"https://www.instagram.com/reel/{post_id}/", queue_id),
        #     )
        # return {"post_id": post_id}

    def _build_caption(self, entry: dict) -> str:
        hashtags = json.loads(entry["hashtags"] or "[]")
        caption = entry["title"]
        if hashtags:
            caption += "\n\n" + " ".join(hashtags)
        return caption[:2200]

    def _create_container(self, video_url: str, caption: str) -> str | None:
        resp = requests.post(
            f"{GRAPH_URL}/{self._account_id}/media",
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": "true",
                "access_token": self._access_token,
            },
        )
        if resp.status_code != 200:
            logger.error(f"Instagram container creation failed: {resp.text[:200]}")
            return None
        container_id = resp.json().get("id")
        # Wait for video processing
        for _ in range(15):
            time.sleep(5)
            status_resp = requests.get(
                f"{GRAPH_URL}/{container_id}",
                params={"fields": "status_code", "access_token": self._access_token},
            )
            status = status_resp.json().get("status_code")
            if status == "FINISHED":
                return container_id
            elif status == "ERROR":
                logger.error("Instagram video processing failed.")
                return None
        return container_id  # Optimistic

    def _publish_container(self, container_id: str) -> str | None:
        resp = requests.post(
            f"{GRAPH_URL}/{self._account_id}/media_publish",
            params={"creation_id": container_id, "access_token": self._access_token},
        )
        if resp.status_code != 200:
            logger.error(f"Instagram publish failed: {resp.text[:200]}")
            return None
        return resp.json().get("id")
