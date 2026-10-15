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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

TIMELINE_VERSION = "timeline-v1"
#: Instruments of each snapshot, stored next to the metrics (MASTER §22: a before/after is
#: comparable only under the same instrument and version).
INSTRUMENTS = "_instruments"
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
    #: The instrument and version that produced the value; None: the metric definition
    #: itself (TIMELINE_VERSION) is the instrument.
    instrument: Callable[[list[Discovery]], str | None] | None = None


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


def _audit_instrument(ds: list[Discovery]) -> str | None:
    for d in _of(ds, "WEB_REPRESENTATION"):
        audit = _detail(d).get("audit")
        if isinstance(audit, Mapping) and audit.get("instrument"):
            return str(audit["instrument"])
    return None


def _probe_instrument(ds: list[Discovery]) -> str | None:
    """The generative probe: kind, model and its frozen conditions (questions, language,
    live search). Another model or other questions is another instrument."""
    import hashlib
    import json

    for d in _of(ds, "GENERATIVE_VISIBILITY"):
        detail = _detail(d)
        instrument = detail.get("instrument")
        if isinstance(instrument, Mapping):
            conditions = json.dumps(detail.get("conditions"), sort_keys=True, default=str)
            digest = hashlib.sha256(conditions.encode("utf-8")).hexdigest()[:12]
            return f"{instrument.get('kind')}:{instrument.get('model')}:{digest}"
    return None


def _audit_passed(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "WEB_REPRESENTATION"):
        audit = _detail(d).get("audit")
        checks = audit.get("checks") if isinstance(audit, Mapping) else None
        if isinstance(checks, list):
            return sum(1 for c in checks if isinstance(c, Mapping) and c.get("status") == "PASS")
    return None


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


def _own_site(
    extract: Callable[[list[Discovery], Mapping[str, Any]], object],
) -> Callable[[list[Discovery], Mapping[str, Any]], object]:
    """Only when the own-site reader read the website: otherwise unknown, never empty."""

    def guarded(ds: list[Discovery], view: Mapping[str, Any]) -> object:
        read = any(
            _detail(d).get("ownSiteVersion")
            for d in _of(ds, "PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED")
        )
        return extract(ds, view) if read else None

    return guarded


def _job_postings(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "OPERATING_SIGNAL", "JOB_POSTINGS_PUBLISHED"):
        count = _detail(d).get("count")
        return int(count) if isinstance(count, int) else None
    return 0


