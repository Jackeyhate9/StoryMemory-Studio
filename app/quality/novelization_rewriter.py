from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.checkers.consistency import ConsistencyChecker
from app.db.database import db_session, log_generation, rows_to_dicts
from app.export.docx_export import export_project_docx
from app.export.docx_preview import preview_docx
from app.llm.client import OllamaClient
from app.llm.ollama_utils import select_best_ollama_model
from app.llm.output_cleaner import clean_model_output
from app.quality.ai_tone_detector import detect_ai_tone
from app.quality.humanizer_zh import humanize_zh_text


TEMPLATE_HOOKS = [
    "关于林照音的秘密，才刚刚开始。",
    "游戏，开始了。",
    "游戏开始了。",
    "游戏，确实才刚刚开始。",
    "这一切才刚刚开始。",
    "更大的风暴正在靠近。",
    "沉睡的巨兽，等待着猎物上门。",
]


def detect_tell_not_show_blocks(text: str) -> list[dict[str, Any]]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    blocks = []
    for idx, paragraph in enumerate(paragraphs):
        score = 0
        reasons = []
        if re.search(r"作为[^。！？]{4,45}(?:她|他|这个人|继承人|操盘手)", paragraph):
            score += 3
            reasons.append("character_card_dump")
        if sum(paragraph.count(w) for w in ["家族企业", "玫瑰资本", "董事会", "商业联盟", "继承权", "资源分配"]) >= 3:
            score += 3
            reasons.append("worldbuilding_dump")
        if sum(paragraph.count(w) for w in ["命运", "秘密", "体面", "真相", "深渊", "巨兽", "风暴"]) >= 4:
            score += 2
            reasons.append("abstract_metaphor_overload")
        if paragraph.count("“") >= 2 and any(w in paragraph for w in ["你知道", "这意味着", "因为", "所以", "玫瑰资本"]):
            score += 2
            reasons.append("dialogue_exposition")
        if any(hook in paragraph for hook in TEMPLATE_HOOKS):
            score += 4
            reasons.append("template_hook")
        if score:
            blocks.append({"index": idx, "score": score, "reasons": reasons, "text": paragraph[:600]})
    return blocks


def reduce_exposition_density(text: str) -> str:
    text = re.sub(r"作为([^，。！？]{2,30})，?([^。！？]{0,80})", r"\2", text)
    text = re.sub(r"这意味着[^。！？]*[。！？]", "", text)
    text = re.sub(r"从某种意义上[^。！？]*[。！？]", "", text)
    text = re.sub(r"所有人都明白[^。！？]*[。！？]", "", text)
    return text


def convert_profile_to_behavior(text: str) -> str:
    text = text.replace("作为玫瑰资本的实际操盘手，她总是能", "王知微把平板往桌面一扣，旁边的人立刻闭了嘴。她")
    text = text.replace("大型家族企业继承人之一", "被安排在主桌空位旁的人")
    text = text.replace("商业联盟中的完美女性", "把餐巾折到同样宽度的女孩")
    return text


def convert_summary_hook_to_event_hook(text: str) -> str:
    replacement = "手机屏幕又亮了一下。论坛文章《玫瑰大厦的黄昏》被人重新编辑，隐藏发布者一栏短暂闪出两个字：林父。"
    for hook in TEMPLATE_HOOKS:
        text = text.replace(hook, replacement)
    return text


def add_subtext_to_dialogue(text: str) -> str:
    text = text.replace("你知道", "你听说过")
    text = text.replace("这意味着", "所以呢")
    text = text.replace("我告诉你", "她停了一下，把后半句咽回去，只说")
    return text


def _fallback_novelize(text: str) -> tuple[str, dict[str, Any]]:
    original = text
    text = clean_model_output(text, mode="prose")
    text = reduce_exposition_density(text)
    text = convert_profile_to_behavior(text)
    text = add_subtext_to_dialogue(text)
    text = convert_summary_hook_to_event_hook(text)
    text, humanizer_report = humanize_zh_text(text)
    return text.strip(), {
        "used_llm": False,
        "humanizer_zh": humanizer_report,
        "reduced_exposition_blocks": detect_tell_not_show_blocks(original),
        "removed_template_hooks": [hook for hook in TEMPLATE_HOOKS if hook in original],
    }


