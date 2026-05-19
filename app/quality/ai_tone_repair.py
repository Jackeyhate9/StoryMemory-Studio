from __future__ import annotations

import re

from app.llm.output_cleaner import clean_model_output
from app.quality.ai_tone_detector import detect_ai_tone
from app.quality.humanizer_zh import humanize_zh_text


REPLACEMENTS = {
    "他知道，这一切才刚刚开始。": "门外又响了一声。比刚才更近。",
    "这一切才刚刚开始。": "屏幕亮了一下，新的消息跳了出来。",
    "命运的齿轮开始转动。": "电梯门合上前，谢临川看见王知微的脸色变了。",
    "空气仿佛凝固了。": "没人说话，杯沿碰在托盘上，轻轻响了一下。",
    "一场更大的风暴正在靠近。": "热搜榜刷新，玫瑰大厦四个字第一次爬进前十。",
    "复杂的情绪": "迟疑",
    "说不清道不明的感觉": "喉咙发紧",
    "五味杂陈": "把杯子握得太紧",
    "百感交集": "指尖在杯壁上停了很久",
}


def repair_ai_tone_sentences(text: str, report: dict | None = None) -> tuple[str, list[dict]]:
    report = report or detect_ai_tone(text).model_dump()
    output = clean_model_output(text, mode="prose")
    changes = []
    for issue in report.get("issues", []):
        if issue.get("can_keep"):
            continue
        original = issue.get("original_text", "")
        replacement = issue.get("natural_rewrite") or ""
        if not original or not replacement or "建议改为" in replacement:
            continue
        if original in output:
            output = output.replace(original, replacement, 1)
            changes.append({"type": issue.get("issue_type"), "from": original, "to": replacement})
    for old, new in REPLACEMENTS.items():
        if old in output:
            output = output.replace(old, new)
            changes.append({"type": "template_sentence", "from": old, "to": new})
    return output, changes


def polish_ai_tone_paragraphs(text: str, report: dict | None = None) -> tuple[str, list[dict]]:
    output, changes = repair_ai_tone_sentences(text, report)
    paragraphs = re.split(r"(\n\s*\n)", output)
    polished = []
    for part in paragraphs:
        if not part.strip() or part.isspace():
            polished.append(part)
            continue
        local = part
        local = re.sub(r"这不仅仅是([^。！？]{0,40})，?更是([^。！？]{0,40})。?", r"\1压在桌面上，没人再把话说满。", local)
        local = re.sub(r"从某种意义上[^。！？]*[。！？]", "", local)
        local = re.sub(r"他终于明白[^。！？]*[。！？]", "他没有再追问，只把那张纸折进了口袋。", local)
        local = re.sub(r"她终于意识到[^。！？]*[。！？]", "她把视线移开，指尖在琴盖边缘停住。", local)
        if local != part:
            changes.append({"type": "paragraph_rewrite", "from": part[:160], "to": local[:160]})
        polished.append(local)
    return "".join(polished).strip(), changes


def polish_chapter_natural_style(text: str, report: dict | None = None) -> tuple[str, list[dict]]:
    output, changes = polish_ai_tone_paragraphs(text, report)
    output = re.sub(r"\n{3,}", "\n\n", output)
    output = re.sub(r"(?m)^\s*#+\s*", "", output)
    output = clean_model_output(output, mode="prose")
    output, humanizer_report = humanize_zh_text(output)
    if humanizer_report.get("changed"):
        changes.append({"type": "humanizer_zh", "report": humanizer_report})
    return output.strip(), changes
