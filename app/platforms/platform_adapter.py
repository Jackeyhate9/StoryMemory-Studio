from __future__ import annotations

import re

from app.platforms.platform_profiles import get_platform_profile
from app.platforms.platform_schema import PlatformFitReport


def analyze_platform_fit(text: str, platform: str) -> PlatformFitReport:
    profile = get_platform_profile(platform)
    opening = text[:300]
    ending = text[-260:]
    strengths: list[str] = []
    weaknesses: list[str] = []
    adjustments: list[str] = []
    score = 70
    if re.search(r"忽然|可是|然而|血|秘密|电话|门外|死|杀|追", opening):
        strengths.append("开头有冲突或异常信号。")
        score += 8
    else:
        weaknesses.append("开头进入冲突偏慢。")
        adjustments.append(profile.chapter_opening)
        score -= 12
    if len(re.findall(r"。", text)) > 80 and platform in {"短剧", "漫画分镜", "小红书推文"}:
        weaknesses.append("文本偏长，需要拆成镜头或短段。")
        adjustments.append("压缩说明，转成动作、对白和视觉节点。")
        score -= 10
    if re.search(r"？|!|！|忽然|真相|秘密|门", ending):
        strengths.append("结尾具备追读钩子。")
        score += 8
    else:
        weaknesses.append("结尾钩子不够明确。")
        adjustments.append(profile.ending_hook)
        score -= 10
    return PlatformFitReport(
        platform=platform,
        fit_score=max(0, min(100, score)),
        strengths=strengths,
        weaknesses=weaknesses,
        required_adjustments=adjustments,
        rewritten_opening_suggestion=f"按{platform}风格重写开头：{profile.chapter_opening}。",
        ending_hook_suggestion=f"按{platform}风格强化结尾：{profile.ending_hook}。",
        style_rules=[profile.pacing, profile.dialogue, profile.description],
        avoid_rules=profile.avoid,
    )


def adapt_platform_text(text: str, platform: str) -> str:
    profile = get_platform_profile(platform)
    return f"【{platform}适配版改写方向】\n- 开头：{profile.chapter_opening}\n- 节奏：{profile.pacing}\n- 对白：{profile.dialogue}\n- 结尾：{profile.ending_hook}\n\n【原章节待改写文本】\n{text}"
