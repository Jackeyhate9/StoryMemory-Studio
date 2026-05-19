from __future__ import annotations

from typing import Any

import httpx

from app.llm.client import ChatCompletionsClient, OllamaClient, get_llm
from app.llm.ollama_utils import select_best_ollama_model


def validate_llm_connection(provider: str | None = None, run_completion: bool = True) -> dict[str, Any]:
    client = get_llm(provider)
    result: dict[str, Any] = {
        "provider": client.provider,
        "model": client.model,
        "ok": False,
        "models_endpoint_ok": False,
        "models_error": "",
        "model_found": None,
        "completion_ok": False,
        "completion_error": "",
        "models": [],
        "message": "",
    }
    if isinstance(client, (ChatCompletionsClient, OllamaClient)):
        try:
            models = client.list_models()
            result["models"] = models[:50]
            result["models_endpoint_ok"] = True
            result["model_found"] = client.model in models if models else None
            if isinstance(client, OllamaClient) and models and client.model not in models:
                selection = select_best_ollama_model(client.base_url)
                if selection.available and selection.model:
                    client.model = selection.model
                    result["model"] = selection.model
                    result["model_found"] = True
                    result["auto_selected_model"] = selection.model
                    result["selection_reason"] = selection.reason
                else:
                    result["message"] = f"Ollama model not found locally: {client.model}. Run: ollama pull qwen3"
                    result["ok"] = False
                    return result
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:1000] if exc.response is not None else ""
            result["models_error"] = f"HTTP {exc.response.status_code}: {body}" if exc.response is not None else str(exc)
        except Exception as exc:
            result["models_error"] = str(exc)

    if run_completion:
        try:
            text = client.complete("请只回复 OK。", temperature=0)
            result["completion_ok"] = bool(text.strip())
            result["sample"] = text.strip()[:200]
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:1000] if exc.response is not None else ""
            result["completion_error"] = f"HTTP {exc.response.status_code}: {body}" if exc.response is not None else str(exc)
        except Exception as exc:
            result["completion_error"] = str(exc)

    if run_completion:
        result["ok"] = bool(result["completion_ok"])
    else:
        result["ok"] = bool(result["models_endpoint_ok"] and result["model_found"] is not False)

    if result["ok"]:
        result["message"] = "Connection validated"
    elif result["completion_error"]:
        result["message"] = result["completion_error"]
    elif result["models_error"]:
        result["message"] = result["models_error"]
    elif result["model_found"] is False:
        result["message"] = f"Configured model was not returned by the model list endpoint: {client.model}"
    else:
        result["message"] = "Connection validation failed"
    return result
