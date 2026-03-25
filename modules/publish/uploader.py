"""
YouTube Uploader — handles OAuth2 auth and video upload via YouTube Data API v3.
SEO enhancements: proper tags, language metadata, SRT captions upload, pinned comment.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from db.connection import execute, fetchone


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def get_youtube_service():
    """Return an authenticated YouTube service object."""
    creds = None
    token_path = Path(settings.youtube_token_path)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.youtube_client_secrets_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


class YouTubeUploader:
    def __init__(self):
        self.service = get_youtube_service()

    def upload(self, queue_id: int) -> dict | None:
        """Upload a video from the publish queue. Returns video info dict or None."""
        entry = fetchone(
            """
            SELECT pq.*, pr.video_path, pr.script_id
            FROM publish_queue pq
            JOIN productions pr ON pr.id = pq.production_id
            WHERE pq.id = ?
            """,
            (queue_id,),
        )
        if not entry:
            logger.error(f"Queue entry {queue_id} not found.")
            return None

        entry = dict(entry)
        video_path = entry.get("video_path")
        if not video_path or not Path(video_path).exists():
            logger.error(f"Video file not found: {video_path}")
            return None

        hashtags = json.loads(entry.get("hashtags", "[]"))
        tags = json.loads(entry.get("tags", "[]"))
        # Tags must not have # prefix (they're hidden metadata, not hashtags)
        tags = [t.lstrip("#") for t in tags if t]

        # Description: body + hashtags appended at end
        description = entry["description"].rstrip()
        if hashtags:
            description += "\n\n" + " ".join(hashtags)

        logger.info(f"Uploading queue entry {queue_id}: {entry['title']}")
        execute(
            "UPDATE publish_queue SET upload_status = 'uploading', updated_at = datetime('now') WHERE id = ?",
            (queue_id,),
        )

        try:
            result = self._upload_video(
                video_path=video_path,
                title=entry["title"],
                description=description,
                tags=tags,
            )
        except Exception as e:
            logger.error(f"Upload failed for queue {queue_id}: {e}")
            execute(
                "UPDATE publish_queue SET upload_status = 'failed', upload_error = ?, updated_at = datetime('now') WHERE id = ?",
                (str(e), queue_id),
            )
            return None

        video_id = result["id"]
        youtube_url = f"https://www.youtube.com/shorts/{video_id}"

        execute(
            """
            UPDATE publish_queue
            SET youtube_video_id = ?, youtube_url = ?, upload_status = 'live',
                uploaded_at = datetime('now'), updated_at = datetime('now')
            WHERE id = ?
            """,
            (video_id, youtube_url, queue_id),
        )
        logger.info(f"Uploaded: {youtube_url}")

        # Post-upload SEO: captions + pinned comment
        script_id = entry.get("script_id")
        if script_id:
            self._upload_captions(video_id, script_id)

        pinned_comment = entry.get("pinned_comment")
        if pinned_comment:
            self._post_pinned_comment(video_id, pinned_comment)

        return {"video_id": video_id, "url": youtube_url}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=60))
    def _upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
    ) -> dict:
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "27",  # Education
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5,  # 5MB chunks
        )

        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                logger.debug(f"Upload progress: {pct}%")

        return response

    def _upload_captions(self, video_id: str, script_id: int) -> None:
        """Generate SRT from script text and upload to YouTube for keyword indexing."""
        try:
            script = fetchone(
                "SELECT full_script, estimated_duration FROM scripts WHERE id = ?",
                (script_id,),
            )
            if not script:
                return

            srt_content = self._generate_srt(
                text=script["full_script"],
                duration=float(script["estimated_duration"] or 60),
            )

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".srt", delete=False, encoding="utf-8"
            ) as f:
                f.write(srt_content)
                srt_path = f.name

            try:
                self.service.captions().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "language": "en",
                            "name": "English",
                            "isDraft": False,
                        }
                    },
                    media_body=MediaFileUpload(srt_path, mimetype="text/plain"),
                ).execute()
                logger.info(f"Captions uploaded for video {video_id}")
            finally:
                os.unlink(srt_path)

        except Exception as e:
            logger.warning(f"Caption upload failed (non-critical): {e}")

    def _generate_srt(self, text: str, duration: float) -> str:
        """Split script into proportionally timed SRT subtitle segments."""
        sentences = [s.strip() for s in text.replace("—", ".").split(".") if s.strip()]
        if not sentences:
            return ""

        time_per_seg = duration / len(sentences)
        lines = []
        for i, sentence in enumerate(sentences):
            start = i * time_per_seg
            end = min((i + 1) * time_per_seg, duration)
            lines.append(str(i + 1))
            lines.append(f"{self._fmt_time(start)} --> {self._fmt_time(end)}")
            lines.append(sentence)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _post_pinned_comment(self, video_id: str, comment_text: str) -> None:
        """Post a comment on the video with secondary keywords for SEO."""
        try:
            self.service.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {"textOriginal": comment_text}
                        },
                    }
                },
            ).execute()
            logger.info(f"Pinned comment posted for video {video_id}")
        except Exception as e:
            logger.warning(f"Pinned comment failed (non-critical): {e}")
