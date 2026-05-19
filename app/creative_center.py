from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.adaptation.adaptation_matrix import adapt_chapter
from app.characters.arc_tracker import analyze_character_arc
from app.characters.arc_updater import save_character_arc
from app.characters.character_drift_detector import detect_character_drift as run_drift
from app.db.database import db_session, init_db, log_generation, row_to_dict, rows_to_dicts
from app.foreshadowing.payoff_planner import write_payoff_plan
from app.foreshadowing.payoff_recommender import recommend_payoffs
from app.pacing.pacing_analyzer import analyze_pacing
from app.platforms.platform_adapter import adapt_platform_text, analyze_platform_fit
from app.platforms.platform_profiles import BUILTIN_PROFILES
from app.quality.ai_tone_detector import detect_ai_tone
from app.quality.ai_tone_repair import polish_chapter_natural_style


def chapter_by_id(conn: sqlite3.Connection, project_id: int, chapter_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM chapters WHERE project_id = ? AND id = ?", (project_id, chapter_id)).fetchone()
    if not row:
        raise ValueError(f"Chapter not found: {chapter_id}")
    return dict(row)


def ensure_builtin_platform_profiles() -> None:
    init_db()
    with db_session() as conn:
        for name, profile in BUILTIN_PROFILES.items():
            conn.execute(
                """
                INSERT INTO platform_profiles (platform_name, profile_json, is_builtin)
                VALUES (?, ?, 1)
                ON CONFLICT(platform_name) DO UPDATE SET profile_json = excluded.profile_json
                """,
                (name, profile.model_dump_json()),
            )


def save_quality_report(conn: sqlite3.Connection, project_id: int, chapter_id: int | None, report_type: str, score: int, risk_level: str, report: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO quality_reports (project_id, chapter_id, report_type, score, risk_level, report_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (project_id, chapter_id, report_type, score, risk_level, json.dumps(report, ensure_ascii=False)),
    )
    log_generation(
        conn,
        project_id,
        report_type,
        response=json.dumps(report, ensure_ascii=False),
        structured=report,
        chapter_id=chapter_id,
        module_name=report_type,
        output_json=report,
        user_action="analyze",
    )
    return int(cur.lastrowid)


def detect_ai_tone_for_chapter(project_id: int, chapter_id: int) -> dict:
    with db_session() as conn:
        chapter = chapter_by_id(conn, project_id, chapter_id)
        report = detect_ai_tone(chapter["content"]).model_dump()
        save_quality_report(conn, project_id, chapter_id, "ai_tone_detector", report["overall_score"], report["risk_level"], report)
        return report


def rewrite_ai_tone_for_chapter(project_id: int, chapter_id: int, apply: bool = False) -> dict:
    with db_session() as conn:
        chapter = chapter_by_id(conn, project_id, chapter_id)
        report = detect_ai_tone(chapter["content"]).model_dump()
        rewritten, changes = polish_chapter_natural_style(chapter["content"], report)
        result = {"rewritten_text": rewritten, "changed_segments": changes, "applied": False, "report": report}
        if apply:
            conn.execute(
                """
                INSERT INTO chapters (project_id, chapter_number, volume, title, content, outline, status, word_count)
                VALUES (?, ?, ?, ?, ?, ?, 'draft', ?)
                """,
                (project_id, int(chapter["chapter_number"]) + 10000, chapter["volume"], f"{chapter['title']} - AI腔自然化版本", result["rewritten_text"], chapter["outline"], len(result["rewritten_text"])),
            )
            result["applied"] = True
        log_generation(conn, project_id, "rewrite_ai_tone", response=result["rewritten_text"], structured=result, chapter_id=chapter_id, module_name="ai_tone_detector", output_json=result, user_action="rewrite", applied_to_chapter=apply)
        return result


def analyze_pacing_for_chapter(project_id: int, chapter_id: int) -> dict:
    with db_session() as conn:
        chapter = chapter_by_id(conn, project_id, chapter_id)
        summaries = [r["short_summary"] or r["detailed_summary"] for r in conn.execute("SELECT * FROM chapter_summaries WHERE project_id = ? ORDER BY id DESC LIMIT 3", (project_id,)).fetchall()]
        report = analyze_pacing(chapter["content"], summaries).model_dump()
        risk = "high" if report["chapter_score"] < 60 else "medium" if report["chapter_score"] < 80 else "low"
        save_quality_report(conn, project_id, chapter_id, "pacing_analyzer", report["chapter_score"], risk, report)
        return report


def recommend_payoff_for_project(project_id: int) -> dict:
    with db_session() as conn:
        report = recommend_payoffs(conn, project_id).model_dump()
        log_generation(conn, project_id, "recommend_payoff", response=json.dumps(report, ensure_ascii=False), structured=report, module_name="foreshadow_payoff", output_json=report, user_action="recommend")
        return report


def plan_payoff_for_foreshadow(project_id: int, foreshadow_id: int) -> dict:
    report = recommend_payoff_for_project(project_id)
    rec = next((x for x in report["recommendations"] if int(x["foreshadow_id"]) == int(foreshadow_id)), None)
    if not rec:
        raise ValueError(f"Foreshadow not found or already resolved: {foreshadow_id}")
    plan = write_payoff_plan(__import__("app.foreshadowing.payoff_schema", fromlist=["PayoffRecommendation"]).PayoffRecommendation.model_validate(rec))
    with db_session() as conn:
        log_generation(conn, project_id, "plan_payoff", response=plan, structured={"plan": plan, "recommendation": rec}, module_name="foreshadow_payoff", output_json={"plan": plan, "recommendation": rec}, user_action="plan")
    return {"plan": plan, "recommendation": rec}


def analyze_character_arc_for_project(project_id: int, character_id: int, chapter_id: int | None = None) -> dict:
    with db_session() as conn:
        report_model = analyze_character_arc(conn, project_id, character_id)
        save_character_arc(conn, project_id, chapter_id, report_model)
        report = report_model.model_dump()
        save_quality_report(conn, project_id, chapter_id, "character_arc_tracker", 100 if report["drift_risk"] == "low" else 70, report["drift_risk"], report)
        return report


def detect_character_drift_for_chapter(project_id: int, chapter_id: int) -> dict:
    with db_session() as conn:
        report = {"drift_reports": run_drift(conn, project_id, chapter_id)}
        risk = "high" if report["drift_reports"] else "low"
        save_quality_report(conn, project_id, chapter_id, "character_drift_detector", 60 if report["drift_reports"] else 95, risk, report)
        return report


def character_presence_for_project(project_id: int) -> list[dict]:
    with db_session() as conn:
        return rows_to_dicts(conn.execute(
            """
            SELECT ch.name, MAX(c.chapter_number) AS last_chapter, COUNT(cp.id) AS presence_count
            FROM characters ch
            LEFT JOIN character_presence cp ON cp.character_id = ch.id
            LEFT JOIN chapters c ON c.id = cp.chapter_id
            WHERE ch.project_id = ?
            GROUP BY ch.id
            ORDER BY COALESCE(last_chapter, 0), ch.importance DESC
            """,
            (project_id,),
        ).fetchall())


def analyze_platform_fit_for_chapter(project_id: int, chapter_id: int, platform: str) -> dict:
    ensure_builtin_platform_profiles()
    with db_session() as conn:
        chapter = chapter_by_id(conn, project_id, chapter_id)
        report = analyze_platform_fit(chapter["content"], platform).model_dump()
        save_quality_report(conn, project_id, chapter_id, "platform_adapter", report["fit_score"], "low" if report["fit_score"] >= 80 else "medium", report)
        return report


def adapt_platform_for_chapter(project_id: int, chapter_id: int, platform: str, apply: bool = False) -> dict:
    with db_session() as conn:
        chapter = chapter_by_id(conn, project_id, chapter_id)
        text = adapt_platform_text(chapter["content"], platform)
        payload = {"platform": platform, "adapted_text": text, "applied": apply}
        if apply:
            conn.execute(
                "INSERT INTO chapters (project_id, chapter_number, volume, title, content, status, word_count) VALUES (?, ?, ?, ?, ?, 'draft', ?)",
                (project_id, int(chapter["chapter_number"]) + 20000, chapter["volume"], f"{chapter['title']} - {platform}适配版", text, len(text)),
            )
        log_generation(conn, project_id, "adapt_platform", response=text, structured=payload, chapter_id=chapter_id, module_name="platform_adapter", output_json=payload, user_action="adapt", applied_to_chapter=apply)
        return payload


def adapt_chapter_for_ip(project_id: int, chapter_id: int, adaptation_type: str = "all") -> dict:
    with db_session() as conn:
        chapter = chapter_by_id(conn, project_id, chapter_id)
        result = adapt_chapter(chapter_id, chapter["title"], chapter["content"], adaptation_type).model_dump()
        markdown = adaptation_to_markdown(result)
        conn.execute(
            "INSERT INTO adaptation_outputs (project_id, chapter_id, adaptation_type, output_json, output_markdown) VALUES (?, ?, ?, ?, ?)",
            (project_id, chapter_id, adaptation_type, json.dumps(result, ensure_ascii=False), markdown),
        )
        log_generation(conn, project_id, "adapt_chapter", response=markdown, structured=result, chapter_id=chapter_id, module_name="adaptation_matrix", output_json=result, user_action="adapt")
        return {"json": result, "markdown": markdown}


def adaptation_to_markdown(result: dict) -> str:
    lines = [f"# 章节改编矩阵：Chapter {result.get('chapter_id')}", ""]
    for key, value in result.get("adaptations", {}).items():
        lines.append(f"## {key}")
        if isinstance(value, str):
            lines.append(value)
        else:
            lines.append("```json")
            lines.append(json.dumps(value, ensure_ascii=False, indent=2))
            lines.append("```")
        lines.append("")
    return "\n".join(lines)
