from __future__ import annotations

from pathlib import Path

from app.db.models import ConsistencyReport
from app.llm.client import LLMClient, extract_json, repair_json_with_llm

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "consistency_check.md"


def heuristic_check(chapter_text: str) -> ConsistencyReport:
    issues = []
    ai_phrases = ["命运的齿轮", "一场关于", "不是简单的", "更是", "内心深处"]
    for phrase in ai_phrases:
        if phrase in chapter_text:
            issues.append(
                {
                    "issue_type": "AI腔表达",
                    "severity": "low",
                    "source_text": phrase,
                    "evidence": "命中常见模板化表达",
                    "suggestion": "改成更具体的动作、感官或人物视角表达。",
                }
            )
    return ConsistencyReport.model_validate({"passed": not issues, "issues": issues, "suggestions": []})


class ConsistencyChecker:
    def __init__(self, client: LLMClient | None = None):
        self.client = client

    def check(self, context_prompt: str, chapter_text: str, chapter_goal: str = "") -> ConsistencyReport:
        if self.client is None:
            return heuristic_check(chapter_text)
        template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = template.format(context=context_prompt, chapter_text=chapter_text, chapter_goal=chapter_goal)
        raw = self.client.complete(prompt, temperature=0)
        try:
            data = extract_json(raw)
        except Exception:
            data = repair_json_with_llm(raw, self.client)
        return ConsistencyReport.model_validate(data)

