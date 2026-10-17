"""A block on AXIGNAL's own context is retried on the next tick; a missing source waits.

Found on the biocultor.com canary (2026-10-17): demand leads blocked because the capability
context had not reached the tick were parked for 30 days, like a source that does not exist.
"""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from application.observation_intelligence import SourceRegistry
from application.observation_runtime import ObservationFamily, run_daily_tick
from application.observation_runtime.families import FAMILY_POLICIES
from application.observation_runtime.ports import Acquisition
from application.observation_runtime.tick import CONTEXT_RECHECK
from tests.observation_runtime.harness import ATTENTION, DAY_1, world


@pytest.mark.parametrize(
    ("blocked", "recheck"),
    [
        ("NO_OBSERVED_CAPABILITY_CONTEXT", CONTEXT_RECHECK),
        ("RIGHTS_REVOKED", FAMILY_POLICIES[ObservationFamily.VALUE].blocked_recheck),
    ],
)
def test_own_context_blocks_recheck_tomorrow_and_world_blocks_wait(
    tmp_path: Path, blocked: str, recheck: timedelta
) -> None:
    w = world(tmp_path)
    source = replace(SourceRegistry().get("official-public-website"), cost_per_request_microunits=0)

    class Blocked:
        def acquisition_key(self, request):  # type: ignore[no-untyped-def]
            return "synthetic:blocked"

        def worst_case_requests(self, request):  # type: ignore[no-untyped-def]
            return 1

        def acquire(self, request):  # type: ignore[no-untyped-def]
            return Acquisition(0, 0, 1, blocked=blocked)

    run_daily_tick(
        store=w.store(), now=DAY_1, attention=ATTENTION,
        acquirers={source.source_id: Blocked()}, recompute=w.downstream,
        policies={ObservationFamily.VALUE: FAMILY_POLICIES[ObservationFamily.VALUE]},
        registry=SourceRegistry((source,)),
    )  # fmt: skip
    parked = [lead for lead in w.store().leads() if lead.blocked_reason == blocked]
    assert parked and all(lead.next_due_at == DAY_1 + recheck for lead in parked)
    assert FAMILY_POLICIES[ObservationFamily.VALUE].blocked_recheck > CONTEXT_RECHECK


def test_a_context_block_parked_for_a_month_by_older_code_is_due_now(tmp_path: Path) -> None:
    from application.observation_runtime.frontier import LeadStatus

    w = world(tmp_path)
    source = replace(SourceRegistry().get("official-public-website"), cost_per_request_microunits=0)

    class Blocked:
        def acquisition_key(self, request):  # type: ignore[no-untyped-def]
            return "synthetic:blocked"

        def worst_case_requests(self, request):  # type: ignore[no-untyped-def]
            return 1

        def acquire(self, request):  # type: ignore[no-untyped-def]
            return Acquisition(0, 0, 1, blocked="RIGHTS_REVOKED")

    run_daily_tick(
        store=w.store(), now=DAY_1, attention=ATTENTION,
        acquirers={source.source_id: Blocked()}, recompute=w.downstream,
        policies={ObservationFamily.VALUE: FAMILY_POLICIES[ObservationFamily.VALUE]},
        registry=SourceRegistry((source,)),
    )  # fmt: skip
    (lead,) = [x for x in w.store().leads() if x.status is LeadStatus.BLOCKED][:1]
    tomorrow = DAY_1 + timedelta(days=1)
    assert not lead.due(tomorrow)  # a refused source waits its recheck
    old = replace(lead, blocked_reason="NO_OBSERVED_CAPABILITY_CONTEXT")  # parked a month
    assert old.due(tomorrow)
