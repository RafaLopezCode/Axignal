"""Timeline: comparable family metrics per day; evolution, regression or plain change."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from application.timeline import TIMELINE_VERSION, changes, snapshot
from pipeline.first_observation.sqlite_store import SqliteFirstObservationStore


def _d(kind: str, code: str, statement: str = "", **detail: Any) -> dict[str, Any]:
    return {"kind": kind, "code": code, "statement": statement, "epistemicState": "OBSERVED",
            "detail": detail}  # fmt: skip


def _view(*discoveries: dict[str, Any], total: int | None = None) -> dict[str, Any]:
    view: dict[str, Any] = {"discoveries": list(discoveries)}
    if total is not None:
        view["demand"] = {"total": total}
    return view


def _changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, Any]]:
    found = changes(snapshot(before), snapshot(after), before_day="2026-10-01",
                    after_day="2026-10-13", observed_at="2026-10-13T08:00:00+00:00")  # fmt: skip
    return {str(c["detail"]["values"]["metric"]): c for c in found}  # type: ignore[index]


def test_unknown_metrics_are_absent_never_zero() -> None:
    held = snapshot(_view())
    assert "presence.ai_named_share" not in held
    assert "economics.revenue" not in held
    assert "demand.open_public_calls" not in held  # no demand reading is not zero demand


def test_polarity_decides_evolution_and_regression() -> None:
    before = _view(
        _d("GENERATIVE_VISIBILITY", "AI_NOT_NAMED_FOR_CATEGORY", "0/4 answers"),
        _d("WEB_REPRESENTATION", "AUDIT"),
        _d("REPRESENTATION_GAP", "AUDIT:STRUCTURED_DATA"),
    )
    after = _view(
        _d("GENERATIVE_VISIBILITY", "AI_NAMED_FOR_CATEGORY", "2/4 answers"),
        _d("WEB_REPRESENTATION", "AUDIT"),
        _d("REPRESENTATION_GAP", "AUDIT:STRUCTURED_DATA"),
        _d("REPRESENTATION_GAP", "AUDIT:TITLE"),
    )
    found = _changes(before, after)
    geo = found["presence.ai_named_share"]
    assert geo["code"] == "presence:presence.ai_named_share:EVOLUTION"
    assert geo["detail"]["values"]["before"] == 0.0 and geo["detail"]["values"]["after"] == 0.5
    audit = found["presence.audit_attention"]
    assert audit["detail"]["values"]["direction"] == "REGRESSION"
    assert audit["detail"]["values"]["added"] == ["TITLE"]
    # Regressions come first: what got worse is what deserves attention.
    assert next(iter(found)) == "presence.audit_attention"
    assert geo["detail"]["timelineVersion"] == TIMELINE_VERSION


def test_neutral_metrics_report_change_without_judgement() -> None:
    before = _view(_d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "Ayuntamiento A"), total=10)
    after = _view(
        _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "Ayuntamiento A"),
        _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "Region B"),
        total=4,
    )
    found = _changes(before, after)
    assert found["relationships.public_clients"]["detail"]["values"]["direction"] == "ADDED"
    assert found["relationships.public_clients"]["detail"]["values"]["added"] == ["Region B"]
    assert found["demand.open_public_calls"]["detail"]["values"]["direction"] == "DOWN"


def test_noise_below_thresholds_is_not_a_change() -> None:
    def fact(value: float) -> dict[str, Any]:
        return _d("ECONOMIC_FACT", "REGISTER:revenue", fact="revenue", value=value)

    assert _changes(_view(fact(1_000_000)), _view(fact(1_020_000))) == {}
    assert "economics.revenue" in _changes(_view(fact(1_000_000)), _view(fact(1_200_000)))
    assert _changes(_view(total=10), _view(total=11)) == {}


def test_a_change_needs_both_readings() -> None:
    after = _view(_d("ECONOMIC_FACT", "REGISTER:employees", fact="employees", value=40))
    assert _changes(_view(), after) == {}


def test_store_keeps_one_row_per_day_bounded_and_scoped(tmp_path: Path) -> None:
    store = SqliteFirstObservationStore(tmp_path / "fo.sqlite3")
    store.save_snapshot("t1", "focus", "org", day="2025-01-01", metrics={"a": 1})
    store.save_snapshot("t1", "focus", "org", day="2026-10-01", metrics={"a": 2})
    store.save_snapshot("t1", "focus", "org", day="2026-10-13", metrics={"a": 3})
    store.save_snapshot("t1", "focus", "org", day="2026-10-13", metrics={"a": 4})
    store.save_snapshot("t2", "focus", "org", day="2026-10-13", metrics={"a": 9})
    assert store.snapshots("t1", "focus", "org") == [("2026-10-01", {"a": 2}),
                                                     ("2026-10-13", {"a": 4})]  # fmt: skip
    assert store.snapshots("t1", "focus", "other") == []


def test_runtime_compares_today_with_a_reading_at_least_a_week_old(tmp_path: Path) -> None:
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    from tools.runtime.first_observation import FirstObservationRuntime

    now = [datetime(2026, 10, 1, 9, tzinfo=UTC)]
    fake = SimpleNamespace(
        store=SqliteFirstObservationStore(tmp_path / "fo.sqlite3"),
        _clock=SimpleNamespace(now=lambda: now[0]),
    )

    def read(named: str, total: int) -> dict[str, Any]:
        view = _view(_d("GENERATIVE_VISIBILITY", "AI_NAMED_FOR_CATEGORY", named), total=total)
        return FirstObservationRuntime._with_timeline(fake, view, "t1", "focus", "org")  # type: ignore[arg-type]

    first = read("1/4 answers", 10)
    assert first["timeline"]["days"] == 1 and first["timeline"]["baselineDay"] is None
    now[0] += timedelta(days=3)  # too recent to compare: no change yet
    assert not [d for d in read("3/4 answers", 10)["discoveries"] if d["kind"] == "CHANGE"]
    now[0] += timedelta(days=5)
    later = read("3/4 answers", 2)
    found = {d["code"] for d in later["discoveries"] if d["kind"] == "CHANGE"}
    assert found == {
        "presence:presence.ai_named_share:EVOLUTION",
        "demand:demand.open_public_calls:DOWN",
    }
    assert later["timeline"]["baselineDay"] == "2026-10-01"
    assert later["timeline"]["series"]["presence.ai_named_share"] == [
        ["2026-10-01", 0.25],
        ["2026-10-04", 0.75],
        ["2026-10-09", 0.75],
    ]


def test_own_site_signals_change_in_time_only_once_the_reader_ran() -> None:
    def site(*ds: dict[str, Any], read: bool = True) -> dict[str, Any]:
        detail = {"ownSiteVersion": "own-site-v1"} if read else {}
        return _view(_d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED", "Acme", **detail), *ds)

    hubspot = _d("RELATIONSHIP", "TECHNOLOGY_SUPPLIER_OBSERVED", "HubSpot")
    salesforce = _d("RELATIONSHIP", "TECHNOLOGY_SUPPLIER_OBSERVED", "Salesforce")
    jobs = _d("OPERATING_SIGNAL", "JOB_POSTINGS_PUBLISHED", "6", count=6)
    found = _changes(site(hubspot), site(salesforce, jobs))
    tech = found["relationships.technology"]["detail"]["values"]
    assert (tech["added"], tech["removed"], tech["direction"]) == (
        ["Salesforce"],
        ["HubSpot"],
        "CHANGED",
    )
    assert found["activity.job_postings"]["detail"]["values"]["after"] == 6
    assert found["activity.hiring_channel"]["code"] == "activity:activity.hiring_channel:UP"
    # A reading from before the own-site reader is unknown, not "nothing": no false ADDED.
    assert "relationships.technology" not in _changes(site(read=False), site(salesforce))
