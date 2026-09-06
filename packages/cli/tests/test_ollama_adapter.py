"""Tests for the OllamaAdapter model provider.

TDD seam: a fake transport replaces the HTTP layer so the adapter is exercised
against the real Ollama API contract without a running Ollama instance.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest

from boskoll_cli.models import ModelAdapter
from boskoll_cli.models.ollama import OllamaAdapter, OllamaError


@dataclass
class FakeResponse:
    """A stand-in for an HTTP response usable for both body and line reads."""

    status: int
    body: bytes

    def read(self) -> bytes:
        return self.body

    def __iter__(self) -> Iterator[bytes]:
        yield from self.body.splitlines()


@dataclass
class FakeTransport:
    """Records calls and returns canned responses keyed by (method, path)."""

    responses: dict[tuple[str, str], FakeResponse] = field(default_factory=dict)
    calls: list[tuple[str, str, Any]] = field(default_factory=list)

    def request(
        self, method: str, path: str, *, body: dict[str, Any] | None = None
    ) -> FakeResponse:
        self.calls.append((method, path, body))
        return self.responses[(method, path)]


@dataclass
class RaisingTransport:
    """Transport that always raises, simulating a down or unreachable Ollama."""

    error: Exception

    def request(
        self, method: str, path: str, *, body: dict[str, Any] | None = None
    ) -> Any:  # pragma: no cover - never returns
        raise self.error


def _adapter(transport: FakeTransport, model: str = "llama3.1") -> OllamaAdapter:
    return OllamaAdapter(model=model, transport=transport)


# ── Seam: adapter satisfies the ModelAdapter contract ─────────────────────────


class TestOllamaAdapterConformance:
    """OllamaAdapter is a ModelAdapter and implements every contract method."""

    def test_is_model_adapter(self) -> None:
        transport = FakeTransport()
        assert isinstance(_adapter(transport), ModelAdapter)

    def test_list_models_returns_strings(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(
                    status=200,
                    body=json.dumps({"models": [{"name": "llama3.1:latest"}]}).encode(),
                )
            }
        )
        adapter = _adapter(transport)
        result = adapter.list_models()
        assert result == ["llama3.1:latest"]
        assert all(isinstance(name, str) for name in result)

    def test_generate_returns_string(self) -> None:
        transport = FakeTransport(
            responses={
                (
                    "POST",
                    "/api/generate",
                ): FakeResponse(
                    status=200,
                    body=json.dumps({"response": "hello"}).encode(),
                )
            }
        )
        adapter = _adapter(transport)
        result = adapter.generate("hi")
        assert isinstance(result, str)
        assert result == "hello"

    def test_stream_yields_strings(self) -> None:
        lines = "".join(
            json.dumps({"response": "chunk-0", "done": False}) + "\n"
            for _ in range(1)
        )
        lines += json.dumps({"done": True}) + "\n"
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200, body=lines.encode()
                )
            }
        )
        adapter = _adapter(transport)
        chunks = list(adapter.stream("hi"))
        assert chunks == ["chunk-0"]
        assert all(isinstance(c, str) for c in chunks)


# ── Seam: connecting to the local Ollama instance ───────────────────────────


class TestOllamaConnection:
    """The adapter targets a local Ollama instance by default."""

    def test_default_base_url_targets_localhost(self) -> None:
        assert OllamaAdapter.DEFAULT_BASE_URL == "http://127.0.0.1:11434"

    def test_custom_base_url_is_configurable(self) -> None:
        transport = FakeTransport()
        adapter = OllamaAdapter(
            base_url="http://127.0.0.1:11444",
            model="llama3.1",
            transport=transport,
        )
        assert adapter.base_url == "http://127.0.0.1:11444"

    def test_request_path_is_prefixed_with_base_url(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(
                    status=200, body=b'{"models": []}'
                )
            }
        )
        adapter = OllamaAdapter(
            base_url="http://127.0.0.1:11444",
            model="llama3.1",
            transport=transport,
        )
        adapter.list_models()
        assert transport.calls[0] == ("GET", "/api/tags", None)


# ── Seam: listing available models ───────────────────────────────────────────


class TestOllamaListModels:
    """list_models calls GET /api/tags and extracts model names."""

    def test_returns_model_names(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(
                    status=200,
                    body=json.dumps(
                        {
                            "models": [
                                {"name": "llama3.1:latest", "size": 4145380000},
                                {"name": "mistral:0.3", "size": 730000000},
                            ]
                        }
                    ).encode(),
                )
            }
        )
        adapter = _adapter(transport)
        assert adapter.list_models() == ["llama3.1:latest", "mistral:0.3"]

    def test_returns_empty_when_no_models(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(
                    status=200, body=b'{"models": []}'
                )
            }
        )
        adapter = _adapter(transport)
        assert adapter.list_models() == []

    def test_tolerates_missing_models_key(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(status=200, body=b"{}")
            }
        )
        adapter = _adapter(transport)
        assert adapter.list_models() == []


# ── Seam: generating completions ─────────────────────────────────────────────


class TestOllamaGenerate:
    """generate posts to /api/generate with stream disabled and returns the text."""

    def _generate_response(self, text: str) -> bytes:
        return json.dumps(
            {"model": "llama3.1", "response": text, "done": True}
        ).encode()

    def test_returns_response_field(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200, body=self._generate_response("hello world")
                )
            }
        )
        adapter = _adapter(transport)
        assert adapter.generate("greet") == "hello world"

    def test_send_uses_stream_false(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = _adapter(transport)
        adapter.generate("hi")
        sent = transport.calls[0][2]
        assert sent["prompt"] == "hi"
        assert sent["stream"] is False

    def test_includes_model_when_set(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = OllamaAdapter(model="mistral:0.3", transport=transport)
        adapter.generate("hi")
        assert transport.calls[0][2]["model"] == "mistral:0.3"

    def test_forwards_system_prompt(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = _adapter(transport)
        adapter.generate("hi", system="be concise")
        assert transport.calls[0][2]["system"] == "be concise"

    def test_omits_system_when_none(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200, body=self._generate_response("ok")
                )
            }
        )
        adapter = _adapter(transport)
        adapter.generate("hi")
        assert "system" not in transport.calls[0][2]


# ── Seam: streaming completions ───────────────────────────────────────────────


class TestOllamaStream:
    """stream posts to /api/generate with stream enabled and yields chunks."""

    @staticmethod
    def _ndjson(lines: list[dict[str, Any]]) -> bytes:
        return "".join(json.dumps(line) + "\n" for line in lines).encode()

    def test_yields_response_chunks_in_order(self) -> None:
        body = self._ndjson(
            [
                {"response": "hello ", "done": False},
                {"response": "world", "done": False},
            ]
        )
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert list(adapter.stream("hi")) == ["hello ", "world"]

    def test_stops_at_done_and_returns_no_further_chunks(self) -> None:
        body = self._ndjson(
            [
                {"response": "a", "done": False},
                {"done": True, "eval_count": 2},
            ]
        )
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert list(adapter.stream("hi")) == ["a"]

    def test_skips_blank_lines(self) -> None:
        body = (
            b'\n'
            + json.dumps({"response": "x", "done": False}).encode()
            + b"\n\n"
            + json.dumps({"done": True}).encode()
            + b"\n"
        )
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert list(adapter.stream("hi")) == ["x"]

    def test_send_uses_stream_true(self) -> None:
        body = self._ndjson([{"done": True}])
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        list(adapter.stream("hi"))
        sent = transport.calls[0][2]
        assert sent["prompt"] == "hi"
        assert sent["stream"] is True

    def test_stream_returns_iterator(self) -> None:
        body = self._ndjson([{"done": True}])
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        assert isinstance(adapter.stream("hi"), Iterator)

    def test_stream_includes_system_when_set(self) -> None:
        body = self._ndjson([{"done": True}])
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=body)
            }
        )
        adapter = _adapter(transport)
        list(adapter.stream("hi", system="be concise"))
        assert transport.calls[0][2]["system"] == "be concise"


# ── Seam: connection error handling ───────────────────────────────────────────


class TestOllamaErrorHandling:
    """Connection and API failures surface as OllamaError."""

    def test_connection_refused_wrapped_as_ollama_error(self) -> None:
        transport = RaisingTransport(OSError("Connection refused"))
        adapter = OllamaAdapter(model="llama3.1", transport=transport)
        with pytest.raises(OllamaError) as exc_info:
            adapter.list_models()
        assert "127.0.0.1:11434" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    def test_http_error_status_wrapped_as_ollama_error(self) -> None:
        transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(
                    status=500, body=b'{"error": "internal"}'
                )
            }
        )
        adapter = OllamaAdapter(model="llama3.1", transport=transport)
        with pytest.raises(OllamaError, match="internal"):
            adapter.list_models()

    def test_api_error_field_in_generate_wrapped(self) -> None:
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"error": "model not found"}).encode(),
                )
            }
        )
        adapter = OllamaAdapter(model="llama3.1", transport=transport)
        with pytest.raises(OllamaError, match="model not found"):
            adapter.generate("hi")

    def test_error_during_stream_wrapped_as_ollama_error(self) -> None:
        body = (
            json.dumps({"response": "a", "done": False}) + "\n"
            + json.dumps({"error": "bad request", "done": True}) + "\n"
        ).encode()
        transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=body)
            }
        )
        adapter = OllamaAdapter(model="llama3.1", transport=transport)
        with pytest.raises(OllamaError, match="bad request"):
            list(adapter.stream("hi"))

    def test_error_is_exception_subtype(self) -> None:
        assert issubclass(OllamaError, Exception)
