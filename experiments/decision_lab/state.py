"""Deterministic compilation and explicit state-variant transformations."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from experiments.decision_lab.models import LabError

STATE_CONTRACT_VERSION = "0.1.0"
STATE_COMPILER_VERSION = "0.2.0"


@dataclass(frozen=True)
class StateVariant:
    variant_id: str
    version: str
    transform: Callable[[dict[str, Any]], dict[str, Any]]


def _identity(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, ensure_ascii=False))


def _without_temporal_provenance(payload: dict[str, Any]) -> dict[str, Any]:
    transformed = _identity(payload)
    transformed.pop("temporal_context", None)
    transformed.pop("provenance", None)
    return transformed


STATE_VARIANTS: Mapping[str, StateVariant] = {
    "full_context": StateVariant("full_context", "0.1.0", _identity),
    "minimal": StateVariant("minimal", "0.1.0", _without_temporal_provenance),
}


def apply_state_variant(payload: dict[str, Any], variant_id: str) -> tuple[dict[str, Any], str]:
    """Apply one named, versioned transformation; unknown variants fail closed."""
    variant = STATE_VARIANTS.get(variant_id)
    if variant is None:
        raise LabError(f"unknown state variant: {variant_id}")
    return variant.transform(payload), variant.version


@dataclass(frozen=True)
class StructuredDecisionState:
    contract_version: str
    compiler_version: str
    canonical_json: str
    fingerprint: str

    @property
    def payload(self) -> dict[str, Any]:
        """Return a fresh object so callers cannot mutate the compiled value."""
        return json.loads(self.canonical_json)


def compile_state(payload: dict[str, Any]) -> StructuredDecisionState:
    """Compile JSON-safe semantic state; no secret/volatile fields are accepted."""
    forbidden = {"api_key", "authorization", "request_id", "trace_id", "timestamp_runtime"}

    def check(value: Any, path: str = "state") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in forbidden:
                    raise ValueError(f"volatile or secret field is forbidden: {path}.{key}")
                check(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check(child, f"{path}[{index}]")
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"state contains a non-finite number: {path}")
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"state is not JSON-safe: {path}")

    check(payload)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return StructuredDecisionState(
        STATE_CONTRACT_VERSION, STATE_COMPILER_VERSION, serialized, digest
    )
