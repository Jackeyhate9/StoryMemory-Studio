from app.config import get_settings
from app.llm.client import ChatCompletionsClient


def create_openai_compatible_client() -> ChatCompletionsClient:
    settings = get_settings()
    return ChatCompletionsClient(
        "openai_compatible",
        settings.openai_compatible_base_url,
        settings.openai_compatible_api_key,
        settings.openai_compatible_model,
    )

