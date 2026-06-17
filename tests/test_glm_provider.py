def test_glm_provider_defaults(monkeypatch):
    monkeypatch.setenv("GLM_API_KEY", "test-key")
    monkeypatch.delenv("DEFAULT_MODEL_PROVIDER", raising=False)

    from app.config import get_settings
    from app.llm.client import ChatCompletionsClient, get_llm

    get_settings.cache_clear()
    client = get_llm("glm")

    assert isinstance(client, ChatCompletionsClient)
    assert client.provider == "glm"
    assert client.base_url == "https://open.bigmodel.cn/api/paas/v4"
    assert client.model == "glm-5.2"
    assert client.extra_payload == {"thinking": {"type": "disabled"}}


def test_glm_provider_accepts_zai_key(monkeypatch):
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.setenv("ZAI_API_KEY", "zai-key")
    monkeypatch.setenv("GLM_DISABLE_THINKING", "false")

    from app.config import get_settings
    from app.llm.client import get_llm

    get_settings.cache_clear()
    client = get_llm("zai")

    assert client.provider == "glm"
    assert client.api_key == "zai-key"
    assert client.extra_payload == {}


def test_auto_provider_can_choose_glm(monkeypatch):
    monkeypatch.setenv("DEFAULT_MODEL_PROVIDER", "glm")
    monkeypatch.setenv("GLM_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")

    from app.config import get_settings
    from app.ui.services import resolve_auto_provider

    get_settings.cache_clear()
    assert resolve_auto_provider("auto") == "glm"
