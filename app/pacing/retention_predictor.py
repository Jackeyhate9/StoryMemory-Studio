from __future__ import annotations

from app.pacing.pacing_schema import PacingReport


def predict_retention(report: PacingReport) -> int:
    return max(0, min(100, round(report.chapter_score * 0.7 + report.ending_hook_score * 0.3)))
