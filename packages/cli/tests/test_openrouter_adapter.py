"""Tests for the OpenRouterAdapter model provider.

TDD seam: a fake transport replaces the HTTP layer so the adapter is exercised
against the real OpenRouter API contract without a live API key or network.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

import pytest

from boskoll_cli.models import ModelAdapter
from boskoll_cli.models.openrouter import OpenRouterAdapter, OpenRouterError


@dataclass
class FakeResponse:
    """A stand-in for an HTTP response usable for both body and line reads."""

    status: int
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)

    def read(self) -> bytes:
        return self.body

    def info(self) -> Mapping[str, str]:
        return self.headers

    def __iter__(self) -> Iterator[bytes]:
        yield from self.body.splitlines()


@dataclass
class FakeTransport:
    """Records calls and returns canned responses keyed by (method, path)."""

    responses: dict[tuple[str, str], FakeResponse] = field(default_factory=dict)
    calls: list[tuple[str, str, Any, dict[str, str] | None]] = field(default_factory=list)

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> FakeResponse:
        self.calls.append(
            (method, path, body, dict(headers) if headers is not None else None)
        )
        return self.responses[(method, path)]


@dataclass
class RaisingTransport:
    """Transport that always raises, simulating a down or unreachable OpenRouter."""

    error: Exception

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:  # pragma: no cover - never returns
        raise self.error


def _adapter(transport: FakeTransport, model: str = "openai/gpt-4o") -> OpenRouterAdapter:
    return OpenRouterAdapter(api_key="test-key", model=model, transport=transport)


# ── Seam: adapter satisfies the ModelAdapter contract ─────────────────────────


class TestOpenRouterAdapterConformance:
    """OpenRouterAdapter is a ModelAdapter and implements every contract method."""

    def test_is_model_adapter(self) -> None:
        transport = FakeTransport()
        assert isinstance(_adapter(transport), ModelAdapter)

    def test_list_models_returns_strings(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=200,
                    body=json.dumps({"data": [{"id": "openai/gpt-4o"}]}).encode(),
                )
            }
        )
        adapter = _adapter(transport)
        result = adapter.list_models()
        assert result == ["openai/gpt-4o"]
        assert all(isinstance(name, str) for name in result)

    def test_generate_returns_string(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200,
                    body=json.dumps({"choices": [{"message": {"content": "hello"}}]}).encode(),
                )
            }
        )
        adapter = _adapter(transport)
        result = adapter.generate("hi")
        assert isinstance(result, str)
        assert result == "hello"

    def test_stream_yields_strings(self) -> None:
        body = (
            "data: " + json.dumps({"choices": [{"delta": {"content": "chunk-0"}}]}) + "\n"
            + "data: [DONE]\n"
        ).encode()
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        chunks = list(adapter.stream("hi"))
        assert chunks == ["chunk-0"]
        assert all(isinstance(c, str) for c in chunks)


# ── Seam: connecting to the OpenRouter API ────────────────────────────────────


class TestOpenRouterConnection:
    """The adapter targets the OpenRouter cloud API by default."""

    def test_default_base_url(self) -> None:
        assert OpenRouterAdapter.DEFAULT_BASE_URL == "https://openrouter.ai/api/v1"

    def test_custom_base_url_is_configurable(self) -> None:
        transport = FakeTransport()
        adapter = OpenRouterAdapter(
            api_key="test-key",
            base_url="https://custom.openrouter.ai/api/v1",
            model="openai/gpt-4o",
            transport=transport,
        )
        assert adapter.base_url == "https://custom.openrouter.ai/api/v1"

    def test_api_key_sent_in_authorization_header(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=200, body=b'{"data": []}'
                )
            }
        )
        adapter = OpenRouterAdapter(
            api_key="my-secret-key",
            model="openai/gpt-4o",
            transport=transport,
        )
        adapter.list_models()
        assert transport.calls[0][3] is not None
        assert transport.calls[0][3]["Authorization"] == "Bearer my-secret-key"


# ── Seam: listing available models ───────────────────────────────────────────


class TestOpenRouterListModels:
    """list_models calls GET /api/v1/models and extracts model ids."""

    def test_returns_model_ids(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=200,
                    body=json.dumps(
                        {
                            "data": [
                                {"id": "openai/gpt-4o", "name": "GPT-4o"},
                                {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
                            ]
                        }
                    ).encode(),
                )
            }
        )
        adapter = _adapter(transport)
        assert adapter.list_models() == ["openai/gpt-4o", "anthropic/claude-3.5-sonnet"]

    def test_returns_empty_when_no_models(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=200, body=b'{"data": []}'
                )
            }
        )
        adapter = _adapter(transport)
        assert adapter.list_models() == []

    def test_tolerates_missing_data_key(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(status=200, body=b"{}")
            }
        )
        adapter = _adapter(transport)
        assert adapter.list_models() == []


# ── Seam: generating completions ─────────────────────────────────────────────


class TestOpenRouterGenerate:
    """generate posts to /api/v1/chat/completions with stream disabled."""

    def _generate_response(self, text: str) -> bytes:
        return json.dumps({"choices": [{"message": {"content": text}}]}).encode()

    def test_returns_response_field(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=self._generate_response("hello world")
                )
            }
        )
        adapter = _adapter(transport)
        assert adapter.generate("greet") == "hello world"

    def test_send_uses_stream_false(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = _adapter(transport)
        adapter.generate("hi")
        sent = transport.calls[0][2]
        assert sent["messages"] == [{"role": "user", "content": "hi"}]
        assert sent["stream"] is False

    def test_includes_model_when_set(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = OpenRouterAdapter(
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet",
            transport=transport,
        )
        adapter.generate("hi")
        assert transport.calls[0][2]["model"] == "anthropic/claude-3.5-sonnet"

    def test_forwards_system_prompt(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = _adapter(transport)
        adapter.generate("hi", system="be concise")
        messages = transport.calls[0][2]["messages"]
        assert messages[0] == {"role": "system", "content": "be concise"}
        assert messages[1] == {"role": "user", "content": "hi"}

    def test_omits_system_when_none(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = _adapter(transport)
        adapter.generate("hi")
        messages = transport.calls[0][2]["messages"]
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "hi"}

    def test_sends_optional_headers(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = _adapter(transport)
        adapter.generate("hi")
        assert transport.calls[0][3] is not None
        assert "HTTP-Referer" in transport.calls[0][3]
        assert "X-Title" in transport.calls[0][3]


# ── Seam: streaming completions ───────────────────────────────────────────────


class TestOpenRouterStream:
    """stream posts to /api/v1/chat/completions with stream enabled and yields chunks."""

    @staticmethod
    def _sse_lines(chunks: list[dict[str, Any]]) -> bytes:
        lines = ""
        for chunk in chunks:
            lines += "data: " + json.dumps(chunk) + "\n"
        lines += "data: [DONE]\n"
        return lines.encode()

    def test_yields_response_chunks_in_order(self) -> None:
        body = self._sse_lines([
            {"choices": [{"delta": {"content": "hello "}}]},
            {"choices": [{"delta": {"content": "world"}}]},
        ])
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert list(adapter.stream("hi")) == ["hello ", "world"]

    def test_stops_at_done(self) -> None:
        body = self._sse_lines([
            {"choices": [{"delta": {"content": "a"}}]},
            {"choices": [{"delta": {}}]},
        ])
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert list(adapter.stream("hi")) == ["a"]

    def test_skips_non_data_lines(self) -> None:
        body = (
            b"\n"
            + b"data: " + json.dumps({"choices": [{"delta": {"content": "x"}}]}).encode() + b"\n"
            + b"\n"
            + b"data: [DONE]\n"
        )
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert list(adapter.stream("hi")) == ["x"]

    def test_send_uses_stream_true(self) -> None:
        body = b"data: [DONE]\n"
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        list(adapter.stream("hi"))
        sent = transport.calls[0][2]
        assert sent["stream"] is True

    def test_stream_returns_iterator(self) -> None:
        body = b"data: [DONE]\n"
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert isinstance(adapter.stream("hi"), Iterator)

    def test_stream_includes_system_when_set(self) -> None:
        body = b"data: [DONE]\n"
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        list(adapter.stream("hi", system="be concise"))
        messages = transport.calls[0][2]["messages"]
        assert messages[0] == {"role": "system", "content": "be concise"}


# ── Seam: error handling and rate limits ──────────────────────────────────────


class TestOpenRouterErrorHandling:
    """Connection and API failures surface as OpenRouterError."""

    def test_connection_refused_wrapped_as_openrouter_error(self) -> None:
        transport = RaisingTransport(OSError("Connection refused"))
        adapter = OpenRouterAdapter(api_key="test-key", model="openai/gpt-4o", transport=transport)
        with pytest.raises(OpenRouterError) as exc_info:
            adapter.list_models()
        assert "openrouter.ai/api/v1" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    def test_http_error_status_wrapped_as_openrouter_error(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=500, body=b'{"error": "internal"}'
                )
            }
        )
        adapter = OpenRouterAdapter(api_key="test-key", model="openai/gpt-4o", transport=transport)
        with pytest.raises(OpenRouterError, match="internal"):
            adapter.list_models()

    def test_api_error_field_in_generate_wrapped(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200,
                    body=json.dumps({"error": "model not found"}).encode(),
                )
            }
        )
        adapter = OpenRouterAdapter(api_key="test-key", model="openai/gpt-4o", transport=transport)
        with pytest.raises(OpenRouterError, match="model not found"):
            adapter.generate("hi")

    def test_api_error_field_with_dict_wrapped(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=429,
                    body=json.dumps(
                        {
                            "error": {
                                "message": "rate limit exceeded",
                                "type": "rate_limit",
                            }
                        }
                    ).encode(),
                )
            }
        )
        adapter = OpenRouterAdapter(
            api_key="test-key",
            model="openai/gpt-4o",
            transport=transport,
        )
        with pytest.raises(OpenRouterError, match="rate limit exceeded"):
            adapter.generate("hi")

    def test_error_during_stream_wrapped_as_openrouter_error(self) -> None:
        body = (
            "data: " + json.dumps({"choices": [{"delta": {"content": "a"}}]}) + "\n"
            + "data: " + json.dumps({"error": "bad request"}) + "\n"
        ).encode()
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=200, body=body)
            }
        )
        adapter = OpenRouterAdapter(api_key="test-key", model="openai/gpt-4o", transport=transport)
        with pytest.raises(OpenRouterError, match="bad request"):
            list(adapter.stream("hi"))

    def test_stream_raises_on_http_error_status(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(status=502, body=b"")
            }
        )
        adapter = OpenRouterAdapter(api_key="test-key", model="openai/gpt-4o", transport=transport)
        with pytest.raises(OpenRouterError, match="HTTP 502"):
            list(adapter.stream("hi"))

    def test_rate_limit_status_wrapped(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=429, body=b'{"error": "rate limit exceeded"}'
                )
            }
        )
        adapter = OpenRouterAdapter(api_key="test-key", model="openai/gpt-4o", transport=transport)
        with pytest.raises(OpenRouterError, match="rate limit exceeded"):
            adapter.list_models()

    def test_error_is_exception_subtype(self) -> None:
        assert issubclass(OpenRouterError, Exception)
