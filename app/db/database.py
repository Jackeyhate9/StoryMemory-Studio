import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import get_settings


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or get_settings().db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | Path | None = None) -> Path:
    path = Path(db_path or get_settings().db_path)
    with db_session(path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _run_light_migrations(conn)
    return path


def _run_light_migrations(conn: sqlite3.Connection) -> None:
    def add_columns(table: str, columns: dict[str, str]) -> None:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")

    add_columns("style_profiles", {
        "style_name": "TEXT",
        "source_type": "TEXT DEFAULT ''",
        "target_usage": "TEXT DEFAULT '[]'",
        "sentence_profile_json": "TEXT DEFAULT '{}'",
        "paragraph_profile_json": "TEXT DEFAULT '{}'",
        "dialogue_profile_json": "TEXT DEFAULT '{}'",
        "emotion_profile_json": "TEXT DEFAULT '{}'",
        "pacing_profile_json": "TEXT DEFAULT '{}'",
        "hook_profile_json": "TEXT DEFAULT '{}'",
        "word_choice_json": "TEXT DEFAULT '{}'",
        "structure_profile_json": "TEXT DEFAULT '{}'",
        "do_rules_json": "TEXT DEFAULT '[]'",
        "dont_rules_json": "TEXT DEFAULT '[]'",
        "safe_style_summary": "TEXT DEFAULT ''",
        "forbidden_copy_rules_json": "TEXT DEFAULT '[]'",
        "updated_at": "TEXT",
    })
    add_columns("generation_logs", {
        "module_name": "TEXT DEFAULT ''",
        "input_summary": "TEXT DEFAULT ''",
        "output_json": "TEXT DEFAULT '{}'",
        "user_action": "TEXT DEFAULT ''",
        "applied_to_chapter": "INTEGER DEFAULT 0",
    })
    add_columns("foreshadows", {
        "first_chapter_id": "INTEGER",
        "last_mentioned_chapter_id": "INTEGER",
        "expected_payoff_chapter": "INTEGER",
        "payoff_type": "TEXT DEFAULT ''",
        "payoff_priority": "INTEGER DEFAULT 50",
        "payoff_risk": "TEXT DEFAULT 'low'",
        "payoff_notes": "TEXT DEFAULT ''",
        "related_plot_thread_id": "INTEGER",
    })
    add_columns("characters", {
        "importance": "INTEGER DEFAULT 50",
    })
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS edit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            row_id INTEGER,
            action TEXT NOT NULL,
            before_json TEXT DEFAULT '{}',
            after_json TEXT DEFAULT '{}',
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edit_logs_project_table ON edit_logs(project_id, table_name, row_id)")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return None if row is None else dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def get_project(conn: sqlite3.Connection, name: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM projects WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise ValueError(f"Project not found: {name}")
    return dict(row)


def log_generation(
    conn: sqlite3.Connection,
    project_id: int,
    operation: str,
    provider: str = "",
    model: str = "",
    prompt: str = "",
    response: str = "",
    structured: dict[str, Any] | None = None,
    chapter_id: int | None = None,
    status: str = "success",
    error: str = "",
    module_name: str = "",
    input_summary: str = "",
    output_json: dict[str, Any] | None = None,
    user_action: str = "",
    applied_to_chapter: bool = False,
) -> None:
    import hashlib

    conn.execute(
        """
        INSERT INTO generation_logs
        (project_id, chapter_id, operation, provider, model, prompt_hash, prompt_preview,
         response_preview, structured_json, status, error, module_name, input_summary, output_json,
         user_action, applied_to_chapter)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            chapter_id,
            operation,
            provider,
            model,
            hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt else "",
            prompt[:4000],
            response[:4000],
            dumps(structured or {}),
            status,
            error,
            module_name or operation,
            input_summary or prompt[:500],
            dumps(output_json or structured or {}),
            user_action,
            1 if applied_to_chapter else 0,
        ),
    )


def log_edit(
    conn: sqlite3.Connection,
    project_id: int,
    table_name: str,
    row_id: int | None,
    action: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    note: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO edit_logs (project_id, table_name, row_id, action, before_json, after_json, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, table_name, row_id, action, dumps(before or {}), dumps(after or {}), note),
    )
