"""Tests for the ModelManager — tickets #46, #47, #48.

The manager's fallback and routing logic is tested against lightweight
fake adapters so no HTTP or network is involved.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from boskoll_cli.models import (
    ModelAdapter,
    ModelConnectionError,
    ModelError,
    ModelInfo,
    ModelManager,
    ModelResponse,
    split_model_ref,
)


class FakeAdapter(ModelAdapter):
    """Configurable adapter recording every call made against it."""

    def __init__(
        self,
        provider: str,
        *,
        models: list[ModelInfo] | None = None,
        fail_list: bool = False,
        fail_generate: bool = False,
        fail_stream: bool = False,
        stream_chunks: tuple[str, ...] = ("local chunk", "done"),
    ) -> None:
        self.provider = provider
        self._models = models or [ModelInfo(id=f"{provider}-model", provider=provider)]
        self._fail_list = fail_list
        self._fail_generate = fail_generate
        self._fail_stream = fail_stream
        self._stream_chunks = stream_chunks
        self.calls: list[str] = []

    def list_models(self) -> list[ModelInfo]:
        self.calls.append("list")
        if self._fail_list:
            raise ModelConnectionError(f"{self.provider} unreachable")
        return self._models

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        self.calls.append(f"generate:{model}")
        if self._fail_generate:
            raise ModelConnectionError(f"{self.provider} failed")
        return ModelResponse(
            text=f"{self.provider} reply to {prompt}",
            model=model or f"{self.provider}/default",
            prompt_tokens=3,
            completion_tokens=6,
        )

    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        self.calls.append(f"stream:{model}")
        if self._fail_stream:
            raise ModelConnectionError(f"{self.provider} failed")
        yield from self._stream_chunks


@pytest.fixture
def local() -> FakeAdapter:
    return FakeAdapter("ollama")


@pytest.fixture
def cloud() -> FakeAdapter:
    return FakeAdapter("openrouter")


# ── Model reference routing ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("ollama/llama3.1", ("ollama", "llama3.1")),
        ("openrouter/openai/gpt-4o", ("openrouter", "openai/gpt-4o")),
        ("openai/gpt-4o", (None, "openai/gpt-4o")),
    ],
)
def test_split_model_ref(ref: str, expected: tuple[str | None, str]) -> None:
    assert split_model_ref(ref) == expected


# ── Listing ──────────────────────────────────────────────────────────────────


def test_list_models_aggregates_backends(local: FakeAdapter, cloud: FakeAdapter) -> None:
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    models = manager.list_models()
    assert [model.id for model in models] == ["ollama-model", "openrouter-model"]


def test_list_models_tolerates_unreachable_backend(
    local: FakeAdapter, cloud: FakeAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    local._fail_list = True
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    with caplog.at_level(logging.WARNING):
        models = manager.list_models()
    assert [model.id for model in models] == ["openrouter-model"]
    assert any("Could not list models" in record.message for record in caplog.records)


# ── Fallback (automatic mode) ────────────────────────────────────────────────


def test_generate_prefers_local(local: FakeAdapter, cloud: FakeAdapter) -> None:
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    response = manager.generate("hi")
    assert response.text == "ollama reply to hi"
    assert cloud.calls == []


def test_generate_falls_back_to_cloud_on_failure(
    local: FakeAdapter, cloud: FakeAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    local._fail_generate = True
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    with caplog.at_level(logging.WARNING):
        response = manager.generate("hi")
    assert response.text == "openrouter reply to hi"
    assert cloud.calls != []
    assert any("falling back" in record.message for record in caplog.records)


def test_generate_raises_when_all_backends_fail(
    local: FakeAdapter, cloud: FakeAdapter
) -> None:
    local._fail_generate = True
    cloud._fail_generate = True
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    with pytest.raises(ModelError):
        manager.generate("hi")


# ── Forcing a model with --model ─────────────────────────────────────────────


def test_generate_forced_local_model_skips_cloud(
    local: FakeAdapter, cloud: FakeAdapter
) -> None:
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    response = manager.generate("hi", model="ollama/llama3.1")
    assert response.model == "llama3.1"
    assert cloud.calls == []


def test_generate_forced_local_model_does_not_fallback(
    local: FakeAdapter, cloud: FakeAdapter
) -> None:
    local._fail_generate = True
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    with pytest.raises(ModelError):
        manager.generate("hi", model="ollama/llama3.1")
    assert cloud.calls == []


def test_generate_forced_cloud_model_uses_cloud(
    local: FakeAdapter, cloud: FakeAdapter
) -> None:
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    response = manager.generate("hi", model="openai/gpt-4o")
    assert response.model == "openai/gpt-4o"
    assert response.text == "openrouter reply to hi"
    assert local.calls == []


def test_forced_cloud_model_requires_cloud_adapter(local: FakeAdapter) -> None:
    manager = ModelManager(local_adapter=local)
    with pytest.raises(ModelError, match="OPENROUTER_API_KEY"):
        manager.generate("hi", model="openai/gpt-4o")


def test_forced_local_model_works_without_cloud(local: FakeAdapter) -> None:
    manager = ModelManager(local_adapter=local)
    response = manager.generate("hi", model="ollama/llama3.1")
    assert response.text == "ollama reply to hi"


# ── Streaming (ticket #47) ───────────────────────────────────────────────────


def test_stream_yields_local_chunks(local: FakeAdapter, cloud: FakeAdapter) -> None:
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    assert list(manager.stream("hi")) == ["local chunk", "done"]
    assert cloud.calls == []


def test_stream_falls_back_before_first_chunk(
    local: FakeAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    cloud_stream = FakeAdapter(
        "openrouter", stream_chunks=("cloud chunk", "done")
    )
    local._fail_stream = True
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud_stream)
    with caplog.at_level(logging.WARNING):
        chunks = list(manager.stream("hi"))
    assert chunks == ["cloud chunk", "done"]
    assert any("falling back" in record.message for record in caplog.records)


def test_stream_forced_model_does_not_fallback(
    local: FakeAdapter, cloud: FakeAdapter
) -> None:
    local._fail_stream = True
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    with pytest.raises(ModelError):
        list(manager.stream("hi", model="ollama/llama3.1"))
    assert cloud.calls == []


# ── Usage tracking (ticket #48) ──────────────────────────────────────────────


def test_generate_records_usage(local: FakeAdapter, cloud: FakeAdapter) -> None:
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    manager.generate("hi")
    assert manager.usage.requests == 1
    assert manager.usage.prompt_tokens == 3
    assert manager.usage.completion_tokens == 6
    assert manager.usage.cost == 0  # ollama is free


def test_stream_records_usage_with_heuristic_tokens(
    local: FakeAdapter, cloud: FakeAdapter
) -> None:
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    list(manager.stream("a" * 40))
    assert manager.usage.requests == 1
    assert manager.usage.prompt_tokens == 10  # 40 chars / 4
    # "local chunkdone" = 16 chars -> 4 tokens
    assert manager.usage.completion_tokens == 4


def test_fallback_stream_records_cloud_usage(
    local: FakeAdapter, cloud: FakeAdapter
) -> None:
    local._fail_stream = True
    manager = ModelManager(local_adapter=local, cloud_adapter=cloud)
    list(manager.stream("hi"))
    assert manager.usage.requests == 1
    # usage model id is provider-prefixed so cloud pricing applies
    assert manager.usage.cost > 0
