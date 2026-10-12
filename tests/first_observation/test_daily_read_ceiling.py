"""The daily ceiling bounds public website reads, not attention that reads nothing.

A target with no website stops at once as NO_PUBLIC_WEBSITE without any request. It must
neither wait for tomorrow behind a spent ceiling nor take the day's only read slot.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.first_observation.contracts import AttentionTarget, IdentityLink, TargetKind
from pipeline.first_observation.sqlite_store import SqliteFirstObservationStore

NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)


def _target(ref: str, website: str | None) -> AttentionTarget:
    return AttentionTarget(
        tenant_id=f"tenant_{ref}",
        principal_id=f"principal_{ref}",
        target_ref=f"pending_{ref}",
        kind=TargetKind.PENDING,
        website=website,
        name=None if website else "Mercadona",
        organization_id=None,
        identity_link=IdentityLink.IDENTITY_PENDING,
    )


def test_offline_attention_runs_after_the_read_ceiling_and_never_spends_it(tmp_path: Path) -> None:
    store = SqliteFirstObservationStore(tmp_path / "first-observation.sqlite3")
    store.enqueue(_target("site", "https://example.org/"), key="a", now=NOW - timedelta(seconds=1))
    store.enqueue(_target("named", None), key="b", now=NOW)
    store.enqueue(
        _target("second-site", "https://example.com/"), key="c", now=NOW + timedelta(seconds=1)
    )

    first = store.claim(now=NOW, lease_seconds=60, max_attempts=3)
    assert first is not None and first.target.website == "https://example.org/"
    assert store.jobs_started_on(NOW.date().isoformat()) == 1

    # The ceiling (1) is spent: only work that reads nothing may still start today.
    offline = store.claim(now=NOW, lease_seconds=60, max_attempts=3, offline_only=True)
    assert offline is not None and offline.target.website is None
    assert store.jobs_started_on(NOW.date().isoformat()) == 1
    # The second website waits for its turn; it is not claimable offline.
    assert store.claim(now=NOW, lease_seconds=60, max_attempts=3, offline_only=True) is None
    later = store.claim(now=NOW, lease_seconds=60, max_attempts=3)
    assert later is not None and later.target.website == "https://example.com/"
    assert store.jobs_started_on(NOW.date().isoformat()) == 2
