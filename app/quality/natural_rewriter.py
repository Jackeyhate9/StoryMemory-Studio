from __future__ import annotations

from app.quality.ai_tone_detector import detect_ai_tone
from app.quality.ai_tone_schema import RewriteResult


def rewrite_ai_tone_text(text: str) -> RewriteResult:
    report = detect_ai_tone(text)
    rewritten = text
    changed = []
    for issue in report.issues:
        if issue.natural_rewrite and issue.original_text in rewritten:
            rewritten = rewritten.replace(issue.original_text, issue.natural_rewrite, 1)
            changed.append({"from": issue.original_text, "to": issue.natural_rewrite, "issue_type": issue.issue_type})
    return RewriteResult(rewritten_text=rewritten, changed_segments=changed, applied=False)
