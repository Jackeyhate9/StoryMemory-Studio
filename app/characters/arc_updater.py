from __future__ import annotations

import sqlite3

from app.characters.arc_schema import CharacterArcReport


def save_character_arc(conn: sqlite3.Connection, project_id: int, chapter_id: int | None, report: CharacterArcReport) -> int:
    cur = conn.execute(
        """
        INSERT INTO character_arcs
        (project_id, character_id, chapter_id, current_goal, psychological_state,
         relationship_state_json, ability_state_json, arc_stage, key_behavior, contradiction_risk)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            report.character_id,
            chapter_id,
            report.current_goal,
            report.psychological_state,
            __import__("json").dumps(report.relationship_changes, ensure_ascii=False),
            __import__("json").dumps(report.ability_changes, ensure_ascii=False),
            report.arc_stage,
            report.key_behavior,
            report.drift_risk,
        ),
    )
    return int(cur.lastrowid)
