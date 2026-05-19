from __future__ import annotations

import re

from app.adaptation.adaptation_schema import AdaptationResult, ComicPanel, ShortDramaScene, VideoShot


def adapt_chapter(chapter_id: int, title: str, text: str, adaptation_type: str = "all") -> AdaptationResult:
    scenes = _split_scenes(text)
    adaptations: dict = {}
    if adaptation_type in {"all", "comic"}:
        adaptations["comic_storyboard"] = [p.model_dump() for p in _comic(scenes)]
    if adaptation_type in {"all", "short_drama"}:
        adaptations["short_drama_script"] = [s.model_dump() for s in _short_drama(scenes)]
    if adaptation_type in {"all", "video"}:
        adaptations["video_storyboard"] = [s.model_dump() for s in _video(scenes)]
    if adaptation_type in {"all", "xiaohongshu"}:
        adaptations["xiaohongshu_post"] = f"《{title}》这一章太适合追更：开局给冲突，中段埋线索，结尾留问题。看点：{_one_line(scenes[0])}"
    if adaptation_type in {"all", "poster"}:
        adaptations["poster_prompts"] = [f"小说章节海报，{title}，主角站在关键场景中，强对比光影，悬疑氛围，电影感构图"]
        adaptations["character_cards"] = []
    if adaptation_type in {"all", "quotes"}:
        adaptations["chapter_quotes"] = _quotes(text)
        adaptations["teaser_copy"] = f"第 {chapter_id} 章，新的线索出现，真正的危险也随之靠近。"
    return AdaptationResult(chapter_id=chapter_id, adaptations=adaptations)


def _split_scenes(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    if not paras:
        paras = [text[:400]]
    return paras[:8]


def _comic(scenes: list[str]) -> list[ComicPanel]:
    return [
        ComicPanel(panel=i, scene=_one_line(scene), camera="中景/特写交替", action=_one_line(scene), caption="", visual_prompt=f"漫画分镜，第{i}格，{_one_line(scene)}")
        for i, scene in enumerate(scenes[:8], 1)
    ]


def _short_drama(scenes: list[str]) -> list[ShortDramaScene]:
    return [
        ShortDramaScene(scene_number=i, location="按原章节场景", time="连续时间", action=_one_line(scene), dialogue=_dialogue(scene), turning_point="信息变化或关系转折", hook="保留下一场冲突")
        for i, scene in enumerate(scenes[:6], 1)
    ]


def _video(scenes: list[str]) -> list[VideoShot]:
    return [
        VideoShot(shot_number=i, scene_base=_one_line(scene), subject_action=_one_line(scene), camera_movement="缓慢推进/切特写", lighting_color="冷暖对比，悬疑氛围", transition="硬切", video_prompt=f"cinematic shot, {_one_line(scene)}")
        for i, scene in enumerate(scenes[:8], 1)
    ]


def _one_line(text: str) -> str:
    return re.sub(r"\s+", "", text)[:80]


def _dialogue(text: str) -> list[str]:
    found = re.findall(r"“([^”]{1,80})”", text)
    return found[:4]


def _quotes(text: str) -> list[str]:
    sentences = re.split(r"(?<=[。！？])", text)
    return [s.strip() for s in sentences if 10 <= len(s.strip()) <= 40][:8]
