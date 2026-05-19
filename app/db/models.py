from typing import Any, Literal

from pydantic import BaseModel, Field


class MemoryExtraction(BaseModel):
    summary: dict[str, Any] = Field(default_factory=dict)
    characters: list[dict[str, Any]] = Field(default_factory=list)
    relationship_changes: list[dict[str, Any]] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    organizations: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    abilities: list[dict[str, Any]] = Field(default_factory=list)
    world_rules: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)
    foreshadows: list[dict[str, Any]] = Field(default_factory=list)
    timeline_events: list[dict[str, Any]] = Field(default_factory=list)
    plot_threads: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: list[dict[str, Any]] = Field(default_factory=list)
    style_features: dict[str, Any] = Field(default_factory=dict)


class ConsistencyIssue(BaseModel):
    issue_type: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    source_text: str = ""
    evidence: str = ""
    suggestion: str = ""


class ConsistencyReport(BaseModel):
    passed: bool = True
    issues: list[ConsistencyIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ContextRequest(BaseModel):
    project: str
    chapter_number: int
    chapter_goal: str = ""
    chapter_outline: str = ""
    volume: str = ""
    characters: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    plot_threads: list[str] = Field(default_factory=list)
    foreshadows: list[str] = Field(default_factory=list)
    mode: Literal["lite", "standard", "deepseek_long", "full_audit"] = "standard"

