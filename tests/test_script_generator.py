"""
Tests for script generator module.
Claude API calls are mocked — no API key required.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from db.connection import execute, fetchall, fetchone
from modules.scripts.script_generator import (
    ScriptGenerator,
    approve_script,
    get_scripts_pending_review,
    reject_script,
)


def make_mock_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


class TestScriptGenerator:
    def test_generates_script_for_idea(
        self, sample_idea, mock_claude_script_response, mock_claude_hooks_response
    ):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            # First call = script, second call = hooks
            mock_client.messages.create.side_effect = [
                make_mock_response(mock_claude_script_response),
                make_mock_response(mock_claude_hooks_response),
            ]

            gen = ScriptGenerator()
            gen.client = mock_client
            result = gen.run(sample_idea["id"])

        assert result is not None
        assert "script_id" in result
        assert "hook_text" in result
        assert result["word_count"] == 138

    def test_script_saved_to_db(
        self, sample_idea, mock_claude_script_response, mock_claude_hooks_response
    ):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.side_effect = [
                make_mock_response(mock_claude_script_response),
                make_mock_response(mock_claude_hooks_response),
            ]
            gen = ScriptGenerator()
            gen.client = mock_client
            result = gen.run(sample_idea["id"])

        script = fetchone("SELECT * FROM scripts WHERE id = ?", (result["script_id"],))
        assert script is not None
        assert script["status"] == "draft"
        assert script["idea_id"] == sample_idea["id"]
        assert script["hook_text"].startswith("Your brain is running")

    def test_hook_variants_saved(
        self, sample_idea, mock_claude_script_response, mock_claude_hooks_response
    ):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.side_effect = [
                make_mock_response(mock_claude_script_response),
                make_mock_response(mock_claude_hooks_response),
            ]
            gen = ScriptGenerator()
            gen.client = mock_client
            result = gen.run(sample_idea["id"])

        variants = fetchall(
            "SELECT * FROM hook_variants WHERE script_id = ?", (result["script_id"],)
        )
        assert len(variants) == 3
        styles = {v["style"] for v in variants}
        assert styles == {"question", "stat", "bold_claim"}

    def test_idea_status_updated_to_scripted(
        self, sample_idea, mock_claude_script_response, mock_claude_hooks_response
    ):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.side_effect = [
                make_mock_response(mock_claude_script_response),
                make_mock_response(mock_claude_hooks_response),
            ]
            gen = ScriptGenerator()
            gen.client = mock_client
            gen.run(sample_idea["id"])

        updated_idea = fetchone("SELECT * FROM ideas WHERE id = ?", (sample_idea["id"],))
        assert updated_idea["status"] == "scripted"

    def test_returns_none_for_invalid_idea(self):
        with patch("anthropic.Anthropic") as MockAnthropic:
            gen = ScriptGenerator()
            gen.client = MockAnthropic.return_value
            result = gen.run(idea_id=99999)

        assert result is None

    def test_handles_malformed_script_response(self, sample_idea):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.return_value = make_mock_response(
                "I cannot write this script."
            )
            gen = ScriptGenerator()
            gen.client = mock_client
            result = gen.run(sample_idea["id"])

        assert result is None


class TestScriptReview:
    def _create_draft_script(self, idea_id: int) -> int:
        return execute(
            """
            INSERT INTO scripts (idea_id, hook_text, body_text, close_text, full_script,
                                 estimated_duration, word_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')
            """,
            (idea_id, "Test hook", "Test body", "Test close", "Test hook Test body Test close", 45, 100),
        )

    def test_approve_script(self, sample_idea):
        script_id = self._create_draft_script(sample_idea["id"])
        approve_script(script_id)

        script = fetchone("SELECT status FROM scripts WHERE id = ?", (script_id,))
        assert script["status"] == "approved"

    def test_reject_script(self, sample_idea):
        script_id = self._create_draft_script(sample_idea["id"])
        reject_script(script_id, reason="Hook too weak")

        script = fetchone("SELECT status, review_notes FROM scripts WHERE id = ?", (script_id,))
        assert script["status"] == "rejected"
        assert "Hook too weak" in script["review_notes"]

    def test_get_scripts_pending_review(self, sample_idea):
        self._create_draft_script(sample_idea["id"])
        pending = get_scripts_pending_review()

        assert len(pending) == 1
        assert pending[0]["idea_title"] == sample_idea["title"]

    def test_approved_not_in_pending_review(self, sample_idea):
        script_id = self._create_draft_script(sample_idea["id"])
        approve_script(script_id)

        pending = get_scripts_pending_review()
        assert len(pending) == 0
