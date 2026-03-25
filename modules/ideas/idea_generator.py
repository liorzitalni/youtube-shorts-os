"""
Idea Generator — calls Claude to produce a batch of ranked video ideas.
Ideas are inserted into the `ideas` table with status='backlog'.
"""

import json
from pathlib import Path

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.template_utils import fill_template
from db.connection import fetchall, execute


PROMPT_PATH = Path("config/prompts/idea_generation.md")


class IdeaGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(self, count: int = 10) -> list[dict]:
        """Generate `count` ideas, save to DB, return list of saved idea dicts."""
        logger.info(f"Generating {count} new ideas...")
        context = self._build_context()
        prompt = self._build_prompt(context, count)

        raw = self._call_claude(prompt)
        ideas = self._parse(raw)

        saved = self._save(ideas)
        logger.info(f"Saved {len(saved)} new ideas to backlog.")
        return saved

    def _build_context(self) -> dict:
        # Top-performing clusters
        clusters = fetchall(
            """
            SELECT cp.pattern_name, cp.avg_view_count, cp.success_rate
            FROM content_patterns cp
            WHERE cp.pattern_type = 'topic_cluster' AND cp.is_active = 1
            ORDER BY cp.success_rate DESC
            LIMIT 5
            """
        )

        # Best hook styles
        hooks = fetchall(
            """
            SELECT cp.pattern_name, cp.success_rate
            FROM content_patterns cp
            WHERE cp.pattern_type = 'hook_style' AND cp.is_active = 1
            ORDER BY cp.success_rate DESC
            """
        )

        # Recent ideas (to avoid duplication)
        recent = fetchall(
            """
            SELECT title, topic, hook_angle
            FROM ideas
            WHERE status != 'rejected'
            ORDER BY created_at DESC
            LIMIT 20
            """
        )

        # Performance summary from recent publishes
        perf = fetchall(
            """
            SELECT i.topic_cluster,
                   AVG(ps.avg_view_pct) as avg_retention,
                   AVG(ps.performance_score) as avg_score,
                   COUNT(*) as n
            FROM performance_snapshots ps
            JOIN publish_queue pq ON pq.id = ps.publish_queue_id
            JOIN productions pr ON pr.id = pq.production_id
            JOIN scripts s ON s.id = pr.script_id
            JOIN ideas i ON i.id = s.idea_id
            GROUP BY i.topic_cluster
            ORDER BY avg_score DESC
            """
        )

        return {
            "top_clusters": [dict(r) for r in clusters],
            "top_hook_styles": [dict(r) for r in hooks],
            "recent_ideas": [dict(r) for r in recent],
            "performance_summary": [dict(r) for r in perf],
        }

    def _build_prompt(self, context: dict, count: int) -> str:
        template = PROMPT_PATH.read_text()
        return fill_template(
            template,
            count=count,
            top_clusters=json.dumps(context["top_clusters"], indent=2),
            top_hook_styles=json.dumps(context["top_hook_styles"], indent=2),
            recent_ideas=json.dumps(context["recent_ideas"], indent=2),
            performance_summary=json.dumps(context["performance_summary"], indent=2),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_claude(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=settings.claude_model_fast,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _parse(self, raw: str) -> list[dict]:
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("Expected JSON array")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse idea generation response: {e}\nRaw: {raw[:500]}")
            return []

    def _save(self, ideas: list[dict]) -> list[dict]:
        saved = []
        for idea in ideas:
            try:
                row_id = execute(
                    """
                    INSERT INTO ideas
                        (title, topic, topic_cluster, hook_angle, hook_style,
                         emotional_trigger, why_watch, originality_score, predicted_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        idea.get("title", ""),
                        idea.get("topic", ""),
                        idea.get("topic_cluster", ""),
                        idea.get("hook_angle", ""),
                        idea.get("hook_style", ""),
                        idea.get("emotional_trigger", ""),
                        idea.get("why_watch", ""),
                        idea.get("originality_score", 0.5),
                        idea.get("predicted_score", 0.5),
                    ),
                )
                idea["id"] = row_id
                saved.append(idea)
            except Exception as e:
                logger.warning(f"Failed to save idea '{idea.get('title')}': {e}")
        return saved


def backlog_count() -> int:
    """Return the number of ideas currently in the active backlog."""
    rows = fetchall(
        "SELECT COUNT(*) as n FROM ideas WHERE status IN ('backlog', 'approved')"
    )
    return rows[0]["n"] if rows else 0


def needs_refill() -> bool:
    return backlog_count() < settings.idea_backlog_min
