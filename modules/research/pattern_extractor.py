"""
Pattern Extractor — uses Claude to analyze competitor videos and extract
hook styles, topic clusters, visual styles, and other patterns.
Updates competitor_videos and content_patterns tables.
"""

import json
from pathlib import Path

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from db.connection import execute, fetchall


ANALYSIS_PROMPT = """
You are analyzing YouTube Shorts titles and descriptions to extract content patterns.

Analyze these videos from a psychology/human behavior channel:

{videos}

For each video, classify:
- hook_style: question | stat | bold_claim | story | challenge
- hook_text: the likely first line or key hook phrase (infer from title)
- topic_cluster: dark_psychology | cognitive_bias | social_dynamics | self_awareness | relationship_psych | other
- visual_style: stock_footage | animation | text_only | dark_bg | unknown
- cta_type: subscribe | comment | question | none

Return ONLY valid JSON array:
[
  {{
    "youtube_video_id": "...",
    "hook_style": "...",
    "hook_text": "...",
    "topic_cluster": "...",
    "visual_style": "...",
    "cta_type": "..."
  }}
]
"""


class PatternExtractor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(self, batch_size: int = 20) -> int:
        """
        Analyze unprocessed competitor videos in batches.
        Returns count of videos processed.
        """
        unprocessed = fetchall(
            """
            SELECT id, youtube_video_id, title, description, view_count, duration_seconds
            FROM competitor_videos
            WHERE hook_style IS NULL
            ORDER BY view_count DESC
            LIMIT ?
            """,
            (batch_size,),
        )

        if not unprocessed:
            logger.info("No unprocessed competitor videos.")
            return 0

        logger.info(f"Extracting patterns from {len(unprocessed)} videos...")
        results = self._analyze_batch([dict(v) for v in unprocessed])

        updated = 0
        for result in results:
            try:
                execute(
                    """
                    UPDATE competitor_videos
                    SET hook_style = ?, hook_text = ?, topic_cluster = ?,
                        visual_style = ?, cta_type = ?
                    WHERE youtube_video_id = ?
                    """,
                    (
                        result.get("hook_style"),
                        result.get("hook_text"),
                        result.get("topic_cluster"),
                        result.get("visual_style"),
                        result.get("cta_type"),
                        result["youtube_video_id"],
                    ),
                )
                updated += 1
            except Exception as e:
                logger.warning(f"Failed to update video {result.get('youtube_video_id')}: {e}")

        logger.info(f"Pattern extraction complete: {updated} videos updated.")
        self._refresh_pattern_stats()
        return updated

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _analyze_batch(self, videos: list[dict]) -> list[dict]:
        video_summaries = [
            {
                "youtube_video_id": v["youtube_video_id"],
                "title": v["title"],
                "description": (v.get("description") or "")[:200],
                "view_count": v["view_count"],
            }
            for v in videos
        ]

        prompt = ANALYSIS_PROMPT.format(videos=json.dumps(video_summaries, indent=2))

        response = self.client.messages.create(
            model=settings.claude_model_fast,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Failed to parse pattern extraction response: {e}")
            return []

    def _refresh_pattern_stats(self) -> None:
        """Update content_patterns with fresh aggregate stats from competitor data."""
        pattern_types = [
            ("hook_style", "hook_style"),
            ("topic_cluster", "topic_cluster"),
        ]

        for field, pattern_type in pattern_types:
            rows = fetchall(
                f"""
                SELECT {field} as pattern_value,
                       AVG(view_count) as avg_views,
                       COUNT(*) as total,
                       SUM(CASE WHEN view_count > 100000 THEN 1 ELSE 0 END) as high_count
                FROM competitor_videos
                WHERE {field} IS NOT NULL
                GROUP BY {field}
                """
            )
            for row in rows:
                if not row["pattern_value"]:
                    continue
                success_rate = row["high_count"] / max(row["total"], 1)
                execute(
                    """
                    UPDATE content_patterns
                    SET avg_view_count = ?, sample_size = ?, success_rate = ?,
                        last_updated = datetime('now')
                    WHERE pattern_name = ? AND pattern_type = ?
                    """,
                    (
                        int(row["avg_views"] or 0),
                        row["total"],
                        round(success_rate, 4),
                        row["pattern_value"],
                        pattern_type,
                    ),
                )
