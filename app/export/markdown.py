import sqlite3
from pathlib import Path


def export_project_markdown(conn: sqlite3.Connection, project_id: int, output: Path) -> Path:
    project = dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())
    lines = [f"# {project['title']}", "", project.get("description", ""), ""]
    sections = [
        ("人物卡", "characters", ["name", "role", "personality", "status", "hard_constraints"]),
        ("世界观硬规则", "world_rules", ["category", "rule_text", "rigidity"]),
        ("伏笔", "foreshadows", ["name", "status", "related_thread", "risk_note"]),
        ("时间线", "timeline_events", ["story_time", "event_text", "location"]),
        ("章节事实", "chapter_facts", ["fact_type", "fact_text"]),
    ]
    for title, table, fields in sections:
        lines.extend([f"## {title}", ""])
        rows = conn.execute(f"SELECT * FROM {table} WHERE project_id = ?", (project_id,)).fetchall()
        for row in rows:
            item = dict(row)
            text = " | ".join(str(item.get(field, "")) for field in fields if item.get(field))
            if text:
                lines.append(f"- {text}")
        lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output

