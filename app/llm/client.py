import json
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import get_settings


class LLMClient(ABC):
    provider: str
    model: str

    @abstractmethod
    def complete(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        raise NotImplementedError


class ChatCompletionsClient(LLMClient):
    def __init__(
        self,
        provider: str,
        base_url: str,
        api_key: str | None,
        model: str,
        *,
        extra_payload: dict[str, Any] | None = None,
    ):
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.extra_payload = extra_payload or {}

    def complete(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        if not self.api_key:
            raise RuntimeError(f"{self.provider} API key is not configured")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system or "You are a careful writing system assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        payload.update(self.extra_payload)
        with httpx.Client(timeout=180) as client:
            endpoint = f"{self.base_url}/chat/completions"
            resp = client.post(endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def list_models(self) -> list[str]:
        if not self.api_key:
            raise RuntimeError(f"{self.provider} API key is not configured")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{self.base_url}/models", headers=headers)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            return [item.get("id", "") for item in data if item.get("id")]


class OllamaClient(LLMClient):
    def __init__(self, base_url: str, model: str):
        self.provider = "ollama"
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "options": {"temperature": temperature, "num_ctx": 32768},
            "messages": [
                {"role": "system", "content": system or "You are a careful writing system assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        last_error: Exception | None = None
        for timeout in (300, 600):
            try:
                with httpx.Client(timeout=timeout, trust_env=False) as client:
                    resp = client.post(f"{self.base_url}/api/chat", json=payload)
                    resp.raise_for_status()
                    return resp.json()["message"]["content"]
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"Ollama generation failed after retry: {last_error}")

    def list_models(self) -> list[str]:
        with httpx.Client(timeout=30, trust_env=False) as client:
            resp = client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json().get("models", [])
            return [item.get("name", "") for item in data if item.get("name")]


def get_llm(provider: str | None = None) -> LLMClient:
    settings = get_settings()
    selected = provider or settings.llm_provider
    if selected == "deepseek":
        return ChatCompletionsClient(
            "deepseek", settings.deepseek_base_url, settings.deepseek_api_key, settings.deepseek_model
        )
    if selected == "openai":
        return ChatCompletionsClient(
            "openai",
            settings.openai_base_url,
            settings.openai_api_key or settings.openai_compatible_api_key,
            settings.openai_model,
        )
    if selected == "openai_compatible":
        return ChatCompletionsClient(
            "openai_compatible",
            settings.openai_compatible_base_url,
            settings.openai_compatible_api_key,
            settings.openai_compatible_model,
        )
    if selected in {"glm", "zhipu", "zai", "bigmodel"}:
        glm_key = settings.glm_api_key or settings.zai_api_key or settings.bigmodel_api_key
        glm_payload = {"thinking": {"type": "disabled"}} if settings.glm_disable_thinking else {}
        return ChatCompletionsClient(
            "glm",
            settings.glm_base_url,
            glm_key,
            settings.glm_model,
            extra_payload=glm_payload,
        )
    if selected == "ollama":
        return OllamaClient(settings.ollama_base_url, settings.ollama_model)
    raise ValueError(f"Unknown LLM provider: {selected}")


def extract_json(text: str) -> Any:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.S)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start_candidates = [i for i in [cleaned.find("{"), cleaned.find("[")] if i >= 0]
        if not start_candidates:
            raise
        start = min(start_candidates)
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        if end <= start:
            raise
        return json.loads(cleaned[start : end + 1])


def repair_json_with_llm(raw_text: str, client: LLMClient) -> Any:
    prompt = (
        "下面内容本应是 JSON，但格式可能损坏。请只输出修复后的合法 JSON，"
        "不要解释，不要添加 Markdown。\n\n"
        f"{raw_text}"
    )
    repaired = client.complete(prompt, temperature=0)
    return extract_json(repaired)
