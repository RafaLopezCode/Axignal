"""Runtime economics of First Observation (spec 063 §10), from stored proofs only.

Counts are measured; money keeps the basis it was recorded with. A figure with no
measured or priced input is reported as UNKNOWN, never as zero.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any


def _value(ledger: Mapping[str, Any], key: str) -> Any:
    item = ledger.get(key)
    return item.get("value") if isinstance(item, dict) else None


def _ratio(numerator: Decimal | int, denominator: int) -> str | None:
    if denominator <= 0:
        return None
    return str((Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.0001")))


def runtime_metrics(proofs: Iterable[Mapping[str, Any]]) -> dict[str, object]:
    jobs = ready = useful_opportunities = http = avoided = site_hits = 0
    jev_calls = jev_tokens = jev_hits = luna_calls = source_requests = source_hits = 0
    jev_usd = Decimal(0)
    jev_usd_unknown = 0
    elapsed: list[int] = []
    states: dict[str, int] = {}
    for proof in proofs:
        ledger = proof.get("ledger") or {}
        jobs += 1
        ready += bool(proof.get("firstProofReady"))
        states[str(proof.get("state"))] = states.get(str(proof.get("state")), 0) + 1
        useful_opportunities += sum(
            1 for d in proof.get("discoveries", ()) if d.get("kind") == "DEMAND"
        )
        http += int(_value(ledger, "httpRequests") or 0)
        avoided += int(_value(ledger, "requestsAvoided") or 0)
        site_hits += int(_value(ledger, "siteReuseHits") or 0)
        source_requests += int(_value(ledger, "sourceRequests") or 0)
        source_hits += int(_value(ledger, "sourceCacheHits") or 0)
        calls = int(_value(ledger, "jevCalls") or 0)
        jev_calls += calls
        jev_tokens += int(_value(ledger, "jevInputTokens") or 0)
        jev_hits += int(_value(ledger, "jevMemoryHits") or 0)
        luna_calls += int(_value(ledger, "lunaCalls") or 0)
        usd = _value(ledger, "jevUsd")
        if calls and usd is None:
            jev_usd_unknown += 1
        elif usd is not None:
            try:
                jev_usd += Decimal(str(usd))
            except InvalidOperation:
                jev_usd_unknown += 1
        elapsed.append(int(_value(ledger, "elapsedMs") or 0))
    elapsed.sort()
    return {
        "jobs": jobs,
        "states": states,
        "firstProofsReady": ready,
        "COST_PER_FIRST_PROOF": {
            "httpRequests": _ratio(http + source_requests, ready),
            "jevUsd": None if jev_usd_unknown else _ratio(jev_usd, ready),
            "jevUsdBasis": "UNKNOWN" if jev_usd_unknown else "VENDOR_PUBLISHED_PRICE",
            "lunaCalls": _ratio(luna_calls, ready),
        },
        "HTTP_REQUESTS_PER_USEFUL_RESULT": _ratio(http + source_requests, ready),
        "COST_PER_USEFUL_OPPORTUNITY": {
            "requests": _ratio(http + source_requests, useful_opportunities),
            "opportunities": useful_opportunities,
        },
        "COST_AVOIDED_BY_REUSE": {
            "requestsAvoided": avoided,
            "siteReadingsReused": site_hits,
            "sourceQueriesReplayed": source_hits,
            "jevMemoryHits": jev_hits,
            "basis": "MEASURED",
        },
        "JEV_ESCALATION_RATE": _ratio(jev_calls, jobs),
        "LUNA_ESCALATION_RATE": _ratio(luna_calls, jobs),
        "jevInputTokens": jev_tokens,
        "latencyMs": {
            "p50": elapsed[len(elapsed) // 2] if elapsed else None,
            "max": elapsed[-1] if elapsed else None,
            "basis": "MEASURED",
        },
        "notes": [
            "COST_PER_ACTIVE_FOCUS_DAY and COST_PER_MATERIAL_CHANGE need the T12 ledger "
            "joined per Focus; not derivable from First Observation proofs alone.",
        ],
    }