def _novelize_prompt(title: str, content: str, chapter_number: int) -> str:
    first_chapter_targets = ""
    if chapter_number == 1:
        first_chapter_targets = """
【《玫瑰大厦》第一章特别要求】
1. 保留宴会厅开场，但减少抽象高级感描写。
2. 王知微、薛明棠、谢老太太的身份不要直接设定卡说明。
3. 林照音父母旧案不要一次性解释完。
4. “林照音是棋子”“谢老太太试探她”等判断不要直接写死，让读者通过行为感受到。
5. 保留关键物件：顶层花园钥匙、《百年孤独》、林照音父亲旧账本、玫瑰死了三年但根还活着、论坛文章《玫瑰大厦的黄昏》。
6. 结尾落在具体钩子上：旧照片、账本夹页、论坛隐藏发布者、谢老太太与林父旧合影、顶层花园监控缺失、《百年孤独》扉页背后的第二行字。
"""
    return f"""
你是资深小说编辑，不是普通润色工具。
你的任务不是让句子更华丽，而是把“设定说明型章节”改写成“场景驱动型章节”。

【硬约束】
1. 保留原剧情事实。
2. 保留人物关系。
3. 保留伏笔。
4. 保留章节核心冲突。
5. 不新增重大设定。
6. 不改变人物动机。
7. 删除或弱化设定卡式介绍。
8. 把人物身份通过动作、称呼、座位安排、旁人反应、物件、消息、场景细节体现。
9. 把世界观解释拆散到场景里。
10. 对话不要直接解释剧情，要有试探、回避、误会、反讽和潜台词。
11. 章节结尾不要使用“游戏开始了”“秘密才刚刚开始”“风暴将至”等模板句。
12. 结尾必须落在具体事件、物件、消息、照片、动作或反常细节上。
13. 减少抽象总结句。
14. 增加具体可感的动作和细节。
15. 保持轻小说可读性，不要改成沉重文学腔。
16. 保持现代都市轻悬疑气质。

【小说化写作约束】
- 不要直接写人物设定卡。
- 不要直接解释人物关系。
- 不要直接解释世界观。
- 每 800-1200 字必须有一次具体互动或信息变化。
- 每个重要人物登场时，优先写动作、姿态、说话方式和他人反应。
- 抽象隐喻每 1000 字不超过 1-2 处。
- 人物心理不要直接解释，优先用动作和反应体现。
{first_chapter_targets}

【章节标题】
{title}

【原章节正文】
{content}

只输出小说化重写后的正文。不要解释，不要列清单，不要输出 Markdown 标题。
"""


def rewrite_as_scene_driven_narrative(content: str, title: str = "", chapter_number: int = 0, client: OllamaClient | None = None) -> tuple[str, dict[str, Any]]:
    if client is None:
        return _fallback_novelize(content)
    prompt = _novelize_prompt(title, content, chapter_number)
    try:
        raw = client.complete(prompt, system="你是成熟小说编辑，只输出小说正文。", temperature=0.55)
    except Exception as exc:
        fallback, meta = _fallback_novelize(content)
        meta["llm_error"] = str(exc)
        return fallback, meta
    rewritten = clean_model_output(raw, mode="prose")
    rewritten, humanizer_report = humanize_zh_text(rewritten)
    if len(rewritten) < max(1200, len(content) * 0.45):
        fallback, meta = _fallback_novelize(content)
        meta["llm_too_short"] = True
        return fallback, meta
    meta = {
        "used_llm": True,
        "humanizer_zh": humanizer_report,
        "reduced_exposition_blocks": detect_tell_not_show_blocks(content),
        "removed_template_hooks": [hook for hook in TEMPLATE_HOOKS if hook in content],
    }
    return rewritten, meta


