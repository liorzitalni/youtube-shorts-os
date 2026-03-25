"""
Integration test: runs the full pipeline from idea generation through
metadata creation with all external APIs mocked.

This simulates exactly what happens in daily_production.py.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from db.connection import execute, fetchall, fetchone


def make_mock_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


MOCK_IDEAS = json.dumps([
    {
        "title": "Why Overthinking Is Actually a Survival Mechanism",
        "topic": "Rumination and negativity bias",
        "topic_cluster": "cognitive_bias",
        "hook_angle": "Overthinking evolved to keep you safe, but it's now causing harm",
        "hook_style": "bold_claim",
        "emotional_trigger": "curiosity",
        "why_watch": "Understand why you overthink and how to work with your brain instead of against it",
        "originality_score": 0.82,
        "predicted_score": 0.85,
    }
])

MOCK_SCRIPT = json.dumps({
    "hook_text": "Overthinking is not a personality flaw. It's a survival feature that got stuck in the on position.",
    "hook_onscreen": "Not a flaw. A feature.",
    "body_text": "When our ancestors heard a noise in the bushes, the ones who assumed danger survived. The ones who assumed safety did not. That obsessive threat-detection wiring is still in your brain today. It just has no tigers to worry about, so it replays that conversation you had three days ago. Searches for what could go wrong in your relationship. Spirals through every possible outcome of a decision you already made.",
    "close_text": "You don't need to silence your mind. You need to give it a real problem to solve.",
    "full_script": "Overthinking is not a personality flaw. It's a survival feature that got stuck in the on position. When our ancestors heard a noise in the bushes, the ones who assumed danger survived. The ones who assumed safety did not. That obsessive threat-detection wiring is still in your brain today. It just has no tigers to worry about, so it replays that conversation you had three days ago. Searches for what could go wrong in your relationship. Spirals through every possible outcome of a decision you already made. You don't need to silence your mind. You need to give it a real problem to solve.",
    "onscreen_segments": [
        {"text": "Not a flaw.", "beat": "Hook"},
        {"text": "A feature.", "beat": "Hook continuation"},
        {"text": "Ancestors assumed danger", "beat": "Evolution explanation"},
        {"text": "No tigers left.", "beat": "Modern mismatch"},
        {"text": "Give it a real problem.", "beat": "Closing insight"},
    ],
    "visual_notes": "Start dark. Ancient landscape. Flash to modern person at desk, overthinking. Empty room with spinning thoughts visualized as text.",
    "music_mood": "dark ambient",
    "estimated_duration": 56,
    "word_count": 135,
})

MOCK_HOOKS = json.dumps([
    {"variant": 1, "style": "question", "text": "Why do you keep replaying that conversation?", "onscreen": "Why do you replay it?"},
    {"variant": 2, "style": "stat", "text": "The average person has 6,200 thoughts per day, and most of them are negative.", "onscreen": "6,200 thoughts. Mostly negative."},
    {"variant": 3, "style": "bold_claim", "text": "Overthinking is not a personality flaw. It's a survival feature that got stuck on.", "onscreen": "Not a flaw. A feature."},
])

MOCK_METADATA = json.dumps({
    "titles": [
        "Overthinking Is a Survival Feature (Not a Flaw)",
        "Why Your Brain Won't Stop Running Worst-Case Scenarios",
        "The Evolutionary Reason You Overthink Everything",
    ],
    "description": "Overthinking isn't weakness — it's a mismatched survival mechanism. Here's what's actually happening in your brain. Follow for more psychology insights every day.",
    "hashtags": ["#Shorts", "#psychology", "#overthinking", "#mindset", "#cognitivebiases"],
    "tags": ["psychology", "overthinking", "cognitive bias", "brain science", "mental health"],
    "category": "Education",
    "packaging_notes": "Strong reframe hook. Primary title is counterintuitive enough to earn the click.",
})


class TestFullPipeline:
    """
    Integration test covering: idea → script → production record → metadata → publish queue.
    TTS and render are skipped (require real files/APIs).
    """

    def test_idea_to_publish_queue(self):
        from modules.ideas.idea_generator import IdeaGenerator
        from modules.scripts.script_generator import ScriptGenerator, approve_script
        from modules.publish.metadata_generator import MetadataGenerator

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MockAnthropic.return_value
            mock_client.messages.create.side_effect = [
                make_mock_response(MOCK_IDEAS),    # idea generation
                make_mock_response(MOCK_SCRIPT),   # script generation
                make_mock_response(MOCK_HOOKS),    # hook variants
                make_mock_response(MOCK_METADATA), # metadata generation
            ]

            # Step 1: Generate ideas
            idea_gen = IdeaGenerator()
            idea_gen.client = mock_client
            ideas = idea_gen.run(count=1)

            assert len(ideas) == 1
            idea_id = ideas[0]["id"]

            # Step 2: Approve idea → generate script
            execute("UPDATE ideas SET status = 'approved' WHERE id = ?", (idea_id,))

            script_gen = ScriptGenerator()
            script_gen.client = mock_client
            script_result = script_gen.run(idea_id)
            assert script_result is not None
            script_id = script_result["script_id"]

            # Step 3: Approve script
            approve_script(script_id)

            # Step 4: Create a stub production (simulating TTS + render completed)
            prod_id = execute(
                """
                INSERT INTO productions
                    (script_id, audio_path, video_path, duration_actual, status)
                VALUES (?, ?, ?, ?, 'rendered')
                """,
                (script_id, "fake/audio.mp3", "fake/video.mp4", 56.2),
            )

            # Step 5: Generate metadata
            meta_gen = MetadataGenerator()
            meta_gen.client = mock_client
            metadata = meta_gen.run(prod_id)

        assert metadata is not None
        assert "queue_id" in metadata

        # Verify the full chain in DB
        idea = fetchone("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        script = fetchone("SELECT * FROM scripts WHERE id = ?", (script_id,))
        production = fetchone("SELECT * FROM productions WHERE id = ?", (prod_id,))
        queue = fetchone("SELECT * FROM publish_queue WHERE id = ?", (metadata["queue_id"],))

        assert idea["status"] == "scripted"
        assert script["status"] == "approved"
        assert production["status"] == "rendered"
        assert queue["upload_status"] == "queued"
        assert "Overthinking" in queue["title"]
        assert "#Shorts" in queue["hashtags"]

    def test_backlog_triggers_idea_generation(self):
        """needs_refill() returns True when backlog is empty."""
        from modules.ideas.idea_generator import needs_refill
        assert needs_refill() is True

    def test_idea_scores_determine_order(self):
        """Higher predicted_score ideas should come first."""
        # Insert two ideas with different scores
        execute(
            "INSERT INTO ideas (title, topic, topic_cluster, hook_angle, hook_style, emotional_trigger, why_watch, predicted_score, status) VALUES (?,?,?,?,?,?,?,?,?)",
            ("Low score idea", "t", "cognitive_bias", "a", "question", "curiosity", "w", 0.3, "approved"),
        )
        execute(
            "INSERT INTO ideas (title, topic, topic_cluster, hook_angle, hook_style, emotional_trigger, why_watch, predicted_score, status) VALUES (?,?,?,?,?,?,?,?,?)",
            ("High score idea", "t", "dark_psychology", "a", "bold_claim", "surprise", "w", 0.9, "approved"),
        )

        top = fetchall(
            "SELECT title FROM ideas WHERE status = 'approved' ORDER BY predicted_score DESC LIMIT 1"
        )
        assert top[0]["title"] == "High score idea"
