from __future__ import annotations

from pathlib import Path

from app.llm.client import LLMClient
from app.llm.output_cleaner import clean_model_output
from app.quality.humanizer_zh import humanize_zh_text
from app.style.similarity_guard import check_similarity


PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "generate_chapter.md"


def _postprocess_generated_prose(text: str) -> str:
    cleaned = clean_model_output(text, mode="prose")
    humanized, _report = humanize_zh_text(cleaned)
    return humanized


def generate_chapter(
    client: LLMClient,
    context_prompt: str,
    mode: str = "generate_chapter",
    extra_instruction: str = "",
    temperature: float = 0.7,
) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = template.format(context=context_prompt, mode=mode, extra_instruction=extra_instruction)
    raw = client.complete(
        prompt,
        system="你是严谨的长篇小说创作中控台，必须优先遵守结构化记忆，并写出自然、具体、场景驱动的中文小说正文。",
        temperature=temperature,
    )
    return _postprocess_generated_prose(raw)


def rewrite_if_too_similar(
    client: LLMClient,
    generated_text: str,
    sample_text: str,
    context_prompt: str,
    style_profile: str,
    user_goal: str = "",
) -> tuple[str, dict]:
    report = check_similarity(sample_text, generated_text)
    if not report.rewrite_required:
        return generated_text, report.model_dump()
    prompt_path = Path(__file__).parents[1] / "prompts" / "style_transfer_rewrite.md"
    prompt = prompt_path.read_text(encoding="utf-8").format(
        context=context_prompt,
        memory="见当前章节上下文",
        style_profile=style_profile,
        user_goal=user_goal,
        text=generated_text,
    )
    rewritten = client.complete(prompt, system="你是原创改写助手，必须避免具体表达相似。", temperature=0.5)
    rewritten = _postprocess_generated_prose(rewritten)
    second = check_similarity(sample_text, rewritten)
    payload = report.model_dump()
    payload["rewritten_similarity"] = second.model_dump()
    payload["humanizer_zh_applied"] = True
    return rewritten, payload