def _copy_memory(conn, source_project_id: int, target_project_id: int) -> None:
    tables = [
        "characters", "character_relationships", "world_rules", "locations", "organizations", "items",
        "abilities", "plot_threads", "foreshadows", "timeline_events", "style_profiles",
        "forbidden_rules", "unresolved_questions",
    ]
    for table in tables:
        rows = rows_to_dicts(conn.execute(f"SELECT * FROM {table} WHERE project_id = ?", (source_project_id,)).fetchall())
        for row in rows:
            row.pop("id", None)
            row["project_id"] = target_project_id
            cols = list(row.keys())
            conn.execute(f"INSERT OR IGNORE INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})", [row[c] for c in cols])


def _ollama_client() -> OllamaClient | None:
    selection = select_best_ollama_model()
    if not selection.available or not selection.model:
        return None
    from app.config import get_settings

    return OllamaClient(get_settings().ollama_base_url, selection.model)


def novelize_chapter(project_id: int, chapter_id: int, save_as_new_version: bool = True, client: OllamaClient | None = None) -> dict[str, Any]:
    client = client if client is not None else _ollama_client()
    with db_session() as conn:
        chapter = dict(conn.execute("SELECT * FROM chapters WHERE project_id = ? AND id = ?", (project_id, chapter_id)).fetchone())
        original_report = detect_ai_tone(chapter["content"]).model_dump()
    rewritten, meta = rewrite_as_scene_driven_narrative(chapter["content"], chapter["title"], int(chapter["chapter_number"]), client)
    new_report = detect_ai_tone(rewritten).model_dump()
    with db_session() as conn:
        new_version_id = None
        if save_as_new_version:
            cur = conn.execute(
                """
                INSERT INTO chapters (project_id, chapter_number, volume, title, content, outline, status, word_count)
                VALUES (?, ?, ?, ?, ?, ?, 'novelized', ?)
                """,
                (
                    project_id,
                    int(chapter["chapter_number"]) + 30000,
                    chapter.get("volume") or "",
                    f"{chapter['title']} - 小说化重写版",
                    rewritten,
                    chapter.get("outline") or "",
                    len(rewritten),
                ),
            )
            new_version_id = int(cur.lastrowid)
        log_generation(
            conn,
            project_id,
            "novelize_chapter",
            provider="ollama" if client else "local",
            model=client.model if client else "",
            prompt=chapter["content"][:4000],
            response=rewritten,
            structured={"meta": meta, "original_ai_tone": original_report, "new_ai_tone": new_report},
            chapter_id=chapter_id,
            module_name="novelization_rewriter",
            output_json={"meta": meta, "new_ai_tone": new_report},
            user_action="novelize",
            applied_to_chapter=save_as_new_version,
        )
    return {
        "chapter_id": chapter_id,
        "original_ai_tone_score": original_report["overall_score"],
        "new_ai_tone_score": new_report["overall_score"],
        "removed_template_hooks": meta.get("removed_template_hooks", []),
        "reduced_exposition_blocks": meta.get("reduced_exposition_blocks", []),
        "converted_character_dumps": [b for b in meta.get("reduced_exposition_blocks", []) if "character_card_dump" in b.get("reasons", [])],
        "dialogue_subtext_improvements": [b for b in meta.get("reduced_exposition_blocks", []) if "dialogue_exposition" in b.get("reasons", [])],
        "ending_hook_changed": bool(meta.get("removed_template_hooks")),
        "new_version_id": new_version_id,
        "docx_path": "",
    }


