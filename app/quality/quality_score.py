from __future__ import annotations


def risk_from_score(score: int) -> str:
    if score < 60:
        return "high"
    if score < 82:
        return "medium"
    return "low"
