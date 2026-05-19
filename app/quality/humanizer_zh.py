from __future__ import annotations

import re
from dataclasses import dataclass


HUMANIZER_ZH_RULES = [
    "删掉模型自我说明、英文草稿、推理残留和提示词残留。",
    "减少模板化总结、主题升华和口号式金句。",
    "避免“这不仅仅是……而是……”“命运的齿轮”“一切才刚刚开始”等套话。",
    "把空泛情绪改成动作、停顿、物件、对话潜台词和场景细节。",
    "打散设定卡式介绍，让身份和关系通过行为、称呼、座位、消息和他人反应露出。",
    "保留剧情事实、人物关系、伏笔和章节钩子，不把轻小说改成沉重文学腔。",
]

TEMPLATE_REPLACEMENTS = {
    "他知道，这一切才刚刚开始。": "门外又传来一声很轻的敲门声。",
    "她知道，这一切才刚刚开始。": "门外又传来一声很轻的敲门声。",
    "命运的齿轮开始转动": "",
    "命运的齿轮已经开始转动": "",
    "一切才刚刚开始": "门外又传来一声很轻的敲门声",
    "秘密才刚刚开始": "短信停在屏幕上，没有署名",
    "更大的风暴正在靠近": "窗外的灯忽然暗了一下",
    "空气仿佛凝固了": "没人立刻接话",
    "说不清道不明的感觉": "迟疑",
    "复杂的情绪": "迟疑",
    "五味杂陈": "一时没说话",
    "这不仅仅是": "这不是",
    "游戏，开始了": "手机屏幕亮了一下",
    "游戏开始了": "手机屏幕亮了一下",
}

META_PATTERNS = [
    r"<think>.*?</think>",
    r"^\s*(?:Let's|I need to|I will|We need to|The chapter should|Draft:|Revision:|Self-Correction).*$",
    r"^\s*(?:结构|目标|约束|提示词|写作要求)[:：].*$",
]


@dataclass
class HumanizerReport:
    changed: bool
    removed_meta_lines: int
    replaced_template_phrases: int
    softened_summary_sentences: int

    def model_dump(self) -> dict:
        return {
            "changed": self.changed,
            "removed_meta_lines": self.removed_meta_lines,
            "replaced_template_phrases": self.replaced_template_phrases,
            "softened_summary_sentences": self.softened_summary_sentences,
        }


def humanizer_zh_constraints() -> str:
    return "\n".join(f"- {rule}" for rule in HUMANIZER_ZH_RULES)


def _remove_meta_lines(text: str) -> tuple[str, int]:
    removed = 0
    text = re.sub(META_PATTERNS[0], "", text, flags=re.I | re.S)
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(re.search(pattern, stripped, flags=re.I) for pattern in META_PATTERNS[1:]):
            removed += 1
            continue
        kept.append(line)
    return "\n".join(kept), removed


def _replace_template_phrases(text: str) -> tuple[str, int]:
    count = 0
    for old, new in TEMPLATE_REPLACEMENTS.items():
        if old in text:
            count += text.count(old)
            text = text.replace(old, new)
    text = re.sub(r"这不是([^，。！？]{1,30})，而是([^。！？]{1,50})。", r"\2。", text)
    return text, count


def _soften_summary_voice(text: str) -> tuple[str, int]:
    count = 0
    patterns = [
        r"这(?:也)?(?:象征|意味着|标志着|代表着)[^。！？]{4,50}[。！？]",
        r"从某种意义上说，?[^。！？]{4,50}[。！？]",
        r"他(?:终于)?明白，?[^。！？]{4,50}[。！？]",
        r"她(?:终于)?明白，?[^。！？]{4,50}[。！？]",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            count += len(matches)
            text = re.sub(pattern, "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, count


def humanize_zh_text(text: str) -> tuple[str, dict]:
    """Lightweight deterministic humanizer for generated Chinese prose.

    This is intentionally conservative: it removes AI traces and obvious
    templates, but does not rewrite plot facts or invent new story content.
    """
    original = text or ""
    if not original.strip():
        return "", HumanizerReport(False, 0, 0, 0).model_dump()
    current, removed_meta = _remove_meta_lines(original)
    current, replaced = _replace_template_phrases(current)
    current, softened = _soften_summary_voice(current)
    current = current.strip()
    report = HumanizerReport(
        changed=current != original.strip(),
        removed_meta_lines=removed_meta,
        replaced_template_phrases=replaced,
        softened_summary_sentences=softened,
    )
    return current, report.model_dump()
