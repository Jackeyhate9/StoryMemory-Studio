from __future__ import annotations

from pydantic import BaseModel, Field


class PayoffRecommendation(BaseModel):
    foreshadow_id: int
    foreshadow_name: str
    current_status: str
    risk_level: str = "low"
    chapters_since_last_mention: int = 0
    recommended_payoff_window: str = ""
    recommended_payoff_type: str = "reveal"
    reason: str = ""
    payoff_method: str = ""
    related_characters: list[str] = Field(default_factory=list)
    related_items: list[str] = Field(default_factory=list)
    suggested_chapter_outline: str = ""
    impact_score: int = Field(default=50, ge=0, le=100)


class PayoffReport(BaseModel):
    recommendations: list[PayoffRecommendation] = Field(default_factory=list)
    urgent_payoffs: list[int] = Field(default_factory=list)
    safe_to_delay: list[int] = Field(default_factory=list)
    forgotten_risks: list[int] = Field(default_factory=list)
