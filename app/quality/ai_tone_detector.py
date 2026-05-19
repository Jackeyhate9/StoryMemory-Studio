from __future__ import annotations

import re
from collections import Counter

from app.quality.ai_tone_schema import AI_TONE_TYPES, AIToneIssue, AIToneReport


META_PATTERNS = [
    r"<think>.*?</think>",
    r"\b(?:Let's|I need to|I will|We need to|The chapter should|Self-Correction|Revision:|Draft:)\b",
    r"Characters in Scene|Plot Points|word count|target precisely|Adjustments during drafting",
]
TEMPLATE_PATTERNS = [
    "他知道，这一切才刚刚开始",
    "这一切才刚刚开始",
    "命运的齿轮开始转动",
    "空气仿佛凝固",
    "一场更大的风暴正在靠近",
    "新的篇章",
    "真正的考验",
    "游戏，开始了",
    "游戏开始了",
    "秘密才刚刚开始",
    "确实才刚刚开始",
    "沉睡的巨兽",
]
VAGUE_EMOTION_PATTERNS = [
    "复杂的情绪",
    "说不清道不明",
    "五味杂陈",
    "百感交集",
    "难以言喻",
    "心中一震",
    "某种预感",
]
SUMMARY_PATTERNS = [
    "这不仅仅是",
    "这意味着",
    "从某种意义上",
    "所有人都明白",
    "他终于明白",
    "她终于意识到",
]
ABSTRACT_WORDS = ["命运", "宿命", "救赎", "羁绊", "深渊", "光明", "黑暗", "试炼", "真相", "秘密", "体面"]
CHARACTER_CARD_PATTERNS = ["作为", "实际操盘手", "继承人之一", "总是能", "擅长处理", "她是", "他是", "身份是"]
WORLDBUILDING_PATTERNS = ["玫瑰资本", "家族企业", "董事会", "商业联盟", "继承权", "资源分配", "资本规则", "舆论"]
RELATIONSHIP_EXPLAIN_PATTERNS = ["两人之间", "他们的关系", "外界默认", "亲近但", "互相利用", "商业联姻"]
LIGHT_NOVEL_ALLOWED = ["吐槽", "离谱", "社死", "热搜", "完了", "救命", "她想"]
ACCEPTABLE_LITERARY = ["像", "仿佛", "雨", "灯光", "玻璃", "影子", "玫瑰", "琴声"]


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?])\s+|(?<=[。！？!?])", text)
    return [p.strip() for p in parts if p and p.strip()]


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", text) if p.strip()]


def _contains_any(text: str, values: list[str]) -> bool:
    return any(v in text for v in values)


def _naturalize(sentence: str, issue_type: str) -> str:
    rewrite = sentence
    replacements = {
        "他知道，这一切才刚刚开始。": "门外又响了一声。比刚才更近。",
        "这一切才刚刚开始。": "屏幕亮了一下，新的消息跳了出来。",
        "命运的齿轮开始转动。": "电梯门合上前，谢临川看见王知微的脸色变了。",
        "空气仿佛凝固了。": "没人说话，杯沿碰在托盘上，轻轻响了一下。",
        "一场更大的风暴正在靠近。": "热搜榜刷新，玫瑰大厦四个字第一次爬进前十。",
        "复杂的情绪": "迟疑",
        "说不清道不明的感觉": "喉咙发紧",
        "五味杂陈": "把杯子握得太紧",
    }
    for old, new in replacements.items():
        rewrite = rewrite.replace(old, new)
    if rewrite == sentence and issue_type in {"vague_emotion", "over_abstract", "summary_voice"}:
        rewrite = f"{sentence.rstrip('。')}。建议改为：用停顿、目光、手部动作、物件变化或对话潜台词承载这层情绪。"
    return rewrite


def _issue(issue_type: str, sentence: str, severity: str, reason: str, why: str, can_keep: bool = False, confidence: float = 0.75) -> AIToneIssue:
    priority = "none" if can_keep else ("paragraph_rewrite" if severity == "high" else "local_sentence_rewrite")
    impact = "high" if severity == "high" else "medium" if severity == "medium" else "low"
    return AIToneIssue(
        issue_type=issue_type,
        severity=severity,
        confidence=confidence,
        reader_impact=impact,
        original_text=sentence[:260],
        reason=reason,
        why_it_feels_ai=why,
        can_keep=can_keep,
        rewrite_priority=priority,
        rewrite_suggestion="保留剧情事实，把抽象判断改成动作、物件、对话或具体事件。",
        natural_rewrite=_naturalize(sentence, issue_type),
    )


