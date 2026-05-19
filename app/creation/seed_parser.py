from __future__ import annotations

import re
from typing import Any

from app.schemas.create_novel import NovelSeedInput


def split_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in re.split(r"[,，、\n]+", value) if x.strip()]


def parse_length(value: str | int | None) -> int:
    if value is None:
        return 100
    if isinstance(value, int):
        return value
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else 100


def parse_seed(mode: str = "minimal", **kwargs: Any) -> NovelSeedInput:
    return NovelSeedInput(
        mode="pro" if mode == "pro" else "minimal",
        title=kwargs.get("title") or "未命名小说",
        genre=kwargs.get("genre") or kwargs.get("topic") or "",
        platform=kwargs.get("platform") or "",
        target_reader=kwargs.get("target_reader") or "",
        expected_word_count=int(kwargs.get("word_count") or kwargs.get("expected_word_count") or 0),
        chapter_word_count=int(kwargs.get("chapter_word_count") or 2500),
        premise=kwargs.get("premise") or kwargs.get("logline") or "",
        protagonist=kwargs.get("protagonist") or "",
        protagonist_goal=kwargs.get("goal") or kwargs.get("protagonist_goal") or "",
        selling_points=split_list(kwargs.get("selling_points")),
        avoid=split_list(kwargs.get("avoid")),
        expected_chapters=parse_length(kwargs.get("length") or kwargs.get("expected_chapters")),
        style_reference=kwargs.get("style") or kwargs.get("style_reference") or "",
        core_conflict=kwargs.get("core_conflict") or "",
        story_highlights=kwargs.get("story_highlights") or "",
        major_characters=kwargs.get("major_characters") or "",
        world_setting=kwargs.get("world_setting") or "",
        ability_system=kwargs.get("ability_system") or "",
        organizations=kwargs.get("organizations") or "",
        opening_event=kwargs.get("opening_event") or "",
        first_volume_climax=kwargs.get("first_volume_climax") or "",
        midpoint_twist=kwargs.get("midpoint_twist") or "",
        ending_direction=kwargs.get("ending_direction") or "",
        hard_rules=split_list(kwargs.get("hard_rules")),
    )

