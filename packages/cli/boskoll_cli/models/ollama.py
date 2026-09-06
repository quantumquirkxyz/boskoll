"""Ollama adapter for local model integration.

Implements :class:`ModelAdapter` against a local Ollama instance (default
``http://127.0.0.1:11434``), speaking its REST API directly:

* ``GET /api/tags`` lists the locally pulled models.
* ``POST /api/generate`` produces completions, with ``stream`` toggling
  non-streaming (single JSON document) versus streaming (newline-delimited JSON).

No third-party dependencies are introduced: HTTP is performed with the standard
library :mod:`urllib`. The HTTP transport is injectable so the adapter can be
exercised offline against a fake transport in tests.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib import request

from boskoll_cli.models.base import ModelAdapter


class OllamaError(Exception):
    """Raised when the local Ollama instance is unreachable or misbehaves."""


class _Response(Protocol):
    """Minimal view of an HTTP response consumed by the adapter."""

    status: int

    def read(self) -> bytes:
        ...

    def __iter__(self) -> Iterator[bytes]:
        ...


class _Transport(Protocol):
    """Pluggable HTTP transport so the adapter is testable without a live server."""

    def request(
        self, method: str, path: str, *, body: Mapping[str, Any] | None = None
    ) -> _Response:
        ...


class _UrllibTransport:
    """Default transport backed by :mod:`urllib` for a local Ollama instance.

    Connection failures surface as ``OSError`` subclasses (e.g. ``URLError``);
    the adapter wraps those in :class:`OllamaError` so callers never see a raw
    transport exception.
    """

    def __init__(self, base_url: str, timeout: float) -> None:
        self._base_url = base_url
        self._timeout = timeout

    def request(
        self, method: str, path: str, *, body: Mapping[str, Any] | None = None
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
class OllamaAdapter(ModelAdapter):
    """Model provider adapter backed by a local Ollama instance.

    Parameters
    ----------
    model:
        The model identifier to generate with, e.g. ``"llama3.1"`` or
        ``"llama3.1:latest"``. When ``None`` the payload omits ``model`` and
        Ollama applies its default.
    base_url:
        Root URL of the local Ollama HTTP API.
    timeout:
        Per-request socket timeout in seconds.
    transport:
        Optional injectable transport, primarily for testing.
    """

    DEFAULT_BASE_URL = "http://127.0.0.1:11434"
    """Default address of a local Ollama instance."""

    DEFAULT_TIMEOUT = 5.0
    """Default per-request timeout in seconds."""

    model: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    transport: _Transport | None = None

    def __post_init__(self) -> None:
        if self.transport is None:
            self.transport = _UrllibTransport(
                self.base_url.rstrip("/"), self.timeout
            )

    def list_models(self) -> list[str]:
        """List the models available from the local Ollama instance.

        Calls ``GET /api/tags`` and returns each model's ``name`` (e.g.
        ``"llama3.1:latest"``).
        """
        payload = self._request_json("GET", "/api/tags")
        return [model["name"] for model in payload.get("models", []) if "name" in model]

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate a complete response for ``prompt`` and return it."""
        body = self._build_body(prompt, system, stream=False)
        payload = self._request_json("POST", "/api/generate", body=body)
        return str(payload.get("response", ""))

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        """Stream response chunks for ``prompt`` as they are generated."""
        body = self._build_body(prompt, system, stream=True)
        response = self._do_request("POST", "/api/generate", body=body)
        if response.status >= 400:
            raise OllamaError(f"HTTP {response.status}")
        for line in response:
            text = line.strip()
            if not text:
                continue
            payload = self._parse_json_line(text)
            api_error = self._api_error(payload)
            if api_error:
                raise OllamaError(api_error)
            chunk = payload.get("response", "")
            if chunk:
                yield str(chunk)
            if payload.get("done"):
                break

    def _do_request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> _Response:
        """Issue a request through the transport, wrapping connection failures."""
        try:
            return self._require_transport().request(method, path, body=body)
        except OSError as exc:
            raise OllamaError(
                f"Unable to connect to Ollama at {self.base_url}: {exc}"
            ) from exc

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Issue a request and return its parsed JSON body as a mapping.

        Raises :class:`OllamaError` for connection failures, non-2xx statuses,
        malformed JSON, or an Ollama-level ``error`` field.
        """
        response = self._do_request(method, path, body=body)
        payload = self._parse_json(response)
        api_error = self._api_error(payload)
        if api_error:
            raise OllamaError(api_error)
        if response.status >= 400:
            raise OllamaError(f"HTTP {response.status}")
        return payload

    def _build_body(
        self, prompt: str, system: str | None, *, stream: bool
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"prompt": prompt, "stream": stream}
        if self.model is not None:
            body["model"] = self.model
        if system is not None:
            body["system"] = system
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
            raise OllamaError(f"Invalid response from Ollama: {exc}") from exc
        if not isinstance(parsed, dict):
            raise OllamaError(
                f"Unexpected response from Ollama: {parsed!r}"
            )
        return parsed

    @staticmethod
    def _parse_json_line(line: bytes) -> dict[str, Any]:
        try:
            parsed = json.loads(line)
        except (ValueError, UnicodeDecodeError) as exc:
            raise OllamaError(f"Invalid JSON streamed from Ollama: {exc}") from exc
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _api_error(payload: Mapping[str, Any]) -> str | None:
        """Return the Ollama-level ``error`` field when present and truthy."""
        error = payload.get("error")
        if error:
            return str(error)
        return None
