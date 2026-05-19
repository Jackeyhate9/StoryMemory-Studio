from __future__ import annotations

from pydantic import BaseModel, Field


class ComicPanel(BaseModel):
    panel: int
    scene: str = ""
    characters: list[str] = Field(default_factory=list)
    camera: str = ""
    action: str = ""
    dialogue: str = ""
    caption: str = ""
    visual_prompt: str = ""


class ShortDramaScene(BaseModel):
    scene_number: int
    location: str = ""
    time: str = ""
    characters: list[str] = Field(default_factory=list)
    action: str = ""
    dialogue: list[str] = Field(default_factory=list)
    turning_point: str = ""
    hook: str = ""


class VideoShot(BaseModel):
    shot_number: int
    duration: str = "5s"
    scene_base: str = ""
    subject_action: str = ""
    camera_movement: str = ""
    lighting_color: str = ""
    transition: str = ""
    video_prompt: str = ""


class AdaptationResult(BaseModel):
    chapter_id: int
    adaptations: dict = Field(default_factory=dict)
