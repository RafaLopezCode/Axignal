"""Durable tenant and subject scoped public-understanding report history."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.first_observation.contracts import (
    AttentionTarget,
    FirstProof,
    IdentityLink,
    ObservationState,
    TargetKind,
)
from pipeline.first_observation.sqlite_store import SqliteFirstObservationStore

NOW = datetime(2026, 10, 9, 10, tzinfo=UTC)


def _proof(
    target: AttentionTarget,
    report_id: str,
    measured_at: datetime,
    retain_until: datetime | None,
    source_expiry: datetime | None = None,
) -> FirstProof:
    return FirstProof(
        target=target,
        state=ObservationState.FIRST_PROOF_READY,
        ready=True,
        discoveries=(),
        attention_scopes=(),
        capabilities=(),
        site_fingerprint="site-fingerprint",
        ledger={},
        judged={},
        observed_at=NOW,
        next_due_at=None,
        retain_until=retain_until,
        understanding={
            "reportId": report_id,
            "measuredAt": measured_at.isoformat(),
            "validUntil": None,
            "contentExpiresAt": None if source_expiry is None else source_expiry.isoformat(),
            "instrument": {"ref": "offer-read", "version": "1"},
            "conditions": {"locale": "en"},
            "authority": "DERIVED_CONDITIONED_NOT_CANONICAL",
            "execution": "EVALUATED",
            "coverage": "BOUNDED_COMPLETE",
            "citations": [{"quote": f"private quote for {report_id}"}],
            "dimensions": [{"quote": f"private quote for {report_id}"}],
        },
    )


def _target(
    tenant: str = "tenant-a",
    target_ref: str = "focus-1",
    organization: str | None = "org-1",
) -> AttentionTarget:
    kind = TargetKind.PENDING if organization is None else TargetKind.FOCUS
    return AttentionTarget(
        tenant_id=tenant,
        principal_id=f"principal:{tenant}",
        target_ref=target_ref,
        kind=kind,
        website="https://example.test/",
        name="Example",
        organization_id=organization,
        identity_link=(
            IdentityLink.IDENTITY_PENDING
            if organization is None
            else IdentityLink.REGISTRY_VERIFIED
        ),
    )


def _complete(
    store: SqliteFirstObservationStore,
    target: AttentionTarget,
    report_id: str,
    *,
    at: datetime,
    retain_until: datetime | None = None,
    source_expiry: datetime | None = None,
) -> bool:
    store.enqueue(target, key=f"job:{report_id}", now=at)
    job = store.claim(now=at, lease_seconds=60, max_attempts=2)
    assert job is not None
    return store.complete(
        job,
        _proof(target, report_id, at, retain_until, source_expiry),
        now=at,
    )


def test_history_survives_restart_and_requires_owned_lease(tmp_path: Path) -> None:
    database = tmp_path / "first-observation.sqlite3"
    store = SqliteFirstObservationStore(database)
    target = _target()
    store.enqueue(target, key="first", now=NOW)
    job = store.claim(now=NOW, lease_seconds=60, max_attempts=2)
    assert job is not None
    proof = _proof(
        target,
        "report-1",
        NOW,
        NOW + timedelta(days=3),
        NOW + timedelta(days=1),
    )

    assert store.complete(job, proof, now=NOW)
    assert not store.complete(job, proof, now=NOW)
    reopened = SqliteFirstObservationStore(database)
    [report] = reopened.history("tenant-a", "focus-1", "org-1")
    assert report["reportId"] == "report-1"
    assert report["measuredAt"] == NOW.isoformat()
    assert report["contentExpiresAt"] == (NOW + timedelta(days=1)).isoformat()
    assert _complete(
        store,
        target,
        "report-1",
        at=NOW + timedelta(minutes=1),
        source_expiry=NOW + timedelta(days=2),
    )
    # Duplicate report identity does not create a second history row or extend its rights.
    [same_report] = SqliteFirstObservationStore(database).history("tenant-a", "focus-1", "org-1")
    assert same_report["contentExpiresAt"] == (NOW + timedelta(days=1)).isoformat()


def test_history_is_bounded_to_latest_eight_for_each_subject(tmp_path: Path) -> None:
    store = SqliteFirstObservationStore(tmp_path / "history.sqlite3")
    target = _target()
    for index in range(10):
        assert _complete(store, target, f"report-{index}", at=NOW + timedelta(minutes=index))

    reports = store.history("tenant-a", "focus-1", "org-1")
    assert len(reports) == 8
    assert [report["reportId"] for report in reports] == [
        f"report-{index}" for index in reversed(range(2, 10))
    ]


def test_history_filters_tenant_target_and_exact_organization_including_none(
    tmp_path: Path,
) -> None:
    store = SqliteFirstObservationStore(tmp_path / "isolation.sqlite3")
    _complete(store, _target("tenant-a", "focus-1", "org-1"), "a1", at=NOW)
    _complete(store, _target("tenant-a", "focus-1", "org-2"), "a2", at=NOW + timedelta(minutes=1))
    _complete(store, _target("tenant-b", "focus-1", "org-1"), "b1", at=NOW + timedelta(minutes=2))
    _complete(
        store, _target("tenant-a", "pending-1", None), "pending", at=NOW + timedelta(minutes=3)
    )

    assert [r["reportId"] for r in store.history("tenant-a", "focus-1", "org-1")] == ["a1"]
    assert [r["reportId"] for r in store.history("tenant-a", "focus-1", "org-2")] == ["a2"]
    assert [r["reportId"] for r in store.history("tenant-b", "focus-1", "org-1")] == ["b1"]
    assert [r["reportId"] for r in store.history("tenant-a", "pending-1", None)] == ["pending"]
    assert store.history("tenant-a", "focus-1", None) == []


def test_purge_removes_expired_history_and_retires_current_proof_citations(
    tmp_path: Path,
) -> None:
    database = tmp_path / "retention.sqlite3"
    store = SqliteFirstObservationStore(database)
    target = _target()
    expires = NOW + timedelta(days=1)
    source_expires = NOW + timedelta(hours=12)
    assert _complete(
        store,
        target,
        "expiring-report",
        at=NOW,
        retain_until=expires,
        source_expiry=source_expires,
    )

    result = store.purge(now=source_expires)
    assert set(result) == {"siteReadings", "proofs"}
    reopened = SqliteFirstObservationStore(database)
    assert reopened.history("tenant-a", "focus-1", "org-1") == []
    proof = reopened.proof("tenant-a", "focus-1")
    assert proof is not None
    assert proof["publicUnderstanding"] == {
        "reportId": "expiring-report",
        "measuredAt": NOW.isoformat(),
        "validUntil": None,
        "contentExpiresAt": source_expires.isoformat(),
        "instrument": {"ref": "offer-read", "version": "1"},
        "conditions": {"locale": "en"},
        "authority": "DERIVED_CONDITIONED_NOT_CANONICAL",
        "execution": "EVALUATED",
        "coverage": "BOUNDED_COMPLETE",
        "status": "NOT_MEASURED",
        "cause": "CONTENT_EXPIRED",
        "currentness": "EXPIRED",
        "citations": [],
        "dimensions": [],
    }
    assert "private quote" not in str(proof)
    assert proof["retainUntil"] == expires.isoformat()

    final_result = reopened.purge(now=expires)
    assert final_result["proofs"] == 1
