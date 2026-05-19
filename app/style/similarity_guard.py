from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.style.style_schema import SimilarityReport


def char_ngrams(text: str, n: int = 8) -> set[str]:
    compact = re.sub(r"\s+", "", text)
    return {compact[i : i + n] for i in range(max(0, len(compact) - n + 1))}


def paragraph_pattern(text: str) -> list[int]:
    return [len(p.strip()) for p in text.splitlines() if p.strip()]


def longest_common_substring(a: str, b: str) -> str:
    a = re.sub(r"\s+", "", a)
    b = re.sub(r"\s+", "", b)
    match = SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))
    return a[match.a : match.a + match.size]


def rare_phrases(text: str) -> set[str]:
    phrases = set()
    for m in re.finditer(r"[\u4e00-\u9fffA-Za-z0-9]{10,24}", re.sub(r"\s+", "", text)):
        s = m.group(0)
        if len(set(s)) >= 6:
            phrases.add(s)
    return phrases


def check_similarity(sample_text: str, generated_text: str) -> SimilarityReport:
    if not sample_text.strip() or not generated_text.strip():
        return SimilarityReport(risk_level="low", reason="缺少样章或生成文本，无法比较。")
    sample_grams = char_ngrams(sample_text)
    gen_grams = char_ngrams(generated_text)
    overlap = len(sample_grams & gen_grams) / max(1, len(gen_grams))
    lcs = longest_common_substring(sample_text, generated_text)
    rare_overlap = sorted((rare_phrases(sample_text) & rare_phrases(generated_text)), key=len, reverse=True)[:10]
    sample_pattern = paragraph_pattern(sample_text)
    gen_pattern = paragraph_pattern(generated_text)
    pattern_score = 0.0
    if sample_pattern and gen_pattern:
        pairs = zip(sample_pattern[:10], gen_pattern[:10])
        close = sum(1 for a, b in pairs if abs(a - b) <= max(10, int(a * 0.15)))
        pattern_score = close / max(1, min(len(sample_pattern), len(gen_pattern), 10))
    score = min(1.0, overlap * 0.65 + (len(lcs) / 120) * 0.25 + pattern_score * 0.1)
    matched = []
    if len(lcs) >= 20:
        matched.append(lcs[:60])
    matched.extend(rare_overlap[:5])
    if score >= 0.22 or len(lcs) >= 40 or len(rare_overlap) >= 3:
        risk = "high"
    elif score >= 0.1 or len(lcs) >= 24 or rare_overlap:
        risk = "medium"
    else:
        risk = "low"
    return SimilarityReport(
        risk_level=risk,
        overlap_score=round(score, 4),
        matched_phrases=matched,
        reason=f"8-gram overlap={overlap:.3f}; longest_common={len(lcs)} chars; paragraph_pattern={pattern_score:.3f}",
        rewrite_required=risk == "high",
    )

