from app.generation.chapter import generate_chapter


def rewrite_chapter(client, context_prompt: str, draft: str, extra_instruction: str = "") -> str:
    instruction = f"{extra_instruction}\n\n【待改写文本】\n{draft}"
    return generate_chapter(client, context_prompt, mode="rewrite", extra_instruction=instruction, temperature=0.5)

