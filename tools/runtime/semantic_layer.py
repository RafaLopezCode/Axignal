"""Opt-in composition of the semantic layer (spec 062). Off unless fully configured.

``AXIGNAL_SEMANTIC_LAYER_ENABLED=true`` plus a readable absolute TypeSafe key file and
a positive per-run token budget build the demand screen. Reasoning escalation reuses
AXENT's Luna binding (model, key file and operator prices) and is enabled only with a
positive ``AXIGNAL_SEMANTIC_REASONING_CALLS``. Any missing or invalid value returns
``None``: projection stays deterministic, nothing is guessed.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from application.observation_intelligence.semantic_screen import (
    DELIVERY,
    FIT,
    SemanticDemandScreen,
)
from application.semantic_layer.cascade import CascadePolicy, SemanticCascade
from application.semantic_layer.ledger import (
    JEV_1_13_PRICE,
    CostLedger,
    PricePolicy,
    SemanticBudget,
)


def _readable(filename: str) -> Path | None:
    path = Path(filename.strip()) if filename.strip() else None
    if path is None or not path.is_absolute() or not path.is_file() or not os.access(path, os.R_OK):
        return None
    return path


def _positive_int(value: str, default: int) -> int | None:
    try:
        number = int(value) if value.strip() else default
    except ValueError:
        return None
    return number if number >= 0 else None


def _luna_price(values: Mapping[str, str], model: str) -> PricePolicy:
    try:
        input_rate = Decimal(values.get("AXIGNAL_AXENT_INPUT_PER_MILLION", ""))
        output_rate = Decimal(values.get("AXIGNAL_AXENT_OUTPUT_PER_MILLION", ""))
    except (InvalidOperation, ValueError):
        input_rate = output_rate = Decimal("NaN")
    known = input_rate.is_finite() and output_rate.is_finite() and input_rate > 0
    return PricePolicy(
        policy_id="luna-operator-configured-price.v1",
        evaluator="luna-responses",
        model=model,
        usd_per_million_input=input_rate if known else None,
        usd_per_million_output=output_rate if known else None,
        source="operator configuration (AXIGNAL_AXENT_*_PER_MILLION)",
        reviewed_on="configured",
    )


@dataclass(frozen=True, slots=True)
class _Composed:
    judge: Any
    memory: Any
    escalation: Any
    prices: tuple[PricePolicy, ...]
    tokens: int
    reasoning_calls: int


def _compose(
    values: Mapping[str, str], data_dir: Path | None, transport: Any | None
) -> _Composed | None:
    if values.get("AXIGNAL_SEMANTIC_LAYER_ENABLED", "false").lower() != "true" or data_dir is None:
        return None
    key_file = _readable(values.get("AXIGNAL_TYPESAFE_API_KEY_FILE", ""))
    model = values.get("AXIGNAL_TYPESAFE_MODEL", JEV_1_13_PRICE.model).strip()
    tokens = _positive_int(values.get("AXIGNAL_SEMANTIC_RUN_TOKEN_BUDGET", ""), 2_000_000)
    reasoning_calls = _positive_int(values.get("AXIGNAL_SEMANTIC_REASONING_CALLS", ""), 0)
    if key_file is None or not model or not tokens or reasoning_calls is None:
        return None

    from cognition.providers.typesafe_system_one import TypeSafeSystemOneJudge
    from pipeline.semantic_layer.sqlite_memory import SqliteJudgmentMemory

    judge = TypeSafeSystemOneJudge(model=model, key_file=key_file, transport=transport)
    memory = SqliteJudgmentMemory(data_dir / "semantic-judgments.sqlite3")
    escalation = None
    # The published price belongs to one model version; another version is UNKNOWN.
    prices: tuple[PricePolicy, ...] = (
        JEV_1_13_PRICE
        if model == JEV_1_13_PRICE.model
        else replace(
            JEV_1_13_PRICE,
            policy_id="typesafe-unpriced-model.v1",
            model=model,
            usd_per_million_input=None,
            usd_per_million_output=None,
        ),
    )
    luna_model = values.get("AXIGNAL_AXENT_LUNA_MODEL", "").strip()
    luna_key = _readable(values.get("AXIGNAL_AXENT_API_KEY_FILE", ""))
    if reasoning_calls and luna_model and luna_key is not None:
        from cognition.providers.luna_responses import LunaResponsesProvider
        from cognition.semantic_escalation import ReasoningEscalation

        escalation = ReasoningEscalation(
            LunaResponsesProvider(authorized_model=luna_model, key_file=luna_key),
            model=luna_model,
        )
        prices = (*prices, _luna_price(values, luna_model))
    return _Composed(judge, memory, escalation, prices, tokens, reasoning_calls)


def semantic_screen_from_env(
    values: Mapping[str, str] | None = None,
    *,
    data_dir: Path | None = None,
    transport: Any | None = None,
) -> SemanticDemandScreen | None:
    """Build the screen from settings; ``transport`` replaces only the network (preflight)."""
    composed = _compose(os.environ if values is None else values, data_dir, transport)
    if composed is None:
        return None
    budget = SemanticBudget(
        max_system_one_input_tokens=composed.tokens,
        max_reasoning_calls=composed.reasoning_calls if composed.escalation is not None else 0,
    )
    policy = CascadePolicy(escalable=frozenset({FIT.question_id, DELIVERY.question_id}))

    def cascade() -> SemanticCascade:
        return SemanticCascade(
            judge=composed.judge,
            ledger=CostLedger(prices=composed.prices),
            budget=budget,
            policy=policy,
            memory=composed.memory,
            escalation=composed.escalation,
        )

    return SemanticDemandScreen(cascade)


def semantic_cascade_factory_from_env(
    values: Mapping[str, str] | None = None,
    *,
    data_dir: Path | None = None,
    transport: Any | None = None,
    token_budget: int,
) -> Callable[[], SemanticCascade] | None:
    """System One only (no escalable question, zero reasoning calls): First Observation.

    Same judge, judgment memory and prices as the demand screen, so a judgment over the
    same public state is paid once for every Focus and tenant (spec 062 memory).
    """
    composed = _compose(os.environ if values is None else values, data_dir, transport)
    if composed is None:
        return None
    budget = SemanticBudget(
        max_system_one_input_tokens=min(token_budget, composed.tokens), max_reasoning_calls=0
    )

    def cascade() -> SemanticCascade:
        return SemanticCascade(
            judge=composed.judge,
            ledger=CostLedger(prices=composed.prices),
            budget=budget,
            policy=CascadePolicy(),
            memory=composed.memory,
            escalation=None,
        )

    return cascade
