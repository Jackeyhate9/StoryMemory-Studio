from __future__ import annotations

import json
from pathlib import Path

from app.llm.client import LLMClient, extract_json, get_llm, repair_json_with_llm
from app.schemas.create_novel import CreateNovelResult, FirstChapterSeed, NovelSeedInput

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "create_novel_from_seed.md"


def _name_from_protagonist(seed: NovelSeedInput) -> str:
    text = seed.protagonist.strip()
    if not text:
        return "主角"
    for sep in ["，", ",", " "]:
        if sep in text:
            return text.split(sep)[0].strip() or "主角"
    return text[:6]


def heuristic_create_novel(seed: NovelSeedInput) -> CreateNovelResult:
    protagonist = _name_from_protagonist(seed)
    title = seed.title
    platform = seed.platform or "通用平台"
    genre = seed.genre or "长篇小说"
    premise = seed.premise or f"{protagonist}被卷入一场改变命运的事件。"
    goal = seed.protagonist_goal or "找到真相并完成自我改变"
    selling = seed.selling_points or ["强冲突", "反转", "成长", "章节钩子"]
    avoid = seed.avoid or ["不要 AI 腔", "不要无意义灌水"]
    location = "故事开局地点"
    if "都市" in genre:
        location = "旧城区"
    elif "玄幻" in genre:
        location = "边境小城"
    elif "悬疑" in genre:
        location = "案发现场"

    chapters = []
    for i in range(1, 11):
        chapters.append(
            {
                "chapter_number": i,
                "title": f"第{i}章 线索{i}",
                "chapter_goal": "推进开局事件并制造新的悬念" if i == 1 else f"推进主线第{i}个关键线索",
                "main_conflict": f"{protagonist}在目标与阻碍之间做出选择",
                "characters": [protagonist],
                "key_events": [f"{protagonist}发现与“{premise}”有关的新线索"],
                "new_information": [f"主线谜题第{i}层信息"],
                "foreshadows": [f"第{i}章留下的关键异常"],
                "ending_hook": f"结尾出现一个推翻前文判断的新细节{i}",
                "memory_facts": [f"{protagonist}的核心目标是{goal}", f"故事主设定：{premise}"],
            }
        )

    first_content = (
        f"{protagonist}第一次意识到事情不对，是在{location}。\n\n"
        f"所有线索都指向同一个答案：{premise}\n\n"
        f"他原本只想{goal}，可眼前的异常逼着他承认，自己已经站在更大的局里。"
        f"手机屏幕亮起，一条没有署名的消息跳了出来：别相信你明天醒来后记得的一切。"
    )
    data = {
        "project": {
            "title": title,
            "genre": genre,
            "platform": platform,
            "target_reader": seed.target_reader,
            "expected_chapters": seed.expected_chapters,
            "chapter_word_count": seed.chapter_word_count,
            "logline": premise,
            "core_selling_points": selling,
        },
        "world_rules": [
            {"category": "核心设定", "rule_text": premise, "rigidity": "hard"},
            {"category": "主角目标", "rule_text": f"{protagonist}必须围绕目标推进：{goal}", "rigidity": "hard"},
        ],
        "characters": [
            {
                "name": protagonist,
                "role": "主角",
                "personality": seed.protagonist,
                "motivation": goal,
                "status": "active",
                "current_location": location,
                "hard_constraints": seed.protagonist,
            },
            {"name": "关键对手", "role": "反派/阻碍者", "personality": "冷静、隐藏真实目的", "motivation": "阻止主角接近真相"},
            {"name": "重要搭档", "role": "搭档/情感线角色", "personality": "敏锐但有所隐瞒", "motivation": "帮助主角，同时保护自己的秘密"},
        ],
        "relationships": [
            {"character_a": protagonist, "character_b": "重要搭档", "relationship_type": "合作/互相试探", "status": "不完全信任", "description": "两人目标暂时一致，但都保留秘密"},
            {"character_a": protagonist, "character_b": "关键对手", "relationship_type": "敌对", "status": "暗线对抗", "description": "对手掌握主角不知道的信息"},
        ],
        "locations": [{"name": location, "type": "开局地点", "description": "第一章冲突发生地", "rules": "这里隐藏主线第一层线索"}],
        "organizations": [{"name": "隐藏势力", "type": "幕后组织", "description": "掌握核心秘密并推动事件发生", "status": "暗中活动"}],
        "abilities": [{"name": "核心机制", "owner": protagonist, "system": genre, "description": premise, "limitations": "能力或机制必须有代价，不能无脑解决问题"}],
        "items": [{"name": "关键证物", "type": "线索道具", "description": "连接第一章和主线真相的物件", "owner": protagonist, "status": "未完全解读"}],
        "plot_threads": [
            {"name": "主线真相", "thread_type": "main", "status": "open", "summary": f"{protagonist}追查：{premise}", "related_characters": [protagonist]},
            {"name": "搭档秘密", "thread_type": "branch", "status": "open", "summary": "重要搭档隐瞒了与开局事件有关的信息", "related_characters": ["重要搭档"]},
        ],
        "foreshadows": [
            {"name": "第一章异常消息", "related_characters": [protagonist], "related_items": ["关键证物"], "related_thread": "主线真相", "expected_resolution_chapter": 12, "risk_note": "需要在第一卷中部分解释"},
            {"name": "搭档的隐瞒", "related_characters": ["重要搭档"], "related_thread": "搭档秘密", "expected_resolution_chapter": 20, "risk_note": "不能过早揭露"},
        ],
        "timeline_events": [{"story_time": "开局当天", "sort_key": "001", "event_text": f"{protagonist}在{location}遭遇开局异常", "location": location, "characters": [protagonist]}],
        "style_profile": {
            "name": "默认文风",
            "platform": platform,
            "pov": "第三人称有限视角",
            "sentence_length": "中短句为主",
            "dialogue_ratio": "35%",
            "description_ratio": "25%",
            "inner_monologue_ratio": "15%",
            "high_point_density": "每章至少一个反转或钩子",
            "common_patterns": selling,
            "banned_expressions": avoid,
            "pacing": seed.style_reference or "快节奏，章节末尾有钩子",
            "sample_text": seed.style_reference,
        },
        "forbidden_rules": [{"rule_text": item, "category": "用户禁忌", "severity": "critical"} for item in avoid],
        "unresolved_questions": [
            {"question": "开局异常的真正来源是什么？", "related_thread": "主线真相", "related_characters": [protagonist], "priority": "high"},
            {"question": "重要搭档为什么隐瞒信息？", "related_thread": "搭档秘密", "related_characters": ["重要搭档"], "priority": "medium"},
        ],
        "volume_outline": [
            f"第一卷：{protagonist}遭遇开局异常，确认主线目标，结尾逼近第一层真相。",
            "第二卷：主角扩大调查范围，发现幕后势力存在。",
            "第三卷：中期反转推翻主角对核心机制的理解。",
        ],
        "chapter_outlines": chapters,
        "first_chapter": {
            "title": chapters[0]["title"],
            "content": first_content,
            "summary": f"{protagonist}在{location}遭遇异常，确认主线目标：{goal}。",
            "facts": [f"{protagonist}的目标是{goal}", f"核心设定是：{premise}", f"开局地点是{location}"],
        },
    }
    return CreateNovelResult.model_validate(data)


