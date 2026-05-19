from __future__ import annotations

import sqlite3

from app.characters.arc_schema import CharacterArcReport, DriftIssue


def analyze_character_arc(conn: sqlite3.Connection, project_id: int, character_id: int) -> CharacterArcReport:
    char = conn.execute("SELECT * FROM characters WHERE project_id = ? AND id = ?", (project_id, character_id)).fetchone()
    if not char:
        raise ValueError(f"Character not found: {character_id}")
    facts = conn.execute(
        """
        SELECT cf.*, c.chapter_number FROM chapter_facts cf
        JOIN chapters c ON c.id = cf.chapter_id
        WHERE cf.project_id = ? AND (cf.subject LIKE ? OR cf.fact_text LIKE ?)
        ORDER BY c.chapter_number DESC LIMIT 20
        """,
        (project_id, f"%{char['name']}%", f"%{char['name']}%"),
    ).fetchall()
    presences = conn.execute(
        """
        SELECT cp.*, c.chapter_number FROM character_presence cp
        LEFT JOIN chapters c ON c.id = cp.chapter_id
        WHERE cp.project_id = ? AND cp.character_id = ?
        ORDER BY COALESCE(c.chapter_number, 0) DESC LIMIT 5
        """,
        (project_id, character_id),
    ).fetchall()
    latest_fact = facts[0]["fact_text"] if facts else char["status"] or ""
    drift_issues: list[DriftIssue] = []
    if char["hard_constraints"] and "违背" in latest_fact:
        drift_issues.append(DriftIssue(issue_type="硬设定风险", reason="最近事实可能触碰角色不可违背设定。", evidence=latest_fact, suggestion="重写行为动机或补充铺垫。"))
    if not presences and facts:
        drift_issues.append(DriftIssue(issue_type="出场记录缺失", reason="有章节事实但缺少 character_presence 记录。", suggestion="运行角色出场同步或补充出场记录。"))
    risk = "high" if any(i.issue_type == "硬设定风险" for i in drift_issues) else "medium" if drift_issues else "low"
    return CharacterArcReport(
        character_id=character_id,
        character_name=char["name"],
        arc_stage=_stage_from_role(char["role"], latest_fact),
        current_goal=char["motivation"] or "待补充当前目标",
        psychological_state=char["status"] or "稳定",
        relationship_changes=[r["fact_text"] for r in facts if "关系" in r["fact_text"]][:5],
        ability_changes=[r["fact_text"] for r in facts if "能力" in r["fact_text"] or "学会" in r["fact_text"]][:5],
        key_behavior=latest_fact,
        drift_risk=risk,
        drift_issues=drift_issues,
        next_arc_suggestions=["给角色安排下一次主动选择。", "让目标变化和主线冲突发生因果关系。", "若长期未出场，安排一次低成本但有效的推进。"],
    )


def _stage_from_role(role: str, latest: str) -> str:
    if "反派" in role or "黑" in latest:
        return "对抗/黑化推进"
    if "成长" in latest or "学会" in latest:
        return "成长推进"
    return "稳定推进"
