"""Adapter for the OpenRouter cloud model API.

OpenRouter exposes an OpenAI-compatible ``/chat/completions`` endpoint
plus a model catalogue at ``/models``. Authentication is a bearer token
read from the ``OPENROUTER_API_KEY`` environment variable.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator

import httpx

from boskoll_cli.models.base import (
    ModelAdapter,
    ModelAuthenticationError,
    ModelError,
    ModelInfo,
    ModelNotFoundError,
    ModelRateLimitError,
    ModelResponse,
)

BASE_URL = "https://openrouter.ai/api/v1"
_API_KEY_ENV = "OPENROUTER_API_KEY"
DEFAULT_MODEL = "openrouter/auto"


class OpenRouterAdapter(ModelAdapter):
    """Model adapter backed by the OpenRouter cloud API."""

    provider = "openrouter"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
        default_model: str = DEFAULT_MODEL,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get(_API_KEY_ENV, "")
        self.default_model = default_model
        self._headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        self._client = client or httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            headers=self._headers,
        )

    def _require_key(self) -> None:
        if not self.api_key:
            raise ModelAuthenticationError(
                f"OpenRouter requires an API key. Set the {_API_KEY_ENV} "
                "environment variable (get one at https://openrouter.ai/keys)."
            )

    def _check_response(self, response: httpx.Response) -> None:
        if response.status_code == 401 or response.status_code == 403:
            raise ModelAuthenticationError(
                f"OpenRouter rejected the API key (status {response.status_code}). "
                "Check that OPENROUTER_API_KEY is valid."
            )
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            hint = (
                f" Try again after {retry_after} seconds."
                if retry_after
                else " Slow down or check your OpenRouter rate limits."
            )
            raise ModelRateLimitError(
                f"OpenRouter rate limit exceeded (status 429).{hint}"
            )
        if response.status_code == 404:
            raise ModelNotFoundError(
                f"Model not found on OpenRouter ({response.url}). "
                "Check the model id against https://openrouter.ai/models."
            )
        if response.status_code >= 400:
            message = self._api_error_message(response)
            raise ModelError(
                f"OpenRouter request failed with status {response.status_code}: {message}"
            )

    @staticmethod
    def _api_error_message(response: httpx.Response) -> str:
        """Extract the human-readable message from an OpenAI-style error body."""
        try:
            payload = response.json()
        except ValueError:
            return response.text.strip() or "(empty response)"
        error = payload.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)
        return str(error or payload)

    @staticmethod
    def _messages(prompt: str, system_prompt: str | None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt is not None:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def list_models(self) -> list[ModelInfo]:
        """List models available through the OpenRouter catalogue."""
        self._require_key()
        try:
            response = self._client.get("/models", headers=self._headers)
        except httpx.HTTPError as error:
            raise ModelError(
                f"Could not reach OpenRouter: {error}"
            ) from error
        self._check_response(response)
        payload = response.json()
        return [
            ModelInfo(id=entry["id"], provider=self.provider)
            for entry in payload.get("data", [])
        ]

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Generate a complete response for ``prompt`` (non-streaming)."""
        self._require_key()
        selected_model = model or self.default_model
        body = {
            "model": selected_model,
            "messages": self._messages(prompt, system_prompt),
            "stream": False,
        }
        try:
            response = self._client.post(
                "/chat/completions", json=body, headers=self._headers
            )
        except httpx.HTTPError as error:
            raise ModelError(f"Could not reach OpenRouter: {error}") from error
        self._check_response(response)
        payload = response.json()
        choices = payload.get("choices") or []
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = payload.get("usage") or {}
        return ModelResponse(
            text=content,
            model=selected_model,
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("completion_tokens") or 0),
        )

    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Yield response chunks for ``prompt`` from the SSE stream."""
        self._require_key()
        selected_model = model or self.default_model
        body = {
            "model": selected_model,
            "messages": self._messages(prompt, system_prompt),
            "stream": True,
        }
        try:
            with self._client.stream(
                "POST", "/chat/completions", json=body, headers=self._headers
            ) as response:
                self._check_response(response)
                for line in response.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        event = json.loads(payload)
                    except ValueError as error:
                        raise ModelError(
                            f"OpenRouter returned an unparseable stream event: {error}"
                        ) from error
                    choices = event.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield content
        except httpx.HTTPError as error:
            raise ModelError(f"Could not reach OpenRouter: {error}") from error
        except ModelError:
            raise
