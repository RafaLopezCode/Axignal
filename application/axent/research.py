"""Private research lifecycle linked to existing T12 leads; no acquisition authority."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol

from application.axent.grounded.answer import ResearchRequest
from application.axent.grounded.corpus import AuthorizedCorpus
from application.axent.grounded.intent import QuestionKind
from application.economic_discovery.continuous_observation import (
    ObservationWorkState,
    SharedObservationWorkMemory,
    opaque_requester_ref,
)
from application.observation_runtime.frontier import LeadOutcome, ResearchLead
from application.observation_runtime.ports import TickClaim
from application.observation_runtime.tick import TickReport

MAX_ATTEMPTS = 3
COOLDOWN = timedelta(days=1)
REQUEST_TTL = timedelta(days=7)
MAX_SELECTED_PER_TICK = 40


@dataclass(frozen=True)
class ResearchState:
    request: ResearchRequest
    status: str = "PENDING"
    attempts: int = 0
    last_attempt: datetime | None = None
    next_eligible: datetime | None = None
    outcome: str | None = None
    work_ids: tuple[str, ...] = ()
    evidence_keys: tuple[str, ...] = ()
    shared_work_key: str | None = None


class ResearchLedger(Protocol):
    def eligible(self, now: datetime) -> tuple[ResearchState, ...]: ...

    def save(self, state: ResearchState, claim: TickClaim, *, now: datetime) -> None:
        """Persist only while the existing tick owns its live fencing token."""


@dataclass
class ResearchConsumer:
    ledger: ResearchLedger
    # Composition must recheck membership, entitlement, Focus, and canonical subject.
    corpus_for: Callable[[ResearchRequest, datetime], AuthorizedCorpus | None]
    evidence_for: Callable[[tuple[str, ...]], tuple[str, ...]] = lambda _: ()
    shared: SharedObservationWorkMemory | None = None
    # Only a server-owned resolver may identify compatible EB-07 work. No model input.
    shared_key_for: Callable[[ResearchRequest], str | None] = lambda _: None

    def prepare(
        self, claim: TickClaim, now: datetime, leads: tuple[ResearchLead, ...]
    ) -> frozenset[tuple[str, str]]:
        """Bind bounded private attention to governed leads, preserving their cadence."""
        selected: dict[tuple[str, str], int] = {}
        tenants: dict[str, int] = {}
        organizations: dict[tuple[str, str], int] = {}
        waiting: set[tuple[str, str]] = set()
        for state in self.ledger.eligible(now):
            item = state.request
            outcome = None
            corpus = self.corpus_for(item, now)
            if (
                corpus is None
                or corpus.organization_id != item.organization_id
                or corpus.tenant_id != item.tenant_id
                or corpus.xeed_id != item.xeed_id
            ):
                outcome = "STOPPED_AUTHORIZATION"
            elif (
                not item.dependency_fingerprint
                or item.family is None
                or item.question_kind not in {kind.value for kind in QuestionKind}
            ):
                outcome = "STOPPED_UNSUPPORTED_SCOPE"
            elif now >= item.created_at + REQUEST_TTL or item.created_at > now:
                outcome = "STOPPED_EXPIRED"
            else:
                if corpus.dependency_fingerprint != item.dependency_fingerprint:
                    # The original cut was superseded. No inference that the new state answers it.
                    outcome = "OBSOLETE"
                elif state.attempts >= MAX_ATTEMPTS:
                    outcome = "STOPPED_ATTEMPT_BOUND"
            if outcome is not None:
                self.ledger.save(
                    replace(
                        state,
                        status="STOPPED" if outcome.startswith("STOPPED") else outcome,
                        outcome=outcome,
                    ),
                    claim,
                    now=now,
                )
                continue
            scope = (item.tenant_id, item.xeed_id)
            global_scope = (item.organization_id, str(item.family))
            if (
                selected.get(scope, 0) >= 1
                or organizations.get(global_scope, 0) >= 4
                or tenants.get(item.tenant_id, 0) >= 4
            ):
                continue
            linked = tuple(
                lead.lead_id
                for lead in leads
                if lead.xeed_id == item.xeed_id
                and lead.family == item.family
                and lead.depth == 0
                and (
                    not item.geographies
                    or (lead.geography is not None and lead.geography.code in item.geographies)
                )
            )
            if not linked:
                self.ledger.save(
                    replace(state, status="STOPPED", outcome="STOPPED_NO_AUTHORIZED_TARGET"),
                    claim,
                    now=now,
                )
                continue
            selected[scope] = selected.get(scope, 0) + 1
            tenants[item.tenant_id] = tenants.get(item.tenant_id, 0) + 1
            organizations[global_scope] = organizations.get(global_scope, 0) + 1
            shared_key = self.shared_key_for(item)
            if self.shared is not None and shared_key is not None:
                work = self.shared.get(shared_key)
                authority = self.shared.prime_authority(item.organization_id)
                if (
                    work is not None
                    and work.intent.subject_id == item.organization_id
                    and authority is not None
                    and authority.valid_until > now
                    and authority.state_fingerprint == work.intent.state_fingerprint
                    and shared_key in authority.authorized_work_keys
                ):
                    self.shared.enqueue(
                        work.intent,
                        opaque_requester_ref(
                            "axent", item.tenant_id, item.xeed_id, item.request_id
                        ),
                    )
                    if work.state is ObservationWorkState.PENDING:
                        waiting.add((item.xeed_id, str(item.family)))
                        self.ledger.save(
                            replace(
                                state,
                                status="PENDING",
                                work_ids=linked,
                                shared_work_key=shared_key,
                                outcome="WAITING_EXISTING_SHARED_WORK",
                                next_eligible=now + COOLDOWN,
                            ),
                            claim,
                            now=now,
                        )
                        continue
            # CLAIMED is reclaimable with the next live T12 token after a crash.
            self.ledger.save(replace(state, status="CLAIMED", work_ids=linked), claim, now=now)
        return frozenset(waiting)

    def finish(self, claim: TickClaim, now: datetime, report: TickReport) -> None:
        by_id = {e.lead_id: e for e in report.executed}
        for state in self.ledger.eligible(now):
            if state.status != "CLAIMED":
                continue
            linked = set(state.work_ids)
            while True:
                children = {
                    child
                    for key in linked
                    if key in by_id
                    for child in by_id[key].opened
                    if child in by_id
                    and by_id[child].xeed_id == state.request.xeed_id
                    and by_id[child].family == str(state.request.family)
                }
                if children <= linked:
                    break
                linked.update(children)
            results = [by_id[key] for key in sorted(linked) if key in by_id]
            if not results:
                # Budget stop or existing cadence; no child call and no attempt consumed.
                blocked = report.stop_reason.value == "BUDGET_EXHAUSTED" or any(
                    key in dict(report.deferred) for key in state.work_ids
                )
                self.ledger.save(
                    replace(
                        state,
                        status="PENDING",
                        outcome="BUDGET_BLOCKED" if blocked else "CADENCE_WAIT",
                        next_eligible=now + COOLDOWN,
                    ),
                    claim,
                    now=now,
                )
                continue
            if any(e.new_evidence for e in results):
                status, outcome = "OBSERVATION_COMPLETED", "OBSERVATION_COMPLETED"
            elif any(e.outcome is LeadOutcome.FAILED for e in results):
                status, outcome = "FAILED_RETRYABLE", "UNAVAILABLE"
            elif all(e.outcome is LeadOutcome.BLOCKED for e in results):
                reasons = " ".join(reason for e in results for reason in e.why)
                status = "STOPPED"
                outcome = (
                    "BUDGET_BLOCKED"
                    if "COST_UNKNOWN" in reasons
                    else "STOPPED_RIGHTS"
                    if "RIGHTS" in reasons
                    else "STOPPED_SOURCE"
                )
            else:
                status, outcome = "UNRESOLVED", "NO_NEW_EVIDENCE"
            self.ledger.save(
                replace(
                    state,
                    status=status,
                    outcome=outcome,
                    attempts=state.attempts + (0 if outcome == "BUDGET_BLOCKED" else 1),
                    last_attempt=now,
                    work_ids=tuple(sorted(linked)),
                    evidence_keys=self.evidence_for(tuple(sorted(linked))),
                    next_eligible=max(datetime.fromisoformat(e.next_due_at) for e in results),
                ),
                claim,
                now=now,
            )
