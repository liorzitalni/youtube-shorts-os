"""
TikTok Uploader — cross-posts rendered videos to TikTok via Content Posting API v2.
Handles token refresh, chunked upload, and publish status polling.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import requests
from loguru import logger

from config.settings import settings
from db.connection import execute, fetchone


TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
TIKTOK_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB chunks


class TikTokUploader:
    def __init__(self):
        self._token_data = self._load_token()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def upload(self, queue_id: int) -> dict | None:
        """Upload video to TikTok. Returns dict with publish_id or None on failure."""
        if not self._token_data:
            logger.warning("TikTok token not found — skipping cross-post. Run setup_tiktok_auth.py")
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

        access_token = self._get_valid_token()
        if not access_token:
            return None

        # Build TikTok caption: hook + save CTA + max 5 hashtags
        hashtags = json.loads(entry["hashtags"] or "[]")
        caption = self._build_tiktok_caption(entry["title"], hashtags)

        try:
            publish_id = self._init_and_upload(access_token, video_path, caption)
            if not publish_id:
                return None

            tiktok_url = self._poll_status(access_token, publish_id)
            if tiktok_url:
                execute(
                    "UPDATE publish_queue SET tiktok_url = ?, updated_at = datetime('now') WHERE id = ?",
                    (tiktok_url, queue_id),
                )
                logger.info(f"TikTok published: {tiktok_url}")
                return {"publish_id": publish_id, "url": tiktok_url}
            else:
                logger.info(f"TikTok upload initiated (publish_id={publish_id}), processing on TikTok servers.")
                execute(
                    "UPDATE publish_queue SET tiktok_url = ?, updated_at = datetime('now') WHERE id = ?",
                    (f"tiktok://publish_id/{publish_id}", queue_id),
                )
                return {"publish_id": publish_id}

        except Exception as e:
            logger.error(f"TikTok upload failed for queue {queue_id}: {e}")
            return None

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_tiktok_caption(self, title: str, hashtags: list) -> str:
        """Build optimized TikTok caption: hook + save CTA + max 5 hashtags."""
        # Save CTAs — highest-value engagement signal for healing/psychology content
        save_ctas = [
            "Save this for when you need it.",
            "Save this — you'll need it when they gaslight you again.",
            "Save this and come back to it when you feel confused.",
            "Save this. Your past self needed it. Your future self will thank you.",
            "Send this to someone who needs to hear it.",
        ]
        import hashlib
        cta_index = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(save_ctas)
        cta = save_ctas[cta_index]

        # TikTok niche hashtags — always include narctok + limit to 5 total
        niche_tags = ["#narctok", "#narcissistrecovery", "#traumarecovery", "#mentalhealth", "#healing"]
        # Merge with video-specific hashtags, cap at 5
        video_tags = [t if t.startswith("#") else f"#{t}" for t in hashtags[:3]]
        combined = list(dict.fromkeys(video_tags + niche_tags))[:5]
        tag_str = " ".join(combined)

        caption = f"{title}\n\n{cta}\n\n{tag_str}"
        return caption[:4000]

    def _init_and_upload(self, access_token: str, video_path: Path, caption: str) -> str | None:
        """Initialize upload, send chunks, return publish_id."""
        file_size = video_path.stat().st_size
        # TikTok chunk_size must be 5MB–64MB.
        # Declare max 64MB single chunk; last chunk can be smaller per TikTok spec.
        chunk_size = 64 * 1024 * 1024  # 64MB declared
        total_chunks = 1

        # Init
        init_resp = requests.post(
            TIKTOK_INIT_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json={
                "post_info": {
                    "title": caption,
                    "privacy_level": "SELF_ONLY",  # Draft until app review approved
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunks,
                },
            },
        )

        if init_resp.status_code != 200:
            logger.error(f"TikTok init failed: {init_resp.status_code} {init_resp.text[:300]}")
            return None

        init_data = init_resp.json()
        if init_data.get("error", {}).get("code") not in ("ok", None, ""):
            logger.error(f"TikTok init error: {init_data.get('error')}")
            return None

        publish_id = init_data["data"]["publish_id"]
        upload_url = init_data["data"]["upload_url"]

        # Upload chunks
        with open(video_path, "rb") as f:
            for chunk_idx in range(total_chunks):
                chunk_data = f.read(chunk_size)
                start = chunk_idx * chunk_size
                end = start + len(chunk_data) - 1

                put_resp = requests.put(
                    upload_url,
                    headers={
                        "Content-Range": f"bytes {start}-{end}/{file_size}",
                        "Content-Length": str(len(chunk_data)),
                        "Content-Type": "video/mp4",
                    },
                    data=chunk_data,
                )
                if put_resp.status_code not in (200, 201, 206):
                    logger.error(f"TikTok chunk {chunk_idx} upload failed: {put_resp.status_code}")
                    return None
                logger.debug(f"TikTok chunk {chunk_idx + 1}/{total_chunks} uploaded")

        return publish_id

    def _poll_status(self, access_token: str, publish_id: str, max_polls: int = 10) -> str | None:
        """Poll until published and return video URL, or None if still processing."""
        for attempt in range(max_polls):
            time.sleep(3)
            resp = requests.post(
                TIKTOK_STATUS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                },
                json={"publish_id": publish_id},
            )
            if resp.status_code != 200:
                break
            data = resp.json().get("data", {})
            status = data.get("status")
            if status == "PUBLISH_COMPLETE":
                return data.get("publicaly_available_post_id", [None])[0]
            elif status in ("FAILED", "PUBLISH_FAILED"):
                logger.error(f"TikTok publish failed: {data}")
                return None
            logger.debug(f"TikTok status: {status} (attempt {attempt + 1})")
        return None  # Still processing — that's OK

    def _get_valid_token(self) -> str | None:
        """Return a valid access token, refreshing if needed."""
        if not self._token_data:
            return None

        access_token = self._token_data.get("access_token")
        refresh_token = self._token_data.get("refresh_token")

        # TikTok access tokens expire after 24h; refresh if we have a refresh token
        expires_in = self._token_data.get("expires_in", 86400)
        saved_at = self._token_data.get("saved_at", "")
        if saved_at and refresh_token:
            from datetime import datetime
            try:
                age_seconds = (datetime.utcnow() - datetime.fromisoformat(saved_at)).total_seconds()
                if age_seconds > (expires_in - 300):  # refresh 5 min before expiry
                    return self._refresh_token(refresh_token)
            except Exception:
                pass

        return access_token

    def _refresh_token(self, refresh_token: str) -> str | None:
        resp = requests.post(
            TIKTOK_TOKEN_URL,
            data={
                "client_key": settings.tiktok_client_key,
                "client_secret": settings.tiktok_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200 or "error" in resp.json():
            logger.error(f"TikTok token refresh failed: {resp.text[:200]}")
            return None

        new_token = resp.json()
        from datetime import datetime
        new_token["saved_at"] = datetime.utcnow().isoformat()
        token_path = Path(settings.tiktok_token_path)
        token_path.write_text(json.dumps(new_token, indent=2))
        self._token_data = new_token
        logger.info("TikTok token refreshed.")
        return new_token.get("access_token")

    def _load_token(self) -> dict | None:
        token_path = Path(settings.tiktok_token_path)
        if not token_path.exists():
            return None
        try:
            return json.loads(token_path.read_text())
        except Exception:
            return None
