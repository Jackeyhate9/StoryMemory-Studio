from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.db.database import db_session, dumps, get_project, init_db, row_to_dict, rows_to_dicts
from app.style.style_safety import safe_excerpt, text_hash
from app.style.style_schema import StyleProfileResult


def save_style_profile(
    project: str,
    profile: StyleProfileResult,
    samples: list[str],
    source_note: str = "",
    save_source: bool = False,
    set_default: bool = False,
) -> int:
    init_db()
    with db_session() as conn:
        p = get_project(conn, project)
        if set_default:
            conn.execute("UPDATE style_profiles SET is_default = 0 WHERE project_id = ?", (p["id"],))
        cur = conn.execute(
            """
            INSERT INTO style_profiles
            (project_id, name, style_name, source_type, target_usage, platform, pov, sentence_length,
             dialogue_ratio, description_ratio, inner_monologue_ratio, high_point_density,
             common_patterns_json, banned_expressions_json, pacing, sample_text, profile_json,
             sentence_profile_json, paragraph_profile_json, dialogue_profile_json, emotion_profile_json,
             pacing_profile_json, hook_profile_json, word_choice_json, structure_profile_json,
             do_rules_json, dont_rules_json, safe_style_summary, forbidden_copy_rules_json, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                p["id"],
                profile.style_name,
                profile.style_name,
                "style_profiler",
                dumps(profile.target_usage),
                "",
                profile.narrative_pov,
                profile.sentence_length.average,
                profile.dialogue_style.dialogue_ratio,
                profile.description_style.visual_density,
                profile.emotion_style.inner_monologue_ratio,
                profile.pacing_style.conflict_frequency,
                dumps(profile.do_rules),
                dumps(profile.dont_rules),
                profile.pacing_style.scene_speed,
                "" if not save_source else "\n\n".join(samples),
                profile.model_dump_json(),
                profile.sentence_length.model_dump_json(),
                profile.paragraph_style.model_dump_json(),
                profile.dialogue_style.model_dump_json(),
                profile.emotion_style.model_dump_json(),
                profile.pacing_style.model_dump_json(),
                profile.hook_style.model_dump_json(),
                profile.word_choice.model_dump_json(),
                profile.structure_style.model_dump_json(),
                dumps(profile.do_rules),
                dumps(profile.dont_rules),
                profile.safe_style_summary,
                dumps(profile.forbidden_copy_rules),
                1 if set_default else 0,
            ),
        )
        style_id = int(cur.lastrowid)
        for idx, sample in enumerate(samples, 1):
            conn.execute(
                """
                INSERT INTO style_samples
                (project_id, style_profile_id, sample_title, sample_text_hash, sample_excerpt_safe,
                 sample_text, sample_length, source_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p["id"],
                    style_id,
                    f"sample_{idx}",
                    text_hash(sample),
                    safe_excerpt(sample),
                    sample if save_source else None,
                    len(sample),
                    source_note,
                ),
            )
        return style_id


def list_style_profiles(project: str) -> list[dict]:
    init_db()
    with db_session() as conn:
        p = get_project(conn, project)
        return rows_to_dicts(conn.execute("SELECT * FROM style_profiles WHERE project_id = ? ORDER BY is_default DESC, id DESC", (p["id"],)).fetchall())


def get_style_profile_by_id(style_profile_id: int) -> dict | None:
    init_db()
    with db_session() as conn:
        return row_to_dict(conn.execute("SELECT * FROM style_profiles WHERE id = ?", (style_profile_id,)).fetchone())


def get_style_samples(style_profile_id: int) -> list[dict]:
    init_db()
    with db_session() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM style_samples WHERE style_profile_id = ? ORDER BY id", (style_profile_id,)).fetchall())


def default_style_profile(project: str) -> dict | None:
    init_db()
    with db_session() as conn:
        p = get_project(conn, project)
        return row_to_dict(
            conn.execute(
                "SELECT * FROM style_profiles WHERE project_id = ? ORDER BY is_default DESC, id DESC LIMIT 1",
                (p["id"],),
            ).fetchone()
        )


def export_style_profile(style_profile_id: int, output_dir: Path) -> Path:
    profile = get_style_profile_by_id(style_profile_id)
    if not profile:
        raise ValueError(f"Style profile not found: {style_profile_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "style_profile": {k: v for k, v in profile.items() if k != "sample_text"},
        "samples": [
            {k: v for k, v in row.items() if k != "sample_text"}
            for row in get_style_samples(style_profile_id)
        ],
    }
    (output_dir / "style_profile.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        f"# {profile.get('style_name') or profile.get('name')}",
        "",
        "## 安全文风摘要",
        profile.get("safe_style_summary") or "",
        "",
        "## 应该遵守",
        *(f"- {x}" for x in json.loads(profile.get("do_rules_json") or "[]")),
        "",
        "## 必须避免",
        *(f"- {x}" for x in json.loads(profile.get("dont_rules_json") or "[]")),
    ]
    (output_dir / "style_profile.md").write_text("\n".join(md), encoding="utf-8")
    prompt_rules = [
        "【文风画像】",
        profile.get("safe_style_summary") or "",
        "",
        "【应该遵守】",
        *(f"- {x}" for x in json.loads(profile.get("do_rules_json") or "[]")),
        "",
        "【必须避免】",
        *(f"- {x}" for x in json.loads(profile.get("dont_rules_json") or "[]")),
        "",
        "【文风安全要求】",
        "- 只学习抽象风格，不复制原文表达。",
        "- 不复用样章句子、段落结构、独特比喻、专有设定。",
        "- 生成新的原创内容。",
    ]
    (output_dir / "style_rules_for_prompt.md").write_text("\n".join(prompt_rules), encoding="utf-8")
    return output_dir
