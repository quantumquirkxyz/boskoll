"""Base classes for the boskoll model manager.

Each model provider (Ollama, OpenRouter, ...) is wrapped by an adapter that
implements :class:`ModelAdapter`. The model manager consumes adapters
through this single interface, so providers can be swapped, listed, and
streamed interchangeably without leaking provider-specific details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator


class ModelAdapter(ABC):
    """Interface every model provider adapter must implement.

    Subclasses wrap one provider behind a common contract: enumerate the
    models it exposes, generate a complete response for a prompt, and
    stream response chunks as they are produced.
    """

    model: str | None = None
    """Model identifier override. When ``None`` the provider default applies."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return the identifiers of the models this provider exposes.

        Model identifiers, e.g. ``["llama3.1", "mistral"]``.
        """

    @abstractmethod
    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate a complete response for ``prompt`` and return it.

        When ``system`` is given it frames the response; when omitted the
        provider's default behaviour applies.
        """

    @abstractmethod
    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        """Stream response chunks for ``prompt`` as they are generated.

        When ``system`` is given it frames the response; when omitted the
        provider's default behaviour applies. Yields response text chunks in
        generation order.
        """
