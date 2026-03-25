"""
Shared test fixtures.
All tests use an isolated in-memory SQLite DB so they never touch the real DB.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set dummy env vars before any imports that need them
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-anthropic")
os.environ.setdefault("ELEVENLABS_API_KEY", "test-key-elevenlabs")
os.environ.setdefault("ELEVENLABS_VOICE_ID", "test-voice-id")
os.environ.setdefault("YOUTUBE_CHANNEL_ID", "UC_test_channel")
os.environ.setdefault("DATABASE_PATH", ":memory:")


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """
    Each test gets a fresh SQLite DB in a temp file.
    We monkeypatch get_db_path to point at the temp file.
    """
    db_file = tmp_path / "test_shorts_os.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))

    # Reinitialize settings with the new DB path
    import importlib
    import config.settings as s_module
    importlib.reload(s_module)

    import db.connection as db_module
    importlib.reload(db_module)

    # Initialize schema in the fresh DB
    from db.connection import initialize_db
    initialize_db()

    yield db_file


@pytest.fixture
def sample_idea():
    """A realistic idea dict for testing."""
    from db.connection import execute, fetchone
    idea_id = execute(
        """
        INSERT INTO ideas
            (title, topic, topic_cluster, hook_angle, hook_style,
             emotional_trigger, why_watch, originality_score, predicted_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Why Your Brain Replays Embarrassing Memories",
            "Involuntary memory recall",
            "cognitive_bias",
            "The brain's negativity bias keeps embarrassing moments fresh",
            "question",
            "curiosity",
            "Understand why this happens and how to stop it",
            0.8,
            0.82,
        ),
    )
    return dict(fetchone("SELECT * FROM ideas WHERE id = ?", (idea_id,)))


@pytest.fixture
def mock_claude_ideas_response():
    """Realistic Claude response for idea generation."""
    return json.dumps([
        {
            "title": "The Reason You Can't Stop Thinking About What People Think of You",
            "topic": "Social anxiety and self-monitoring",
            "topic_cluster": "cognitive_bias",
            "hook_angle": "Evolution wired you to obsess over social judgment",
            "hook_style": "bold_claim",
            "emotional_trigger": "validation",
            "why_watch": "Understand why this happens and how to turn it off",
            "originality_score": 0.78,
            "predicted_score": 0.81,
        },
        {
            "title": "Why People Who Never Get Angry Are Actually Dangerous",
            "topic": "Emotional suppression psychology",
            "topic_cluster": "dark_psychology",
            "hook_angle": "Chronic anger suppression is a warning sign, not a virtue",
            "hook_style": "bold_claim",
            "emotional_trigger": "surprise",
            "why_watch": "Recognize this pattern in people around you",
            "originality_score": 0.85,
            "predicted_score": 0.87,
        },
    ])


@pytest.fixture
def mock_claude_script_response():
    """Realistic Claude response for script generation."""
    return json.dumps({
        "hook_text": "Your brain is running a program right now that you never agreed to install.",
        "hook_onscreen": "You didn't agree to this.",
        "body_text": "Every time you walk into a room, your brain automatically scans for social threats. Who looks displeased. Who isn't making eye contact. This isn't anxiety. This is evolution. For 200,000 years, being rejected from your tribe meant death. So your brain evolved to monitor social signals obsessively. The problem is, the modern world doesn't work like that anymore. Your boss's bad mood isn't a survival threat. But your brain doesn't know that.",
        "close_text": "The question isn't why you care what people think. The question is — can you tell the difference between a real threat and a ghost?",
        "full_script": "Your brain is running a program right now that you never agreed to install. Every time you walk into a room, your brain automatically scans for social threats. Who looks displeased. Who isn't making eye contact. This isn't anxiety. This is evolution. For 200,000 years, being rejected from your tribe meant death. So your brain evolved to monitor social signals obsessively. The problem is, the modern world doesn't work like that anymore. Your boss's bad mood isn't a survival threat. But your brain doesn't know that. The question isn't why you care what people think. The question is — can you tell the difference between a real threat and a ghost?",
        "onscreen_segments": [
            {"text": "You didn't agree to this.", "beat": "Over the hook line"},
            {"text": "200,000 years", "beat": "When mentioning evolution timeline"},
            {"text": "Rejection = death", "beat": "Tribe rejection line"},
            {"text": "Your brain doesn't know.", "beat": "Modern world mismatch"},
            {"text": "Real threat or ghost?", "beat": "Closing question"},
        ],
        "visual_notes": "Dark, moody. Open on empty room, someone entering. Brain scan imagery. Tribal fire imagery. Cut to modern office. End on person alone, thoughtful.",
        "music_mood": "dark ambient",
        "estimated_duration": 57,
        "word_count": 138,
    })


@pytest.fixture
def mock_claude_hooks_response():
    """Realistic Claude response for hook variants."""
    return json.dumps([
        {
            "variant": 1,
            "style": "question",
            "text": "Why do you obsess over what people think of you, even when you know it doesn't matter?",
            "onscreen": "Why do you obsess?",
        },
        {
            "variant": 2,
            "style": "stat",
            "text": "Studies show humans check for social approval every 6 minutes on average.",
            "onscreen": "Every 6 minutes.",
        },
        {
            "variant": 3,
            "style": "bold_claim",
            "text": "Your brain is running a program you never agreed to install.",
            "onscreen": "You didn't agree to this.",
        },
    ])


@pytest.fixture
def mock_claude_metadata_response():
    """Realistic Claude response for metadata generation."""
    return json.dumps({
        "titles": [
            "Why Your Brain Won't Stop Judging You",
            "The Evolutionary Reason You Care What Others Think",
            "Your Brain Has a Social Threat Detector (And It's Broken)",
        ],
        "description": "Your obsession with what others think isn't weakness — it's evolution. Here's what's actually happening in your brain. Follow for more psychology insights.",
        "hashtags": ["#Shorts", "#psychology", "#mindset", "#cognitivebiases", "#humanpsychology"],
        "tags": ["psychology", "human behavior", "cognitive bias", "social anxiety", "brain science"],
        "category": "Education",
        "packaging_notes": "Strong curiosity gap in primary title. Reframes a common negative (caring what people think) as evolutionary rather than shameful.",
    })
