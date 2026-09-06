"""Tests for token counting and cost estimation — ticket #48."""

from __future__ import annotations

from decimal import Decimal

from boskoll_cli.models.tokens import SessionUsage, count_tokens, estimate_cost


def test_count_tokens_scales_with_length() -> None:
    assert count_tokens("x" * 100) == 25
    assert count_tokens("x" * 200) == 50


def test_count_tokens_counts_at_least_one() -> None:
    assert count_tokens("") == 1
    assert count_tokens("hi") == 1


def test_local_models_are_free() -> None:
    assert estimate_cost("ollama/llama3.1", 1000, 500) == Decimal("0")


def test_cost_uses_model_specific_pricing() -> None:
    # openrouter/openai/gpt-4o: $2.50 per 1M input, $10.00 per 1M output.
    cost = estimate_cost("openrouter/openai/gpt-4o", 1_000_000, 0)
    assert cost == Decimal("2.50")


def test_cost_uses_default_cloud_pricing_for_unknown_models() -> None:
    cost = estimate_cost("openrouter/some/new-model", 1_000_000, 1_000_000)
    assert cost == Decimal("0.20") + Decimal("0.60")


def test_estimate_cost_requires_positive_tokens() -> None:
    assert estimate_cost("ollama/llama3.1", 0, 0) == Decimal("0")


def test_session_usage_tracks_totals() -> None:
    usage = SessionUsage()
    usage.record("ollama/llama3.1", prompt_tokens=10, completion_tokens=20)
    usage.record("ollama/llama3.1", prompt_tokens=5, completion_tokens=5)

    assert usage.requests == 2
    assert usage.prompt_tokens == 15
    assert usage.completion_tokens == 25
    assert usage.total_tokens == 40
    assert usage.cost == Decimal("0")


def test_session_usage_records_cost_for_cloud() -> None:
    usage = SessionUsage()
    usage.record("openrouter/openai/gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=0)
    assert usage.cost == Decimal("0.15")


def test_session_usage_summary_is_readable() -> None:
    usage = SessionUsage()
    usage.record("ollama/llama3.1", prompt_tokens=10, completion_tokens=20)
    summary = usage.summary()
    assert "1 request(s)" in summary
    assert "10 prompt + 20 completion tokens" in summary
    assert "$" in summary
