from __future__ import annotations

import re


META_LINE_PATTERNS = [
    r"^\s*(?:[-*]\s*)?(?:Let's|I need to|I will|I'll|We need to|The chapter should|Need to ensure|Check hook|Check ending hook|Check dialogue|Self-Correction|Revision:|Draft:).*$",
    r"^\s*[-*]?\s*\*?\s*(?:Characters in Scene|Plot Points|Setting:|Scene \d+|Drafting|Adjustments during drafting|Structure:|Goal:|Info shifts|Jade Details|Added content|Final Polish|Final output|Notes?|End on specific object|Word Count Check|Interaction & Testing|The Jade & Examination).*$",
    r".*\b(?:I'll|I need to|Need to|Let's|Ending Hook|Opening|Jade Details|Added content|Final Polish|No English|Connect to Ch\d+|Word Count Check|Interaction & Testing|The Jade & Examination)\b.*",
    r".*(?:cumulative|constraint|Within limit|appearance|psychology through action|hits constraint).*",
]
CUT_PATTERNS = [
    r"\n\s*<think>.*?</think>",
    r"\n\s*\*?\s*Self-Correction/Refinement during thought:?\*?",
    r"\n\s*\*?\s*Adjustments during drafting:?\*?",
    r"\n\s*\*?\s*(?:Added content|Final Polish|Final output|Notes?|End on specific object|Word Count Check|Interaction & Testing|The Jade & Examination)\s*:?\s*\*?",
    r"\n\s*(?:Structure:|Goal:|Info shifts|.*cumulative.*|.*Within limit.*|.*hits constraint.*)",
]


def _strip_unclosed_think_block(text: str) -> str:
    """Remove Ollama reasoning leakage when a model emits <think> without </think>."""
    match = re.search(r"<think\b[^>]*>", text, flags=re.I)
    if not match:
        return text

    before = text[: match.start()]
    after = text[match.end() :]
    kept: list[str] = []
    in_reasoning = True
    for line in after.splitlines():
        stripped = line.strip()
        if not stripped:
            if not in_reasoning:
                kept.append(line)
            continue
        if re.search(r"</think>", stripped, flags=re.I):
            in_reasoning = False
            tail = re.sub(r".*?</think>", "", line, flags=re.I).strip()
            if tail:
                kept.append(tail)
            continue
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", stripped))
        ascii_letters = len(re.findall(r"[A-Za-z]", stripped))
        looks_like_meta = (
            stripped.startswith(("-", "*", "1.", "2.", "3.", "4.", "5."))
            or stripped.startswith(("(", "（"))
            or re.search(r"\b(?:Analyze|Opening|Ending|Hook|Structure|Strategy|Need|Let's|I'll|Prompt)\b", stripped, flags=re.I)
        )
        if in_reasoning:
            if chinese_chars >= 20 and ascii_letters < 12 and not looks_like_meta:
                in_reasoning = False
                kept.append(line)
            continue
        kept.append(line)

    return (before + "\n".join(kept)).strip()


def clean_model_output(text: str, mode: str = "prose") -> str:
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    text = _strip_unclosed_think_block(text)
    text = re.sub(r"```(?:json|markdown|text)?", "", text, flags=re.I).replace("```", "")
    for pattern in CUT_PATTERNS:
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            text = text[: match.start()]
    text = re.sub(r"(?m)^\s*\((?:Opening|Draft|Revision)\)\s*", "", text, flags=re.I)
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue
        ascii_letters = len(re.findall(r"[A-Za-z]", stripped))
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", stripped))
        if any(re.search(pattern, stripped, flags=re.I) for pattern in META_LINE_PATTERNS):
            continue
        if mode == "prose" and ascii_letters >= 20 and chinese_chars < 8:
            continue
        kept.append(line)
    text = "\n".join(kept).strip()
    if mode == "json":
        start = min([i for i in [text.find("{"), text.find("[")] if i >= 0], default=0)
        end = max(text.rfind("}"), text.rfind("]"))
        if end >= start:
            text = text[start : end + 1]
    return text
