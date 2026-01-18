"""
SQLite-based storage for pipeline runs.

Single file database: data/pipeline.db
"""
import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Optional

from app.config import DATA_DIR, DB_PATH


def _ensure_db():
    """Create database and tables if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                stage TEXT NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stages (
                run_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (run_id, stage),
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE TABLE IF NOT EXISTS outputs (
                run_id TEXT PRIMARY KEY,
                markdown TEXT NOT NULL,
                artifact TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE TABLE IF NOT EXISTS article_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                definition TEXT NOT NULL,
                guideline TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)


@contextmanager
def _get_conn():
    """Get a database connection with auto-commit."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# Initialize DB on module load
_ensure_db()


def write_status(run_id: str, payload: Dict[str, Any]) -> None:
    """Write or update run status."""
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO runs (run_id, status, stage, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status = excluded.status,
                stage = excluded.stage,
                error = excluded.error,
                updated_at = excluded.updated_at
        """, (
            run_id,
            payload.get("state", "pending"),
            payload.get("stage", "stage_0"),
            payload.get("error"),
            payload.get("updated_at", ""),
            payload.get("updated_at", ""),
        ))


def read_status(run_id: str) -> Optional[Dict[str, Any]]:
    """Read run status."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "run_id": row["run_id"],
            "state": row["status"],
            "stage": row["stage"],
            "error": row["error"],
            "updated_at": row["updated_at"],
        }


def write_stage_result(run_id: str, stage: str, payload: Dict[str, Any]) -> None:
    """Write stage result."""
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO stages (run_id, stage, data, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(run_id, stage) DO UPDATE SET
                data = excluded.data,
                created_at = excluded.created_at
        """, (
            run_id,
            stage,
            json.dumps(payload, default=str),
            payload.get("created_at", ""),
        ))


def read_stage_result(run_id: str, stage: str) -> Optional[Dict[str, Any]]:
    """Read stage result."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT data FROM stages WHERE run_id = ? AND stage = ?",
            (run_id, stage)
        ).fetchone()
        if not row:
            return None
        return json.loads(row["data"])


def write_markdown(run_id: str, markdown: str) -> str:
    """Write markdown output. Returns a reference string."""
    # We'll store in outputs table, called from write_artifact
    return f"db:outputs:{run_id}"


def write_artifact(run_id: str, payload: Dict[str, Any]) -> str:
    """Write final artifact with markdown."""
    markdown = payload.pop("markdown", "")  # Extract and remove markdown from payload

    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO outputs (run_id, markdown, artifact, created_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(run_id) DO UPDATE SET
                markdown = excluded.markdown,
                artifact = excluded.artifact,
                created_at = excluded.created_at
        """, (
            run_id,
            markdown,
            json.dumps(payload, default=str),
        ))
    return f"db:outputs:{run_id}"


def read_output(run_id: str) -> Optional[Dict[str, Any]]:
    """Read final output (markdown + artifact)."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT markdown, artifact FROM outputs WHERE run_id = ?",
            (run_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "markdown": row["markdown"],
            "artifact": json.loads(row["artifact"]),
        }


def cleanup_run(run_id: str) -> None:
    """Delete all data for a specific run."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM outputs WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM stages WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))


def clear_all() -> int:
    """Delete ALL data from the database. Returns count of deleted runs."""
    with _get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        conn.execute("DELETE FROM outputs")
        conn.execute("DELETE FROM stages")
        conn.execute("DELETE FROM runs")
        return count


def get_all_runs() -> list:
    """Get all runs for debugging."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT run_id, status, stage, updated_at FROM runs ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def write_article_type(name: str, definition: str, guideline: str = None) -> int:
    """Write or update an article type. Returns the article type ID."""
    with _get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO article_types (name, definition, guideline, created_at, updated_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(name) DO UPDATE SET
                definition = excluded.definition,
                guideline = CASE WHEN excluded.guideline IS NOT NULL THEN excluded.guideline ELSE article_types.guideline END,
                updated_at = excluded.updated_at
        """, (name, definition, guideline))
        return cursor.lastrowid or conn.execute(
            "SELECT id FROM article_types WHERE name = ?", (name,)
        ).fetchone()[0]


def read_article_types() -> list:
    """Read all article types with their definitions."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, definition, guideline, created_at, updated_at FROM article_types ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]


def read_article_type_names() -> list:
    """Read just the article type names."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT name FROM article_types ORDER BY name"
        ).fetchall()
        return [row["name"] for row in rows]


def read_article_definitions() -> list:
    """Read article type definitions for classification."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT name, definition FROM article_types ORDER BY name"
        ).fetchall()
        return [f"- {row['name']} → {row['definition']}" for row in rows]


def get_article_type_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Read a specific article type by name."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM article_types WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            return None
        return dict(row)


def delete_article_type(article_type_id: int) -> bool:
    """Delete an article type by ID. Returns True if deleted, False if not found."""
    with _get_conn() as conn:
        cursor = conn.execute("DELETE FROM article_types WHERE id = ?", (article_type_id,))
        return cursor.rowcount > 0


# Legacy compatibility - these were used by old code
def read_json(path) -> Dict[str, Any]:
    """Legacy: no longer used."""
    raise NotImplementedError("JSON file storage removed - use SQLite")
