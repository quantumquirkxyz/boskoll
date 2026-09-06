"""Tests for the OllamaAdapter — ticket #44.

The adapter talks to a local Ollama server; these tests replace the HTTP
transport with :class:`httpx.MockTransport`, so no real server is needed.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from boskoll_cli.models import (
    ModelConnectionError,
    ModelError,
    ModelNotFoundError,
    ModelResponse,
)
from boskoll_cli.models.ollama import OllamaAdapter

Handler = Callable[[httpx.Request], httpx.Response]


def make_adapter(handler: Handler) -> OllamaAdapter:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama.test")
    return OllamaAdapter(base_url="http://ollama.test", client=client)


def test_list_models_parses_tags() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "llama3.1:latest"}]})

    adapter = make_adapter(handler)
    models = adapter.list_models()
    assert len(models) == 1
    assert models[0].id == "llama3.1:latest"
    assert models[0].provider == "ollama"


def test_list_models_empty_when_no_tags() -> None:
    adapter = make_adapter(lambda request: httpx.Response(200, json={"models": []}))
    assert adapter.list_models() == []


def test_generate_returns_complete_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read()
        assert b'"stream":false' in body
        assert b'"model":"llama3.1:latest"' in body
        return httpx.Response(
            200,
            json={
                "model": "llama3.1:latest",
                "response": "Hello, world!",
                "done": True,
                "prompt_eval_count": 12,
                "eval_count": 7,
            },
        )

    adapter = make_adapter(handler)
    response = adapter.generate("hi", model="llama3.1:latest")
    assert isinstance(response, ModelResponse)
    assert response.text == "Hello, world!"
    assert response.prompt_tokens == 12
    assert response.completion_tokens == 7
    assert response.model == "llama3.1:latest"


def test_generate_includes_system_prompt() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read()
        assert b'"system":"be nice"' in body
        return httpx.Response(200, json={"response": "ok", "done": True})

    adapter = make_adapter(handler)
    adapter.generate("hi", model="llama3.1:latest", system_prompt="be nice")


def test_generate_uses_default_model_when_none_given() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "default-model"}]})
        body = request.read()
        assert b'"model":"default-model"' in body
        return httpx.Response(200, json={"response": "ok", "done": True})

    adapter = make_adapter(handler)
    assert adapter.generate("hi").text == "ok"


def test_generate_raises_when_no_models_installed() -> None:
    adapter = make_adapter(lambda request: httpx.Response(200, json={"models": []}))
    with pytest.raises(ModelNotFoundError, match="ollama pull"):
        adapter.generate("hi")


def test_stream_yields_chunks_from_ndjson() -> None:
    ndjson = (
        '{"model":"m","response":"Hello","done":false}\n'
        '{"model":"m","response":" world","done":false}\n'
        '{"model":"m","response":"!","done":true}\n'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"stream":true' in request.read()
        return httpx.Response(200, text=ndjson)

    adapter = make_adapter(handler)
    assert list(adapter.stream("hi", model="m")) == ["Hello", " world", "!"]


def test_connection_error_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    adapter = make_adapter(handler)
    with pytest.raises(ModelConnectionError, match="ollama serve"):
        adapter.list_models()


def test_missing_model_is_reported() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="model not found")

    adapter = make_adapter(handler)
    with pytest.raises(ModelNotFoundError, match="ollama list"):
        adapter.generate("hi", model="ghost")


def test_server_error_is_reported() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    adapter = make_adapter(handler)
    with pytest.raises(ModelError, match="500"):
        adapter.generate("hi", model="m")
