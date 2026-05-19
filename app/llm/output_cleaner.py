from __future__ import annotations

import re


META_LINE_PATTERNS = [
    r"^\s*(?:Let's|I need to|I will|We need to|The chapter should|Need to ensure|Check hook|Check dialogue|Self-Correction|Revision:|Draft:).*$",
    r"^\s*\*?\s*(?:Characters in Scene|Plot Points|Setting:|Scene \d+|Drafting|Adjustments during drafting|Structure:|Goal:|Info shifts).*$",
    r".*(?:cumulative|constraint|Within limit|appearance|psychology through action|hits constraint).*",
]
CUT_PATTERNS = [
    r"\n\s*<think>.*?</think>",
    r"\n\s*\*?\s*Self-Correction/Refinement during thought:?\*?",
    r"\n\s*\*?\s*Adjustments during drafting:?\*?",
    r"\n\s*(?:Structure:|Goal:|Info shifts|.*cumulative.*|.*Within limit.*|.*hits constraint.*)",
]


def clean_model_output(text: str, mode: str = "prose") -> str:
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    text = re.sub(r"```(?:json|markdown|text)?", "", text, flags=re.I).replace("```", "")
    for pattern in CUT_PATTERNS:
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            text = text[: match.start()]
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
