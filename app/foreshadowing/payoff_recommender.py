from __future__ import annotations

import json
import sqlite3

from app.foreshadowing.payoff_schema import PayoffRecommendation, PayoffReport


def recommend_payoffs(conn: sqlite3.Connection, project_id: int) -> PayoffReport:
    current = conn.execute("SELECT COALESCE(MAX(chapter_number), 0) AS n FROM chapters WHERE project_id = ?", (project_id,)).fetchone()["n"]
    rows = conn.execute(
        """
        SELECT * FROM foreshadows
        WHERE project_id = ? AND status NOT IN ('resolved', '已回收', '废弃', 'abandoned')
        ORDER BY COALESCE(last_mentioned_chapter_id, first_chapter_id, 0), id
        """,
        (project_id,),
    ).fetchall()
    recs: list[PayoffRecommendation] = []
    urgent: list[int] = []
    delay: list[int] = []
    forgotten: list[int] = []
    for row in rows:
        last_chapter_no = _chapter_no(conn, row["last_mentioned_chapter_id"]) or _chapter_no(conn, row["first_chapter_id"]) or 0
        gap = max(0, current - last_chapter_no)
        risk = "high" if gap >= 15 else "medium" if gap >= 8 else "low"
        impact = min(100, 45 + gap * 3 + (15 if row["related_thread"] else 0))
        if risk == "high":
            urgent.append(row["id"])
            forgotten.append(row["id"])
        elif gap <= 3:
            delay.append(row["id"])
        chars = _loads(row["related_characters_json"], [])
        items = _loads(row["related_items_json"], [])
        payoff_type = row["payoff_type"] or _guess_type(row["name"], row["resolution_method"])
        window = row["expected_payoff_chapter"] or row["expected_resolution_chapter"] or (current + (1 if risk == "high" else 3))
        recs.append(
            PayoffRecommendation(
                foreshadow_id=row["id"],
                foreshadow_name=row["name"],
                current_status=row["status"],
                risk_level=risk,
                chapters_since_last_mention=gap,
                recommended_payoff_window=f"第 {window} 章前后",
                recommended_payoff_type=payoff_type,
                reason=f"距离上次提及已间隔 {gap} 章，当前遗忘风险为 {risk}。",
                payoff_method=row["resolution_method"] or "让相关人物或道具重新出现，先部分兑现信息，再保留更高层真相。",
                related_characters=chars,
                related_items=items,
                suggested_chapter_outline=f"安排“{row['name']}”在行动阻力或反转处被重新提及，并让它改变主角下一步选择。",
                impact_score=impact,
            )
        )
    return PayoffReport(recommendations=recs, urgent_payoffs=urgent, safe_to_delay=delay, forgotten_risks=forgotten)


def _chapter_no(conn: sqlite3.Connection, chapter_id: int | None) -> int:
    if not chapter_id:
        return 0
    row = conn.execute("SELECT chapter_number FROM chapters WHERE id = ?", (chapter_id,)).fetchone()
    return int(row["chapter_number"]) if row else 0


def _loads(value: str | None, default):
    try:
        return json.loads(value or "")
    except Exception:
        return default


def _guess_type(name: str, method: str) -> str:
    text = f"{name}{method}"
    if "身份" in text or "秘密" in text:
        return "character_secret"
    if "规则" in text or "世界" in text:
        return "world_rule"
    if "反转" in text or "骗" in text:
        return "twist"
    return "reveal"
