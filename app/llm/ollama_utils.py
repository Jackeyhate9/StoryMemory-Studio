from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import httpx

from app.config import get_settings


OLLAMA_MODEL_PRIORITY = [
    "qwen3",
    "qwen2.5",
    "deepseek-r1",
    "yi",
    "glm",
    "llama3.1",
    "llama3",
    "mistral",
    "gemma",
]


@dataclass
class OllamaModelSelection:
    available: bool
    model: str
    models: list[str]
    reason: str
    install_hint: str = ""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def list_ollama_models(base_url: str | None = None, timeout: float = 5.0) -> list[dict[str, Any]]:
    settings = get_settings()
    url = (base_url or settings.ollama_base_url).rstrip("/")
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        response = client.get(f"{url}/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])


def select_best_ollama_model(base_url: str | None = None) -> OllamaModelSelection:
    try:
        models = list_ollama_models(base_url)
    except Exception as exc:
        return OllamaModelSelection(
            available=False,
            model="",
            models=[],
            reason=f"Ollama 连接失败：{exc}",
            install_hint="请先启动 Ollama：ollama serve；再安装中文写作模型：ollama pull qwen3 或 ollama pull qwen2.5:14b",
        )
    names = [item.get("name") or item.get("model") or "" for item in models]
    names = [name for name in names if name]
    if not names:
        return OllamaModelSelection(
            available=False,
            model="",
            models=[],
            reason="Ollama 可连接，但没有发现已安装模型。",
            install_hint="建议安装：ollama pull qwen3 或 ollama pull qwen2.5:14b",
        )
    lowered = {name: name.lower() for name in names}
    for key in OLLAMA_MODEL_PRIORITY:
        matched = [name for name, low in lowered.items() if key in low]
        if matched:
            matched.sort(key=lambda n: ("embed" in n.lower(), len(n)))
            return OllamaModelSelection(
                available=True,
                model=matched[0],
                models=names,
                reason=f"命中优先级 {key}，更适合中文长篇、人物关系和连续章节生成。",
            )
    return OllamaModelSelection(
        available=True,
        model=names[0],
        models=names,
        reason="未命中内置优先级，使用本地模型列表中的第一个可用模型。",
    )
