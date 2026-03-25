"""
Metadata Generator — calls Claude to produce title, description, hashtags.
"""

from __future__ import annotations

import json
from pathlib import Path

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.template_utils import fill_template
from db.connection import execute, fetchone


PROMPT_PATH = Path("config/prompts/metadata_generation.md")


class MetadataGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(self, production_id: int) -> dict | None:
        """Generate metadata for a production and insert into publish_queue."""
        production = fetchone("SELECT * FROM productions WHERE id = ?", (production_id,))
        if not production:
            logger.error(f"Production {production_id} not found.")
            return None

        script = fetchone("SELECT * FROM scripts WHERE id = ?", (production["script_id"],))
        if not script:
            return None
        script = dict(script)

        idea = fetchone("SELECT * FROM ideas WHERE id = ?", (script["idea_id"],))
        if not idea:
            return None
        idea = dict(idea)

        logger.info(f"Generating metadata for production {production_id}...")

        prompt = self._build_prompt(script, idea)
        raw = self._call_claude(prompt)
        metadata = self._parse(raw)
        if not metadata:
            return None

        queue_id = self._save_to_queue(production_id, metadata)
        logger.info(f"Publish queue entry {queue_id} created for production {production_id}.")
        return {"queue_id": queue_id, **metadata}

    def _build_prompt(self, script: dict, idea: dict) -> str:
        template = PROMPT_PATH.read_text()
        excerpt = script.get("full_script", "")[:400]
        return fill_template(
            template,
            hook_text=script["hook_text"],
            script_excerpt=excerpt,
            topic_cluster=idea["topic_cluster"],
            emotional_trigger=idea.get("emotional_trigger", ""),
            hook_angle=idea.get("hook_angle", ""),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_claude(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=settings.claude_model_fast,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _parse(self, raw: str) -> dict | None:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata: {e}\nRaw: {raw[:400]}")
            return None

    def _save_to_queue(self, production_id: int, metadata: dict) -> int:
        titles = metadata.get("titles", ["Untitled"])
        primary_title = titles[0] if titles else "Untitled"

        return execute(
            """
            INSERT INTO publish_queue
                (production_id, title, description, hashtags, tags, title_variants, pinned_comment, upload_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'queued')
            """,
            (
                production_id,
                primary_title,
                metadata.get("description", ""),
                json.dumps(metadata.get("hashtags", [])),
                json.dumps(metadata.get("tags", [])),
                json.dumps(titles),
                metadata.get("pinned_comment", ""),
            ),
        )