def _hiring_channel(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    return 1 if _of(ds, "OPERATING_SIGNAL") else 0


def _open_positions(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "OPERATING_SIGNAL", "OPEN_POSITIONS"):
        count = _detail(d).get("count")
        return int(count) if isinstance(count, int) else None
    return None


def _hiring_countries(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "OPERATING_SIGNAL", "OPEN_POSITIONS"):
        return sorted(str(c) for c in _detail(d).get("countries") or {})
    return None


def _wikipedia_views(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "MENTION", "WIKIPEDIA_NOTORIETY"):
        views = _detail(d).get("views")
        return int(views) if isinstance(views, int) else None
    return None


def _wikipedia_languages(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "MENTION", "WIKIPEDIA_NOTORIETY"):
        return sorted(str(x) for x in _detail(d).get("languages") or [])
    return None


def _self_rating(ds: list[Discovery], _v: Mapping[str, Any]) -> object:
    for d in _of(ds, "RATING", "RATING_SELF_PUBLISHED"):
        value = _detail(d).get("value")
        return float(value) if isinstance(value, int | float) else None
    return None


METRICS: tuple[Metric, ...] = (
    Metric("presence.ai_named_share", "presence", +1, "OBSERVED", _geo_named, 0.25, 0.0,
           _probe_instrument),
    Metric("presence.ai_knows_brand", "presence", +1, "OBSERVED", _brand_known, 1.0, 0.0,
           _probe_instrument),
    Metric("presence.audit_attention", "presence", -1, "OBSERVED", _audit_attention,
           instrument=_audit_instrument),
    Metric("presence.audit_passed", "presence", +1, "OBSERVED", _audit_passed, 1.0, 0.0,
           _audit_instrument),
    Metric("presence.lcp_ms", "presence", -1, "OBSERVED",
           _field_ms("LOADING_SPEED_REAL_USERS"), 200.0, 0.1, _audit_instrument),
    Metric("presence.inp_ms", "presence", -1, "OBSERVED",
           _field_ms("RESPONSIVENESS_REAL_USERS"), 40.0, 0.15, _audit_instrument),
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
    Metric("relationships.technology", "relationships", 0, "OBSERVED",
           _own_site(_set("RELATIONSHIP", "TECHNOLOGY_SUPPLIER_OBSERVED"))),
    Metric("relationships.declared_clients", "relationships", 0, "DECLARED",
           _own_site(_set("RELATIONSHIP", "CLIENT_DECLARED"))),
    Metric("relationships.declared_partners", "relationships", 0, "DECLARED",
           _own_site(_set("RELATIONSHIP", "PARTNER_DECLARED"))),
    Metric("value.credentials", "value", 0, "DECLARED", _own_site(_set("CREDENTIAL"))),
    Metric("activity.job_postings", "activity", 0, "DECLARED", _own_site(_job_postings),
           2.0, 0.25),
    Metric("activity.hiring_channel", "activity", 0, "DECLARED", _own_site(_hiring_channel),
           1.0, 0.0),
    Metric("reputation.review_profiles", "reputation", 0, "DECLARED",
           _own_site(_set("RATING", "REVIEW_PROFILE_LINKED"))),
    Metric("activity.open_positions", "activity", 0, "DECLARED", _open_positions, 3.0, 0.2),
    Metric("markets.hiring_countries", "markets", 0, "DECLARED", _hiring_countries),
    Metric("reputation.wikipedia_views", "reputation", 0, "OBSERVED", _wikipedia_views,
           50.0, 0.2),
    Metric("reputation.wikipedia_languages", "reputation", 0, "OBSERVED",
           _wikipedia_languages),
    Metric("reputation.self_rating", "reputation", 0, "DECLARED", _own_site(_self_rating),
           0.1, 0.0),
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
    instruments: dict[str, str] = {}
    for metric in METRICS:
        try:
            value = metric.extract(ds, view)
        except (TypeError, ValueError, KeyError):
            value = None
        if value is not None:
            out[metric.key] = value
            used = metric.instrument(ds) if metric.instrument is not None else None
            instruments[metric.key] = used or TIMELINE_VERSION
    if instruments:
        out[INSTRUMENTS] = instruments
    return out


def instrument_of(snapshot_metrics: Mapping[str, object], key: str) -> str | None:
    """The instrument a stored value came from. Snapshots stored before instruments were kept
    carry none: a metric defined by the timeline itself is still that definition; a measured
    one (audit, generative probe) is unknown, comparable only with another unknown."""
    held = snapshot_metrics.get(INSTRUMENTS)
    if isinstance(held, Mapping) and key in held:
        return str(held[key])
    metric = BY_KEY.get(key)
    return TIMELINE_VERSION if metric is not None and metric.instrument is None else None


def comparable(before: Mapping[str, object], after: Mapping[str, object], key: str) -> bool:
    """Same instrument and version (an unknown instrument compares only with another unknown)."""
    return instrument_of(before, key) == instrument_of(after, key)


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
        if not comparable(before, after, key):
            continue  # another instrument or version: a discontinuity, never a change
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


MAX_EVOLUTION_DAYS = 180
#: Items kept per set metric in the evolution sent to a view (lists of names stay small).
MAX_EVOLUTION_ITEMS = 30


def catalog() -> dict[str, dict[str, object]]:
    """What a client needs to compare two days exactly as ``changes`` does (spec 076)."""
    return {
        m.key: {"family": m.family, "polarity": m.polarity, "state": m.state,
                "minAbs": m.min_abs, "minRel": m.min_rel}
        for m in METRICS
    }  # fmt: skip


def evolution(snapshots: Sequence[tuple[str, Mapping[str, object]]]) -> dict[str, object]:
    """Every recorded day (up to 180) as versions: consecutive identical days collapse into
    one (from, to) range, so any day X can be compared with any day Y at little cost."""
    recent = list(snapshots)[-MAX_EVOLUTION_DAYS:]
    versions: list[dict[str, object]] = []
    for day, metrics in recent:
        compact = {
            k: v[:MAX_EVOLUTION_ITEMS] if isinstance(v, list) else v for k, v in metrics.items()
        }
        if versions and versions[-1]["metrics"] == compact:
            versions[-1]["to"] = day
        else:
            versions.append({"from": day, "to": day, "metrics": compact})
    return {
        "timelineVersion": TIMELINE_VERSION,
        "days": [day for day, _ in recent],
        "versions": versions,
        "catalog": catalog(),
    }


MAX_HISTORY_EVENTS = 300
MAX_SERIES_POINTS = 120


def history(
    snapshots: Sequence[tuple[str, Mapping[str, object]]], *, family: str | None = None
) -> dict[str, object]:
    """The whole recorded history, oldest first: numeric series and dated set events.

    Numbers become series (thinned to at most MAX_SERIES_POINTS, keeping first and last);
    sets become events: on which day each item appeared or disappeared. A metric absent
    on a day is unknown that day, never zero or empty, and breaks no comparison.
    """
    series: dict[str, list[list[object]]] = {}
    events: list[dict[str, object]] = []
    last_set: dict[str, tuple[str, set[str]]] = {}
    for day, metrics in snapshots:
        for key, value in metrics.items():
            metric = BY_KEY.get(key)
            if metric is None or (family is not None and metric.family != family):
                continue
            if isinstance(value, int | float) and not isinstance(value, bool):
                series.setdefault(key, []).append([day, value])
            elif isinstance(value, list):
                current = {str(v) for v in value}
                if key in last_set:
                    since, before = last_set[key]
                    added, removed = sorted(current - before), sorted(before - current)
                    if added or removed:
                        events.append({"day": day, "previousDay": since, "metric": key,
                                       "family": metric.family, "added": added[:20],
                                       "removed": removed[:20]})  # fmt: skip
                else:
                    events.append({"day": day, "metric": key, "family": metric.family,
                                   "firstSeen": sorted(current)[:20]})  # fmt: skip
                last_set[key] = (day, current)
    thinned: dict[str, list[list[object]]] = {}
    for key, points in series.items():
        if len(points) > MAX_SERIES_POINTS:
            step = len(points) / (MAX_SERIES_POINTS - 1)
            points = [points[int(i * step)] for i in range(MAX_SERIES_POINTS - 1)] + [points[-1]]
        thinned[key] = points
    return {
        "timelineVersion": TIMELINE_VERSION,
        "firstDay": snapshots[0][0] if snapshots else None,
        "lastDay": snapshots[-1][0] if snapshots else None,
        "daysRecorded": len(snapshots),
        "series": thinned,
        "events": events[-MAX_HISTORY_EVENTS:],
        "current": {k: v for k, v in (snapshots[-1][1].items() if snapshots else ())
                    if family is None or (k in BY_KEY and BY_KEY[k].family == family)},
    }  # fmt: skip
