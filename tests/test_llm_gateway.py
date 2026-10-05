"""Offline regression checks for configurable gateway transport."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.llm import MeteredLLM, Usage, _openai_client, configured_price


def test_gateway_base_url_is_passed_to_sdk(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    with patch("openai.OpenAI") as client:
        _openai_client("openai")
    client.assert_called_once_with(api_key="test-only", base_url="https://gateway.example/v1")


def test_responses_json_and_token_metering():
    llm = MeteredLLM.__new__(MeteredLLM)
    llm.chat_provider = "openai"
    llm.chat_api = "responses"
    llm.chat_model_id = "gpt-4o-mini"
    llm.usage = Usage()
    llm._chat_client = Mock()
    llm._chat_client.responses.create.return_value = SimpleNamespace(
        output_text='```json\n{"cases": []}\n```',
        usage=SimpleNamespace(input_tokens=25, output_tokens=5),
    )
    assert llm.chat("Extract cases", json_mode=True) == '{"cases": []}'
    kwargs = llm._chat_client.responses.create.call_args.kwargs
    assert kwargs["store"] is False
    assert "JSON" in kwargs["input"]
    assert "temperature" not in kwargs
    assert llm.usage.input_tokens == 25
    assert llm.usage.output_tokens == 5
    assert llm.usage.calls == 1
    llm._chat_client.chat.completions.create.assert_not_called()


def test_gateway_price_accounts_for_cached_input(monkeypatch):
    monkeypatch.setenv("OPENAI_CHAT_INPUT_USD_PER_M", "1.8")
    monkeypatch.setenv("OPENAI_CHAT_OUTPUT_USD_PER_M", "9")
    monkeypatch.setenv("OPENAI_CHAT_CACHED_INPUT_USD_PER_M", "0.09")
    assert abs(configured_price("openai", "chat", "gateway-model", 1000, 100, 500) - 0.001845) < 1e-10


def test_embedding_retries_server_delay_and_counts_only_success(monkeypatch):
    import httpx
    from openai import RateLimitError
    monkeypatch.setenv("GEMINI_EMBEDDING_MIN_INTERVAL", "0")
    monkeypatch.setenv("GEMINI_EMBEDDING_INPUT_USD_PER_M", "0")
    llm = MeteredLLM.__new__(MeteredLLM)
    llm.embed_provider = "gemini"
    llm.embed_model_id = "gemini-embedding-001"
    llm._last_embed_request = 0
    llm.usage = Usage()
    llm._embed_client = Mock()
    error = RateLimitError("rate limit", response=httpx.Response(429, request=httpx.Request("POST", "https://example.test")),
                          body={"details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "2s"}]})
    llm._embed_client.embeddings.create.side_effect = [error, SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=10), data=[SimpleNamespace(embedding=[0.1, 0.2])])]
    with patch("src.llm.time.sleep") as sleep:
        assert llm.embed("text") == [0.1, 0.2]
    sleep.assert_called_once_with(3)
    assert llm.usage.calls == 1
    assert llm.usage.input_tokens == 10
