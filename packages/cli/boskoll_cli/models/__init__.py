"""Model manager: adapters, fallback routing, and usage tracking.

Public surface::

    ModelManager(local_adapter, cloud_adapter)   # route with fallback
    OllamaAdapter()                              # local backend
    OpenRouterAdapter()                          # cloud backend
"""

from boskoll_cli.models.base import (
    ModelAdapter,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelError,
    ModelInfo,
    ModelNotFoundError,
    ModelRateLimitError,
    ModelResponse,
)
from boskoll_cli.models.manager import ModelManager, split_model_ref
from boskoll_cli.models.ollama import OllamaAdapter
from boskoll_cli.models.openrouter import OpenRouterAdapter
from boskoll_cli.models.tokens import SessionUsage, count_tokens, estimate_cost

__all__ = [
    "ModelAdapter",
    "ModelAuthenticationError",
    "ModelConnectionError",
    "ModelError",
    "ModelInfo",
    "ModelManager",
    "ModelNotFoundError",
    "ModelRateLimitError",
    "ModelResponse",
    "OllamaAdapter",
    "OpenRouterAdapter",
    "SessionUsage",
    "count_tokens",
    "estimate_cost",
    "split_model_ref",
]
