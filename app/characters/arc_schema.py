from __future__ import annotations

from pydantic import BaseModel, Field


class DriftIssue(BaseModel):
    issue_type: str
    reason: str
    evidence: str = ""
    suggestion: str = ""


class CharacterArcReport(BaseModel):
    character_id: int
    character_name: str
    arc_stage: str = ""
    current_goal: str = ""
    psychological_state: str = ""
    relationship_changes: list[str] = Field(default_factory=list)
    ability_changes: list[str] = Field(default_factory=list)
    key_behavior: str = ""
    drift_risk: str = "low"
    drift_issues: list[DriftIssue] = Field(default_factory=list)
    next_arc_suggestions: list[str] = Field(default_factory=list)
