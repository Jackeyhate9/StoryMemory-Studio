from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from app.checkers.consistency import ConsistencyChecker
from app.context.builder import ContextBuilder
from app.creative_center import detect_ai_tone_for_chapter
from app.creation.commit_memory import commit_create_novel_result
from app.creation.preview_store import save_preview
from app.db.database import db_session, get_project, init_db, log_generation
from app.db.models import ContextRequest
from app.export.docx_export import export_project_docx
from app.generation.chapter import generate_chapter as product_generate_chapter
from app.llm.client import OllamaClient
from app.llm.ollama_utils import select_best_ollama_model
from app.llm.output_cleaner import clean_model_output
from app.memory.extractor import MemoryExtractor
from app.memory.writer import upsert_extraction
from app.schemas.create_novel import CreateNovelResult


ROSE_PROJECT_NAME = "玫瑰大厦"


def rose_mansion_bible(chapters: int = 10, words_per_chapter: int = 3000, title: str = ROSE_PROJECT_NAME) -> CreateNovelResult:
    chapter_titles = [
        "玻璃穹顶下的欢迎会",
        "寄居者的琴房",
        "完美女孩的午餐局",
        "凤尾会议室",
        "热搜之前",
        "玫瑰慈善夜",
        "旧账本",
        "雨中的顶层花园",
        "崩塌预告",
        "大厦停电夜",
    ]
    goals = [
        "让谢临川回到玫瑰大厦，并与寄居少女林照音第一次正面交锋。",
        "展示林照音的艺术天赋和寄居处境，埋下她父母旧案线索。",
        "让商业联盟少女薛明棠入场，形成温柔规则与锋利自尊的对照。",
        "展示年轻管理者王知微的控制力，以及家族企业表面体面的裂缝。",
        "引入新媒体热搜危机，让年轻一代被迫站队。",
        "用慈善夜呈现家族繁华和衰败，推进感情误解。",
        "让旧账本出现，轻悬疑线进入实质阶段。",
        "让谢临川和林照音短暂靠近，又因误会分开。",
        "揭示玫瑰大厦财务危机和继承权暗战。",
        "停电夜集中爆发秘密，留下第二卷钩子。",
    ]
    outlines = []
    for i in range(1, chapters + 1):
        title = chapter_titles[i - 1] if i <= len(chapter_titles) else f"第{i}章 暗流"
        outlines.append(
            {
                "chapter_number": i,
                "title": title,
                "chapter_goal": goals[i - 1] if i <= len(goals) else "推进家族暗线和人物关系。",
                "main_conflict": "年轻一代在情感、继承权、艺术理想和商业利益之间互相试探。",
                "characters": ["谢临川", "林照音", "薛明棠", "王知微"],
                "key_events": [f"{title}中出现新的家族暗流和情感误解。"],
                "new_information": [f"玫瑰大厦衰败真相第{i}层信息。"],
                "foreshadows": ["旧账本", "顶层花园钥匙", "匿名账号“玫瑰灰”"],
                "ending_hook": f"章节结尾抛出一个足以改变第{i + 1}章关系判断的新线索。",
                "memory_facts": [
                    "谢临川厌恶继承规则但无法逃离。",
                    "林照音害怕被家族再次抛弃。",
                    "玫瑰大厦表面繁华，内部正在衰败。",
                ],
            }
        )

    return CreateNovelResult.model_validate(
        {
            "project": {
                "title": title,
                "genre": "现代都市轻小说 / 青春群像 / 家族企业 / 情感讽刺 / 轻悬疑",
                "platform": "轻小说 / 小红书连载 / 番茄小说可读风格",
                "target_reader": "喜欢现代群像、家族关系、青春情感、轻悬疑和人物关系拉扯的读者。",
                "expected_chapters": chapters,
                "chapter_word_count": words_per_chapter,
                "logline": "一座由旧家族企业建成的豪华大厦里，年轻一代在继承、爱情、艺术和利益之间互相靠近又互相伤害，而这座大厦的繁华正在悄悄崩塌。",
                "core_selling_points": ["现代家族群像", "情感拉扯", "精致讽刺", "隐藏秘密", "继承权暗战", "青春伤痛", "轻悬疑"],
            },
            "world_rules": [
                {"category": "现代都市", "rule_text": "故事发生在大型家族企业、私立学院、艺术圈和新媒体圈交织的现代都市环境。", "rigidity": "hard"},
                {"category": "家族结构", "rule_text": "谢家以玫瑰大厦和玫瑰资本为核心，资源分配由长辈和企业董事会共同影响。", "rigidity": "hard"},
                {"category": "改编边界", "rule_text": "可以借鉴古典群像气质，但不能复刻《红楼梦》章节、原句和具体情节。", "rigidity": "hard"},
                {"category": "主题", "rule_text": "表面繁华必须始终伴随衰败迹象：债务、舆论、继承权争夺、情感误解。", "rigidity": "hard"},
            ],
            "characters": [
                {"name": "谢临川", "role": "男主 / 家族继承人之一", "personality": "敏感、散漫、共情力强，厌恶功利规则。", "motivation": "想逃离继承位，却又无法放下大厦里的人。", "secrets": "知道父亲离开董事会前留下过一份旧账本。", "status": "active", "current_location": "玫瑰大厦", "hard_constraints": "不能写成无脑霸总或爽文式支配者。"},
                {"name": "林照音", "role": "女主 / 寄居天才少女", "personality": "敏感锋利，自尊心强，擅长写作和音乐。", "motivation": "想证明自己不是被施舍的人，也想查清父母旧事。", "secrets": "她收藏的旧曲谱夹着玫瑰资本早年转账复印件。", "status": "active", "current_location": "玫瑰大厦琴房", "hard_constraints": "不能弱化为单纯被拯救角色。"},
                {"name": "薛明棠", "role": "商业联盟中的完美女性", "personality": "理性、稳重、情商高，懂规则，也被规则困住。", "motivation": "维系家族联盟，同时保留自己的选择权。", "status": "active", "hard_constraints": "不能扁平化为情敌。"},
                {"name": "王知微", "role": "年轻企业管理者", "personality": "精明、能干、控制欲强，擅长处理人情和利益。", "motivation": "守住玫瑰资本现金流和自己的权力位置。", "status": "active", "hard_constraints": "强势但必须有代价和疲惫感。"},
                {"name": "谢老太太", "role": "家族精神核心", "personality": "表面慈爱，实际掌握资源分配。", "motivation": "维持家族体面，防止玫瑰大厦的真相外泄。", "status": "active"},
                {"name": "许见微", "role": "新媒体账号主理人", "personality": "聪明、八卦、擅长捕捉情绪裂缝。", "motivation": "借豪门秘闻出圈。", "status": "active"},
            ],
            "relationships": [
                {"character_a": "谢临川", "character_b": "林照音", "relationship_type": "共鸣 / 误解 / 试探", "status": "亲近但不稳定", "description": "两人都厌恶被安排的命运，却常因自尊和误会互相刺伤。"},
                {"character_a": "谢临川", "character_b": "薛明棠", "relationship_type": "商业联姻压力", "status": "礼貌合作", "description": "外界默认两人适合结盟，但两人都知道这不是爱情。"},
                {"character_a": "林照音", "character_b": "薛明棠", "relationship_type": "欣赏 / 嫉妒 / 防备", "status": "暗中比较", "description": "一个锐利，一个周全，都能看穿对方的孤独。"},
                {"character_a": "王知微", "character_b": "谢老太太", "relationship_type": "执行者 / 授权者", "status": "互相利用", "description": "王知微替家族处理脏活，也因此握住部分秘密。"},
            ],
            "locations": [
                {"name": "玫瑰大厦", "type": "家族企业总部与居住空间", "description": "顶层花园、玻璃穹顶、宴会厅、办公室和家族套房叠在一起的豪华大厦。", "rules": "越往上越接近权力，也越接近秘密。"},
                {"name": "星河私立学院", "type": "私立学院", "description": "年轻一代读书、社交、被比较和被曝光的地方。"},
                {"name": "白盒艺术中心", "type": "艺术圈场域", "description": "林照音演出和展览的主要地点，也是家族做形象工程的窗口。"},
                {"name": "镜面传媒", "type": "新媒体圈", "description": "许见微所在的内容公司，擅长制造热搜。"},
            ],
            "organizations": [
                {"name": "玫瑰资本", "type": "家族企业", "description": "谢家核心资产，表面仍强盛，实际现金流紧张。", "leader": "谢老太太", "status": "暗中衰败"},
                {"name": "明棠集团", "type": "商业盟友", "description": "薛明棠家族企业，是玫瑰资本最重要的外部盟友。", "leader": "薛家", "status": "观望"},
                {"name": "镜面传媒", "type": "新媒体机构", "description": "掌握年轻圈层舆论，盯上玫瑰大厦秘闻。", "leader": "许见微", "status": "试探中"},
            ],
            "abilities": [
                {"name": "情绪洞察", "owner": "谢临川", "system": "人物能力", "description": "能敏锐察觉他人情绪变化，但常因此逃避决断。"},
                {"name": "文字与音乐表达", "owner": "林照音", "system": "艺术天赋", "description": "能把难以说出口的情绪写进短文和旋律。"},
                {"name": "关系调度", "owner": "王知微", "system": "管理能力", "description": "能迅速判断人情和利益走向。"},
            ],
            "items": [
                {"name": "旧账本", "type": "关键证物", "description": "记录玫瑰资本早年灰色交易的账本。", "status": "失踪"},
                {"name": "顶层花园钥匙", "type": "地点钥匙", "description": "能打开玫瑰大厦顶层旧温室。", "owner": "谢老太太"},
                {"name": "匿名账号“玫瑰灰”", "type": "新媒体线索", "description": "持续发布玫瑰大厦内部隐喻短文。", "status": "未确认身份"},
            ],
            "plot_threads": [
                {"name": "继承权暗战", "thread_type": "main", "status": "open", "summary": "谢临川被推向继承位，各方借情感和舆论施压。", "related_characters": ["谢临川", "王知微", "谢老太太"]},
                {"name": "林照音父母旧案", "thread_type": "mystery", "status": "open", "summary": "林照音父母与玫瑰资本早年交易有关。", "related_characters": ["林照音", "谢临川"]},
                {"name": "玫瑰大厦衰败", "thread_type": "main", "status": "open", "summary": "豪华表象下，企业现金流和家族关系同时崩坏。", "related_characters": ["王知微", "谢老太太"]},
            ],
            "foreshadows": [
                {"name": "旧账本", "related_characters": ["谢临川", "林照音"], "related_items": ["旧账本"], "related_thread": "林照音父母旧案", "expected_resolution_chapter": 7, "risk_note": "第7章必须出现实体线索。"},
                {"name": "顶层花园钥匙", "related_characters": ["谢老太太"], "related_items": ["顶层花园钥匙"], "related_thread": "玫瑰大厦衰败", "expected_resolution_chapter": 8, "risk_note": "钥匙代表资源分配和家族秘密。"},
                {"name": "匿名账号“玫瑰灰”", "related_characters": ["许见微"], "related_items": ["匿名账号“玫瑰灰”"], "related_thread": "继承权暗战", "expected_resolution_chapter": 10, "risk_note": "第10章至少揭示账号与大厦内部有关。"},
            ],
            "timeline_events": [
                {"story_time": "开篇当天傍晚", "sort_key": "001", "event_text": "谢临川回到玫瑰大厦参加欢迎会。", "location": "玫瑰大厦", "characters": ["谢临川", "林照音"]},
                {"story_time": "三年前", "sort_key": "P001", "event_text": "林照音父母离开玫瑰资本关联项目。", "location": "玫瑰资本", "characters": ["林照音"]},
            ],
            "style_profile": {
                "name": "现代轻小说群像文风",
                "platform": "轻小说 / 小红书连载 / 番茄小说可读风格",
                "pov": "第三人称有限视角，多角色切换但每场只跟随一个核心视角。",
                "sentence_length": "中短句为主，关键情绪处允许短句断裂。",
                "dialogue_ratio": "35%-45%",
                "description_ratio": "25%",
                "inner_monologue_ratio": "20%",
                "high_point_density": "每章至少一个关系反转、秘密线索或情绪钩子。",
                "common_patterns": ["细腻关系", "轻讽刺", "现代都市画面", "章节结尾钩子"],
                "banned_expressions": ["命运的齿轮", "空气凝固", "复杂的情绪", "这一切才刚刚开始"],
                "pacing": "开头快速入场，中段用对话推进关系，结尾留下悬念。",
                "sample_text": "语言自然，不古风，不生硬说明。",
            },
            "forbidden_rules": [
                {"rule_text": "不要修仙，不要系统，不要无脑霸总，不要低俗擦边，不要简单校园恋爱。", "category": "内容禁忌"},
                {"rule_text": "不要直接照搬《红楼梦》情节、章节和原句。", "category": "改编安全"},
                {"rule_text": "不要 AI 腔、直译腔、生硬总结。", "category": "文风禁忌"},
            ],
            "unresolved_questions": [
                {"question": "旧账本现在在谁手里？", "related_thread": "林照音父母旧案", "related_characters": ["林照音", "谢临川"], "priority": "high"},
                {"question": "匿名账号“玫瑰灰”是谁在运营？", "related_thread": "继承权暗战", "related_characters": ["许见微"], "priority": "high"},
                {"question": "谢老太太是否知道玫瑰资本真实债务？", "related_thread": "玫瑰大厦衰败", "related_characters": ["谢老太太"], "priority": "medium"},
            ],
            "volume_outline": ["第一卷：玫瑰大厦欢迎会到停电夜，年轻一代的亲密、误解和继承权暗战被热搜与旧账本推到台前。"],
            "chapter_outlines": outlines,
            "first_chapter": {
                "title": "玻璃穹顶下的欢迎会",
                "content": "玫瑰大厦的玻璃穹顶亮得像一场永不散场的宴会。谢临川回到这里时，所有人都在笑，只有林照音站在琴房门口，像听见了楼体深处第一声细小的裂响。",
                "summary": "谢临川回到玫瑰大厦，林照音在欢迎会上入场，两人第一次正面交锋。",
                "facts": ["谢临川回到玫瑰大厦。", "林照音寄居在玫瑰大厦。", "玫瑰大厦表面繁华，内部有衰败迹象。"],
            },
        }
    )


