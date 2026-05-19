from pathlib import Path

from app.llm.client import LLMClient, extract_json, repair_json_with_llm

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "style_profile.md"


def profile_style(client: LLMClient, sample_text: str, platform: str = "") -> dict:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").format(sample_text=sample_text, platform=platform)
    raw = client.complete(prompt, temperature=0)
    try:
        return extract_json(raw)
    except Exception:
        return repair_json_with_llm(raw, client)

