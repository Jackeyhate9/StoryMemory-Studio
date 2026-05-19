from __future__ import annotations

import json
from pathlib import Path

from app.llm.client import extract_json, get_llm, repair_json_with_llm
from app.style.style_safety import clean_sample_text, sample_stats
from app.style.style_schema import StyleProfileInput, StyleProfileResult

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "analyze_style_profile.md"


def heuristic_style_profile(input_data: StyleProfileInput) -> StyleProfileResult:
    text = clean_sample_text("\n\n".join(input_data.samples))
    stats = sample_stats(text)
    avg_sentence = stats["avg_sentence_chars"]
    short_ratio = "偏高" if avg_sentence <= 24 else "中等"
    long_ratio = "偏高" if avg_sentence >= 45 else "中低"
    dialogue_ratio = "较高" if stats["dialogue_mark_count"] >= 8 else "中等偏低"
    summary = (
        f"文风以{'短句快节奏' if avg_sentence <= 28 else '中长句叙述'}为主，"
        f"平均句长约 {avg_sentence} 字，段落平均约 {stats['avg_paragraph_chars']} 字。"
        "后续生成只能继承节奏、信息释放和情绪控制方式，不得复用样章具体表达。"
    )
    return StyleProfileResult(
        style_name=input_data.style_name,
        source_summary=f"共 {stats['chars']} 字，{stats['paragraphs']} 段，{stats['sentences']} 句。",
        target_usage=input_data.target_usage,
        narrative_pov="根据样章抽象为有限视角叙事",
        tense="中文叙事常规时态",
        sentence_length={
            "average": f"{avg_sentence} 字左右",
            "variation": "长短句交替" if avg_sentence > 28 else "短句密集，偶尔插入中句",
            "short_sentence_ratio": short_ratio,
            "long_sentence_ratio": long_ratio,
        },
        paragraph_style={
            "average_paragraph_length": f"{stats['avg_paragraph_chars']} 字左右",
            "line_break_frequency": "较频繁" if stats["avg_paragraph_chars"] < 120 else "中等",
            "white_space_style": "用换行制造节奏和悬念",
        },
        dialogue_style={
            "dialogue_ratio": dialogue_ratio,
            "dialogue_speed": "推进剧情，避免解释性对白",
            "subtext_level": "中等",
            "common_dialogue_functions": ["推进冲突", "隐藏信息", "制造误导"],
        },
        description_style={
            "sensory_focus": ["视觉", "动作", "气氛"],
            "visual_density": "中等",
            "metaphor_density": "低到中等",
            "action_detail_level": "用具体动作承载情绪",
        },
        emotion_style={
            "emotion_intensity": "中等",
            "emotion_expression_mode": "克制表达，更多通过动作和选择体现",
            "inner_monologue_ratio": "中低",
            "restraint_level": "较高",
        },
        pacing_style={
            "scene_speed": "偏快",
            "conflict_frequency": "每个场景至少一个明确阻力",
            "cliffhanger_frequency": "章节末尾保留钩子",
            "information_release_pattern": "分层释放，不一次性解释",
        },
        hook_style={
            "opening_hook_methods": ["异常开场", "直接冲突", "信息缺口"],
            "chapter_ending_hook_methods": ["反转细节", "危险逼近", "新问题"],
            "suspense_methods": ["延迟解释", "局部误导", "目标受阻"],
        },
        word_choice={
            "register": "通俗清晰",
            "common_word_types": ["动作词", "感官词", "短促判断"],
            "avoid_word_types": ["空泛抒情", "AI 腔套话", "过度形容词"],
            "platform_specific_terms": [],
        },
        structure_style={
            "scene_transition_methods": ["动作承接", "线索推进", "问题转场"],
            "flashback_usage": "少量使用，避免打断主线",
            "reversal_frequency": "中高",
            "foreshadowing_style": "用异常细节轻埋伏笔",
        },
        do_rules=["保持节奏紧凑", "用动作和场景呈现情绪", "章节末尾保留问题或反转"],
        dont_rules=["不要复用样章原句", "不要复用样章角色地点设定", "不要保留样章段落顺序", "不要写空泛 AI 腔"],
        safe_style_summary=summary,
    )


def analyze_style(input_data: StyleProfileInput, provider: str = "none") -> StyleProfileResult:
    if provider == "none":
        return heuristic_style_profile(input_data)
    client = get_llm(provider)
    sample_text = clean_sample_text("\n\n".join(input_data.samples))
    prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
        style_name=input_data.style_name,
        target_usage=", ".join(input_data.target_usage),
        source_note=input_data.source_note,
        sample_text=sample_text[:20000],
    )
    raw = client.complete(prompt, system="你是只抽象分析文风、不复制表达的小说编辑。", temperature=0.1)
    try:
        data = extract_json(raw)
    except Exception:
        data = repair_json_with_llm(raw, client)
    result = StyleProfileResult.model_validate(data)
    if not result.safe_style_summary:
        result.safe_style_summary = heuristic_style_profile(input_data).safe_style_summary
    return result
