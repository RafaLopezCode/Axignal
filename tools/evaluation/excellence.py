"""Family excellence report: how well AXIGNAL reads each family across the golden set.

Input: a JSON list of ``{"domain", "name", "country", "view"}`` (the subscriber view of
each organization, as ``run_golden`` dumps it). Output: per family, coverage (organizations
with at least one finding that is not UNKNOWN), observability distribution (MASTER §21,
the same rules the MCP panorama uses), findings by state and distinct sources; per
country, coverage; and, against a baseline report, the families that regressed.

Deterministic and offline: no network, no model. It measures; it does not judge
precision, which needs human sampling (see ``sample``).

    python -m tools.evaluation.excellence report views.json --out report.json
    python -m tools.evaluation.excellence report views.json --baseline old.json
    python -m tools.evaluation.excellence sample views.json --family reputation --n 20
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.first_observation.families import FAMILIES, family_of
from application.product_mcp.panorama import finding_id, observability

REPORT_VERSION = "excellence-report-v1"
#: A family regresses when its coverage drops by more than this many points.
REGRESSION_POINTS = 5.0
_NOT_FINDINGS = {"SIGNIFICANT_UNKNOWN", "CHANGE"}


def _discoveries(view: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    held = (view or {}).get("discoveries")
    return [d for d in held if isinstance(d, Mapping)] if isinstance(held, list) else []


def report(rows: Sequence[Mapping[str, Any]], *, now: datetime) -> dict[str, Any]:
    families: dict[str, dict[str, Any]] = {
        f: {"covered": 0, "observability": {}, "by_state": {}, "findings": 0, "sources": set()}
        for f in FAMILIES
    }
    countries: dict[str, dict[str, Any]] = {}
    organizations: list[dict[str, Any]] = []
    for row in rows:
        view = row.get("view") if isinstance(row.get("view"), Mapping) else None
        found = _discoveries(view)
        crossings = [d for d in found if d.get("kind") == "INXIGHT"]
        per_org: dict[str, str] = {}
        covered_here = 0
        for name in FAMILIES:
            held = [d for d in found if family_of(d) == name and d.get("kind") != "INXIGHT"]
            known = [d for d in held if d.get("kind") not in _NOT_FINDINGS]
            level = observability(held, [c for c in crossings if family_of(c) == name], now=now)
            per_org[name] = level
            stats = families[name]
            stats["observability"][level] = stats["observability"].get(level, 0) + 1
            if known:
                stats["covered"] += 1
                covered_here += 1
            stats["findings"] += len(known)
            for d in known:
                state = str(d.get("epistemicState") or "UNKNOWN")
                stats["by_state"][state] = stats["by_state"].get(state, 0) + 1
                if d.get("sourceUrl"):
                    stats["sources"].add(str(d["sourceUrl"]))
        country = str(row.get("country") or "??")
        tally = countries.setdefault(country, {"organizations": 0, "family_cells": 0})
        tally["organizations"] += 1
        tally["family_cells"] += covered_here
        organizations.append(
            {
                "domain": row.get("domain"),
                "country": country,
                "state": (view or {}).get("state", "NO_VIEW"),
                "families_covered": covered_here,
                "observability": per_org,
            }
        )
    total = len(rows) or 1
    return {
        "version": REPORT_VERSION,
        "generated_at": now.isoformat(),
        "organizations_measured": len(rows),
        "families": {
            name: {
                "coverage_pct": round(100 * s["covered"] / total, 1),
                "covered": s["covered"],
                "observability": dict(sorted(s["observability"].items())),
                "findings": s["findings"],
                "by_state": dict(sorted(s["by_state"].items())),
                "distinct_sources": len(s["sources"]),
            }
            for name, s in families.items()
        },
        "countries": {
            c: {
                "organizations": t["organizations"],
                "family_coverage_pct": round(
                    100 * t["family_cells"] / (t["organizations"] * len(FAMILIES)), 1
                ),
            }
            for c, t in sorted(countries.items())
        },
        "organizations": organizations,
    }


def regressions(current: Mapping[str, Any], baseline: Mapping[str, Any]) -> list[str]:
    """Families whose coverage dropped by more than REGRESSION_POINTS."""
    out: list[str] = []
    for name in FAMILIES:
        now = current["families"][name]["coverage_pct"]
        before = baseline.get("families", {}).get(name, {}).get("coverage_pct")
        if isinstance(before, int | float) and before - now > REGRESSION_POINTS:
            out.append(f"{name}: {before} -> {now}")
    return out


def markdown(current: Mapping[str, Any], baseline: Mapping[str, Any] | None = None) -> str:
    lines = [
        f"Organizations measured: {current['organizations_measured']}",
        "",
        "| Family | Coverage | Before | STRONG | PARTIAL | LIMITED | UNKNOWN | Findings | Sources |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name in FAMILIES:
        f = current["families"][name]
        before = (baseline or {}).get("families", {}).get(name, {}).get("coverage_pct", "")
        o = f["observability"]
        lines.append(
            f"| {name} | {f['coverage_pct']}% | {before}{'%' if before != '' else ''} | "
            f"{o.get('STRONG', 0)} | {o.get('PARTIAL', 0)} | {o.get('LIMITED', 0)} | "
            f"{o.get('UNKNOWN', 0)} | {f['findings']} | {f['distinct_sources']} |"
        )
    lines += ["", "| Country | Organizations | Family coverage |", "|---|---|---|"]
    for country, c in current["countries"].items():
        lines.append(f"| {country} | {c['organizations']} | {c['family_coverage_pct']}% |")
    return "\n".join(lines)


def sample(
    rows: Sequence[Mapping[str, Any]], family: str, n: int, *, seed: int = 7
) -> list[dict[str, Any]]:
    """A reproducible random sample of findings of one family, for human precision review."""
    pool = [
        {"domain": row.get("domain"), "id": finding_id(d), "code": d.get("code"),
         "statement": d.get("statement"), "state": d.get("epistemicState"),
         "source": d.get("sourceUrl"), "verdict": None}
        for row in rows
        for d in _discoveries(row.get("view") if isinstance(row.get("view"), Mapping) else None)
        if family_of(d) == family and d.get("kind") not in _NOT_FINDINGS | {"INXIGHT"}
    ]  # fmt: skip
    return random.Random(seed).sample(pool, min(n, len(pool)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.evaluation.excellence")
    sub = parser.add_subparsers(dest="command", required=True)
    rep = sub.add_parser("report")
    rep.add_argument("views", type=Path)
    rep.add_argument("--baseline", type=Path)
    rep.add_argument("--out", type=Path)
    smp = sub.add_parser("sample")
    smp.add_argument("views", type=Path)
    smp.add_argument("--family", required=True, choices=FAMILIES)
    smp.add_argument("--n", type=int, default=20)
    args = parser.parse_args(argv)
    rows = json.loads(args.views.read_text(encoding="utf-8"))
    if args.command == "sample":
        print(json.dumps(sample(rows, args.family, args.n), ensure_ascii=False, indent=1))
        return 0
    current = report(rows, now=datetime.now(UTC))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline else None
    if args.out:
        args.out.write_text(json.dumps(current, ensure_ascii=False, indent=1), encoding="utf-8")
    print(markdown(current, baseline))
    worse = regressions(current, baseline) if baseline else []
    for line in worse:
        print(f"REGRESSION {line}", file=sys.stderr)
    return 1 if worse else 0


if __name__ == "__main__":
    raise SystemExit(main())
