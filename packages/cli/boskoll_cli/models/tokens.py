"""Token counting and cost estimation for model usage.

Token counts are approximate: without a model-specific tokenizer we fall
back to the common rule of thumb of ~4 characters per token. Costs are
estimated from a static pricing table (USD per 1M tokens); prices change,
so treat them as estimates until a live pricing endpoint is queried.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

_CHARS_PER_TOKEN = 4

# Model prices in USD per 1,000,000 tokens, as (input, output) pairs.
# Keys are matched against the start of the model id.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "ollama/": (0.0, 0.0),
    "openrouter/openai/gpt-4o": (2.50, 10.00),
    "openrouter/openai/gpt-4o-mini": (0.15, 0.60),
    "openrouter/anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "openrouter/meta-llama/llama-3.1-8b": (0.05, 0.05),
}

# Fallback pricing for cloud models not in the table.
DEFAULT_CLOUD_PRICING: tuple[float, float] = (0.20, 0.60)


def count_tokens(text: str) -> int:
    """Approximate the number of tokens in ``text``.

    Uses the ~4 characters per token heuristic; always counts at least one
    token so every recorded request has a non-zero cost basis.
    """
    return max(1, round(len(text) / _CHARS_PER_TOKEN))


def _pricing_for(model: str) -> tuple[float, float]:
    """Return the (input, output) USD-per-1M pricing for ``model``.

    Longest prefix wins so ``openrouter/openai/gpt-4o-mini`` matches its own
    entry rather than the ``gpt-4o`` entry.
    """
    for prefix, pricing in sorted(
        MODEL_PRICING.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if model.startswith(prefix):
            return pricing
    if model.startswith("ollama"):
        return MODEL_PRICING["ollama/"]
    return DEFAULT_CLOUD_PRICING


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> Decimal:
    """Estimate the USD cost of a request against ``model``.

    Parameters
    ----------
    model:
        Model id as reported by the adapter (may carry a provider prefix).
    prompt_tokens:
        Tokens in the request.
    completion_tokens:
        Tokens in the response.
    """
    input_price, output_price = _pricing_for(model)
    return (
        Decimal(prompt_tokens) / Decimal(1_000_000) * Decimal(str(input_price))
        + Decimal(completion_tokens) / Decimal(1_000_000) * Decimal(str(output_price))
    )


@dataclass
class SessionUsage:
    """Running token and cost totals for a chat session."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: Decimal = field(default_factory=Decimal)
    requests: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed across all recorded requests."""
        return self.prompt_tokens + self.completion_tokens

    def record(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Add one request's usage to the session totals."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.cost += estimate_cost(model, prompt_tokens, completion_tokens)
        self.requests += 1

    def summary(self) -> str:
        """Human-readable one-line usage summary."""
        return (
            f"{self.requests} request(s), {self.prompt_tokens} prompt + "
            f"{self.completion_tokens} completion tokens "
            f"(${self.cost:.6f})"
        )
