"""Versioned experimental pricing policy; no preflight cost from request bytes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from experiments.decision_lab.models import LabError

PRICING_POLICY_PATH = Path(__file__).parent / "pricing/v0.1/typesafe-jev-1.13.json"


def load_pricing_policy(path: Path = PRICING_POLICY_PATH) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "policy_version",
        "provider",
        "model",
        "price_dimension",
        "price",
        "currency",
        "unit",
        "reviewed_date",
        "source_authority",
        "source_url",
    }
    if not isinstance(policy, dict) or not required <= policy.keys():
        raise LabError("pricing policy is incomplete")
    if policy["price_dimension"] != "input_tokens" or policy["price"] < 0:
        raise LabError("unsupported pricing policy dimension or price")
    return policy


def estimate_cost_from_usage(
    policy: Mapping[str, Any], usage: Mapping[str, Any] | None, *, model: str
) -> dict[str, Any]:
    """Price provider-reported input usage only; never treat bytes as tokens."""
    input_tokens = usage.get("input_tokens") if usage is not None else None
    if (
        model != policy.get("model")
        or not isinstance(input_tokens, int)
        or isinstance(input_tokens, bool)
        or input_tokens < 0
    ):
        return {
            "estimated_cost": "UNKNOWN",
            "invoice_cost": "UNKNOWN",
            "pricing_policy_version": policy.get("policy_version"),
        }
    return {
        "estimated_cost": input_tokens * float(policy["price"]) / 1_000_000,
        "currency": policy["currency"],
        "pricing_policy_version": policy["policy_version"],
        "input_tokens": input_tokens,
        "invoice_cost": "UNKNOWN",
    }
