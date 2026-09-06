"""Tests for the OpenRouterAdapter — ticket #45.

The adapter talks to the OpenRouter cloud API; these tests replace the
HTTP transport with :class:`httpx.MockTransport` and inject an API key,
so no real network access is needed.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from boskoll_cli.models import (
    ModelAuthenticationError,
    ModelError,
    ModelNotFoundError,
    ModelRateLimitError,
)
from boskoll_cli.models.openrouter import OpenRouterAdapter

Handler = Callable[[httpx.Request], httpx.Response]

API_KEY = "test-key-123"


def make_adapter(handler: Handler) -> OpenRouterAdapter:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://openrouter.ai/api/v1")
    return OpenRouterAdapter(api_key=API_KEY, client=client)


def test_operations_require_api_key() -> None:
    adapter = OpenRouterAdapter(api_key="")
    with pytest.raises(ModelAuthenticationError, match="OPENROUTER_API_KEY"):
        adapter.list_models()


def test_list_models_authenticates_and_parses() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/models"
        assert request.headers["Authorization"] == f"Bearer {API_KEY}"
        return httpx.Response(
            200,
            json={"data": [{"id": "openai/gpt-4o"}, {"id": "anthropic/claude-3.5-sonnet"}]},
        )

    adapter = make_adapter(handler)
    models = adapter.list_models()
    assert [model.id for model in models] == ["openai/gpt-4o", "anthropic/claude-3.5-sonnet"]
    assert all(model.provider == "openrouter" for model in models)


def test_generate_sends_chat_messages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read()
        assert b'"stream":false' in body
        assert b'"model":"openai/gpt-4o"' in body
        assert b'"role":"system"' in body
        assert b'"role":"user"' in body
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            },
        )

    adapter = make_adapter(handler)
    response = adapter.generate("hi", model="openai/gpt-4o", system_prompt="be terse")
    assert response.text == "Hello!"
    assert response.prompt_tokens == 5
    assert response.completion_tokens == 2


def test_generate_uses_default_model_when_none_given() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"model":"openrouter/auto"' in request.read()
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    adapter = make_adapter(handler)
    assert adapter.generate("hi").text == "ok"


def test_generate_rejects_bad_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    adapter = make_adapter(handler)
    with pytest.raises(ModelAuthenticationError, match="OPENROUTER_API_KEY"):
        adapter.generate("hi", model="m")


def test_generate_handles_rate_limit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "30"}, json={})

    adapter = make_adapter(handler)
    with pytest.raises(ModelRateLimitError, match="30 seconds"):
        adapter.generate("hi", model="m")


def test_generate_reports_unknown_model() -> None:
    adapter = make_adapter(lambda request: httpx.Response(404, json={}))
    with pytest.raises(ModelNotFoundError, match="openrouter.ai/models"):
        adapter.generate("hi", model="nope")


def test_generate_surfaces_api_error_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": "insufficient credits"}},
        )

    adapter = make_adapter(handler)
    with pytest.raises(ModelError, match="insufficient credits"):
        adapter.generate("hi", model="m")


def test_stream_yields_delta_content() -> None:
    sse = (
        'data: {"choices": [{"delta": {"role": "assistant"}}]}\n\n'
        'data: {"choices": [{"delta": {"content": "Hel"}}]}\n\n'
        'data: {"choices": [{"delta": {"content": "lo"}}]}\n\n'
        'data: [DONE]\n\n'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"stream":true' in request.read()
        return httpx.Response(200, text=sse)

    adapter = make_adapter(handler)
    assert list(adapter.stream("hi", model="m")) == ["Hel", "lo"]


def test_stream_stops_at_done_and_skips_empty_deltas() -> None:
    sse = (
        'data: {"choices": [{"delta": {"content": "a"}}]}\n\n'
        'data: [DONE]\n\n'
        'data: {"choices": [{"delta": {"content": "ignored"}}]}\n\n'
    )

    adapter = make_adapter(lambda request: httpx.Response(200, text=sse))
    assert list(adapter.stream("hi", model="m")) == ["a"]
