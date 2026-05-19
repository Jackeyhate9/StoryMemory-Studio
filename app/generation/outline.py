from app.generation.chapter import generate_chapter


def generate_outline(client, context_prompt: str, extra_instruction: str = "") -> str:
    return generate_chapter(client, context_prompt, mode="generate_outline", extra_instruction=extra_instruction, temperature=0.4)

