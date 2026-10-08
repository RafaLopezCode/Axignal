"""Cost and budget for semantic judgments: measured usage, versioned prices.

Prices are policy data with their source and review date. A price that is not
published in the repository stays ``None`` (UNKNOWN): the ledger then reports the
call and its tokens but never invents a cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from application.semantic_layer.contracts import BatchResult


@dataclass(frozen=True, slots=True)
class PricePolicy:
    policy_id: str
    evaluator: str
    model: str
    usd_per_million_input: Decimal | None
    usd_per_million_output: Decimal | None
    source: str
    reviewed_on: str

    def cost(self, input_tokens: int | None, output_tokens: int | None) -> Decimal | None:
        if self.usd_per_million_input is None or input_tokens is None:
            return None
        total = Decimal(input_tokens) * self.usd_per_million_input
        if output_tokens:
            if self.usd_per_million_output is None:
                return None
            total += Decimal(output_tokens) * self.usd_per_million_output
        return total / Decimal(1_000_000)


#: TypeSafe Jev 1.13: input tokens only; output tokens are free (official models page).
JEV_1_13_PRICE = PricePolicy(
    policy_id="typesafe-jev-1.13-input-price.v0.2",
    evaluator="typesafe-system-one",
    model="jev-1.13.0",
    usd_per_million_input=Decimal("0.042"),
    usd_per_million_output=Decimal("0"),
    source="https://docs.typesafe.ai/models",
    reviewed_on="2026-10-08",
)

#: Luna's price is not recorded in the repository: cost stays UNKNOWN, calls are counted.
LUNA_PRICE_UNKNOWN = PricePolicy(
    policy_id="luna-price-unrecorded.v0",
    evaluator="luna-responses",
    model="gpt-6-luna",
    usd_per_million_input=None,
    usd_per_million_output=None,
    source="not recorded",
    reviewed_on="2026-10-08",
)


@dataclass(frozen=True, slots=True)
class SemanticBudget:
    """Hard ceilings for one run. Exhausting one abstains (UNKNOWN); it never guesses."""

    max_system_one_input_tokens: int
    max_reasoning_calls: int = 0

    def __post_init__(self) -> None:
        if self.max_system_one_input_tokens < 0 or self.max_reasoning_calls < 0:
            raise ValueError("semantic budgets cannot be negative")


@dataclass(slots=True)
class LedgerLine:
    evaluator: str
    model: str
    calls: int = 0
    questions: int = 0
    input_tokens: int = 0
    unknown_token_calls: int = 0
    usd: Decimal = Decimal(0)
    unknown_cost_calls: int = 0


@dataclass(slots=True)
class CostLedger:
    prices: tuple[PricePolicy, ...] = (JEV_1_13_PRICE, LUNA_PRICE_UNKNOWN)
    lines: dict[tuple[str, str], LedgerLine] = field(default_factory=dict)
    memory_hits: int = 0

    def record(self, result: BatchResult) -> None:
        key = (result.evaluator, result.model)
        line = self.lines.setdefault(key, LedgerLine(result.evaluator, result.model))
        line.calls += 1
        line.questions += len(result.answers)
        if result.usage.input_tokens is None:
            line.unknown_token_calls += 1
        else:
            line.input_tokens += result.usage.input_tokens
        policy = next(
            (p for p in self.prices if (p.evaluator, p.model) == key),
            None,
        )
        cost = (
            None
            if policy is None
            else policy.cost(result.usage.input_tokens, result.usage.output_tokens)
        )
        if cost is None:
            line.unknown_cost_calls += 1
        else:
            line.usd += cost

    def system_one_tokens(self, evaluator: str) -> int:
        return sum(line.input_tokens for line in self.lines.values() if line.evaluator == evaluator)

    def reasoning_calls(self, evaluator: str) -> int:
        return sum(line.calls for line in self.lines.values() if line.evaluator == evaluator)

    def to_wire(self) -> dict[str, object]:
        return {
            "memoryHits": self.memory_hits,
            "lines": [
                {
                    "evaluator": line.evaluator,
                    "model": line.model,
                    "calls": line.calls,
                    "questions": line.questions,
                    "inputTokens": line.input_tokens,
                    "unknownTokenCalls": line.unknown_token_calls,
                    "usd": str(line.usd),
                    "unknownCostCalls": line.unknown_cost_calls,
                }
                for line in self.lines.values()
            ],
        }


def monthly_system_one_usd(
    *,
    batches_per_day: float,
    tokens_per_batch: int,
    reuse_ratio: float,
    price: PricePolicy = JEV_1_13_PRICE,
    days: int = 30,
) -> Decimal | None:
    """Planning estimate, not measurement: batches a day x tokens x (1 - reuse) x price.

    ``reuse_ratio`` is the share of judgments served from shared memory because another
    Focus already met the same world-level state (MASTER §8 demand-materialized reuse).
    """
    if not 0.0 <= reuse_ratio <= 1.0:
        raise ValueError("reuse ratio is a share between 0 and 1")
    tokens = round(batches_per_day * days * tokens_per_batch * (1.0 - reuse_ratio))
    return price.cost(tokens, 0)
