"""Model manager with automatic fallback from local to cloud providers.

The :class:`ModelManager` wraps two :class:`~boskoll_cli.models.base.ModelAdapter`
instances — a primary (typically Ollama) and a fallback (typically OpenRouter) —
and transparently routes requests. When the primary provider fails, the manager
logs the failure and retries against the fallback provider.

A forced ``model`` override is applied to both adapters so the same model
identifier is tried on each provider during fallback.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from boskoll_cli.models.base import ModelAdapter


class ModelManagerError(Exception):
    """Raised when both the primary and fallback providers fail."""


class ModelManager(ModelAdapter):
    """Route model requests through a primary adapter with automatic fallback.

    Parameters
    ----------
    primary:
        The preferred provider (e.g. :class:`~boskoll_cli.models.ollama.OllamaAdapter`).
    fallback:
        The secondary provider used when ``primary`` fails (e.g.
        :class:`~boskoll_cli.models.openrouter.OpenRouterAdapter`).
    model:
        When given, override the ``model`` attribute on both adapters so the
        same model identifier is tried regardless of which provider is active.
    logger:
        Optional logger instance. Defaults to a module-level logger.
    """

    def __init__(
        self,
        primary: ModelAdapter,
        fallback: ModelAdapter,
        model: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._model = model
        if model is not None:
            primary.model = model
            fallback.model = model
        self._logger = logger or logging.getLogger(__name__)

    def list_models(self) -> list[str]:
        """Return models from the primary provider, falling back on failure."""
        try:
            return self._primary.list_models()
        except Exception as exc:
            self._logger.warning(
                "Primary provider list_models failed: %s. Falling back to %s.",
                exc,
                type(self._fallback).__name__,
            )
            try:
                return self._fallback.list_models()
            except Exception as fallback_exc:
                raise ModelManagerError(
                    f"Both providers failed list_models: primary={exc}, fallback={fallback_exc}"
                ) from fallback_exc

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate a response, trying the primary provider first."""
        try:
            return self._primary.generate(prompt, system=system)
        except Exception as exc:
            self._logger.warning(
                "Primary provider generate failed: %s. Falling back to %s.",
                exc,
                type(self._fallback).__name__,
            )
            try:
                return self._fallback.generate(prompt, system=system)
            except Exception as fallback_exc:
                raise ModelManagerError(
                    f"Both providers failed generate: primary={exc}, fallback={fallback_exc}"
                ) from fallback_exc

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        """Stream response chunks, trying the primary provider first.

        If the primary provider fails before producing any output, the manager
        falls back to the secondary provider. If the primary fails mid-stream,
        the partial output is preserved and the exception propagates.
        """
        try:
            iterator = self._primary.stream(prompt, system=system)
            chunk = next(iterator)
        except StopIteration:
            return
        except Exception as exc:
            self._logger.warning(
                "Primary provider stream failed: %s. Falling back to %s.",
                exc,
                type(self._fallback).__name__,
            )
            yield from self._fallback.stream(prompt, system=system)
            return

        yield chunk
        for chunk in iterator:
            yield chunk
