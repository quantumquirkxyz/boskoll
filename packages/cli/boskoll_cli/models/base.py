"""Abstract base class and shared types for model adapters.

Every model backend (Ollama, OpenRouter, ...) implements
:class:`ModelAdapter`, exposing a standard interface for listing models,
generating completions, and streaming responses. The rest of boskoll talks
to the :class:`~boskoll_cli.models.manager.ModelManager`, never to an
adapter directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass


class ModelError(Exception):
    """Base class for errors raised while talking to a model backend."""


class ModelConnectionError(ModelError):
    """The model backend could not be reached."""


class ModelAuthenticationError(ModelError):
    """The model backend rejected the provided credentials."""


class ModelRateLimitError(ModelError):
    """The model backend rate-limited the request."""


class ModelNotFoundError(ModelError):
    """The requested model does not exist on the backend."""


@dataclass(frozen=True)
class ModelInfo:
    """A model exposed by a backend."""

    id: str
    provider: str
    description: str = ""


@dataclass(frozen=True)
class ModelResponse:
    """A complete (non-streaming) model response."""

    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used by the request and response."""
        return self.prompt_tokens + self.completion_tokens


class ModelAdapter(ABC):
    """Standard interface implemented by every model backend.

    Subclasses set :attr:`provider` (e.g. ``"ollama"``) and implement
    :meth:`list_models`, :meth:`generate`, and :meth:`stream`. Adapters
    raise :class:`ModelError` subclasses on failure so the
    :class:`~boskoll_cli.models.manager.ModelManager` can fall back across
    backends.
    """

    provider: str

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """Return the models this backend currently exposes."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Generate a complete response for ``prompt``.

        Parameters
        ----------
        prompt:
            The user's message.
        model:
            Which model to use; ``None`` selects the backend default.
        system_prompt:
            Optional system prompt framing the model's behaviour.
        """

    @abstractmethod
    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Yield response text chunks for ``prompt`` as they arrive."""
