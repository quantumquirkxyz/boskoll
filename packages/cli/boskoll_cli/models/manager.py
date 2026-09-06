"""Model manager with automatic fallback from local to cloud.

The :class:`ModelManager` sits between the CLI and the model adapters. In
automatic mode it tries the local adapter (Ollama) first and falls back to
the cloud adapter (OpenRouter) when the local backend fails. Passing an
explicit ``model`` argument forces that model: ``ollama/<name>`` routes to
the local adapter and any other id routes to the cloud adapter, with no
fallback — the user asked for that model specifically.

Every request's token usage and estimated cost are recorded on
:attr:`ModelManager.usage` (a :class:`SessionUsage`).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from boskoll_cli.models.base import ModelAdapter, ModelError, ModelInfo, ModelResponse
from boskoll_cli.models.tokens import SessionUsage, count_tokens

_OLLAMA_PREFIX = "ollama/"
_OPENROUTER_PREFIX = "openrouter/"


def split_model_ref(ref: str) -> tuple[str | None, str]:
    """Split a ``provider/name`` model reference into its parts.

    Returns ``(provider, name)`` where provider is ``"ollama"``,
    ``"openrouter"``, or ``None`` when the reference has no known prefix
    (such refs are treated as cloud model ids).
    """
    if ref.startswith(_OLLAMA_PREFIX):
        return "ollama", ref[len(_OLLAMA_PREFIX) :]
    if ref.startswith(_OPENROUTER_PREFIX):
        return "openrouter", ref[len(_OPENROUTER_PREFIX) :]
    return None, ref


class ModelManager:
    """Routes model requests across backends with automatic fallback."""

    def __init__(
        self,
        local_adapter: ModelAdapter,
        cloud_adapter: ModelAdapter | None = None,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._local = local_adapter
        self._cloud = cloud_adapter
        self._logger = logger or logging.getLogger("boskoll_cli.models")
        self.usage = SessionUsage()

    def _resolve_adapter(self, model: str | None) -> tuple[ModelAdapter, str | None]:
        """Return the (adapter, model name) pair for a request.

        ``model=None`` means automatic mode: prefer the local adapter.
        Otherwise the provider prefix in ``model`` decides the adapter and
        the request is pinned to it (no fallback).
        """
        if model is None:
            return self._local, None
        provider, name = split_model_ref(model)
        if provider == "ollama":
            return self._local, name
        if self._cloud is None:
            raise ModelError(
                f"Model {model!r} needs OpenRouter, which is not configured. "
                "Set OPENROUTER_API_KEY or use an 'ollama/' model id."
            )
        return self._cloud, name

    def _log_fallback(self, adapter: ModelAdapter, error: ModelError) -> None:
        cloud_name = self._cloud.provider if self._cloud is not None else "none"
        self._logger.warning(
            "Model backend %s failed (%s); falling back to %s",
            adapter.provider,
            error,
            cloud_name,
        )

    def list_models(self) -> list[ModelInfo]:
        """List models from every configured backend.

        A backend that is unreachable or misconfigured is skipped with a
        warning rather than failing the whole listing.
        """
        models: list[ModelInfo] = []
        for adapter in (self._local, self._cloud):
            if adapter is None:
                continue
            try:
                models.extend(adapter.list_models())
            except ModelError as error:
                self._logger.warning(
                    "Could not list models from %s: %s", adapter.provider, error
                )
        return models

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Generate a complete response, falling back local → cloud."""
        adapter, model_name = self._resolve_adapter(model)
        response = self._generate_once(adapter, prompt, model_name, system_prompt)
        self.usage.record(
            self._usage_model_id(adapter, model_name),
            response.prompt_tokens,
            response.completion_tokens,
        )
        return response

    def _generate_once(
        self,
        adapter: ModelAdapter,
        prompt: str,
        model_name: str | None,
        system_prompt: str | None,
    ) -> ModelResponse:
        if self._cloud is None or adapter is self._cloud or model_name is not None:
            return adapter.generate(prompt, model=model_name, system_prompt=system_prompt)
        try:
            return self._local.generate(prompt, system_prompt=system_prompt)
        except ModelError as error:
            self._log_fallback(self._local, error)
            return self._cloud.generate(prompt, system_prompt=system_prompt)

    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Yield response chunks, falling back local → cloud before the first chunk.

        Fallback only applies in automatic mode (``model=None``) and only
        before any chunk has been delivered; once a chunk is yielded the
        stream is committed to that backend.
        """
        adapter, model_name = self._resolve_adapter(model)
        fallback_allowed = model is None and self._cloud is not None
        chunks = adapter.stream(prompt, model=model_name, system_prompt=system_prompt)
        try:
            first = next(chunks)
        except ModelError as error:
            if not fallback_allowed:
                raise
            assert self._cloud is not None  # fallback_allowed implies a cloud adapter
            self._log_fallback(adapter, error)
            adapter = self._cloud
            model_name = None
            chunks = adapter.stream(prompt, system_prompt=system_prompt)
            first = next(chunks)

        parts = [first]
        yield first
        for chunk in chunks:
            parts.append(chunk)
            yield chunk

        self.usage.record(
            self._usage_model_id(adapter, model_name),
            count_tokens(prompt),
            count_tokens("".join(parts)),
        )

    @staticmethod
    def _usage_model_id(adapter: ModelAdapter, model_name: str | None) -> str:
        """Model id used for pricing lookups (provider-prefixed)."""
        return f"{adapter.provider}/{model_name or ''}"
