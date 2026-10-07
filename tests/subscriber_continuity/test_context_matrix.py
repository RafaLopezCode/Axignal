"""TASK-050 T024: 1 / 2 / 100 Foci, cross-context isolation, Customer Zero separation."""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from application.xeed_access.reader import TrustedRequestContext, XeedReadError
from domain.identity import OrganizationId, PrincipalId, TenantId
from domain.organizations.model import Organization
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from tests.economic_discovery.test_first_vertical_e2e import _run_fixture
from tests.subscriber_continuity.harness import Auth, observation, runtime, seed_eb04_evidence


@pytest.mark.parametrize("foci", [1, 2, 100])
def test_context_matrix_isolates_private_continuity_over_shared_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, foci: int
) -> None:
    result, *_ = _run_fixture(monkeypatch, tmp_path / "eb04")
    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    org_a_id, _activity = seed_eb04_evidence(result, memory)
    org_a = Organization(OrganizationId(org_a_id), "Arbor Cooling")
    org_b = Organization(OrganizationId("org:unrelated"), "Unrelated SL")
    auth = Auth()
    contexts = [auth.focus(n, org_a if n % 2 == 0 else org_b) for n in range(foci)]
    economic, store = runtime(tmp_path, auth, memory)
    t0 = result.reasoning.vector.evaluated_at
    on_a = [(c, x) for c, x in contexts if x.organization_id == org_a.id]
    on_b = [(c, x) for c, x in contexts if x.organization_id == org_b.id]
    for context, xeed in on_a:
        assert economic.publish(context, xeed.id, result) is True  # same evidence, own snapshot
    for context, xeed in on_b:
        economic.continuity.record(context, xeed.id, as_of=t0)

    # One canonical Organization per subject, one private continuity per Focus.
    checkpoints = {xeed.id: store.history(xeed.tenant_id, xeed.id) for _c, xeed in contexts}
    assert all(len(history) == 1 for history in checkpoints.values())
    assert len({history[0].checkpoint_id for history in checkpoints.values()}) == foci
    assert {
        h[0].origin.organization_id
        for x, h in checkpoints.items()
        if auth.xeeds[x].organization_id == org_a.id
    } <= {org_a.id}
    assert set(store.dependents(org_a.id)) == {(x.tenant_id, x.id) for _c, x in on_a}
    assert set(store.dependents(org_b.id)) == {(x.tenant_id, x.id) for _c, x in on_b}

    # Cross-context reads fail before any private data is loaded (sampled, not N²).
    for index, (context, _xeed) in enumerate(contexts[:5]):
        for _other_context, other in contexts[index + 1 : index + 6]:
            with pytest.raises(XeedReadError):
                economic.continuity.read(context, other.id, as_of=t0)

    # Shared evidence changes for Organization A: only A's dependents are reconciled.
    if on_a:
        (first,) = store.history(on_a[0][1].tenant_id, on_a[0][1].id)
        dependency = first.state.dependencies[0]
        memory.append(
            observation(
                str(dependency.subject_id),
                "replaced:1",
                source_ref=dependency.source_ref,
                observed_at=t0 + timedelta(hours=1),
                content="changed",
            )
        )
        reports = economic.continuity.subject_changed(
            str(dependency.subject_id), now=t0 + timedelta(hours=2)
        )
        assert {(r.tenant_id, r.xeed_id) for r in reports} == {
            (x.tenant_id, x.id) for _c, x in on_a
        }
        assert all(r.statuses[dependency.key] == "REPLACED" for r in reports)
        for _c, xeed in on_b:
            assert (
                store.invalidations(
                    xeed.tenant_id, xeed.id, store.latest(xeed.tenant_id, xeed.id).checkpoint_id
                )
                == ()
            )  # type: ignore[union-attr]

    # The fan-out is an index lookup, not a scan of every Focus.
    with sqlite3.connect(tmp_path / "subscriber-economic-output.sqlite3") as connection:
        plan = " ".join(
            str(row[-1])
            for row in connection.execute(
                "EXPLAIN QUERY PLAN SELECT tenant_id, xeed_id FROM subscriber_continuity_dependents WHERE subject_id=?",
                (org_a.id,),
            )
        )
    assert "USING" in plan and "SCAN subscriber_continuity_dependents" not in plan


def test_customer_zero_is_not_a_subscriber_and_reads_no_private_continuity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, *_ = _run_fixture(monkeypatch, tmp_path / "eb04")
    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    org_id, _ = seed_eb04_evidence(result, memory)
    auth = Auth()
    context, xeed = auth.focus(1, Organization(OrganizationId(org_id), "Arbor Cooling"))
    economic, store = runtime(tmp_path, auth, memory)
    economic.publish(context, xeed.id, result)
    # AXIGNAL observing an Organization (Customer Zero / operator) grants no membership.
    operator = TrustedRequestContext(
        PrincipalId("principal:customer-zero"), TenantId("tenant:axignal")
    )
    auth.principals["principal:customer-zero"] = auth.principals[context.principal_id].__class__(
        PrincipalId("principal:customer-zero")
    )
    for ctx in (
        operator,
        TrustedRequestContext(PrincipalId("principal:customer-zero"), xeed.tenant_id),
    ):
        with pytest.raises(XeedReadError):
            economic.continuity.read(ctx, xeed.id, as_of=result.reasoning.vector.evaluated_at)
    # Customer Zero has no Focus: the dependents index holds only subscriber Foci.
    assert set(store.dependents(org_id)) == {(xeed.tenant_id, xeed.id)}
