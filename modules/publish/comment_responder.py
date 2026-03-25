"""
Comment Responder — fetches new YouTube comments and replies with Claude-generated responses.
"""

from __future__ import annotations

from pathlib import Path

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.template_utils import fill_template
from db.connection import execute, fetchall, fetchone
from modules.publish.uploader import get_youtube_service


PROMPT_PATH = Path("config/prompts/comment_response.md")


class CommentResponder:
    def __init__(self):
        self.youtube = get_youtube_service()
        self.claude = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._own_channel_id = self._get_own_channel_id()

    def _get_own_channel_id(self) -> str:
        result = self.youtube.channels().list(part="id", mine=True).execute()
        return result["items"][0]["id"]

    def run(self, max_comments: int = 50) -> dict:
        """Fetch unread comments across all videos and reply to each."""
        videos = fetchall(
            "SELECT youtube_video_id, title FROM publish_queue WHERE youtube_video_id IS NOT NULL"
        )

        stats = {"videos": 0, "comments_found": 0, "replied": 0, "skipped": 0}

        for video in videos:
            video_id = video["youtube_video_id"]
            title = video["title"]
            count = self._process_video(video_id, title, max_comments)
            stats["videos"] += 1
            stats["comments_found"] += count["found"]
            stats["replied"] += count["replied"]
            stats["skipped"] += count["skipped"]

        logger.info(
            f"Comment run done: {stats['replied']} replied, "
            f"{stats['skipped']} skipped across {stats['videos']} videos."
        )
        return stats

    def _process_video(self, video_id: str, title: str, max_comments: int) -> dict:
        """Fetch top-level comments for a video and reply to unanswered ones."""
        count = {"found": 0, "replied": 0, "skipped": 0}

        try:
            response = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_comments, 100),
                order="relevance",
                textFormat="plainText",
            ).execute()
        except Exception as e:
            logger.warning(f"Could not fetch comments for {video_id}: {e}")
            return count

        threads = response.get("items", [])
        count["found"] = len(threads)

        for thread in threads:
            thread_id = thread["id"]
            snippet = thread["snippet"]["topLevelComment"]["snippet"]
            comment_text = snippet.get("textDisplay", "").strip()
            author = snippet.get("authorDisplayName", "")
            author_channel_id = snippet.get("authorChannelId", {}).get("value", "")
            reply_count = thread["snippet"].get("totalReplyCount", 0)

            # Skip our own channel's comments (pinned comments we posted)
            if author_channel_id == self._own_channel_id:
                count["skipped"] += 1
                continue

            # Skip if already replied (has replies) or already logged in DB
            if reply_count > 0:
                count["skipped"] += 1
                continue

            already_done = fetchone(
                "SELECT id FROM comment_replies WHERE thread_id = ?", (thread_id,)
            )
            if already_done:
                count["skipped"] += 1
                continue

            if not comment_text or len(comment_text) < 3:
                count["skipped"] += 1
                continue

            reply = self._generate_reply(comment_text, title)

            if reply is None:
                logger.debug(f"Skipping spam/bot comment: {comment_text[:60]}")
                execute(
                    "INSERT INTO comment_replies (thread_id, video_id, comment_text, reply_text, status) VALUES (?,?,?,?,?)",
                    (thread_id, video_id, comment_text, None, "skipped"),
                )
                count["skipped"] += 1
                continue

            self._post_reply(thread_id, reply)
            execute(
                "INSERT INTO comment_replies (thread_id, video_id, comment_text, reply_text, status) VALUES (?,?,?,?,?)",
                (thread_id, video_id, comment_text, reply, "replied"),
            )
            logger.info(f"Replied to [{author}]: {comment_text[:60]}...")
            count["replied"] += 1

        return count

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate_reply(self, comment_text: str, video_title: str) -> str | None:
        template = PROMPT_PATH.read_text()
        prompt = fill_template(template, comment_text=comment_text, video_title=video_title)

        response = self.claude.messages.create(
            model=settings.claude_model_fast,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.lower() == "null":
            return None
        return text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=30))
    def _post_reply(self, thread_id: str, reply_text: str) -> None:
        self.youtube.comments().insert(
            part="snippet",
            body={
                "snippet": {
                    "parentId": thread_id,
                    "textOriginal": reply_text,
                }
            },
        ).execute()
