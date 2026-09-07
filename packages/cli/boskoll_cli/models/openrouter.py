"""OpenRouter adapter for cloud model integration.

Implements :class:`ModelAdapter` against the OpenRouter API
(``https://openrouter.ai/api/v1``), speaking its OpenAI-compatible REST API:

* ``GET /api/v1/models`` lists the available models.
* ``POST /api/v1/chat/completions`` produces completions, with ``stream``
  toggling non-streaming versus streaming (SSE) responses.

Authentication is performed via an ``Authorization: Bearer <api_key>`` header.
No third-party dependencies are introduced: HTTP is performed with the standard
library :mod:`urllib`. The HTTP transport is injectable so the adapter can be
exercised offline against a fake transport in tests.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib import request

from boskoll_cli.models.base import ModelAdapter


class OpenRouterError(Exception):
    """Raised when the OpenRouter API is unreachable or returns an error."""


class _Response(Protocol):
    """Minimal view of an HTTP response consumed by the adapter."""

    status: int

    def read(self) -> bytes:
        ...

    def info(self) -> Mapping[str, str]:
        ...

    def __iter__(self) -> Iterator[bytes]:
        ...


class _Transport(Protocol):
    """Pluggable HTTP transport so the adapter is testable without a live server."""

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> _Response:
        ...


class _UrllibTransport:
    """Default transport backed by :mod:`urllib` for the OpenRouter API.

    Connection failures surface as ``OSError`` subclasses (e.g. ``URLError``);
    the adapter wraps those in :class:`OpenRouterError` so callers never see a
    raw transport exception.
    """

    def __init__(self, base_url: str, timeout: float) -> None:
        self._base_url = base_url
        self._timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> _Response:
        url = self._base_url + path
        data: bytes | None = None
        headers: dict[str, str] = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url, data=data, method=method, headers=headers)
        response = request.urlopen(req, timeout=self._timeout)
        return cast("_Response", response)


@dataclass
class OpenRouterAdapter(ModelAdapter):
    """Model provider adapter backed by the OpenRouter cloud API.

    Parameters
    ----------
    api_key:
        OpenRouter API key for authentication.
    model:
        The model identifier to generate with, e.g. ``"openai/gpt-4o"`` or
        ``"anthropic/claude-3.5-sonnet"``. When ``None`` the payload omits
        ``model`` and OpenRouter applies its default.
    base_url:
        Root URL of the OpenRouter HTTP API.
    timeout:
        Per-request socket timeout in seconds.
    transport:
        Optional injectable transport, primarily for testing.
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    """Default base URL of the OpenRouter API."""

    DEFAULT_TIMEOUT = 30.0
    """Default per-request timeout in seconds."""

    DEFAULT_MAX_RETRIES = 3
    """Default maximum retry attempts for rate-limited requests."""

    DEFAULT_RETRY_BACKOFF_BASE = 1.0
    """Default base delay in seconds for exponential backoff."""

    api_key: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_backoff_base: float = DEFAULT_RETRY_BACKOFF_BASE
    model: str | None = None
    transport: _Transport | None = None

    def __post_init__(self) -> None:
        if self.api_key is None:
            raise OpenRouterError("OpenRouter API key is required")
        if self.transport is None:
            self.transport = _UrllibTransport(self.base_url.rstrip("/"), self.timeout)

    def list_models(self) -> list[str]:
        """List the models available from OpenRouter.

        Calls ``GET /api/v1/models`` and returns each model's ``id`` (e.g.
        ``"openai/gpt-4o"``).
        """
        payload = self._request_json(
            "GET", "/api/v1/models", headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return [model["id"] for model in payload.get("data", []) if "id" in model]

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate a complete response for ``prompt`` and return it."""
        body = self._build_body(prompt, system, stream=False)
        payload = self._request_json(
            "POST",
            "/api/v1/chat/completions",
            body=body,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        choices = payload.get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", ""))

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        """Stream response chunks for ``prompt`` as they are generated."""
        body = self._build_body(prompt, system, stream=True)
        response = self._do_request(
            "POST",
            "/api/v1/chat/completions",
            body=body,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if response.status >= 400:
            raise OpenRouterError(f"HTTP {response.status}")
        for line in response:
            text = line.decode("utf-8").strip() if isinstance(line, bytes) else line.strip()
            if not text.startswith("data:"):
                continue
            data = text[5:].strip()
            if data == "[DONE]":
                break
            try:
                payload = json.loads(data)
            except (ValueError, UnicodeDecodeError) as exc:
                raise OpenRouterError(f"Invalid JSON streamed from OpenRouter: {exc}") from exc
            if not isinstance(payload, dict):
                continue
            api_error = self._api_error(payload)
            if api_error:
                raise OpenRouterError(api_error)
            choices = payload.get("choices", [])
            if choices and "delta" in choices[0]:
                delta = choices[0]["delta"]
                if "content" in delta and delta["content"]:
                    yield str(delta["content"])

    def _do_request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> _Response:
        """Issue a request through the transport, wrapping connection failures."""
        try:
            response = self._require_transport().request(method, path, body=body)
        except OSError as exc:
            raise OpenRouterError(
                f"Unable to connect to OpenRouter at {self.base_url}: {exc}"
            ) from exc

        if response.status == 429 and self.max_retries > 0:
            return self._retry_rate_limited(method, path, body=body, response=response)

        return response

        return response

    def _retry_rate_limited(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        response: _Response,
    ) -> _Response:
        """Retry a rate-limited request with exponential backoff."""
        attempt = 0
        while attempt < self.max_retries:
            delay = self.retry_backoff_base * (2 ** attempt)
            time.sleep(delay)
            attempt += 1
            try:
                response = self._require_transport().request(method, path, body=body)
            except OSError as exc:
                raise OpenRouterError(
                    f"Unable to connect to OpenRouter at {self.base_url}: {exc}"
                ) from exc
            if response.status != 429:
                break
        return response

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Issue a request and return its parsed JSON body as a mapping.

        Raises :class:`OpenRouterError` for connection failures, non-2xx statuses,
        malformed JSON, or an OpenRouter-level ``error`` field.
        """
        response = self._do_request(method, path, body=body, headers=headers)
        payload = self._parse_json(response)
        api_error = self._api_error(payload)
        if api_error:
            raise OpenRouterError(api_error)
        if response.status >= 400:
            raise OpenRouterError(f"HTTP {response.status}")
        return payload

    def _build_body(
        self, prompt: str, system: str | None, *, stream: bool
    ) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body: dict[str, Any] = {"messages": messages, "stream": stream}
        if self.model is not None:
            body["model"] = self.model
        return body

    def _require_transport(self) -> _Transport:
        transport = self.transport
        assert transport is not None  # assigned in __post_init__
        return transport

    @staticmethod
    def _parse_json(response: _Response) -> dict[str, Any]:
        try:
            parsed = json.loads(response.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise OpenRouterError(f"Invalid response from OpenRouter: {exc}") from exc
        if not isinstance(parsed, dict):
            raise OpenRouterError(
                f"Unexpected response from OpenRouter: {parsed!r}"
            )
        return parsed

    @staticmethod
    def _api_error(payload: Mapping[str, Any]) -> str | None:
        """Return the OpenRouter-level ``error`` field when present and truthy."""
        error = payload.get("error")
        if error:
            if isinstance(error, dict):
                return str(error.get("message", error))
            return str(error)
        return None
