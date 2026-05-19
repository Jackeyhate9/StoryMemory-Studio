from app.config import get_settings
from app.llm.client import ChatCompletionsClient


def create_deepseek_client() -> ChatCompletionsClient:
    settings = get_settings()
    return ChatCompletionsClient(
        "deepseek", settings.deepseek_base_url, settings.deepseek_api_key, settings.deepseek_model
    )

