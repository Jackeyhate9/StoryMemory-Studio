from __future__ import annotations

from pydantic import BaseModel, Field


class PlatformProfile(BaseModel):
    platform_name: str
    chapter_opening: str
    pacing: str
    dialogue: str
    description: str
    ending_hook: str
    avoid: list[str] = Field(default_factory=list)
    best_for: list[str] = Field(default_factory=list)


class PlatformFitReport(BaseModel):
    platform: str
    fit_score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    required_adjustments: list[str] = Field(default_factory=list)
    rewritten_opening_suggestion: str = ""
    ending_hook_suggestion: str = ""
    style_rules: list[str] = Field(default_factory=list)
    avoid_rules: list[str] = Field(default_factory=list)