def strip_model_artifacts(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    text = re.sub(r"```(?:text|markdown)?", "", text)
    cut_patterns = [
        r"\n\s*(?:Let's|Self-Correction|Self-Correction/Refinement|Refinement during thought|I will carefully craft|Need to ensure|Check dialogue ratio|Check banned words|Check hook)\b",
        r"\n\s*\*Self-Correction/Refinement during thought:\*",
        r"\n\s*\*\s*\*Adjustments during drafting:\*",
        r"\n\s*\*\s*Adjustments during drafting:\*",
    ]
    for pattern in cut_patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            text = text[: match.start()]
    text = re.sub(r"(?m)^\s*(?:Let's|Need to|Check |I will carefully|Self-Correction|Adjustments during drafting).*$", "", text)
    cleaned_lines = []
    for line in text.splitlines():
        ascii_letters = len(re.findall(r"[A-Za-z]", line))
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", line))
        meta_markers = ["Characters in Scene", "Setting:", "Plot Points", "Scene ", "Drafting", "word count", "Foreshadows:"]
        if ascii_letters >= 18 and chinese_chars < 8:
            continue
        if any(marker in line for marker in meta_markers):
            continue
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)
    return text.strip()


def clean_existing_generated_chapters(project_id: int) -> int:
    cleaned = 0
    with db_session() as conn:
        rows = conn.execute("SELECT id, content FROM chapters WHERE project_id = ?", (project_id,)).fetchall()
        for row in rows:
            content = row["content"] or ""
            clean = strip_model_artifacts(content)
            if clean != content:
                conn.execute(
                    "UPDATE chapters SET content = ?, word_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (clean, len(clean), row["id"]),
                )
                cleaned += 1
    return cleaned


