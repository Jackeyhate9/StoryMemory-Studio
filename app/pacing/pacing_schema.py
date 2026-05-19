from __future__ import annotations

from pydantic import BaseModel, Field


class PacingIssue(BaseModel):
    issue_type: str
    severity: str = "medium"
    location: str = ""
    reason: str
    suggestion: str
    rewrite_direction: str = ""


class PacingReport(BaseModel):
    chapter_score: int = Field(ge=0, le=100)
    opening_hook_score: int = Field(ge=0, le=100)
    conflict_score: int = Field(ge=0, le=100)
    plot_progress_score: int = Field(ge=0, le=100)
    emotion_peak_score: int = Field(ge=0, le=100)
    middle_drag_risk: str = "low"
    ending_hook_score: int = Field(ge=0, le=100)
    retention_prediction: int = Field(ge=0, le=100)
    issues: list[PacingIssue] = Field(default_factory=list)
    next_chapter_suggestions: list[str] = Field(default_factory=list)
