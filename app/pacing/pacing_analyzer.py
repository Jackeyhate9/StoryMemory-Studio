from __future__ import annotations

import re

from app.pacing.pacing_schema import PacingIssue, PacingReport

CONFLICT_WORDS = "冲突|危险|杀|死|逃|追|拒绝|质问|威胁|暴露|背叛|争|夺|打|骗|秘密"
EMOTION_WORDS = "痛|怕|怒|恨|哭|笑|沉默|颤|崩溃|后悔|嫉妒|心跳|发抖"
HOOK_WORDS = "可是|然而|忽然|就在这时|门外|电话|短信|血|真相|秘密|是谁|为什么"


def analyze_pacing(text: str, recent_summaries: list[str] | None = None) -> PacingReport:
    recent_summaries = recent_summaries or []
    opening = text[:300]
    middle = text[len(text) // 3 : len(text) * 2 // 3]
    ending = text[-300:]
    opening_score = _score(opening, HOOK_WORDS, 45, 90)
    conflict_score = _score(text, CONFLICT_WORDS, 40, 92)
    emotion_score = _score(text, EMOTION_WORDS, 38, 88)
    ending_score = _score(ending, HOOK_WORDS, 35, 94)
    progress_score = 75 if len(set(re.findall(r"第?\w{1,8}(?:线索|真相|任务|目标|计划)", text))) else 58
    issues: list[PacingIssue] = []
    if opening_score < 60:
        issues.append(PacingIssue(issue_type="开头吸引力不足", location="开头 300 字", reason="开头缺少异常、冲突或明确问题。", suggestion="前 300 字放入危险、误会、选择或反常细节。", rewrite_direction="强悬疑版"))
    if conflict_score < 60:
        issues.append(PacingIssue(issue_type="核心冲突不清", location="全文", reason="缺少可识别的阻力和对抗。", suggestion="让主角目标被具体人物、规则或时间限制阻挡。", rewrite_direction="强冲突版"))
    if emotion_score < 55:
        issues.append(PacingIssue(issue_type="情绪波峰弱", location="中后段", reason="角色情绪变化不明显。", suggestion="增加一次选择代价或关系推进。", rewrite_direction="强情绪版"))
    if ending_score < 65:
        issues.append(PacingIssue(issue_type="结尾钩子弱", location="结尾 300 字", reason="结尾缺少下一章期待。", suggestion="用新线索、反转或迫近危险收尾。", rewrite_direction="强钩子版"))
    middle_drag = "high" if len(middle) > 800 and _score(middle, CONFLICT_WORDS, 20, 70) < 45 else "medium" if len(middle) > 1200 else "low"
    repetition_risk = _repeat_risk(text, recent_summaries)
    if repetition_risk:
        issues.append(PacingIssue(issue_type="连续剧情重复", severity="high", location="最近章节", reason="当前章节和最近摘要存在重复推进风险。", suggestion="换冲突类型或明确推进新信息。", rewrite_direction="去水版"))
    chapter_score = max(0, min(100, round((opening_score + conflict_score + progress_score + emotion_score + ending_score) / 5) - (12 if repetition_risk else 0)))
    return PacingReport(
        chapter_score=chapter_score,
        opening_hook_score=opening_score,
        conflict_score=conflict_score,
        plot_progress_score=progress_score,
        emotion_peak_score=emotion_score,
        middle_drag_risk=middle_drag,
        ending_hook_score=ending_score,
        retention_prediction=max(0, min(100, round(chapter_score * 0.75 + ending_score * 0.25))),
        issues=issues,
        next_chapter_suggestions=["下一章开头承接本章结尾问题。", "至少兑现一个信息点，并埋下一个更大的阻力。", "避免连续使用同一种冲突场景。"],
    )


def _score(text: str, pattern: str, base: int, cap: int) -> int:
    hits = len(re.findall(pattern, text))
    return min(cap, base + hits * 8)


def _repeat_risk(text: str, summaries: list[str]) -> bool:
    tokens = set(re.findall(r"[\u4e00-\u9fa5]{2,}", text[:800]))
    if not tokens:
        return False
    for summary in summaries[-3:]:
        other = set(re.findall(r"[\u4e00-\u9fa5]{2,}", summary))
        if other and len(tokens & other) / max(1, len(tokens | other)) > 0.45:
            return True
    return False
