"""TASK-050 T022-T024 end to end through the real composition and the T12 runtime.

Principal → Tenant → Focus → canonical Organization → governed observations → Brain
snapshot S1 → checkpoint → dependency change → invalidation → recompute owed → restart
→ the existing tick/RecomputationPort → S2 → semantic delta → authorized read.
And: two Tenants, one Organization, one fenced shared execution, isolated continuity.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from application.economic_discovery.batch_research import (
    claim_research_batch,
    complete_research_batch,
)
from application.economic_discovery.continuous_observation import (
    SharedObservationIntent,
    opaque_requester_ref,
)
from application.xeed_access.reader import TrustedRequestContext, XeedReadError
from domain.identity import XeedId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory
from pipeline.observation_intelligence import TedSearchAdapter
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from tests.integration.test_subscriber_composition import (
    _append_opportunity_capability_source,
    _build,
    _commit_verified_projection,
    _register_canonical_organization,
    _signup,
)
from tests.observation_intelligence.scenarios import AS_OF, HOMEPAGES
from tests.observation_runtime.harness import CountingTed
from tests.subscriber_continuity.harness import observation
from tools.runtime.observation_daily import ObservationEnrollment, build_economic_runtime, run_once

ORGANIZATION = "org:registry:shared"
HOMEPAGE = "https://solartec.example/"


class _Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def _subscriber(facade: Any, tmp_path: Path, subject: str, ref: str) -> ObservationEnrollment:
    token, tenant_id = _signup(facade, subject)
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    _commit_verified_projection(billing, tenant_id, now=datetime.now(AS_OF.tzinfo))
    added = facade.handle(
        "POST",
        "/subscriber/portfolio",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
        {"action": "add", "requestRef": ref, "locator": "Shared Registry Example SLU"},
    )
    assert added.status == 200, added.body
    member = facade.identity.authenticate(token)
    return ObservationEnrollment(
        TrustedRequestContext(member.principal_id, member.tenant_id),
        XeedId(str(added.body["focusId"])),
    )


@pytest.fixture
def world(tmp_path: Path):  # type: ignore[no-untyped-def]
    _register_canonical_organization(tmp_path)
    attention = tmp_path / "subscriber-observation-plan.json"
    attention.write_text(
        '[{"organizationId":"org:registry:shared","markets":'
        '[{"jurisdiction":"EU/ES","roles":["PUBLIC_BUYERS"]}]}]',
        encoding="utf-8",
    )
    facade = _build(tmp_path)
    _append_opportunity_capability_source(tmp_path)
    clock = _Clock(AS_OF)
    ted = CountingTed()

    def tick(day: int, enrollment: tuple[ObservationEnrollment, ...], economic: Any):  # type: ignore[no-untyped-def]
        clock.current = AS_OF + timedelta(days=day - 1)
        return run_once(
            economic=economic,
            store=SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3"),
            clock=clock,
            attention_file=attention,
            enrollment=enrollment,
            source_ports={"ted-search-v3": TedSearchAdapter(ted, clock=clock.now)},
        )

    return facade, clock, tick


def _changed_homepage(tmp_path: Path, at: datetime) -> None:
    """New governed evidence for the same public page: its content changed."""
    SqliteObservationMemory(tmp_path / "observation-memory.sqlite3").append(
        observation(
            ORGANIZATION,
            "obs:xeed:solartec:homepage:2",
            source_ref=HOMEPAGE,
            observed_at=at,
            content=HOMEPAGES["xeed:solartec"] + " Nueva línea: almacenamiento con baterías.",
        )
    )


def test_dependency_change_recomputes_once_after_restart_and_explains_the_delta(
    tmp_path: Path, world
) -> None:  # type: ignore[no-untyped-def]
    facade, clock, tick = world
    focus = _subscriber(facade, tmp_path, "subject:continuity", "add:continuity")
    economic = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    xeed = economic.authorize(focus.context, focus.focus_id).authorized_xeed.xeed

    # Day 1: the autonomous runtime reaches the Brain; S1 is checkpointed with its support.
    tick(1, (focus,), economic)
    (s1,) = economic.continuity.store.history(xeed.tenant_id, xeed.id)
    assert any(item.kind == "OPPORTUNITY" for item in s1.state.items)
    assert "obs:obs:xeed:solartec:homepage" in {d.key for d in s1.state.dependencies}
    assert s1.state.trace.get("instruments")  # which instrument produced the demand evidence

    # Day 2: nothing changed: no artificial checkpoint or delta.
    tick(2, (focus,), economic)
    assert len(economic.continuity.store.history(xeed.tenant_id, xeed.id)) == 1

    # The page changes (new governed evidence). Invalidation is declared and owed...
    _changed_homepage(tmp_path, AS_OF + timedelta(days=1, hours=12))
    owed = economic.continuity.reconcile(
        xeed.tenant_id,
        xeed.id,
        now=AS_OF + timedelta(days=2),
        owe=SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3"),
    )
    assert owed.statuses["obs:obs:xeed:solartec:homepage"] == "REPLACED"
    assert owed.owed == ("demand",) and owed.delivered == ("demand",)

    # ...and survives a process restart: a new runtime and the next tick recompute it once.
    restarted = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    _report, brain = tick(3, (focus,), restarted)
    assert [o for o in brain.outcomes if o[3].startswith("PROJECTION_RECOMPUTED")]
    history = restarted.continuity.store.history(xeed.tenant_id, xeed.id)
    assert len(history) == 2
    s2 = history[-1]
    assert s2.origin.previous_checkpoint_id == s1.checkpoint_id
    assert "obs:obs:xeed:solartec:homepage:2" in {d.key for d in s2.state.dependencies}
    read = restarted.continuity.read(focus.context, focus.focus_id, as_of=clock.now())
    assert read["currentSupport"]["isCurrent"] is True
    assert read["deltaFromPrevious"]["entries"]  # semantic change, explained
    assert {item["deliveredAt"] is not None for item in read["recompute"]} == {True}
    # History is immutable: S1 is still readable at its own cut.
    assert (
        restarted.continuity.read(focus.context, focus.focus_id, as_of=s1.origin.temporal_cut)[
            "checkpoint"
        ]["checkpointId"]
        == s1.checkpoint_id
    )
    # The authorized subscriber projection reflects the recomputed Brain.
    assert restarted.read(focus.context, focus.focus_id, clock.now()).status.value == "success"

    # Day 4: the debt was paid exactly once.
    _report, brain = tick(4, (focus,), restarted)
    assert not [o for o in brain.outcomes if o[3].startswith("PROJECTION_RECOMPUTED")]
    assert len(restarted.continuity.store.history(xeed.tenant_id, xeed.id)) == 2


def test_two_tenants_share_one_fenced_execution_and_keep_private_continuity(
    tmp_path: Path, world
) -> None:  # type: ignore[no-untyped-def]
    facade, clock, tick = world
    a = _subscriber(facade, tmp_path, "subject:tenant-a", "add:a")
    b = _subscriber(facade, tmp_path, "subject:tenant-b", "add:b")
    economic = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    xa = economic.authorize(a.context, a.focus_id).authorized_xeed.xeed
    xb = economic.authorize(b.context, b.focus_id).authorized_xeed.xeed
    assert xa.organization_id == xb.organization_id == ORGANIZATION and xa.id != xb.id
    tick(1, (a, b), economic)
    store = economic.continuity.store
    (a1,), (b1,) = store.history(xa.tenant_id, xa.id), store.history(xb.tenant_id, xb.id)
    assert a1.checkpoint_id != b1.checkpoint_id  # same evidence, separate continuity

    # Both Foci need the same public research for the same Organization: one work item.
    work = SqliteSharedObservationWorkMemory(tmp_path / "research-work.sqlite3")
    intent = SharedObservationIntent(
        subject_id=ORGANIZATION,
        state_fingerprint="state:homepage:1",
        dimension_id="value",
        missing_requirements=("current-offering",),
        research_policy_id="public-page-research",
        research_policy_version="1",
        research_context_fingerprint="public-web@1",
    )
    assert work.enqueue(intent, opaque_requester_ref("focus", xa.tenant_id, xa.id)) is True
    assert work.enqueue(intent, opaque_requester_ref("focus", xb.tenant_id, xb.id)) is False
    claimed = claim_research_batch(
        work,
        work_keys=(intent.work_key,),
        now=clock.now(),
        lease_for=timedelta(minutes=5),
        max_batch_size=1,
    )
    assert (
        claim_research_batch(
            work,
            work_keys=(intent.work_key,),
            now=clock.now(),
            lease_for=timedelta(minutes=5),
            max_batch_size=1,
        )
        == ()
    )
    _changed_homepage(tmp_path, clock.now() + timedelta(minutes=1))  # the one execution's result
    runtime_store = SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3")
    fanned: list[tuple[str, str]] = []

    def dependents_changed(subject: str, at: datetime) -> None:
        for report in economic.continuity.subject_changed(subject, now=at, owe=runtime_store):
            fanned.append((report.tenant_id, report.xeed_id))

    assert complete_research_batch(
        work,
        claimed=claimed,
        completed_at=clock.now() + timedelta(minutes=2),
        on_subject_changed=dependents_changed,
    ) == (intent.work_key,)
    assert sorted(fanned) == sorted([(xa.tenant_id, xa.id), (xb.tenant_id, xb.id)])

    _report, brain = tick(2, (a, b), economic)
    recomputed = {o[0] for o in brain.outcomes if o[3].startswith("PROJECTION_RECOMPUTED")}
    assert recomputed == {xa.id, xb.id}
    a2, b2 = store.latest(xa.tenant_id, xa.id), store.latest(xb.tenant_id, xb.id)
    assert a2 is not None and b2 is not None
    assert a2.origin.previous_checkpoint_id == a1.checkpoint_id
    assert b2.origin.previous_checkpoint_id == b1.checkpoint_id
    assert a2.checkpoint_id != b2.checkpoint_id

    # No cross-Tenant continuity read; each read carries only its own Focus.
    with pytest.raises(XeedReadError):
        economic.continuity.read(a.context, b.focus_id, as_of=clock.now())
    own = economic.continuity.read(a.context, a.focus_id, as_of=clock.now())
    assert xb.id not in str(own) and xb.tenant_id not in str(own)
