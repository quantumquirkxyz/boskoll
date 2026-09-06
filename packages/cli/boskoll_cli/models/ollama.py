"""Adapter for the local Ollama model server.

Talks to the Ollama HTTP API (``/api/tags`` and ``/api/generate``). By
default connects to ``http://localhost:11434``; the URL can be overridden
with the ``OLLAMA_HOST`` environment variable.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator

import httpx

from boskoll_cli.models.base import (
    ModelAdapter,
    ModelConnectionError,
    ModelError,
    ModelInfo,
    ModelNotFoundError,
    ModelResponse,
)

DEFAULT_BASE_URL = "http://localhost:11434"
_OLLAMA_HOST_ENV = "OLLAMA_HOST"


class OllamaAdapter(ModelAdapter):
    """Model adapter backed by a local Ollama server."""

    provider = "ollama"

    def __init__(
        self,
        base_url: str | None = None,
        *,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url or os.environ.get(_OLLAMA_HOST_ENV) or DEFAULT_BASE_URL
        self._client = client or httpx.Client(base_url=self.base_url, timeout=timeout)

    def _default_model(self) -> str:
        models = self.list_models()
        if not models:
            raise ModelNotFoundError(
                "Ollama has no models installed. Pull one first, e.g. "
                "`ollama pull llama3.1`."
            )
        return models[0].id

    def _wrap_connection_error(self, error: httpx.HTTPError) -> ModelConnectionError:
        return ModelConnectionError(
            f"Could not reach Ollama at {self.base_url} — is the server "
            f"running? (try `ollama serve`). Original error: {error}"
        )

    def _check_response(self, response: httpx.Response) -> None:
        if response.status_code == 404:
            raise ModelNotFoundError(
                f"Model not found on Ollama ({response.url}). "
                "Check the model name with `ollama list`."
            )
        if response.status_code >= 400:
            raise ModelError(
                f"Ollama request failed with status {response.status_code}: "
                f"{response.text.strip()}"
            )

    def list_models(self) -> list[ModelInfo]:
        """List models installed on the local Ollama server."""
        try:
            response = self._client.get("/api/tags")
        except httpx.HTTPError as error:
            raise self._wrap_connection_error(error) from error
        self._check_response(response)
        payload = response.json()
        return [
            ModelInfo(id=entry["name"], provider=self.provider)
            for entry in payload.get("models", [])
        ]

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Generate a complete response for ``prompt`` (non-streaming)."""
        selected_model = model or self._default_model()
        body: dict[str, object] = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt is not None:
            body["system"] = system_prompt
        try:
            response = self._client.post("/api/generate", json=body)
        except httpx.HTTPError as error:
            raise self._wrap_connection_error(error) from error
        self._check_response(response)
        payload = response.json()
        return ModelResponse(
            text=payload.get("response", ""),
            model=selected_model,
            prompt_tokens=int(payload.get("prompt_eval_count") or 0),
            completion_tokens=int(payload.get("eval_count") or 0),
        )

    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Yield response chunks for ``prompt`` as NDJSON arrives."""
        selected_model = model or self._default_model()
        body: dict[str, object] = {
            "model": selected_model,
            "prompt": prompt,
            "stream": True,
        }
        if system_prompt is not None:
            body["system"] = system_prompt
        try:
            with self._client.stream("POST", "/api/generate", json=body) as response:
                self._check_response(response)
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    yield chunk.get("response", "")
                    if chunk.get("done"):
                        break
        except httpx.HTTPError as error:
            raise self._wrap_connection_error(error) from error
        except ModelError:
            raise
        except ValueError as error:
            raise ModelError(
                f"Ollama returned an unparseable stream response: {error}"
            ) from error
