from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.checkers.consistency import ConsistencyChecker
from app.db.database import db_session, log_generation, rows_to_dicts
from app.export.docx_export import export_project_docx
from app.export.docx_preview import preview_docx
from app.quality.ai_tone_detector import detect_ai_tone
from app.quality.ai_tone_repair import polish_chapter_natural_style, polish_ai_tone_paragraphs, repair_ai_tone_sentences


def _risk_counts(reports: list[dict]) -> dict[str, int]:
    counts = {"low": 0, "medium": 0, "high": 0}
    for report in reports:
        counts[report.get("risk_level", "low")] = counts.get(report.get("risk_level", "low"), 0) + 1
    return counts


def _copy_memory(conn, source_project_id: int, target_project_id: int) -> None:
    tables = [
        "characters",
        "character_relationships",
        "world_rules",
        "locations",
        "organizations",
        "items",
        "abilities",
        "plot_threads",
        "foreshadows",
        "timeline_events",
        "style_profiles",
        "forbidden_rules",
        "unresolved_questions",
    ]
    for table in tables:
        rows = rows_to_dicts(conn.execute(f"SELECT * FROM {table} WHERE project_id = ?", (source_project_id,)).fetchall())
        for row in rows:
            row.pop("id", None)
            row["project_id"] = target_project_id
            cols = list(row.keys())
            placeholders = ", ".join("?" for _ in cols)
            conn.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})", [row[c] for c in cols])


def polish_ai_tone_batch(
    project_id: int,
    mode: str = "chapter_polish",
    save_as_new_version: bool = True,
    export_docx: bool = True,
    output_dir: str | Path = "exports",
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    original_reports: list[dict] = []
    polished_reports: list[dict] = []
    chapter_results: list[dict] = []

    with db_session() as conn:
        source = dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())
        chapters = rows_to_dicts(conn.execute("SELECT * FROM chapters WHERE project_id = ? ORDER BY chapter_number", (project_id,)).fetchall())
        if save_as_new_version:
            new_name = f"{source['name']}_自然化润色版"
            conn.execute("DELETE FROM projects WHERE name = ?", (new_name,))
            cur = conn.execute(
                """
                INSERT INTO projects (name, title, description, genre, target_platform, status, metadata_json)
                VALUES (?, ?, ?, ?, ?, 'active', ?)
                """,
                (
                    new_name,
                    f"{source['title']}_自然化润色版",
                    source.get("description") or "",
                    source.get("genre") or "",
                    source.get("target_platform") or "",
                    source.get("metadata_json") or "{}",
                ),
            )
            target_project_id = int(cur.lastrowid)
            _copy_memory(conn, project_id, target_project_id)
        else:
            target_project_id = project_id

        for chapter in chapters:
            original_report = detect_ai_tone(chapter.get("content") or "").model_dump()
            original_reports.append(original_report)
            if mode == "local_sentence_rewrite":
                polished, changes = repair_ai_tone_sentences(chapter["content"], original_report)
            elif mode == "paragraph_rewrite":
                polished, changes = polish_ai_tone_paragraphs(chapter["content"], original_report)
            else:
                polished, changes = polish_chapter_natural_style(chapter["content"], original_report)
            polished_report = detect_ai_tone(polished).model_dump()
            polished_reports.append(polished_report)
            consistency = ConsistencyChecker(None).check("", polished, "").model_dump()
            conn.execute(
                """
                INSERT INTO chapters (project_id, chapter_number, volume, title, content, outline, status, word_count)
                VALUES (?, ?, ?, ?, ?, ?, 'polished', ?)
                """,
                (
                    target_project_id,
                    chapter["chapter_number"],
                    chapter.get("volume") or "",
                    chapter["title"],
                    polished,
                    chapter.get("outline") or "",
                    len(polished),
                ),
            )
            new_chapter_id = conn.execute(
                "SELECT id FROM chapters WHERE project_id = ? AND chapter_number = ?",
                (target_project_id, chapter["chapter_number"]),
            ).fetchone()["id"]
            for report_type, report in [("ai_tone_detector", polished_report), ("consistency", consistency)]:
                conn.execute(
                    "INSERT INTO quality_reports (project_id, chapter_id, report_type, score, risk_level, report_json) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        target_project_id,
                        new_chapter_id,
                        report_type,
                        report.get("overall_score") or (100 if consistency.get("passed") else 70),
                        report.get("risk_level") or ("low" if consistency.get("passed") else "medium"),
                        json.dumps(report, ensure_ascii=False),
                    ),
                )
            log_generation(
                conn,
                target_project_id,
                "polish_ai_tone_batch",
                response=polished,
                structured={"original_report": original_report, "polished_report": polished_report, "changes": changes},
                chapter_id=new_chapter_id,
                module_name="ai_tone_detector",
                output_json={"changes": changes, "polished_report": polished_report},
                user_action="polish",
                applied_to_chapter=True,
            )
            chapter_results.append(
                {
                    "chapter_number": chapter["chapter_number"],
                    "title": chapter["title"],
                    "original_risk": original_report["risk_level"],
                    "polished_risk": polished_report["risk_level"],
                    "changes": len(changes),
                    "original_chars": len(chapter["content"] or ""),
                    "polished_chars": len(polished),
                }
            )

        docx_path = ""
        preview = {}
        if export_docx:
            title = source.get("title") or source.get("name")
            docx_path = str(output_dir / f"{title}_10章自然化润色版.docx")
            export_project_docx(conn, target_project_id, docx_path, model_name="local_ai_tone_polish")
            preview = preview_docx(docx_path)

        report = {
            "source_project_id": project_id,
            "target_project_id": target_project_id,
            "mode": mode,
            "processed_chapters": len(chapters),
            "original_ai_tone_distribution": _risk_counts(original_reports),
            "polished_ai_tone_distribution": _risk_counts(polished_reports),
            "chapters": chapter_results,
            "docx_path": docx_path,
            "docx_preview": preview,
        }
        json_path = output_dir / f"{source.get('title') or source.get('name')}_AI腔修复报告.json"
        md_path = output_dir / f"{source.get('title') or source.get('name')}_AI腔修复报告.md"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        md_lines = [
            f"# {source.get('title') or source.get('name')} AI 腔修复报告",
            "",
            f"- 源项目 ID：{project_id}",
            f"- 润色项目 ID：{target_project_id}",
            f"- 处理章节数：{len(chapters)}",
            f"- 原始风险分布：{report['original_ai_tone_distribution']}",
            f"- 润色后风险分布：{report['polished_ai_tone_distribution']}",
            f"- DOCX：{docx_path}",
            "",
            "## 分章结果",
        ]
        for item in chapter_results:
            md_lines.append(f"- 第 {item['chapter_number']} 章《{item['title']}》：{item['original_risk']} -> {item['polished_risk']}，修改 {item['changes']} 处，{item['original_chars']} -> {item['polished_chars']} 字符")
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        report["report_json_path"] = str(json_path)
        report["report_md_path"] = str(md_path)
        return report
