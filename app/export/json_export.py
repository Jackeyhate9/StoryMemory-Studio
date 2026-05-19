import json
import sqlite3
from pathlib import Path


EXPORT_TABLES = [
    "projects",
    "characters",
    "character_relationships",
    "world_rules",
    "locations",
    "organizations",
    "items",
    "abilities",
    "chapters",
    "chapter_summaries",
    "chapter_facts",
    "plot_threads",
    "foreshadows",
    "timeline_events",
    "style_profiles",
    "forbidden_rules",
    "unresolved_questions",
    "memory_chunks",
    "generation_logs",
]


def export_project_json(conn: sqlite3.Connection, project_id: int, output: Path) -> Path:
    payload = {}
    for table in EXPORT_TABLES:
        if table == "projects":
            rows = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {table} WHERE project_id = ?", (project_id,)).fetchall()
        payload[table] = [dict(row) for row in rows]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
