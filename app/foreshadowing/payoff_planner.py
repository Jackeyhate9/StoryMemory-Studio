from __future__ import annotations

from app.foreshadowing.payoff_schema import PayoffRecommendation


def write_payoff_plan(rec: PayoffRecommendation) -> str:
    return (
        f"伏笔：{rec.foreshadow_name}\n"
        f"回收窗口：{rec.recommended_payoff_window}\n"
        f"回收类型：{rec.recommended_payoff_type}\n"
        f"方案：{rec.payoff_method}\n"
        f"章纲建议：{rec.suggested_chapter_outline}\n"
    )
