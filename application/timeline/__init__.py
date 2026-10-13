"""Timeline: every family of an organization in time — what evolved, what regressed.

A daily snapshot condenses each family of an observation view into comparable metrics
(numbers and sets, all public). Comparing today's snapshot with one at least a week old
yields CHANGE discoveries: a metric that rose or fell, an item that appeared or
disappeared. Direction carries meaning only where it has one (an AI assistant naming the
organization is better, a slower site is worse); elsewhere a change is just a change.
Changes inherit the epistemic state of what they compare and cite both readings.
Global by construction: metrics come from the view, whatever country fed it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

TIMELINE_VERSION = "timeline-v1"
Discovery = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Metric:
    key: str
    family: str
    #: +1: higher is better; -1: lower is better; 0: no value judgement.
    polarity: int
    #: OBSERVED when read from observed facts; POTENTIAL when from derived readings.
    state: str
    extract: Callable[[list[Discovery], Mapping[str, Any]], object]
    #: Minimum change that counts (numbers): absolute and relative.
    min_abs: float = 1.0
    min_rel: float = 0.2


def _of(ds: list[Discovery], kind: str, *codes: str) -> list[Discovery]:
    return [d for d in ds if d.get("kind") == kind and (not codes or d.get("code") in codes)]


def _detail(d: Discovery) -> Mapping[str, Any]:
    detail = d.get("detail")
    return detail if isinstance(detail, Mapping) else {}


def _names(ds: list[Discovery]) -> list[str]:
    return sorted({str(d.get("statement") or "") for d in ds if d.get("statement")})


def _geo_named(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "GENERATIVE_VISIBILITY", "AI_NAMED_FOR_CATEGORY", "AI_NOT_NAMED_FOR_CATEGORY"):
        found = re.match(r"(\d+)/(\d+)", str(d.get("statement") or ""))
        if found and int(found.group(2)):
            return round(int(found.group(1)) / int(found.group(2)), 2)
    return None


def _brand_known(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    if _of(ds, "GENERATIVE_VISIBILITY", "AI_KNOWS_BRAND"):
        return 1
    if _of(ds, "GENERATIVE_VISIBILITY", "AI_DOES_NOT_KNOW_BRAND"):
        return 0
    return None


def _audit_attention(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    gaps = [d for d in _of(ds, "REPRESENTATION_GAP") if str(d.get("code", "")).startswith("AUDIT:")]
    return sorted(str(d["code"])[6:] for d in gaps) if _of(ds, "WEB_REPRESENTATION") else None


def _field_ms(check: str) -> Callable[[list[Discovery], Mapping[str, Any]], object]:
    def extract(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
        for d in _of(ds, "WEB_REPRESENTATION"):
            audit = _detail(d).get("audit")
            for c in (audit or {}).get("checks") or [] if isinstance(audit, Mapping) else []:
                if (
                    isinstance(c, Mapping)
                    and c.get("id") == check
                    and isinstance(c.get("value"), Mapping)
                ):
                    value = c["value"].get("p75")
                    return float(value) if isinstance(value, int | float) else None
        return None

    return extract


def _languages(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "LANGUAGES"):
        return sorted(str(x) for x in _detail(d).get("languages") or [])
    return None


def _economic(fact: str) -> Callable[[list[Discovery], Mapping[str, Any]], object]:
    def extract(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
        for d in _of(ds, "ECONOMIC_FACT"):
            detail = _detail(d)
            if detail.get("fact") == fact and isinstance(detail.get("value"), int | float):
                return float(detail["value"])
        return None

    return extract


def _open_tenders(_ds: list[Discovery], view: Mapping[str, Any]) -> object:
    demand = view.get("demand")
    return int(demand.get("total") or 0) if isinstance(demand, Mapping) else None


def _set(kind: str, *codes: str) -> Callable[[list[Discovery], Mapping[str, Any]], object]:
    def extract(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
        found = _of(ds, kind, *codes)
        return _names(found) if found else []

    return extract


def _count(kind: str, *codes: str) -> Callable[[list[Discovery], Mapping[str, Any]], object]:
    return lambda ds, _v: len(_of(ds, kind, *codes))


METRICS: tuple[Metric, ...] = (
    Metric("presence.ai_named_share", "presence", +1, "OBSERVED", _geo_named, 0.25, 0.0),
    Metric("presence.ai_knows_brand", "presence", +1, "OBSERVED", _brand_known, 1.0, 0.0),
    Metric("presence.audit_attention", "presence", -1, "OBSERVED", _audit_attention),
    Metric("presence.lcp_ms", "presence", -1, "OBSERVED",
           _field_ms("LOADING_SPEED_REAL_USERS"), 200.0, 0.1),
    Metric("presence.inp_ms", "presence", -1, "OBSERVED",
           _field_ms("RESPONSIVENESS_REAL_USERS"), 40.0, 0.15),
    Metric("presence.languages", "presence", 0, "OBSERVED", _languages),
    Metric("reputation.press_mentions", "reputation", 0, "POTENTIAL",
           _count("MENTION", "PRESS_MENTION")),
    Metric("activity.own_publications", "activity", 0, "OBSERVED",
           _count("MENTION", "OWN_PUBLICATION", "PRESS_RELEASE")),
    Metric("value.activities", "value", 0, "POTENTIAL", _set("ACTIVITY")),
    Metric("markets.premises", "markets", 0, "DECLARED",
           _set("DECLARED_LOCATION", "PREMISES_PINNED_ON_MAP", "ADDRESS_DECLARED")),
    Metric("markets.group_countries", "markets", 0, "OBSERVED",
           lambda ds, _v: sorted(
               str(c) for d in _of(ds, "DECLARED_LOCATION", "GROUP_ENTITIES_IN_COUNTRIES")
               for c in (_detail(d).get("countries") or {}))),
    Metric("relationships.public_clients", "relationships", 0, "OBSERVED",
           _set("RELATIONSHIP", "PUBLIC_CONTRACTS_WON")),
    Metric("relationships.partners", "relationships", 0, "POTENTIAL",
           _set("RELATIONSHIP", "PUBLIC_CONTRACT_PARTNER")),
    Metric("relationships.competitors", "relationships", 0, "POTENTIAL", _set("COMPETITION")),
    Metric("demand.open_public_calls", "demand", 0, "POTENTIAL", _open_tenders, 3.0, 0.25),
    Metric("demand.recurrent_buyers", "demand", 0, "POTENTIAL",
           _set("DEMAND", "RECURRING_PUBLIC_BUYER")),
    Metric("economics.revenue", "economics", 0, "OBSERVED", _economic("revenue"), 1.0, 0.05),
    Metric("economics.employees", "economics", 0, "OBSERVED", _economic("employees"), 2.0, 0.05),
    Metric("organization.identifiers", "organization", 0, "DECLARED",
           lambda ds, _v: _names(_of(ds, "IDENTITY_HINT")) if _of(ds, "IDENTITY_HINT") else []),
    Metric("context.sector_headlines", "context", 0, "POTENTIAL",
           _count("CONTEXT_SIGNAL", "SECTOR_HEADLINE"), 3.0, 0.5),
    Metric("context.regulation", "context", 0, "POTENTIAL",
           _set("CONTEXT_SIGNAL", "REGULATION")),
)  # fmt: skip
BY_KEY = {m.key: m for m in METRICS}


def snapshot(view: Mapping[str, Any]) -> dict[str, object]:
    """The comparable metrics of one view (unknown metrics are absent, never zero)."""
    held = view.get("discoveries")
    ds = [d for d in (held if isinstance(held, list) else []) if isinstance(d, Mapping)]
    out: dict[str, object] = {}
    for metric in METRICS:
        try:
            value = metric.extract(ds, view)
        except (TypeError, ValueError, KeyError):
            value = None
        if value is not None:
            out[metric.key] = value
    return out


def _change(
    metric: Metric, before: object, after: object, *, before_day: str, after_day: str
) -> dict[str, object] | None:
    values: dict[str, object] = {"metric": metric.key, "before": before, "after": after,
                                 "beforeDay": before_day, "afterDay": after_day}  # fmt: skip
    if isinstance(before, list) and isinstance(after, list):
        added = sorted(set(map(str, after)) - set(map(str, before)))
        removed = sorted(set(map(str, before)) - set(map(str, after)))
        if not added and not removed:
            return None
        values.update({"added": added[:10], "removed": removed[:10]})
        direction = (
            "ADDED" if added and not removed else "REMOVED" if removed and not added else "CHANGED"
        )
        if metric.polarity:  # a list where fewer is better (audit checks needing attention)
            better = len(after) < len(before) if metric.polarity < 0 else len(after) > len(before)
            worse = len(after) > len(before) if metric.polarity < 0 else len(after) < len(before)
            direction = "EVOLUTION" if better else "REGRESSION" if worse else direction
    elif isinstance(before, int | float) and isinstance(after, int | float):
        delta = float(after) - float(before)
        rel = abs(delta) / abs(float(before)) if before else 1.0
        if abs(delta) < metric.min_abs or rel < metric.min_rel:
            return None
        values["delta"] = round(delta, 4)
        if metric.polarity:
            direction = "EVOLUTION" if delta * metric.polarity > 0 else "REGRESSION"
        else:
            direction = "UP" if delta > 0 else "DOWN"
    else:
        return None
    values["direction"] = direction
    return values


def changes(
    before: Mapping[str, object], after: Mapping[str, object], *, before_day: str,
    after_day: str, observed_at: str, source_url: str | None = None,
) -> list[dict[str, object]]:  # fmt: skip
    """CHANGE discoveries between two snapshots (only metrics present in both)."""
    out: list[dict[str, object]] = []
    for key, metric in BY_KEY.items():
        if key not in before or key not in after:
            continue
        values = _change(metric, before[key], after[key], before_day=before_day,
                         after_day=after_day)  # fmt: skip
        if values is None:
            continue
        out.append(
            {
                "kind": "CHANGE",
                "code": f"{metric.family}:{key}:{values['direction']}",
                "statement": f"{key}: {before[key]} -> {after[key]}",
                "epistemicState": metric.state,
                "sourceUrl": source_url,
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "family": metric.family,
                    "values": values,
                    "timelineVersion": TIMELINE_VERSION,
                    "limitation": "A comparison of two readings by the same instrument; what "
                    "changed between them, not why.",
                },
            }
        )
    order = {"REGRESSION": 0, "EVOLUTION": 1}
    out.sort(key=lambda c: order.get(str(c["detail"]["values"]["direction"]), 2))  # type: ignore[index]
    return out
