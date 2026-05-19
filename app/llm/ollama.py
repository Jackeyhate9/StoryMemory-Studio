from app.config import get_settings
from app.llm.client import OllamaClient


def create_ollama_client() -> OllamaClient:
    settings = get_settings()
    return OllamaClient(settings.ollama_base_url, settings.ollama_model)

