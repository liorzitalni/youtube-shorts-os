"""
Database connection and query utilities.
Single source of truth for all DB access.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from loguru import logger

from config.settings import settings


def get_db_path() -> Path:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def initialize_db() -> None:
    """Run schema.sql to create/migrate all tables."""
    schema_path = Path("data/schema.sql")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with get_connection() as conn:
        conn.executescript(schema_path.read_text())
    logger.info("Database initialized.")


@contextmanager
def get_connection():
    """Context manager yielding a configured SQLite connection."""
    conn = sqlite3.connect(
        str(get_db_path()),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetchone(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(sql, params).fetchone()


def fetchall(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql: str, params: tuple = ()) -> int:
    """Execute a write statement, return lastrowid."""
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def executemany(sql: str, params_list: list[tuple]) -> None:
    with get_connection() as conn:
        conn.executemany(sql, params_list)


def enqueue_job(
    job_type: str,
    payload: dict,
    priority: int = 5,
    run_after: str | None = None,
) -> int:
    """Add a job to the queue. Returns job ID."""
    import json
    return execute(
        """
        INSERT INTO jobs (job_type, payload, priority, run_after)
        VALUES (?, ?, ?, ?)
        """,
        (job_type, json.dumps(payload), priority, run_after),
    )


def claim_next_job(job_type: str | None = None) -> dict | None:
    """
    Atomically claim the next pending job.
    Returns None if queue is empty.
    """
    import json

    type_filter = "AND job_type = ?" if job_type else ""
    params: tuple[Any, ...] = (job_type,) if job_type else ()

    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT * FROM jobs
            WHERE status = 'pending'
              AND attempts < max_attempts
              AND (run_after IS NULL OR run_after <= datetime('now'))
              {type_filter}
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
            """,
            params,
        ).fetchone()

        if not row:
            return None

        conn.execute(
            """
            UPDATE jobs
            SET status = 'running', started_at = datetime('now'), attempts = attempts + 1
            WHERE id = ?
            """,
            (row["id"],),
        )
        job = dict(row)
        job["status"] = "running"   # reflect the update we just applied
        job["payload"] = json.loads(job["payload"])
        return job


def complete_job(job_id: int, result: dict | None = None) -> None:
    import json
    execute(
        """
        UPDATE jobs
        SET status = 'complete', completed_at = datetime('now'), result = ?
        WHERE id = ?
        """,
        (json.dumps(result or {}), job_id),
    )


def fail_job(job_id: int, error: str) -> None:
    execute(
        """
        UPDATE jobs
        SET status = 'failed', error_message = ?, completed_at = datetime('now')
        WHERE id = ?
        """,
        (error, job_id),
    )
