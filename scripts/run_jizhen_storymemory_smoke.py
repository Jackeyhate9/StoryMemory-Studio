from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.context.builder import ContextBuilder
from app.db.database import db_session, dumps, init_db, log_generation, rows_to_dicts
from app.db.models import ContextRequest
from app.export.docx_export import export_project_docx
from app.generation.chapter import generate_chapter
from app.llm.client import OllamaClient
from app.memory.extractor import MemoryExtractor
from app.memory.writer import upsert_extraction


PROJECT_NAME = "jizhenzhai_storymemory_smoke"
TITLE = "集珍斋"
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
MODEL_PRIORITY = ["qwen3", "qwen2.5", "deepseek-r1", "yi", "glm", "llama3.1", "mistral", "gemma"]


def choose_model(client: OllamaClient) -> str:
    models = client.list_models()
    lowered = [(m, m.lower()) for m in models]
    for key in MODEL_PRIORITY:
        for name, lower in lowered:
            if key in lower:
                return name
    if not models:
        raise RuntimeError("Ollama 未返回可用模型，请先运行：ollama pull qwen2.5:7b 或 ollama pull qwen3")
    return models[0]


def seed_project(conn) -> dict:
    conn.execute("DELETE FROM projects WHERE name = ?", (PROJECT_NAME,))
    conn.execute(
        """
        INSERT INTO projects (name, title, description, genre, target_platform, current_volume, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            PROJECT_NAME,
            TITLE,
            "民国初年到解放战争时期，一家玉器老字号在东陵盗宝余波、同行竞争、军阀贪欲与侵略阴影中守住手艺和底线。",
            "历史传奇 / 民国商战 / 玉器修复 / 家族群像 / 轻悬疑",
            "长篇连载",
            "第一卷：碎玉照人心",
            dumps({"expected_chapters": 100, "smoke_test": True}),
        ),
    )
    project = dict(conn.execute("SELECT * FROM projects WHERE name = ?", (PROJECT_NAME,)).fetchone())
    pid = project["id"]

    characters = [
        ("改松岩", "集珍斋掌柜，碎玉修复高手", "沉稳克制，眼力极准，不轻易许诺", "守住集珍斋与师门手艺，不让国宝落入外人手中", "active", "集珍斋"),
        ("叶含章", "前朝旧族之女，懂古玉来历", "清冷敏锐，话少但看事通透", "查清父亲卷入东陵残玉案的真相", "active", "北平"),
        ("改砚秋", "改松岩的侄女，学徒", "胆大心细，想证明女子也能掌眼修玉", "成为集珍斋真正的传人", "active", "集珍斋"),
        ("范允初", "同行玉器商，改松岩旧友", "圆滑有野心，常在忠义和利益间摇摆", "借乱世翻身，吞并几家老字号", "active", "隆玉堂"),
        ("罗振魁", "军阀副官", "粗豪贪婪，但懂得借势", "替上峰搜罗珍玩，逼迫商号交货", "active", "北平城"),
        ("宫本佐纪", "日本古董商代理人", "礼貌、冷静、危险", "追查东陵流出的玉册残件", "active", "东交民巷"),
    ]
    conn.executemany(
        """
        INSERT INTO characters
        (project_id, name, role, personality, motivation, status, current_location, hard_constraints, importance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(pid, *row, "不直接解释全部秘密，重要动机通过行动逐步暴露", 90 if row[0] in {"改松岩", "叶含章"} else 70) for row in characters],
    )

    relationships = [
        ("改松岩", "叶含章", "互相试探", "未完全信任", "叶含章带来残玉线索，改松岩怀疑她另有隐情。"),
        ("改松岩", "改砚秋", "叔侄/师徒", "亲近但严格", "改松岩不愿让她卷入危险，改砚秋偏要进柜台学真本事。"),
        ("改松岩", "范允初", "旧友/竞争者", "暗中破裂", "二人曾同门学艺，如今一个守旧规，一个逐利。"),
        ("范允初", "罗振魁", "利益勾连", "互相利用", "范允初想借军阀压力逼集珍斋交出残玉。"),
        ("叶含章", "宫本佐纪", "旧案牵连", "危险接近", "宫本掌握叶父旧案碎片，试图引她开口。"),
    ]
    conn.executemany(
        """
        INSERT INTO character_relationships
        (project_id, character_a_name, character_b_name, relationship_type, status, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(pid, *row) for row in relationships],
    )

    rules = [
        ("时代规则", "故事处于民国乱世，商号必须同时应对警署、军阀、同行会馆和租界势力。", "hard"),
        ("玉器规则", "碎玉修复讲究补、锔、磨、沁色与旧痕判断，不能像变魔术一样瞬间复原。", "hard"),
        ("行业规则", "老字号的信誉比一单买卖更重，失信会被同行会馆除名。", "hard"),
        ("东陵残玉", "东陵盗宝案流出的残玉牵涉军阀、外商、旧族和古董行，任何线索都可能招祸。", "hard"),
        ("民族底线", "集珍斋不能把疑似国宝级文物流向侵略者或走私线。", "hard"),
        ("叙事规则", "秘密不能一次性解释完，必须通过物件、来客、账本、修复痕迹和人物反应逐步释放。", "hard"),
        ("人物规则", "改松岩不会轻易把恐惧说出口；叶含章不会直接讲明全部来意；范允初不会公开承认背叛。", "hard"),
        ("章节规则", "每章结尾必须落在具体物件、信件、账页、破损纹路、来客或一句未说完的话上。", "hard"),
    ]
    conn.executemany(
        "INSERT INTO world_rules (project_id, category, rule_text, rigidity) VALUES (?, ?, ?, ?)",
        [(pid, *row) for row in rules],
    )

    locations = [
        ("集珍斋", "老字号玉器行", "前店后院，柜台下藏着旧账暗格，修玉室只许少数人进。", "夜里不可随意开后院暗柜。"),
        ("隆玉堂", "竞争商号", "范允初经营的新派玉器行，常和军政人物往来。", "账目干净得反常。"),
        ("琉璃厂", "古玩街", "消息流动最快的地方，真货假货、真话假话混在一起。", "任何消息都可能被转卖。"),
        ("东交民巷", "租界边缘", "外商、买办和情报贩子出没。", "国宝线索到这里就会变得危险。"),
    ]
    conn.executemany(
        "INSERT INTO locations (project_id, name, type, description, rules) VALUES (?, ?, ?, ?, ?)",
        [(pid, *row) for row in locations],
    )

    organizations = [
        ("集珍斋", "玉器老字号", "改家经营三代，以修玉和掌眼闻名。", "改松岩", "active"),
        ("隆玉堂", "同行商号", "新派古董行，善借权势压价收货。", "范允初", "active"),
        ("北平古玩行会", "行业组织", "维持行规，也会被权势左右。", "会首许廷瑞", "shaky"),
        ("罗公馆", "军阀势力", "以搜罗珍玩为名敲诈商号。", "罗振魁", "active"),
    ]
    conn.executemany(
        "INSERT INTO organizations (project_id, name, type, description, leader, status) VALUES (?, ?, ?, ?, ?, ?)",
        [(pid, *row) for row in organizations],
    )

    items = [
        ("青白玉龙纹佩残片", "残玉", "疑似东陵流出玉册的一角，断口有旧修痕。", "叶含章", "集珍斋", "待鉴定"),
        ("改家旧账本", "账本", "记录多年修玉往来，其中夹有几笔不能公开的旧账。", "改松岩", "修玉室暗格", "封存"),
        ("银锔钉匣", "工具", "改松岩师父留下的修玉工具，匣底藏着旧门规。", "改松岩", "修玉室", "可用"),
    ]
    conn.executemany(
        "INSERT INTO items (project_id, name, type, description, owner, location, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(pid, *row) for row in items],
    )

    threads = [
        ("东陵残玉线", "main", "open", "残玉来源牵出盗宝旧案和外商走私线。", ["改松岩", "叶含章", "宫本佐纪"]),
        ("集珍斋存亡线", "business", "open", "军阀和同行逼迫集珍斋交货，老字号信誉遭遇考验。", ["改松岩", "范允初", "罗振魁"]),
        ("师门旧债线", "character", "open", "改松岩与范允初同门旧事逐步暴露。", ["改松岩", "范允初"]),
    ]
    conn.executemany(
        """
        INSERT INTO plot_threads (project_id, name, thread_type, status, summary, related_characters_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(pid, name, typ, status, summary, dumps(chars)) for name, typ, status, summary, chars in threads],
    )

    foreshadows = [
        ("残玉断口的双层旧沁", ["改松岩", "叶含章"], ["青白玉龙纹佩残片"], "东陵残玉线", "unresolved", 18, "证明残玉曾被二次修复", "断口不合常理，像被人故意修旧。"),
        ("旧账本缺页", ["改松岩"], ["改家旧账本"], "师门旧债线", "unresolved", 25, "揭出改家曾替某位旧臣修过禁物", "账本页码连不上。"),
        ("范允初袖口的银粉", ["范允初"], ["银锔钉匣"], "师门旧债线", "unresolved", 12, "暗示他仍在偷偷修一件不能见光的玉", "袖口沾有修玉银粉。"),
        ("叶含章的半枚印章", ["叶含章"], ["青白玉龙纹佩残片"], "东陵残玉线", "unresolved", 30, "连接叶父旧案与东陵残玉", "印章缺半边，只能和另一枚合读。"),
    ]
    conn.executemany(
        """
        INSERT INTO foreshadows
        (project_id, name, related_characters_json, related_items_json, related_thread, status,
         expected_resolution_chapter, resolution_method, risk_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(pid, name, dumps(chars), dumps(items), thread, status, exp, method, risk) for name, chars, items, thread, status, exp, method, risk in foreshadows],
    )

    timeline = [
        ("民国初年", "001", "改家接下第一批宫中旧玉修复，集珍斋名声立住。", "集珍斋", ["改家"]),
        ("东陵盗宝后", "010", "一批失散珍玩流入北平古董行，集珍斋拒绝替陌生来路的玉件出具保书。", "琉璃厂", ["改松岩"]),
        ("第一卷开端", "020", "叶含章携残玉夜访集珍斋，罗振魁随后派人送来请帖。", "集珍斋", ["叶含章", "改松岩"]),
    ]
    conn.executemany(
        "INSERT INTO timeline_events (project_id, story_time, sort_key, event_text, location, characters_json) VALUES (?, ?, ?, ?, ?, ?)",
        [(pid, t, sk, e, loc, dumps(chars)) for t, sk, e, loc, chars in timeline],
    )

    conn.execute(
        """
        INSERT INTO style_profiles
        (project_id, name, platform, pov, sentence_length, dialogue_ratio, description_ratio,
         inner_monologue_ratio, high_point_density, pacing, safe_style_summary, do_rules_json, dont_rules_json, is_default)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            pid,
            "民国商战轻悬疑文风",
            "长篇连载",
            "第三人称有限视角",
            "中短句为主，关键处用短句压住节奏",
            "35%",
            "重视物件、手艺、店铺细节，少空泛抒情",
            "克制，不直接解释人物全部动机",
            "每章至少一个具体信息变化或物件钩子",
            "场景推进，结尾落在具体物证或来客上",
            "民国市井质感、玉器修复细节、商号人情与乱世压力并行；对话有试探和留白。",
            dumps(["用物件和动作释放信息", "保持章节衔接", "让人物通过选择暴露立场"]),
            dumps(["不要英文思考", "不要模板化结尾", "不要一次性解释设定卡"]),
        ),
    )

    forbidden = [
        ("不得出现英文草稿、<think>、模型自我说明或提示词残留。", "format", "critical"),
        ("不得让人物直接复述世界观设定。", "style", "high"),
        ("不得使用“游戏开始了”“一切才刚刚开始”“风暴将至”等模板钩子。", "style", "high"),
        ("不得把东陵残玉真相在前十章一次性揭开。", "plot", "critical"),
    ]
    conn.executemany(
        "INSERT INTO forbidden_rules (project_id, rule_text, category, severity) VALUES (?, ?, ?, ?)",
        [(pid, *row) for row in forbidden],
    )

    conn.execute(
        """
        INSERT INTO memory_chunks (project_id, source_type, chunk_type, title, content, keywords_json, importance)
        VALUES (?, 'project', 'outline', '前十章总纲', ?, ?, 80)
        """,
        (
            pid,
            "前十章围绕叶含章夜访、残玉鉴定、罗振魁施压、范允初暗中设局、集珍斋旧账本缺页、改砚秋误入修玉室线索展开。每章必须承接上一章结尾。",
            dumps(["前十章", "东陵残玉", "集珍斋", "承接"]),
        ),
    )
    return project


