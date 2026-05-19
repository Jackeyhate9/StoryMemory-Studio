from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LengthTarget:
    target_chars: int
    min_chars: int
    max_chars: int


def chapter_length_target(words_per_chapter: int | str = 3000) -> LengthTarget:
    text = str(words_per_chapter)
    digits = "".join(ch for ch in text if ch.isdigit())
    target = int(digits or 3000)
    return LengthTarget(target_chars=target, min_chars=int(target * 0.9), max_chars=int(target * 1.2))


def polish_length_bounds(original_chars: int) -> tuple[int, int]:
    return int(original_chars * 0.85), int(original_chars * 1.15)


def length_status(text: str, target: LengthTarget) -> str:
    size = len(text)
    if size < target.min_chars:
        return "too_short"
    if size > target.max_chars:
        return "too_long"
    return "ok"
