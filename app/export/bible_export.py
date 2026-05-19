from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.db.database import rows_to_dicts
from app.export.json_export import export_project_json


def _write_md(path: Path, title: str, rows: list[dict], fields: list[str]) -> None:
    lines = [f"# {title}", ""]
    if not rows:
        lines.append("暂无内容")
    for row in rows:
        heading = row.get("name") or row.get("title") or row.get("category") or row.get("story_time") or row.get("id")
        lines.extend([f"## {heading}", ""])
        for field in fields:
            value = row.get(field)
            if value not in (None, "", "[]", "{}"):
                lines.append(f"- **{field}**：{value}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def export_bible(conn: sqlite3.Connection, project_id: int, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    project = dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())

    world_rules = rows_to_dicts(conn.execute("SELECT * FROM world_rules WHERE project_id = ? ORDER BY id", (project_id,)).fetchall())
    locations = rows_to_dicts(conn.execute("SELECT * FROM locations WHERE project_id = ? ORDER BY id", (project_id,)).fetchall())
    organizations = rows_to_dicts(conn.execute("SELECT * FROM organizations WHERE project_id = ? ORDER BY id", (project_id,)).fetchall())
    world_rows = [{"name": "项目概览", **project}, *world_rules, *locations, *organizations]
    _write_md(output_dir / "world_bible.md", "世界观圣经", world_rows, ["title", "description", "genre", "target_platform", "category", "rule_text", "rigidity", "type", "description", "rules", "leader", "status"])

    characters = rows_to_dicts(conn.execute("SELECT * FROM characters WHERE project_id = ? ORDER BY id", (project_id,)).fetchall())
    relationships = rows_to_dicts(conn.execute("SELECT * FROM character_relationships WHERE project_id = ? ORDER BY id", (project_id,)).fetchall())
    _write_md(output_dir / "character_bible.md", "角色圣经", [*characters, *relationships], ["name", "role", "appearance", "personality", "motivation", "abilities", "status", "current_location", "hard_constraints", "character_a_name", "character_b_name", "relationship_type", "description"])

    threads = rows_to_dicts(conn.execute("SELECT * FROM plot_threads WHERE project_id = ? ORDER BY id", (project_id,)).fetchall())
    chapters = rows_to_dicts(conn.execute("SELECT chapter_number, title, outline FROM chapters WHERE project_id = ? ORDER BY chapter_number", (project_id,)).fetchall())
    _write_md(output_dir / "outline.md", "剧情大纲", [*threads, *chapters], ["name", "thread_type", "status", "summary", "chapter_number", "title", "outline"])

    foreshadows = rows_to_dicts(conn.execute("SELECT * FROM foreshadows WHERE project_id = ? ORDER BY id", (project_id,)).fetchall())
    _write_md(output_dir / "foreshadows.md", "伏笔表", foreshadows, ["name", "status", "related_thread", "expected_resolution_chapter", "resolution_method", "risk_note", "evidence"])

    timeline = rows_to_dicts(conn.execute("SELECT * FROM timeline_events WHERE project_id = ? ORDER BY sort_key, id", (project_id,)).fetchall())
    _write_md(output_dir / "timeline.md", "时间线", timeline, ["story_time", "sort_key", "event_text", "location", "characters_json", "duration"])

    first = conn.execute("SELECT * FROM chapters WHERE project_id = ? AND chapter_number = 1", (project_id,)).fetchone()
    first_rows = [dict(first)] if first else []
    _write_md(output_dir / "first_chapter.md", "第一章", first_rows, ["title", "volume", "content"])

    export_project_json(conn, project_id, output_dir / "story_memory.json")
    return output_dir

