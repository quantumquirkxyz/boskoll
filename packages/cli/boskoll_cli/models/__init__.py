"""Model provider abstractions for the boskoll model manager."""

from boskoll_cli.models.base import ModelAdapter
from boskoll_cli.models.ollama import OllamaAdapter, OllamaError
from boskoll_cli.models.openrouter import OpenRouterAdapter, OpenRouterError

__all__ = ["ModelAdapter", "OllamaAdapter", "OllamaError", "OpenRouterAdapter", "OpenRouterError"]
