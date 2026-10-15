"""Cases the web's day-X-versus-day-Y comparison must state exactly as the engine (spec 076).

``python -m tools.evaluation.evolution_parity`` rewrites the fixture the web test reads;
``tests/timeline`` fails when the engine's rules and the committed fixture disagree.
"""

from __future__ import annotations

import json
from pathlib import Path

from application.timeline import BY_KEY, TIMELINE_VERSION, _change, catalog, comparable

FIXTURE = Path("apps/web/experience/tests/fixtures/evolution-parity.json")

#: (metric, before, after, instruments before, instruments after): numbers, sets, polarity,
#: thresholds, unknown, and an instrument change.
CASES: list[tuple[str, object, object, dict[str, str] | None, dict[str, str] | None]] = [
    ("demand.open_public_calls", 10, 14, None, None),
    ("demand.open_public_calls", 10, 12, None, None),
    ("demand.open_public_calls", 10, 6, None, None),
    (
        "presence.ai_named_share",
        0.25,
        0.75,
        {"presence.ai_named_share": "P:m1"},
        {"presence.ai_named_share": "P:m1"},
    ),
    (
        "presence.ai_named_share",
        0.25,
        0.75,
        {"presence.ai_named_share": "P:m1"},
        {"presence.ai_named_share": "P:m2"},
    ),
    ("presence.ai_named_share", 0.25, 0.75, None, {"presence.ai_named_share": "P:m1"}),
    ("presence.lcp_ms", 2400.0, 1900.0, {"presence.lcp_ms": "a1"}, {"presence.lcp_ms": "a1"}),
    ("presence.lcp_ms", 2400.0, 2300.0, {"presence.lcp_ms": "a1"}, {"presence.lcp_ms": "a1"}),
    (
        "presence.audit_attention",
        ["A", "B"],
        ["A"],
        {"presence.audit_attention": "a1"},
        {"presence.audit_attention": "a1"},
    ),
    (
        "presence.audit_attention",
        ["A"],
        ["A", "C"],
        {"presence.audit_attention": "a1"},
        {"presence.audit_attention": "a1"},
    ),
    ("relationships.competitors", ["X"], ["X", "Y"], None, None),
    ("relationships.competitors", ["X", "Y"], ["Y"], None, None),
    ("relationships.competitors", ["X"], ["Z"], None, None),
    ("relationships.competitors", ["X"], ["X"], None, None),
    ("economics.employees", 100.0, 103.0, None, None),
    ("economics.employees", 100.0, 120.0, None, None),
]


def cases() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for key, before, after, inst_before, inst_after in CASES:
        b: dict[str, object] = {key: before}
        a: dict[str, object] = {key: after}
        if inst_before is not None:
            b["_instruments"] = inst_before
        if inst_after is not None:
            a["_instruments"] = inst_after
        if not comparable(b, a, key):
            direction = "NOT_COMPARABLE"
        else:
            change = _change(BY_KEY[key], before, after, before_day="d1", after_day="d2")
            direction = "SAME" if change is None else str(change["direction"])
        out.append({"metric": key, "before": b, "after": a, "direction": direction})
    return out


def main() -> None:
    payload = {"timelineVersion": TIMELINE_VERSION, "catalog": catalog(), "cases": cases()}
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{len(payload['cases'])} cases -> {FIXTURE}")


if __name__ == "__main__":
    main()