CHAPTERS = [
    ("夜扣集珍斋", "叶含章携残玉夜访，改松岩发现断口异常，门外同时响起罗公馆来人的敲门声。", ["改松岩", "叶含章", "改砚秋"], ["集珍斋"]),
    ("罗公馆的请帖", "承接敲门声，罗振魁送来请帖逼集珍斋赴宴鉴玉；改松岩不当场答应，叶含章留下《申报》旧剪报。", ["改松岩", "叶含章", "改砚秋", "罗振魁"], ["集珍斋"]),
    ("袖口银粉", "赴宴前改松岩去琉璃厂探消息，范允初出现并试探残玉，改砚秋发现他袖口有银粉。", ["改松岩", "范允初", "改砚秋"], ["琉璃厂", "隆玉堂"]),
    ("一只空锦盒", "罗公馆宴上拿出空锦盒逼问残玉下落，叶含章认出盒底暗纹却不肯明说。", ["改松岩", "叶含章", "罗振魁", "范允初"], ["罗公馆"]),
    ("账本缺页", "改松岩回店翻旧账，发现师父留下的账本缺页；改砚秋在暗格里摸到半枚印泥。", ["改松岩", "改砚秋"], ["集珍斋"]),
    ("东交民巷的买办", "宫本佐纪经买办递话愿高价收残玉，叶含章被迫承认父亲曾见过另一半玉册。", ["宫本佐纪", "叶含章", "改松岩"], ["东交民巷"]),
    ("修玉室的灯", "夜里修玉室灯亮，改砚秋误以为进贼，却撞见改松岩试拼残玉与旧印泥。", ["改松岩", "改砚秋"], ["集珍斋"]),
    ("隆玉堂放话", "范允初散布集珍斋藏赃谣言，行会要求改松岩三日内说明残玉来路。", ["改松岩", "范允初", "改砚秋"], ["琉璃厂", "集珍斋"]),
    ("雨夜验玉", "暴雨夜叶含章带来第二条线索：父亲旧友临终前说残玉不是从陵里出来，而是被人送进去过。", ["叶含章", "改松岩"], ["集珍斋"]),
    ("柜台下的名字", "改松岩撬开柜台暗格，找到缺页拓片；拓片背面出现范允初师父的名字。", ["改松岩", "改砚秋", "范允初"], ["集珍斋"]),
]