def generate_chapter_text(client: OllamaClient, context: str, title: str, target_words: int) -> str:
    system = "你是长篇现代都市轻小说作者。只输出原创小说正文，不要解释，不要复述提示词。"
    base_rules = f"""
请创作《玫瑰大厦》的章节《{title}》。
目标长度约 {target_words} 字，现代都市轻小说风格，人物关系细腻，有轻讽刺和轻悬疑。
不要古风腔，不要 AI 腔，不要直接照搬《红楼梦》原句或情节。
必须遵守 Story Memory，不要让人物、伏笔、时间线穿帮。
章节结尾必须有明确追读钩子。
"""
    if target_words >= 2200:
        first = client.complete(
            f"{context}\n\n{base_rules}\n先写本章上半章，约 {target_words // 2} 字，停在一个小转折处。",
            system=system,
            temperature=0.72,
        )
        first = clean_model_output(strip_model_artifacts(first), mode="prose")
        second = client.complete(
            f"{context}\n\n本章上半章如下：\n{first[-2500:]}\n\n继续写下半章，约 {target_words // 2} 字。承接上文，不重复开头，结尾给出强钩子。",
            system=system,
            temperature=0.72,
        )
        text = f"{first}\n\n{clean_model_output(strip_model_artifacts(second), mode='prose')}"
    else:
        text = clean_model_output(strip_model_artifacts(client.complete(f"{context}\n\n{base_rules}", system=system, temperature=0.72)), mode="prose")
    if len(text) < target_words * 0.55:
        more = client.complete(
            f"{context}\n\n已有正文：\n{text[-3000:]}\n\n正文偏短，请补写 800-1200 字，增加对话、场景动作和结尾钩子，不要重复。",
            system=system,
            temperature=0.72,
        )
        text = f"{text}\n\n{clean_model_output(strip_model_artifacts(more), mode='prose')}"
    return text


