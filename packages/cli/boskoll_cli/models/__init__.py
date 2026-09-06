"""Model provider abstractions for the boskoll model manager."""

from boskoll_cli.models.base import ModelAdapter
from boskoll_cli.models.ollama import OllamaAdapter, OllamaError

__all__ = ["ModelAdapter", "OllamaAdapter", "OllamaError"]
