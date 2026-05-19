from __future__ import annotations

import json
from collections import Counter
from typing import Any


CONSTRAINTS = {
    "meta_model_trace": "输出前必须删除英文草稿、推理残留、提示词复述和模型自我说明。",
    "template_sentence": "章节结尾必须落在具体事件、物件、消息或人物动作上，避免模板化悬念句。",
    "vague_emotion": "情绪必须用动作和对话呈现，避免空泛心理总结。",
    "exposition_dump": "设定信息必须通过冲突、误会、试探和细节泄露呈现，不要说明书式讲解。",
    "summary_voice": "减少段落结尾的主题升华，让事件和人物选择自己表达意义。",
    "unnatural_dialogue": "人物不要直接解释剧情和设定，用潜台词、打断和利益冲突推进对话。",
    "repetitive_rhythm": "变化句首和段落入口，交替使用动作、对话、环境和物件推进。",
    "over_abstract": "减少抽象名词堆叠，每个关键判断都配一个具体动作或视觉细节。",
}


def recent_ai_tone_feedback(conn, project_id: int, limit: int = 3) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT report_json
        FROM quality_reports
        WHERE project_id = ? AND report_type = 'ai_tone_detector'
        ORDER BY id DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    counts: Counter[str] = Counter()
    for row in rows:
        try:
            payload = json.loads(row["report_json"] or "{}")
        except json.JSONDecodeError:
            continue
        for key, value in (payload.get("issue_distribution") or {}).items():
            if key in CONSTRAINTS and int(value or 0) > 0:
                counts[key] += int(value)
    patterns = [key for key, _ in counts.most_common(5)]
    return {
        "recent_ai_tone_patterns": patterns,
        "next_generation_constraints": [CONSTRAINTS[key] for key in patterns],
    }


def feedback_block(conn, project_id: int, limit: int = 3) -> str:
    feedback = recent_ai_tone_feedback(conn, project_id, limit)
    if not feedback["next_generation_constraints"]:
        return "- 暂无最近 AI 腔高频问题。"
    lines = ["- 最近 AI 腔高频问题：" + "、".join(feedback["recent_ai_tone_patterns"])]
    lines.extend(f"- {item}" for item in feedback["next_generation_constraints"])
    return "\n".join(lines)
