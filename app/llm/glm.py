from app.config import get_settings
from app.llm.client import ChatCompletionsClient


def create_glm_client() -> ChatCompletionsClient:
    settings = get_settings()
    api_key = settings.glm_api_key or settings.zai_api_key or settings.bigmodel_api_key
    extra_payload = {"thinking": {"type": "disabled"}} if settings.glm_disable_thinking else {}
    return ChatCompletionsClient(
        "glm",
        settings.glm_base_url,
        api_key,
        settings.glm_model,
        extra_payload=extra_payload,
    )
