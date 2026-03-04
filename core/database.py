"""SQLite database layer for Task Manager."""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Optional

from config import DB_PATH

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    description      TEXT DEFAULT '',
    due_datetime     TEXT,
    priority         TEXT DEFAULT 'Medium',
    completed        INTEGER DEFAULT 0,
    snoozed_until    TEXT,
    last_notified_at TEXT,
    created_at       TEXT NOT NULL
);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create/migrate the database schema."""
    try:
        with _get_conn() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    except sqlite3.Error as exc:
        logger.exception("Failed to initialise database: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# CRUD helpers
# ─────────────────────────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def create_task(
    title: str,
    description: str = "",
    due_datetime: Optional[str] = None,
    priority: str = "Medium",
) -> int:
    """Insert a new task and return its id."""
    sql = """
        INSERT INTO tasks (title, description, due_datetime, priority, completed,
                           snoozed_until, last_notified_at, created_at)
        VALUES (?, ?, ?, ?, 0, NULL, NULL, ?)
    """
    try:
        with _get_conn() as conn:
            cur = conn.execute(sql, (title, description, due_datetime, priority, _now_iso()))
            conn.commit()
            new_id = cur.lastrowid
            logger.debug("Created task id=%s title=%r", new_id, title)
            return new_id
    except sqlite3.Error as exc:
        logger.exception("create_task failed: %s", exc)
        raise


def update_task(
    task_id: int,
    title: str,
    description: str,
    due_datetime: Optional[str],
    priority: str,
) -> None:
    """Update mutable fields on a task."""
    sql = """
        UPDATE tasks SET title=?, description=?, due_datetime=?, priority=?
        WHERE id=?
    """
    try:
        with _get_conn() as conn:
            conn.execute(sql, (title, description, due_datetime, priority, task_id))
            conn.commit()
            logger.debug("Updated task id=%s", task_id)
    except sqlite3.Error as exc:
        logger.exception("update_task failed: %s", exc)
        raise


def delete_task(task_id: int) -> None:
    """Delete a task by id."""
    try:
        with _get_conn() as conn:
            conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            logger.debug("Deleted task id=%s", task_id)
    except sqlite3.Error as exc:
        logger.exception("delete_task failed: %s", exc)
        raise


def mark_complete(task_id: int, completed: bool = True) -> None:
    try:
        with _get_conn() as conn:
            conn.execute("UPDATE tasks SET completed=? WHERE id=?", (int(completed), task_id))
            conn.commit()
            logger.debug("Task id=%s completed=%s", task_id, completed)
    except sqlite3.Error as exc:
        logger.exception("mark_complete failed: %s", exc)
        raise


def set_snoozed_until(task_id: int, dt_iso: str) -> None:
    try:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET snoozed_until=?, last_notified_at=? WHERE id=?",
                (dt_iso, _now_iso(), task_id),
            )
            conn.commit()
            logger.debug("Snoozed task id=%s until %s", task_id, dt_iso)
    except sqlite3.Error as exc:
        logger.exception("set_snoozed_until failed: %s", exc)
        raise


def set_last_notified(task_id: int) -> None:
    try:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET last_notified_at=? WHERE id=?",
                (_now_iso(), task_id),
            )
            conn.commit()
            logger.debug("Updated last_notified_at for task id=%s", task_id)
    except sqlite3.Error as exc:
        logger.exception("set_last_notified failed: %s", exc)
        raise


def get_all_tasks() -> List[dict]:
    """Return all tasks as a list of dicts."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.exception("get_all_tasks failed: %s", exc)
        return []
