"""Configurable cost model. Prices are deployment configuration, never domain constants."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CostRates:
    """Price per million tokens for one provider/model, in one currency (e.g. EUR)."""

    input_per_million: Decimal
    output_per_million: Decimal
    currency: str = "EUR"

    def __post_init__(self) -> None:
        if self.input_per_million < 0 or self.output_per_million < 0 or not self.currency.strip():
            raise ValueError("cost rates must be non-negative with a currency")


def turn_cost(input_tokens: int, output_tokens: int, rates: CostRates) -> Decimal:
    return (
        Decimal(input_tokens) * rates.input_per_million
        + Decimal(output_tokens) * rates.output_per_million
    ) / Decimal(1_000_000)


def projections(
    *, input_tokens: float, output_tokens: float, rates: CostRates, turns_per_subscriber_month: int
) -> dict[str, str]:
    """Per turn, per 100 turns and per subscriber-month, from average tokens per turn."""

    per_turn = turn_cost(round(input_tokens), round(output_tokens), rates)
    return {
        "currency": rates.currency,
        "per_turn": f"{per_turn:.6f}",
        "per_100_turns": f"{per_turn * 100:.4f}",
        "per_subscriber_month": f"{per_turn * turns_per_subscriber_month:.4f}",
    }


def avoided_cost(tokens_avoided: int, rates: CostRates) -> Decimal:
    """What not sending these input tokens saves (e.g. per 1M retrieved tokens avoided)."""
    return Decimal(tokens_avoided) * rates.input_per_million / Decimal(1_000_000)
