"""Tests for the ModelManager fallback logic.

TDD seam: the manager wraps two adapters and routes requests, falling back
from the primary to the fallback provider on failure. Logging of fallback
events is also verified.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

import pytest

from boskoll_cli.models import ModelAdapter, ModelManager, ModelManagerError
from boskoll_cli.models.ollama import OllamaAdapter, OllamaError
from boskoll_cli.models.openrouter import OpenRouterAdapter, OpenRouterError

# ── Shared fakes ───────────────────────────────────────────────────────────────


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
    calls: list[tuple[str, str, Any]] = field(default_factory=list)

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> FakeResponse:
        self.calls.append((method, path, body))
        return self.responses[(method, path)]


@dataclass
class RaisingTransport:
    """Transport that always raises, simulating a down provider."""

    error: Exception

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> Any:  # pragma: no cover - never returns
        raise self.error


def _ollama_adapter(transport: FakeTransport, model: str = "llama3.1") -> OllamaAdapter:
    return OllamaAdapter(model=model, transport=transport)


def _openrouter_adapter(
    transport: FakeTransport, model: str = "openai/gpt-4o"
) -> OpenRouterAdapter:
    return OpenRouterAdapter(api_key="test-key", model=model, transport=transport)


# ── Seam: ModelManager satisfies ModelAdapter contract ────────────────────────


class TestModelManagerConformance:
    """ModelManager is a ModelAdapter and implements every contract method."""

    def test_is_model_adapter(self) -> None:
        primary = _ollama_adapter(FakeTransport())
        fallback = _openrouter_adapter(FakeTransport())
        manager = ModelManager(primary=primary, fallback=fallback)
        assert isinstance(manager, ModelAdapter)

    def test_list_models_returns_strings(self) -> None:
        primary_transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(
                    status=200,
                    body=json.dumps({"models": [{"name": "llama3.1:latest"}]}).encode(),
                )
            }
        )
        fallback_transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=200,
                    body=json.dumps({"data": [{"id": "openai/gpt-4o"}]}).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=_ollama_adapter(primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        result = manager.list_models()
        assert result == ["llama3.1:latest"]

    def test_generate_returns_string(self) -> None:
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"response": "hello"}).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=_ollama_adapter(primary_transport),
            fallback=_openrouter_adapter(FakeTransport()),
        )
        assert manager.generate("hi") == "hello"

    def test_stream_yields_strings(self) -> None:
        lines = "".join(
            json.dumps({"response": "chunk-0", "done": False}) + "\n"
            for _ in range(1)
        )
        lines += json.dumps({"done": True}) + "\n"
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(status=200, body=lines.encode())
            }
        )
        manager = ModelManager(
            primary=_ollama_adapter(primary_transport),
            fallback=_openrouter_adapter(FakeTransport()),
        )
        assert list(manager.stream("hi")) == ["chunk-0"]


# ── Seam: generate fallback ────────────────────────────────────────────────────


class TestGenerateFallback:
    """generate tries primary first, then falls back on failure."""

    def test_uses_primary_when_it_succeeds(self) -> None:
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"response": "from ollama"}).encode(),
                )
            }
        )
        fallback_transport = FakeTransport()
        manager = ModelManager(
            primary=_ollama_adapter(primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        assert manager.generate("hi") == "from ollama"
        assert len(fallback_transport.calls) == 0

    def test_falls_back_when_primary_raises(self) -> None:
        primary_transport = RaisingTransport(OllamaError("connection refused"))
        fallback_transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200,
                    body=json.dumps(
                        {"choices": [{"message": {"content": "from openrouter"}}]}
                    ).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        assert manager.generate("hi") == "from openrouter"

    def test_raises_model_manager_error_when_both_fail(self) -> None:
        primary_transport = RaisingTransport(OllamaError("ollama down"))
        fallback_transport = RaisingTransport(OpenRouterError("openrouter down"))
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=OpenRouterAdapter(
                api_key="test-key", model="openai/gpt-4o", transport=fallback_transport
            ),
        )
        with pytest.raises(ModelManagerError, match="Both providers failed generate"):
            manager.generate("hi")

    def test_fallback_logs_warning_and_returns_result(self) -> None:
        primary_transport = RaisingTransport(OllamaError("ollama down"))
        fallback_transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200,
                    body=json.dumps(
                        {"choices": [{"message": {"content": "fallback"}}]}
                    ).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        assert manager.generate("hi") == "fallback"


# ── Seam: stream fallback ──────────────────────────────────────────────────────


class TestStreamFallback:
    """stream tries primary first, falls back if no output is produced."""

    def test_yields_from_primary_when_it_succeeds(self) -> None:
        body = (
            "data: "
            + json.dumps({"choices": [{"delta": {"content": "hello "}}]})
            + "\n"
            + "data: [DONE]\n"
        ).encode()
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=body
                )
            }
        )
        fallback_transport = FakeTransport()
        manager = ModelManager(
            primary=_openrouter_adapter(primary_transport),
            fallback=_ollama_adapter(fallback_transport),
        )
        assert list(manager.stream("hi")) == ["hello "]
        assert len(fallback_transport.calls) == 0

    def test_falls_back_when_primary_fails_before_chunks(self) -> None:
        primary_transport = RaisingTransport(OllamaError("connection refused"))
        fallback_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"response": "fallback chunk", "done": True}).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=_ollama_adapter(fallback_transport),
        )
        assert list(manager.stream("hi")) == ["fallback chunk"]

    def test_propagates_exception_when_primary_fails_mid_stream(self) -> None:
        body = (
            "data: "
            + json.dumps({"choices": [{"delta": {"content": "partial"}}]})
            + "\n"
            + "data: "
            + json.dumps({"error": "stream broken"})
            + "\n"
        ).encode()
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200, body=body
                )
            }
        )
        fallback_transport = FakeTransport()
        manager = ModelManager(
            primary=_openrouter_adapter(primary_transport),
            fallback=_ollama_adapter(fallback_transport),
        )
        with pytest.raises(OpenRouterError, match="stream broken"):
            list(manager.stream("hi"))

    def test_returns_empty_when_primary_completes_without_chunks(self) -> None:
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"done": True}).encode(),
                )
            }
        )
        fallback_transport = FakeTransport()
        manager = ModelManager(
            primary=_ollama_adapter(primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        assert list(manager.stream("hi")) == []


# ── Seam: list_models fallback ────────────────────────────────────────────────


class TestListModelsFallback:
    """list_models tries primary first, then falls back on failure."""

    def test_uses_primary_when_it_succeeds(self) -> None:
        primary_transport = FakeTransport(
            responses={
                ("GET", "/api/tags"): FakeResponse(
                    status=200,
                    body=json.dumps({"models": [{"name": "llama3.1"}]}).encode(),
                )
            }
        )
        fallback_transport = FakeTransport()
        manager = ModelManager(
            primary=_ollama_adapter(primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        assert manager.list_models() == ["llama3.1"]

    def test_falls_back_when_primary_raises(self) -> None:
        primary_transport = RaisingTransport(OllamaError("connection refused"))
        fallback_transport = FakeTransport(
            responses={
                ("GET", "/api/v1/models"): FakeResponse(
                    status=200,
                    body=json.dumps({"data": [{"id": "gpt-4o"}]}).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        assert manager.list_models() == ["gpt-4o"]

    def test_raises_when_both_fail(self) -> None:
        primary_transport = RaisingTransport(OllamaError("ollama down"))
        fallback_transport = RaisingTransport(OpenRouterError("openrouter down"))
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=OpenRouterAdapter(
                api_key="test-key", model="openai/gpt-4o", transport=fallback_transport
            ),
        )
        with pytest.raises(ModelManagerError, match="Both providers failed list_models"):
            manager.list_models()


# ── Seam: model override ──────────────────────────────────────────────────────


class TestModelOverride:
    """Forced model is applied to both adapters."""

    def test_override_sets_model_on_both_adapters(self) -> None:
        primary = _ollama_adapter(FakeTransport(), model="llama3.1")
        fallback = _openrouter_adapter(FakeTransport(), model="openai/gpt-4o")
        ModelManager(primary=primary, fallback=fallback, model="mistral")
        assert primary.model == "mistral"
        assert fallback.model == "mistral"

    def test_none_override_preserves_adapter_models(self) -> None:
        primary = _ollama_adapter(FakeTransport(), model="llama3.1")
        fallback = _openrouter_adapter(FakeTransport(), model="openai/gpt-4o")
        ModelManager(primary=primary, fallback=fallback, model=None)
        assert primary.model == "llama3.1"
        assert fallback.model == "openai/gpt-4o"

    def test_override_used_in_generate(self) -> None:
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"response": "ok"}).encode(),
                )
            }
        )
        primary = OllamaAdapter(model="old-model", transport=primary_transport)
        fallback = _openrouter_adapter(FakeTransport(), model="openai/gpt-4o")
        manager = ModelManager(primary=primary, fallback=fallback, model="new-model")
        manager.generate("hi")
        assert primary_transport.calls[0][2]["model"] == "new-model"


# ── Seam: fallback logging ────────────────────────────────────────────────────


class TestFallbackLogging:
    """Fallback events are logged as warnings."""

    def test_generate_fallback_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        primary_transport = RaisingTransport(OllamaError("connection refused"))
        fallback_transport = FakeTransport(
            responses={
                ("POST", "/api/v1/chat/completions"): FakeResponse(
                    status=200,
                    body=json.dumps(
                        {"choices": [{"message": {"content": "fallback"}}]}
                    ).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=_openrouter_adapter(fallback_transport),
        )
        with caplog.at_level(logging.WARNING, logger="boskoll_cli.models.manager"):
            result = manager.generate("hi")
        assert result == "fallback"
        assert "Primary provider generate failed" in caplog.text
        assert "Falling back" in caplog.text

    def test_stream_fallback_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        primary_transport = RaisingTransport(OllamaError("connection refused"))
        fallback_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"response": "chunk", "done": True}).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
            fallback=_ollama_adapter(fallback_transport),
        )
        with caplog.at_level(logging.WARNING, logger="boskoll_cli.models.manager"):
            result = list(manager.stream("hi"))
        assert result == ["chunk"]
        assert "Primary provider stream failed" in caplog.text
        assert "Falling back" in caplog.text

    def test_no_log_when_primary_succeeds(self, caplog: pytest.LogCaptureFixture) -> None:
        primary_transport = FakeTransport(
            responses={
                ("POST", "/api/generate"): FakeResponse(
                    status=200,
                    body=json.dumps({"response": "ok"}).encode(),
                )
            }
        )
        manager = ModelManager(
            primary=_ollama_adapter(primary_transport),
            fallback=_openrouter_adapter(FakeTransport()),
        )
        with caplog.at_level(logging.WARNING, logger="boskoll_cli.models.manager"):
            manager.generate("hi")
        assert caplog.text == ""