def build_novel_from_seed(seed: NovelSeedInput, provider: str = "none") -> CreateNovelResult:
    if provider == "none":
        return heuristic_create_novel(seed)
    client = get_llm(provider)
    template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = template.format(seed_json=seed.model_dump_json(indent=2))
    raw = client.complete(prompt, system="你是严谨的长篇小说项目 Bible 生成器。", temperature=0.6)
    try:
        data = extract_json(raw)
    except Exception:
        data = repair_json_with_llm(raw, client)
    return CreateNovelResult.model_validate(data)


def regenerate_section(seed: NovelSeedInput, current: CreateNovelResult, section: str, provider: str = "none") -> CreateNovelResult:
    if provider == "none":
        fresh = heuristic_create_novel(seed)
    else:
        fresh = build_novel_from_seed(seed, provider)
    data = current.model_dump()
    if section == "characters":
        for key in ["characters", "relationships"]:
            data[key] = fresh.model_dump()[key]
    elif section == "world":
        for key in ["world_rules", "locations", "organizations", "abilities", "items", "forbidden_rules"]:
            data[key] = fresh.model_dump()[key]
    elif section == "outline":
        for key in ["plot_threads", "foreshadows", "timeline_events", "volume_outline", "chapter_outlines", "unresolved_questions"]:
            data[key] = fresh.model_dump()[key]
    else:
        data = fresh.model_dump()
    return CreateNovelResult.model_validate(data)

