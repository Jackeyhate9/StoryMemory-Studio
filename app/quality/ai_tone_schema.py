from __future__ import annotations

from pydantic import BaseModel, Field


AI_TONE_TYPES = [
    "meta_model_trace",
    "template_sentence",
    "vague_emotion",
    "exposition_dump",
    "summary_voice",
    "unnatural_dialogue",
    "repetitive_rhythm",
    "over_abstract",
    "acceptable_literary_expression",
    "light_novel_allowed",
    "character_card_dump",
    "worldbuilding_dump",
    "abstract_metaphor_overload",
    "dialogue_exposition",
    "template_hook",
    "lack_of_scene_friction",
    "insufficient_subtext",
    "overexplained_relationship",
]


class AIToneIssue(BaseModel):
    issue_type: str
    severity: str = "medium"
    confidence: float = Field(default=0.7, ge=0, le=1)
    reader_impact: str = "medium"
    original_text: str
    reason: str
    why_it_feels_ai: str = ""
    can_keep: bool = False
    rewrite_priority: str = "local_sentence_rewrite"
    rewrite_suggestion: str = ""
    natural_rewrite: str = ""


class AIToneReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    risk_level: str = "low"
    ai_tone_density: float = Field(default=0, ge=0)
    reader_impact: str = "low"
    rewrite_priority: str = "none"
    summary: str = ""
    issue_distribution: dict[str, int] = Field(default_factory=dict)
    issues: list[AIToneIssue] = Field(default_factory=list)
    chapter_level_advice: list[str] = Field(default_factory=list)
    generation_prompt_adjustments: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class RewriteResult(BaseModel):
    rewritten_text: str
    changed_segments: list[dict] = Field(default_factory=list)
    applied: bool = False