def detect_ai_tone(text: str) -> AIToneReport:
    sentences = _sentences(text)
    paragraphs = _paragraphs(text)
    issues: list[AIToneIssue] = []

    for sentence in sentences:
        if any(re.search(pattern, sentence, flags=re.I | re.S) for pattern in META_PATTERNS):
            issues.append(_issue("meta_model_trace", sentence, "high", "检测到模型自我暴露、英文草稿或提示词残留。", "这会直接破坏读者沉浸感，必须删除或重写。", confidence=0.98))
            continue
        if _contains_any(sentence, TEMPLATE_PATTERNS):
            issue_type = "template_hook" if sentence in sentences[-3:] else "template_sentence"
            issues.append(_issue(issue_type, sentence, "high", "命中常见模板化悬念或套路句。", "悬念没有落在具体事件上，读起来像生成器收束语。", confidence=0.92))
            continue
        if _contains_any(sentence, CHARACTER_CARD_PATTERNS) and len(sentence) > 35:
            issues.append(_issue("character_card_dump", sentence, "medium", "人物登场像设定卡插入。", "身份、能力和性格被直接说明，缺少动作、称呼和他人反应。", confidence=0.76))
            continue
        if sum(1 for word in WORLDBUILDING_PATTERNS if word in sentence) >= 2 and len(sentence) > 45:
            issues.append(_issue("worldbuilding_dump", sentence, "medium", "世界观/商业关系解释密度偏高。", "像在替读者讲背景，而不是让信息从场景中露出。", confidence=0.72))
            continue
        if sentence.startswith(("“", "\"")) and len(sentence) > 60 and sum(1 for word in WORLDBUILDING_PATTERNS if word in sentence) >= 1:
            issues.append(_issue("dialogue_exposition", sentence, "medium", "对话承担过多剧情说明。", "人物像在解释设定，缺少试探、回避、打断和潜台词。", confidence=0.74))
            continue
        if _contains_any(sentence, RELATIONSHIP_EXPLAIN_PATTERNS) and len(sentence) > 35:
            issues.append(_issue("overexplained_relationship", sentence, "medium", "人物关系被直接说明。", "关系应通过称呼、座位、眼神、动作、消息和物件体现。", confidence=0.7))
            continue
        if _contains_any(sentence, VAGUE_EMOTION_PATTERNS):
            issues.append(_issue("vague_emotion", sentence, "medium", "情绪表达偏空泛。", "读者知道人物有情绪，但看不到动作、表情或场景反馈。", confidence=0.78))
            continue
        if _contains_any(sentence, SUMMARY_PATTERNS):
            issues.append(_issue("summary_voice", sentence, "medium", "句子倾向于替读者总结意义。", "段落在升华主题，而不是让情节和人物自己完成表达。", confidence=0.72))
            continue
        abstract_hits = sum(1 for word in ABSTRACT_WORDS if word in sentence)
        if abstract_hits >= 4 and len(sentence) > 35:
            issues.append(_issue("abstract_metaphor_overload", sentence, "medium", "抽象隐喻和高级感词密度偏高。", "句子显得漂亮但不落地，缺少可感知的动作、空间、物件或身体反应。", confidence=0.68))
            continue
        if sentence.count("，") >= 5 and ("因为" in sentence or "所以" in sentence or "意味着" in sentence):
            issues.append(_issue("exposition_dump", sentence, "medium", "单句承载过多解释信息。", "像说明书或剧情梳理，弱化了小说现场感。", confidence=0.66))
            continue
        if sentence.startswith(("“", "\"")) and len(sentence) > 90 and _contains_any(sentence, ["因为", "所以", "意味着", "真相", "规则", "资本"]):
            issues.append(_issue("unnatural_dialogue", sentence, "medium", "对话解释感偏强。", "人物像在替作者给读者讲设定。", confidence=0.7))
            continue
        if _contains_any(sentence, LIGHT_NOVEL_ALLOWED) and len(sentence) < 80:
            issues.append(_issue("light_novel_allowed", sentence, "low", "轻小说语境下可接受的吐槽或情绪夸张。", "这类句子服务节奏和人物口吻，不应强制改。", can_keep=True, confidence=0.55))
            continue
        if _contains_any(sentence, ACCEPTABLE_LITERARY) and len(sentence) < 100:
            issues.append(_issue("acceptable_literary_expression", sentence, "low", "可接受的文学化表达。", "有画面感且没有明显模板化，可保留或轻微压实。", can_keep=True, confidence=0.45))

    starts = Counter(s[:3] for s in sentences if len(s) >= 6)
    for prefix, count in starts.items():
        if count >= 5:
            issues.append(_issue("repetitive_rhythm", prefix, "medium", f"相似句首结构重复 {count} 次。", "节奏重复会造成机械感。", confidence=0.65))

    dialogue_sentences = [s for s in sentences if s.startswith(("“", "\""))]
    if len(dialogue_sentences) >= 8:
        long_explain = [s for s in dialogue_sentences if len(s) > 70 and ("因为" in s or "所以" in s or "你知道" in s or "玫瑰资本" in s)]
        if len(long_explain) / max(len(dialogue_sentences), 1) > 0.28:
            issues.append(_issue("insufficient_subtext", "本章多处长对白直接解释信息。", "medium", "对白潜台词不足。", "人物把本应藏在试探和误会里的信息直接说穿。", confidence=0.72))
    if len(paragraphs) >= 6:
        friction_markers = ["停", "顿", "打断", "沉默", "没接", "避开", "移开", "碰", "放下", "看了眼"]
        friction_count = sum(1 for p in paragraphs if any(m in p for m in friction_markers))
        if friction_count / len(paragraphs) < 0.18:
            issues.append(_issue("lack_of_scene_friction", "全章互动摩擦偏少。", "medium", "场景过顺，缺少真实互动里的停顿、尴尬、误会、动作打断。", "人物交换信息太顺滑，像剧情流程而不是现场。", confidence=0.62))

    distribution = {name: 0 for name in AI_TONE_TYPES}
    for item in issues:
        distribution[item.issue_type] = distribution.get(item.issue_type, 0) + 1

    severe_issues = [i for i in issues if not i.can_keep and i.severity in {"medium", "high"}]
    meta_count = distribution["meta_model_trace"]
    sentence_count = max(len(sentences), 1)
    density = round(len(severe_issues) / sentence_count, 4)
    paragraph_density = len(severe_issues) / max(len(paragraphs), 1)

    score = 0
    score += meta_count * 100
    score += distribution["template_sentence"] * 16
    score += distribution.get("template_hook", 0) * 22
    score += distribution.get("character_card_dump", 0) * 11
    score += distribution.get("worldbuilding_dump", 0) * 11
    score += distribution.get("dialogue_exposition", 0) * 13
    score += distribution.get("lack_of_scene_friction", 0) * 8
    score += distribution.get("insufficient_subtext", 0) * 10
    score += distribution.get("overexplained_relationship", 0) * 10
    score += distribution["summary_voice"] * 10
    score += distribution["vague_emotion"] * 9
    score += distribution["unnatural_dialogue"] * 12
    score += distribution["exposition_dump"] * 10
    score += distribution["over_abstract"] * 7
    score += distribution.get("abstract_metaphor_overload", 0) * 9
    score += distribution["repetitive_rhythm"] * 8
    score += int(density * 120)
    score += int(max(0, paragraph_density - 0.45) * 35)
    score = min(100, score)

    if meta_count:
        risk = "high"
    elif score <= 30:
        risk = "low"
    elif score <= 65:
        risk = "medium"
    else:
        risk = "high"

    if meta_count:
        rewrite_priority = "full_regeneration" if meta_count > 2 else "paragraph_rewrite"
        reader_impact = "high"
    elif risk == "high":
        rewrite_priority = "chapter_polish"
        reader_impact = "high" if density > 0.12 else "medium"
    elif risk == "medium":
        rewrite_priority = "paragraph_rewrite" if density > 0.08 else "local_sentence_rewrite"
        reader_impact = "medium"
    elif severe_issues:
        rewrite_priority = "local_sentence_rewrite"
        reader_impact = "low"
    else:
        rewrite_priority = "none"
        reader_impact = "low"

    top = [k for k, _ in Counter({k: v for k, v in distribution.items() if k not in {"acceptable_literary_expression", "light_novel_allowed"} and v}).most_common(3)]
    prompt_adjustments = _prompt_adjustments(distribution)
    advice = [
        "先删除模型痕迹和英文草稿，再处理模板句。",
        "高风险不等于整章失败：如果没有 meta_model_trace，优先做整章轻润色或段落改写。",
        "可接受的文学化表达和轻小说吐槽可以保留，只在影响清晰度时压实。",
    ]
    summary = f"检测到 {len(severe_issues)} 处需要关注的问题，AI 腔密度 {density:.2%}。主要类型：{', '.join(top) if top else '无明显高频问题'}。"
    return AIToneReport(
        overall_score=score,
        risk_level=risk,
        ai_tone_density=density,
        reader_impact=reader_impact,
        rewrite_priority=rewrite_priority,
        summary=summary,
        issue_distribution=distribution,
        issues=issues[:80],
        chapter_level_advice=advice,
        generation_prompt_adjustments=prompt_adjustments,
        recommended_actions=[
            "局部句子级修复：替换 meta_model_trace、template_sentence、vague_emotion。",
            "段落级自然化：问题连续出现时，改写整段而不是硬换词。",
            "整章轻润色：保留剧情事实、伏笔和钩子，只压掉总结腔和说明书口吻。",
        ],
    )


def _prompt_adjustments(distribution: dict[str, int]) -> list[str]:
    rules = []
    if distribution.get("vague_emotion", 0) >= 2:
        rules.append("情绪必须用动作、对话、物件和场景反馈呈现，避免空泛心理总结。")
    if distribution.get("summary_voice", 0) >= 2:
        rules.append("减少段落结尾的主题升华，让读者从事件里自己感受到意义。")
    if distribution.get("template_sentence", 0) >= 1:
        rules.append("章节结尾必须落在具体事件、物件、消息或人物动作上，避免模板化悬念句。")
    if distribution.get("unnatural_dialogue", 0) >= 1:
        rules.append("人物不要直接解释设定，用试探、误解、打断和潜台词传递信息。")
    if distribution.get("over_abstract", 0) >= 2:
        rules.append("减少抽象名词堆叠，每个关键判断都配一个具体动作或视觉细节。")
    if distribution.get("meta_model_trace", 0) >= 1:
        rules.append("输出前必须删除英文草稿、推理残留、提示词复述和模型自我说明。")
    return rules
