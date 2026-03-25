"""
Tests for database connection, job queue, and core query utilities.
"""

import json

import pytest

from db.connection import (
    claim_next_job,
    complete_job,
    enqueue_job,
    execute,
    fail_job,
    fetchall,
    fetchone,
)


class TestBasicQueries:
    def test_fetchall_returns_list(self):
        rows = fetchall("SELECT * FROM content_patterns")
        assert isinstance(rows, list)

    def test_seed_patterns_present(self):
        rows = fetchall("SELECT * FROM content_patterns WHERE pattern_type = 'hook_style'")
        assert len(rows) == 4
        names = {r["pattern_name"] for r in rows}
        assert "bold_claim_hook" in names
        assert "question_hook" in names

    def test_fetchone_returns_none_for_missing(self):
        row = fetchone("SELECT * FROM ideas WHERE id = 99999")
        assert row is None

    def test_execute_returns_lastrowid(self):
        row_id = execute(
            "INSERT INTO ideas (title, topic, topic_cluster, hook_angle, hook_style, emotional_trigger, why_watch) VALUES (?,?,?,?,?,?,?)",
            ("Test Idea", "Test topic", "cognitive_bias", "Test angle", "question", "curiosity", "Test why"),
        )
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_rollback_on_error(self):
        """Verify that a failed transaction doesn't leave partial state."""
        initial = fetchall("SELECT COUNT(*) as n FROM ideas")[0]["n"]
        with pytest.raises(Exception):
            execute("INSERT INTO nonexistent_table (col) VALUES (?)", ("val",))
        after = fetchall("SELECT COUNT(*) as n FROM ideas")[0]["n"]
        assert after == initial


class TestJobQueue:
    def test_enqueue_creates_job(self):
        job_id = enqueue_job("generate_ideas", {"count": 10})
        assert isinstance(job_id, int)

        job = fetchone("SELECT * FROM jobs WHERE id = ?", (job_id,))
        assert job is not None
        assert job["status"] == "pending"
        assert job["job_type"] == "generate_ideas"
        assert json.loads(job["payload"]) == {"count": 10}

    def test_claim_next_job(self):
        enqueue_job("render_video", {"production_id": 42})
        job = claim_next_job()
        assert job is not None
        assert job["job_type"] == "render_video"
        assert job["payload"]["production_id"] == 42
        assert job["status"] == "running"

    def test_claim_returns_none_when_empty(self):
        job = claim_next_job(job_type="nonexistent_type")
        assert job is None

    def test_complete_job(self):
        job_id = enqueue_job("test_job", {})
        job = claim_next_job()
        complete_job(job["id"], result={"done": True})

        updated = fetchone("SELECT * FROM jobs WHERE id = ?", (job_id,))
        assert updated["status"] == "complete"
        assert json.loads(updated["result"]) == {"done": True}

    def test_fail_job(self):
        enqueue_job("failing_job", {})
        job = claim_next_job()
        fail_job(job["id"], error="Connection refused")

        updated = fetchone("SELECT * FROM jobs WHERE id = ?", (job["id"],))
        assert updated["status"] == "failed"
        assert "Connection refused" in updated["error_message"]

    def test_priority_ordering(self):
        enqueue_job("low_priority", {}, priority=9)
        enqueue_job("high_priority", {}, priority=1)

        job = claim_next_job()
        assert job["job_type"] == "high_priority"
