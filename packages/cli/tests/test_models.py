"""Tests for the :class:`ModelAdapter` abstract base class contract.

TDD seam: the adapter interface every model provider (Ollama, OpenRouter)
must implement. A stub adapter exercises the contract without touching a
real provider.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from boskoll_cli.models import ModelAdapter


class StubAdapter(ModelAdapter):
    """Minimal concrete adapter used to exercise the base contract."""

    def __init__(self, models: list[str]) -> None:
        self._models = models

    def list_models(self) -> list[str]:
        return list(self._models)

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        if system:
            return f"{system}: {prompt}"
        return prompt

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        for i in range(2):
            yield f"{prompt}-{i}"


class MissingGenerate(ModelAdapter):
    """Subclass that never implements ``generate``."""

    def list_models(self) -> list[str]:
        return []

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        yield prompt


class MissingListModels(ModelAdapter):
    """Subclass that never implements ``list_models``."""

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        return prompt

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        yield prompt


class MissingStream(ModelAdapter):
    """Subclass that never implements ``stream``."""

    def list_models(self) -> list[str]:
        return []

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        return prompt


# ── Seam: ABC abstractness ────────────────────────────────────────────────────


class TestModelAdapterAbstractness:
    """ModelAdapter cannot be instantiated and enforces all three methods."""

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            ModelAdapter()  # type: ignore[abstract]

    def test_missing_generate_prevents_instantiation(self) -> None:
        with pytest.raises(TypeError):
            MissingGenerate()  # type: ignore[abstract]

    def test_missing_list_models_prevents_instantiation(self) -> None:
        with pytest.raises(TypeError):
            MissingListModels()  # type: ignore[abstract]

    def test_missing_stream_prevents_instantiation(self) -> None:
        with pytest.raises(TypeError):
            MissingStream()  # type: ignore[abstract]

    def test_concrete_subclass_is_instantiable(self) -> None:
        adapter = StubAdapter(["llama3.1"])
        assert isinstance(adapter, ModelAdapter)

    def test_contract_methods_are_documented(self) -> None:
        assert ModelAdapter.list_models.__doc__
        assert ModelAdapter.generate.__doc__
        assert ModelAdapter.stream.__doc__


# ── Seam: adapter contract behavior ──────────────────────────────────────────


class TestModelAdapterContract:
    """A concrete adapter satisfies the list/generate/stream contract."""

    @pytest.fixture()
    def adapter(self) -> StubAdapter:
        return StubAdapter(["llama3.1", "mistral"])

    def test_list_models_returns_model_identifiers(self, adapter: StubAdapter) -> None:
        assert adapter.list_models() == ["llama3.1", "mistral"]

    def test_generate_returns_string(self, adapter: StubAdapter) -> None:
        response = adapter.generate("write a test")
        assert isinstance(response, str)
        assert response == "write a test"

    def test_generate_accepts_optional_system_prompt(self, adapter: StubAdapter) -> None:
        response = adapter.generate("write a test", system="be concise")
        assert response == "be concise: write a test"

    def test_stream_yields_string_chunks(self, adapter: StubAdapter) -> None:
        chunks = list(adapter.stream("hello"))
        assert chunks == ["hello-0", "hello-1"]
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_stream_returns_an_iterator(self, adapter: StubAdapter) -> None:
        chunks = adapter.stream("hello")
        assert isinstance(chunks, Iterator)
