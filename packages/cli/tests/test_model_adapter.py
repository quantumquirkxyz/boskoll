"""Tests for the ModelAdapter abstract base class — ticket #43.

Validates the standard adapter interface: ``list_models()``,
``generate()``, and ``stream()`` must exist on every adapter, and the
shared response/info types behave as documented.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from boskoll_cli.models import (
    ModelAdapter,
    ModelError,
    ModelInfo,
    ModelResponse,
    OllamaAdapter,
    OpenRouterAdapter,
)


class ConcreteAdapter(ModelAdapter):
    """Minimal concrete adapter used to prove the ABC is satisfiable."""

    provider = "test"

    def list_models(self) -> list[ModelInfo]:
        return []

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        return ModelResponse(text="", model=model or "test")

    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        yield from ()


def test_model_adapter_is_abstract() -> None:
    with pytest.raises(TypeError):
        ModelAdapter()  # type: ignore[abstract]


def test_concrete_adapter_satisfies_abc() -> None:
    assert isinstance(ConcreteAdapter(), ModelAdapter)


@pytest.mark.parametrize(
    "adapter",
    [OllamaAdapter(), OpenRouterAdapter()],
)
def test_adapters_expose_provider(adapter: ModelAdapter) -> None:
    assert isinstance(adapter.provider, str)
    assert adapter.provider


def test_model_response_total_tokens() -> None:
    response = ModelResponse(
        text="hello",
        model="ollama/llama3.1",
        prompt_tokens=10,
        completion_tokens=5,
    )
    assert response.total_tokens == 15


def test_model_info_defaults() -> None:
    info = ModelInfo(id="openai/gpt-4o", provider="openrouter")
    assert info.description == ""
    assert info.id == "openai/gpt-4o"


def test_model_error_is_exception() -> None:
    assert issubclass(ModelError, Exception)
