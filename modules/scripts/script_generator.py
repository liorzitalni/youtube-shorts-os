"""
Script Generator — takes an idea from the backlog and produces a full script.
Includes main script + 3 hook variants.
"""

from __future__ import annotations

import json
from pathlib import Path

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.template_utils import fill_template
from db.connection import execute, fetchone, fetchall


SCRIPT_PROMPT_PATH = Path("config/prompts/script_generation.md")
HOOK_PROMPT_PATH = Path("config/prompts/hook_variants.md")


class ScriptGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(self, idea_id: int) -> dict | None:
        """Generate a script for the given idea. Returns script dict or None on failure."""
        idea = fetchone("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        if not idea:
            logger.error(f"Idea {idea_id} not found.")
            return None

        idea = dict(idea)
        logger.info(f"Generating script for idea {idea_id}: {idea['title']}")

        # Generate main script
        script_prompt = self._build_script_prompt(idea)
        script_raw = self._call_claude(script_prompt, model=settings.claude_model_smart)
        script_data = self._parse_json(script_raw, "script")
        if not script_data:
            return None

        # Save script
        script_id = self._save_script(idea_id, script_data)
        if not script_id:
            return None

        # Generate hook variants
        hook_prompt = self._build_hook_prompt(idea, script_data["hook_text"])
        hook_raw = self._call_claude(hook_prompt, model=settings.claude_model_fast)
        hook_variants = self._parse_json(hook_raw, "hooks")
        if hook_variants:
            self._save_hooks(script_id, hook_variants)

        # Update idea status
        execute(
            "UPDATE ideas SET status = 'scripted', updated_at = datetime('now') WHERE id = ?",
            (idea_id,),
        )

        logger.info(f"Script {script_id} created for idea {idea_id}.")
        return {"script_id": script_id, "idea_id": idea_id, **script_data}

    def _build_script_prompt(self, idea: dict) -> str:
        template = SCRIPT_PROMPT_PATH.read_text()
        return fill_template(template, **idea)

    def _build_hook_prompt(self, idea: dict, original_hook: str) -> str:
        template = HOOK_PROMPT_PATH.read_text()
        return fill_template(
            template,
            title=idea["title"],
            topic=idea["topic"],
            original_hook=original_hook,
            emotional_trigger=idea["emotional_trigger"],
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_claude(self, prompt: str, model: str) -> str:
        response = self.client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _parse_json(self, raw: str, label: str) -> dict | list | None:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {label} response: {e}\nRaw: {raw[:400]}")
            return None

    def _save_script(self, idea_id: int, data: dict) -> int | None:
        onscreen = json.dumps(data.get("onscreen_segments", []))
        try:
            return execute(
                """
                INSERT INTO scripts
                    (idea_id, hook_text, hook_onscreen, body_text, close_text,
                     full_script, onscreen_segments, visual_notes, music_mood,
                     estimated_duration, word_count, model_used, prompt_version, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')
                """,
                (
                    idea_id,
                    data.get("hook_text", ""),
                    data.get("hook_onscreen", ""),
                    data.get("body_text", ""),
                    data.get("close_text", ""),
                    data.get("full_script", ""),
                    onscreen,
                    data.get("visual_notes", ""),
                    data.get("music_mood", ""),
                    data.get("estimated_duration", 0),
                    data.get("word_count", 0),
                    settings.claude_model_smart,
                    "v1",
                ),
            )
        except Exception as e:
            logger.error(f"Failed to save script for idea {idea_id}: {e}")
            return None

    def _save_hooks(self, script_id: int, variants: list) -> None:
        for v in variants:
            try:
                execute(
                    """
                    INSERT INTO hook_variants (script_id, variant, style, text, onscreen)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        script_id,
                        v.get("variant", 0),
                        v.get("style", ""),
                        v.get("text", ""),
                        v.get("onscreen", ""),
                    ),
                )
            except Exception as e:
                logger.warning(f"Failed to save hook variant: {e}")


def get_scripts_pending_review() -> list[dict]:
    rows = fetchall(
        """
        SELECT s.*, i.title as idea_title, i.topic_cluster
        FROM scripts s
        JOIN ideas i ON i.id = s.idea_id
        WHERE s.status = 'draft'
        ORDER BY s.created_at ASC
        """
    )
    return [dict(r) for r in rows]


def approve_script(script_id: int) -> None:
    execute(
        "UPDATE scripts SET status = 'approved', updated_at = datetime('now') WHERE id = ?",
        (script_id,),
    )


def reject_script(script_id: int, reason: str) -> None:
    execute(
        "UPDATE scripts SET status = 'rejected', review_notes = ?, updated_at = datetime('now') WHERE id = ?",
        (reason, script_id),
    )