def novelize_project(project_id: int, save_as_new_version: bool = True, export_docx: bool = True, output_dir: str | Path = "exports") -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    client = _ollama_client()
    chapter_reports = []
    with db_session() as conn:
        source = dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())
        chapters = rows_to_dicts(conn.execute("SELECT * FROM chapters WHERE project_id = ? AND chapter_number < 30000 ORDER BY chapter_number", (project_id,)).fetchall())
        if save_as_new_version:
            new_name = "玫瑰大厦_小说化重写版" if "玫瑰" in (source.get("title") or "") else f"{source['name']}_小说化重写版"
            conn.execute("DELETE FROM projects WHERE name = ?", (new_name,))
            cur = conn.execute(
                """
                INSERT INTO projects (name, title, description, genre, target_platform, status, metadata_json)
                VALUES (?, ?, ?, ?, ?, 'active', ?)
                """,
                (new_name, new_name, source.get("description") or "", source.get("genre") or "", source.get("target_platform") or "", source.get("metadata_json") or "{}"),
            )
            target_project_id = int(cur.lastrowid)
            _copy_memory(conn, project_id, target_project_id)
        else:
            target_project_id = project_id

    for chapter in chapters[:10]:
        original_report = detect_ai_tone(chapter["content"]).model_dump()
        rewritten, meta = rewrite_as_scene_driven_narrative(chapter["content"], chapter["title"], int(chapter["chapter_number"]), client)
        new_report = detect_ai_tone(rewritten).model_dump()
        consistency = ConsistencyChecker(None).check("", rewritten, "").model_dump()
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO chapters (project_id, chapter_number, volume, title, content, outline, status, word_count)
                VALUES (?, ?, ?, ?, ?, ?, 'novelized', ?)
                """,
                (target_project_id, chapter["chapter_number"], chapter.get("volume") or "", chapter["title"], rewritten, chapter.get("outline") or "", len(rewritten)),
            )
            new_chapter_id = conn.execute("SELECT id FROM chapters WHERE project_id = ? AND chapter_number = ?", (target_project_id, chapter["chapter_number"])).fetchone()["id"]
            for report_type, report in [("ai_tone_detector", new_report), ("consistency", consistency)]:
                conn.execute(
                    "INSERT INTO quality_reports (project_id, chapter_id, report_type, score, risk_level, report_json) VALUES (?, ?, ?, ?, ?, ?)",
                    (target_project_id, new_chapter_id, report_type, report.get("overall_score") or (100 if consistency.get("passed") else 70), report.get("risk_level") or ("low" if consistency.get("passed") else "medium"), json.dumps(report, ensure_ascii=False)),
                )
            log_generation(conn, target_project_id, "novelize_project", provider="ollama" if client else "local", model=client.model if client else "", response=rewritten, structured={"meta": meta, "original_ai_tone": original_report, "new_ai_tone": new_report}, chapter_id=new_chapter_id, module_name="novelization_rewriter", output_json={"meta": meta, "new_ai_tone": new_report}, user_action="novelize", applied_to_chapter=True)
        chapter_reports.append({
            "chapter_number": chapter["chapter_number"],
            "title": chapter["title"],
            "original_ai_tone_score": original_report["overall_score"],
            "new_ai_tone_score": new_report["overall_score"],
            "original_risk": original_report["risk_level"],
            "new_risk": new_report["risk_level"],
            "original_chars": len(chapter["content"] or ""),
            "new_chars": len(rewritten),
            "removed_template_hooks": meta.get("removed_template_hooks", []),
            "reduced_exposition_blocks": len(meta.get("reduced_exposition_blocks", [])),
        })

    docx_path = ""
    preview = {}
    if export_docx:
        docx_path = str(output_dir / "玫瑰大厦_小说化重写版.docx")
        with db_session() as conn:
            export_project_docx(conn, target_project_id, docx_path, model_name=client.model if client else "local_novelization")
        preview = preview_docx(docx_path)

    report = {
        "source_project_id": project_id,
        "target_project_id": target_project_id,
        "processed_chapters": len(chapter_reports),
        "chapters": chapter_reports,
        "docx_path": docx_path,
        "docx_preview": preview,
    }
    (output_dir / "玫瑰大厦_小说化重写报告.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# 玫瑰大厦 小说化重写报告", "", f"- 源项目 ID：{project_id}", f"- 新项目 ID：{target_project_id}", f"- 处理章节数：{len(chapter_reports)}", f"- DOCX：{docx_path}", "", "## 分章结果"]
    for item in chapter_reports:
        md.append(f"- 第 {item['chapter_number']} 章《{item['title']}》：{item['original_risk']}({item['original_ai_tone_score']}) -> {item['new_risk']}({item['new_ai_tone_score']})，{item['original_chars']} -> {item['new_chars']} 字符")
    (output_dir / "玫瑰大厦_小说化重写报告.md").write_text("\n".join(md), encoding="utf-8")
    report["report_json_path"] = str(output_dir / "玫瑰大厦_小说化重写报告.json")
    report["report_md_path"] = str(output_dir / "玫瑰大厦_小说化重写报告.md")
    return report
