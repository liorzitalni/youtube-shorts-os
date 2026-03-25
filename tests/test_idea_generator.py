"""
Tests for the idea generator module.
Claude API calls are mocked — no API key required.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from db.connection import fetchall
from modules.ideas.idea_generator import IdeaGenerator, backlog_count, needs_refill


def make_mock_claude_response(text: str) -> MagicMock:
    """Build a mock Anthropic response object."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=text)]
    return mock_response


class TestIdeaGenerator:
    def test_generates_and_saves_ideas(self, mock_claude_ideas_response):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.return_value = make_mock_claude_response(
                mock_claude_ideas_response
            )

            gen = IdeaGenerator()
            gen.client = mock_client
            ideas = gen.run(count=2)

        assert len(ideas) == 2
        assert ideas[0]["title"] == "The Reason You Can't Stop Thinking About What People Think of You"
        assert ideas[1]["topic_cluster"] == "dark_psychology"

        # Verify persisted to DB
        db_ideas = fetchall("SELECT * FROM ideas WHERE status = 'backlog'")
        assert len(db_ideas) == 2

    def test_saves_required_fields(self, mock_claude_ideas_response):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.return_value = make_mock_claude_response(
                mock_claude_ideas_response
            )
            gen = IdeaGenerator()
            gen.client = mock_client
            ideas = gen.run(count=2)

        idea = ideas[0]
        for field in ["title", "topic", "topic_cluster", "hook_angle", "hook_style",
                      "emotional_trigger", "why_watch", "originality_score", "predicted_score"]:
            assert field in idea, f"Missing field: {field}"

    def test_handles_malformed_json_gracefully(self):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.return_value = make_mock_claude_response(
                "Sorry, I cannot generate those ideas."  # non-JSON response
            )
            gen = IdeaGenerator()
            gen.client = mock_client
            ideas = gen.run(count=5)

        assert ideas == []
        db_ideas = fetchall("SELECT * FROM ideas")
        assert len(db_ideas) == 0

    def test_handles_json_in_code_fence(self, mock_claude_ideas_response):
        fenced = f"```json\n{mock_claude_ideas_response}\n```"
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.return_value = make_mock_claude_response(fenced)
            gen = IdeaGenerator()
            gen.client = mock_client
            ideas = gen.run(count=2)

        assert len(ideas) == 2


class TestBacklogManagement:
    def test_backlog_count_empty(self):
        assert backlog_count() == 0

    def test_backlog_count_with_ideas(self, mock_claude_ideas_response):
        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.return_value = make_mock_claude_response(
                mock_claude_ideas_response
            )
            gen = IdeaGenerator()
            gen.client = mock_client
            gen.run(count=2)

        assert backlog_count() == 2

    def test_needs_refill_when_empty(self):
        assert needs_refill() is True

    def test_needs_refill_false_when_sufficient(self, mock_claude_ideas_response):
        from config.settings import settings
        # Generate enough ideas to exceed threshold
        big_batch = json.dumps([
            {
                "title": f"Idea {i}",
                "topic": "Test topic",
                "topic_cluster": "cognitive_bias",
                "hook_angle": "Test angle",
                "hook_style": "question",
                "emotional_trigger": "curiosity",
                "why_watch": "Test",
                "originality_score": 0.7,
                "predicted_score": 0.7,
            }
            for i in range(settings.idea_backlog_min + 2)
        ])

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.return_value = make_mock_claude_response(big_batch)
            gen = IdeaGenerator()
            gen.client = mock_client
            gen.run(count=settings.idea_backlog_min + 2)

        assert needs_refill() is False