def generate_chapter_text(client: OllamaClient, context: str, title: str, target_words: int) -> str:
    """Use the production chapter pipeline for E2E runs.

    Older acceptance smoke code called Ollama directly and could leak model
    thinking, English drafting notes, or duplicated fragments. Keeping this
    wrapper aligned with app.generation.chapter makes opencode/CLI smoke tests
    behave like the Streamlit MVP path.
    """
    extra = (
        f"请创作章节《{title}》，目标长度约 {target_words} 个中文字符。"
        "只输出中文小说正文，不要输出英文、<think>、提纲、检查项、创作说明或 Markdown。"
        "必须遵守 Story Memory、上一章桥接、人物关系、伏笔和时间线。"
        "结尾必须落在具体事件、物件、账页、消息、来客或一句未说完的话上。"
    )
    return product_generate_chapter(client, context, mode="generate_chapter", extra_instruction=extra, temperature=0.72)


def run_rose_mansion_e2e(
    title: str = ROSE_PROJECT_NAME,
    chapters: int = 10,
    words_per_chapter: int = 3000,
    output_docx: str | Path | None = "exports/玫瑰大厦_10章测试版.docx",
    reset: bool = True,
) -> dict[str, Any]:
    started = time.time()
    init_db()
    selection = select_best_ollama_model()
    if not selection.available or not selection.model:
        return {"ok": False, "stage": "ollama", "selection": selection.model_dump()}

    if reset:
        with db_session() as conn:
            row = conn.execute("SELECT id FROM projects WHERE name = ? OR title = ?", (title, title)).fetchone()
            if row:
                conn.execute("DELETE FROM projects WHERE id = ?", (row["id"],))

    bible = rose_mansion_bible(chapters, words_per_chapter, title)
    preview_path = save_preview(bible, title)
    committed = commit_create_novel_result(bible, title, "ollama")
    client = OllamaClient(_ollama_base_url(), selection.model)

    chapter_stats = []
    for outline in bible.chapter_outlines[:chapters]:
        with db_session() as conn:
            project = get_project(conn, title)
            context = ContextBuilder(conn, project).build(
                ContextRequest(
                    project=title,
                    chapter_number=outline.chapter_number,
                    chapter_goal=outline.chapter_goal,
                    chapter_outline=json.dumps(outline.model_dump(), ensure_ascii=False),
                    characters=outline.characters,
                    locations=["玫瑰大厦", "星河私立学院", "白盒艺术中心"],
                    mode="standard",
                )
            )
        text = generate_chapter_text(client, context, outline.title, words_per_chapter)
        with db_session() as conn:
            project = get_project(conn, title)
            conn.execute(
                """
                INSERT INTO chapters (project_id, chapter_number, volume, title, content, outline, status, word_count)
                VALUES (?, ?, ?, ?, ?, ?, 'draft', ?)
                ON CONFLICT(project_id, chapter_number) DO UPDATE SET
                  title=excluded.title, content=excluded.content, outline=excluded.outline,
                  word_count=excluded.word_count, updated_at=CURRENT_TIMESTAMP
                """,
                (project["id"], outline.chapter_number, "第一卷：玫瑰大厦", outline.title, text, json.dumps(outline.model_dump(), ensure_ascii=False), len(text)),
            )
            chapter_id = conn.execute(
                "SELECT id FROM chapters WHERE project_id = ? AND chapter_number = ?",
                (project["id"], outline.chapter_number),
            ).fetchone()["id"]
            extraction = MemoryExtractor(None).extract(outline.title, text)
            upsert_extraction(conn, project["id"], chapter_id, extraction)
            consistency = ConsistencyChecker(None).check(context, text, outline.chapter_goal).model_dump()
            conn.execute(
                """
                INSERT INTO quality_reports (project_id, chapter_id, report_type, score, risk_level, report_json)
                VALUES (?, ?, 'consistency', ?, ?, ?)
                """,
                (
                    project["id"],
                    chapter_id,
                    100 if consistency.get("passed") else 70,
                    "low" if consistency.get("passed") else "medium",
                    json.dumps(consistency, ensure_ascii=False),
                ),
            )
            log_generation(
                conn,
                project["id"],
                "e2e_ollama_generate_chapter",
                provider="ollama",
                model=selection.model,
                prompt=context,
                response=text,
                structured={"consistency": consistency, "outline": outline.model_dump()},
                chapter_id=chapter_id,
                module_name="acceptance_e2e",
                output_json={"chapter_number": outline.chapter_number, "word_count": len(text), "consistency": consistency},
                user_action="generate",
                applied_to_chapter=True,
            )
            project_id = project["id"]
        ai_report = detect_ai_tone_for_chapter(project_id, chapter_id)
        chapter_stats.append(
            {
                "chapter_number": outline.chapter_number,
                "title": outline.title,
                "chars": len(text),
                "ai_tone": ai_report.get("risk_level"),
                "hook_likely": any(mark in text[-400:] for mark in ["？", "!", "！", "短信", "账号", "钥匙", "账本", "停电", "门", "电话", "热搜"]),
            }
        )

    with db_session() as conn:
        project = get_project(conn, title)
        project_id = int(project["id"])
    cleaned_chapters = clean_existing_generated_chapters(project_id)

    with db_session() as conn:
        project = get_project(conn, title)
        output_path = export_project_docx(conn, project["id"], output_docx, selection.model) if output_docx else ""
        counts = {
            "characters": conn.execute("SELECT COUNT(*) n FROM characters WHERE project_id=?", (project["id"],)).fetchone()["n"],
            "world_rules": conn.execute("SELECT COUNT(*) n FROM world_rules WHERE project_id=?", (project["id"],)).fetchone()["n"],
            "foreshadows": conn.execute("SELECT COUNT(*) n FROM foreshadows WHERE project_id=?", (project["id"],)).fetchone()["n"],
            "timeline_events": conn.execute("SELECT COUNT(*) n FROM timeline_events WHERE project_id=?", (project["id"],)).fetchone()["n"],
            "chapter_facts": conn.execute("SELECT COUNT(*) n FROM chapter_facts WHERE project_id=?", (project["id"],)).fetchone()["n"],
            "generation_logs": conn.execute("SELECT COUNT(*) n FROM generation_logs WHERE project_id=?", (project["id"],)).fetchone()["n"],
            "quality_reports": conn.execute("SELECT COUNT(*) n FROM quality_reports WHERE project_id=?", (project["id"],)).fetchone()["n"],
        }
        project_id = project["id"]

    return {
        "ok": True,
        "project_id": project_id,
        "project_name": title,
        "preview_path": str(preview_path),
        "committed": committed,
        "ollama": selection.model_dump(),
        "chapter_stats": chapter_stats,
        "counts": counts,
        "docx_path": str(output_path),
        "cleaned_chapters": cleaned_chapters,
        "elapsed_seconds": round(time.time() - started, 1),
    }


def _ollama_base_url() -> str:
    from app.config import get_settings

    return get_settings().ollama_base_url
