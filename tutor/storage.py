from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS learners (
            learner_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            preferred_language TEXT NOT NULL,
            mastery_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            skill TEXT NOT NULL,
            correct INTEGER NOT NULL,
            response_text TEXT,
            response_value INTEGER,
            language_detected TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def list_learners(db_path: Path) -> list[tuple[str, str]]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT learner_id, display_name FROM learners ORDER BY display_name").fetchall()
    conn.close()
    return rows


def latest_learner(db_path: Path) -> tuple[str, str] | None:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        """
        SELECT learner_id, display_name
        FROM learners
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
        """
    ).fetchone()
    conn.close()
    return (row[0], row[1]) if row else None


def get_or_create_learner(db_path: Path, display_name: str, preferred_language: str, default_mastery: dict[str, float]) -> tuple[str, str]:
    display_name = display_name.strip() or "Learner"
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT learner_id, display_name FROM learners WHERE display_name = ?", (display_name,)).fetchone()
    if row:
        learner_id = row[0]
        conn.execute(
            "UPDATE learners SET preferred_language = ?, updated_at = ? WHERE learner_id = ?",
            (preferred_language, utc_now(), learner_id),
        )
        conn.commit()
        conn.close()
        return learner_id, row[1]
    learner_id = uuid.uuid4().hex[:12]
    payload = json.dumps(default_mastery)
    now = utc_now()
    conn.execute(
        """
        INSERT INTO learners (learner_id, display_name, preferred_language, mastery_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (learner_id, display_name, preferred_language, payload, now, now),
    )
    conn.commit()
    conn.close()
    return learner_id, display_name


def load_mastery(db_path: Path, learner_id: str) -> dict[str, float]:
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT mastery_json FROM learners WHERE learner_id = ?", (learner_id,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else {}


def save_mastery(db_path: Path, learner_id: str, mastery: dict[str, float]) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE learners SET mastery_json = ?, updated_at = ? WHERE learner_id = ?",
        (json.dumps(mastery), utc_now(), learner_id),
    )
    conn.commit()
    conn.close()


def save_attempt(
    db_path: Path,
    learner_id: str,
    item_id: str,
    skill: str,
    correct: bool,
    response_text: str,
    response_value: int | None,
    language_detected: str,
) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO attempts (learner_id, item_id, skill, correct, response_text, response_value, language_detected, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (learner_id, item_id, skill, int(bool(correct)), response_text, response_value, language_detected, utc_now()),
    )
    conn.commit()
    conn.close()


def load_recent_item_ids(db_path: Path, learner_id: str, limit: int = 6) -> list[str]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT item_id FROM attempts WHERE learner_id = ? ORDER BY attempt_id DESC LIMIT ?",
        (learner_id, limit),
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def recent_attempts(db_path: Path, learner_id: str, limit: int = 12) -> list[dict]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT item_id, skill, correct, response_text, response_value, language_detected, created_at
        FROM attempts
        WHERE learner_id = ?
        ORDER BY attempt_id DESC
        LIMIT ?
        """,
        (learner_id, limit),
    ).fetchall()
    conn.close()
    return [
        {
            "item_id": row[0],
            "skill": row[1],
            "correct": bool(row[2]),
            "response_text": row[3],
            "response_value": row[4],
            "language_detected": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]


def learner_attempt_summary(db_path: Path, learner_id: str) -> dict:
    conn = sqlite3.connect(db_path)
    total = conn.execute("SELECT COUNT(*) FROM attempts WHERE learner_id = ?", (learner_id,)).fetchone()[0]
    correct = conn.execute(
        "SELECT COUNT(*) FROM attempts WHERE learner_id = ? AND correct = 1",
        (learner_id,),
    ).fetchone()[0]
    by_skill = conn.execute(
        """
        SELECT skill, AVG(correct), COUNT(*)
        FROM attempts
        WHERE learner_id = ?
        GROUP BY skill
        """,
        (learner_id,),
    ).fetchall()
    by_language = conn.execute(
        """
        SELECT language_detected, COUNT(*)
        FROM attempts
        WHERE learner_id = ?
        GROUP BY language_detected
        ORDER BY COUNT(*) DESC
        """,
        (learner_id,),
    ).fetchall()
    conn.close()
    return {
        "total_attempts": int(total),
        "correct_attempts": int(correct),
        "accuracy": round((correct / total), 3) if total else 0.0,
        "by_skill": [
            {"skill": row[0], "accuracy": round(float(row[1]), 3), "attempts": int(row[2])}
            for row in by_skill
        ],
        "language_mix": [{"language": row[0] or "unknown", "count": int(row[1])} for row in by_language],
    }


def dashboard_snapshot(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    learner_count = conn.execute("SELECT COUNT(*) FROM learners").fetchone()[0]
    attempt_count = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    skill_rows = conn.execute(
        """
        SELECT skill, AVG(correct), COUNT(*)
        FROM attempts
        GROUP BY skill
        ORDER BY skill
        """
    ).fetchall()
    language_rows = conn.execute(
        """
        SELECT COALESCE(language_detected, 'unknown') as language_detected, COUNT(*)
        FROM attempts
        GROUP BY language_detected
        ORDER BY COUNT(*) DESC
        """
    ).fetchall()
    recent_rows = conn.execute(
        """
        SELECT learner_id, item_id, skill, correct, response_value, language_detected, created_at
        FROM attempts
        ORDER BY attempt_id DESC
        LIMIT 20
        """
    ).fetchall()
    conn.close()
    return {
        "learners": int(learner_count),
        "attempts": int(attempt_count),
        "skill_accuracy": [
            {"skill": row[0], "accuracy": round(float(row[1]), 3), "attempts": int(row[2])}
            for row in skill_rows
        ],
        "language_mix": [{"language": row[0], "count": int(row[1])} for row in language_rows],
        "recent_attempts": [
            {
                "learner_id": row[0],
                "item_id": row[1],
                "skill": row[2],
                "correct": bool(row[3]),
                "response_value": row[4],
                "language_detected": row[5],
                "created_at": row[6],
            }
            for row in recent_rows
        ],
    }