def insert_chapter(conn, project_id: int, number: int, title: str, content: str, outline: str) -> int:
    conn.execute(
        """
        INSERT INTO chapters (project_id, chapter_number, volume, title, content, outline, status, word_count)
        VALUES (?, ?, '第一卷：碎玉照人心', ?, ?, ?, 'draft', ?)
        ON CONFLICT(project_id, chapter_number) DO UPDATE SET
          title=excluded.title,
          content=excluded.content,
          outline=excluded.outline,
          word_count=excluded.word_count,
          updated_at=CURRENT_TIMESTAMP
        """,
        (project_id, number, title, content, outline, len(content)),
    )
    return int(conn.execute("SELECT id FROM chapters WHERE project_id = ? AND chapter_number = ?", (project_id, number)).fetchone()["id"])


def main() -> None:
    started = time.time()
    init_db()
    model_probe = OllamaClient(OLLAMA_BASE_URL, "dummy")
    model = choose_model(model_probe)
    client = OllamaClient(OLLAMA_BASE_URL, model)
    extractor = MemoryExtractor(None)

    with db_session() as conn:
        project = seed_project(conn)
        project_id = project["id"]

    context_samples: dict[str, str] = {}
    chapter_stats = []
    for index, (title, outline, characters, locations) in enumerate(CHAPTERS, start=1):
        with db_session() as conn:
            project = dict(conn.execute("SELECT * FROM projects WHERE name = ?", (PROJECT_NAME,)).fetchone())
            builder = ContextBuilder(conn, project)
            req = ContextRequest(
                project=PROJECT_NAME,
                chapter_number=index,
                chapter_goal=f"生成《{TITLE}》第 {index} 章《{title}》，必须和上一章自然衔接，并推进本章核心事件。",
                chapter_outline=outline,
                characters=characters,
                locations=locations,
                plot_threads=["东陵残玉线", "集珍斋存亡线", "师门旧债线"],
                mode="standard",
            )
            context = builder.build(req)
            if index in (1, 2, 3):
                context_samples[f"chapter_{index}"] = context[:8000]

        extra = (
            "烟测要求：生成 900-1400 个中文字符的正式小说正文，只输出正文。"
            "开头必须承接【上一章桥接】；不要出现英文、<think>、分析提纲、Markdown 标题。"
            "不要设定卡介绍人物；用玉器、店铺、账本、敲门声、座位和眼神推进关系。"
            "结尾必须落在一个具体物件、来客、账页、破损纹路或未说完的话上。"
        )
        content = generate_chapter(client, context, mode="generate_chapter", extra_instruction=extra, temperature=0.72)

        with db_session() as conn:
            project = dict(conn.execute("SELECT * FROM projects WHERE name = ?", (PROJECT_NAME,)).fetchone())
            chapter_id = insert_chapter(conn, project["id"], index, title, content, outline)
            extraction = extractor.extract(title, content)
            upsert_extraction(conn, project["id"], chapter_id, extraction)
            log_generation(
                conn,
                project["id"],
                "generate_chapter",
                provider="ollama",
                model=model,
                prompt=context,
                response=content,
                structured={"chapter_number": index, "title": title, "context_builder": True, "memory_extractor": True},
                chapter_id=chapter_id,
                module_name="storymemory_smoke",
                input_summary=outline,
                output_json={"chars": len(content), "title": title},
                user_action="smoke_test",
                applied_to_chapter=True,
            )
            chapter_stats.append({"chapter": index, "title": title, "chars": len(content), "chapter_id": chapter_id})
            print(f"chapter {index:02d} done: {title} ({len(content)} chars)", flush=True)

    exports = ROOT / "exports"
    exports.mkdir(exist_ok=True)
    md_path = exports / "jizhen_storymemory_smoke.md"
    docx_path = exports / "jizhen_storymemory_smoke.docx"
    report_path = exports / "jizhen_storymemory_smoke_report.json"

    with db_session() as conn:
        project = dict(conn.execute("SELECT * FROM projects WHERE name = ?", (PROJECT_NAME,)).fetchone())
        project_id = project["id"]
        chapters = rows_to_dicts(conn.execute("SELECT * FROM chapters WHERE project_id = ? ORDER BY chapter_number", (project_id,)).fetchall())
        characters = conn.execute("SELECT COUNT(*) AS n FROM characters WHERE project_id = ?", (project_id,)).fetchone()["n"]
        facts = conn.execute("SELECT COUNT(*) AS n FROM chapter_facts WHERE project_id = ?", (project_id,)).fetchone()["n"]
        summaries = conn.execute("SELECT COUNT(*) AS n FROM chapter_summaries WHERE project_id = ?", (project_id,)).fetchone()["n"]
        logs = conn.execute("SELECT COUNT(*) AS n FROM generation_logs WHERE project_id = ?", (project_id,)).fetchone()["n"]
        export_project_docx(conn, project_id, docx_path, model_name=model)

    md_lines = [f"# {TITLE}（Story Memory / Context Builder 烟测版）", ""]
    for ch in chapters:
        md_lines.extend([f"## 第 {ch['chapter_number']} 章  {ch['title']}", "", ch["content"], ""])
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    report = {
        "project_name": PROJECT_NAME,
        "title": TITLE,
        "model": model,
        "elapsed_seconds": round(time.time() - started, 2),
        "chapter_count": len(chapters),
        "chapter_stats": chapter_stats,
        "memory_stats": {
            "characters": characters,
            "chapter_summaries": summaries,
            "chapter_facts": facts,
            "generation_logs": logs,
        },
        "context_bridge_verified": "上一章结尾原文" in context_samples.get("chapter_2", ""),
        "context_samples": context_samples,
        "markdown_path": str(md_path),
        "docx_path": str(docx_path),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
