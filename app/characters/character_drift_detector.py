from __future__ import annotations

import sqlite3

from app.characters.arc_tracker import analyze_character_arc


def detect_character_drift(conn: sqlite3.Connection, project_id: int, chapter_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM characters WHERE project_id = ? ORDER BY importance DESC, id LIMIT 20",
        (project_id,),
    ).fetchall()
    reports = []
    for row in rows:
        report = analyze_character_arc(conn, project_id, row["id"])
        if report.drift_risk != "low":
            reports.append(report.model_dump())
    return reports
