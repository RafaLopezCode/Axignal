"""AO-16 deterministic brief composition, review and governed delivery."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol

from application.admin_acquisition.service import AcquisitionStore, reduce_brief_request
from application.admin_integrations.service import AdminIntegrationService, CredentialResolver
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationMemory,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.temporal_currentness import (
    TemporalCurrentnessPolicy,
    evaluate_currentness,
)
from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_acquisition import BriefRequestSnapshot
from domain.admin_integrations import IntegrationEnvironment
from domain.admin_weekly_brief import (
    WeeklyBriefApproval,
    WeeklyBriefCorrection,
    WeeklyBriefDelivery,
    WeeklyBriefIssue,
    WeeklyBriefIssueKind,
    WeeklyBriefItem,
    WeeklyBriefReconstruction,
    evidence_fingerprint,
)


class WeeklyBriefStore(Protocol):
    def put_issue(self, issue: WeeklyBriefIssue) -> bool: ...
    def get_issue(self, issue_id: str) -> WeeklyBriefIssue | None: ...
    def put_approval(self, approval: WeeklyBriefApproval) -> bool: ...
    def get_approval(self, issue_id: str) -> WeeklyBriefApproval | None: ...
    def put_delivery(self, delivery: WeeklyBriefDelivery) -> bool: ...
    def deliveries_for_issue(self, issue_id: str) -> tuple[WeeklyBriefDelivery, ...]: ...
    def put_correction(self, correction: WeeklyBriefCorrection) -> bool: ...
    def corrections_for_issue(self, issue_id: str) -> tuple[WeeklyBriefCorrection, ...]: ...


WEEKLY_BRIEF_PILOT_CURRENTNESS_POLICY = TemporalCurrentnessPolicy(
    policy_id="weekly-brief-currentness",
    version="v1",
    stale_after=timedelta(days=14),
    historical_after=timedelta(days=90),
)


class WeeklyBriefDeliveryProvider(Protocol):
    def send(self, *, recipient_email: str, issue: WeeklyBriefIssue, delivery_id: str) -> str: ...


@dataclass(frozen=True, slots=True)
class MaterialObservationCandidate:
    observation_id: str
    why_may_matter: str
    unknowns: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.why_may_matter.strip():
            raise ValueError("material candidate requires observation and rationale")
        if not self.unknowns or any(not item.strip() for item in self.unknowns):
            raise ValueError("material candidate requires explicit UNKNOWN statements")


@dataclass(frozen=True, slots=True)
class InterpretationDraft:
    observation_id: str
    why_may_matter: str

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.why_may_matter.strip():
            raise ValueError("interpretation draft fields must be non-empty")


def _request_snapshot(store: AcquisitionStore, request_id: str) -> BriefRequestSnapshot:
    events = store.events_for_request(request_id)
    if not events:
        raise LookupError(request_id)
    return reduce_brief_request(events)


def _require_reviewer(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.ACQUISITION_WRITE not in grant.scopes:
        raise PermissionError("weekly brief review requires admin:acquisition:write")
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("weekly brief review requires STEP_UP assurance")


def _observation_summary(observation: GovernedObservation) -> str | None:
    if not observation.fields:
        return None
    return "; ".join(f"{field.name}={field.value}" for field in observation.fields)


def compose_issue(
    *,
    store: WeeklyBriefStore,
    acquisition_store: AcquisitionStore,
    observation_memory: ObservationMemory,
    request_id: str,
    issue_id: str,
    issue_version: str,
    candidates: tuple[MaterialObservationCandidate, ...],
    currentness_policy: TemporalCurrentnessPolicy,
    now: datetime,
    drafts: tuple[InterpretationDraft, ...] = (),
    composition_policy_id: str = "weekly-brief-composition",
    composition_policy_version: str = "v1",
) -> WeeklyBriefIssue:
    request = _request_snapshot(acquisition_store, request_id)
    if not request.delivery_eligible or request.subject_reference is None:
        raise PermissionError("brief request is not eligible for composition")

    observations = {
        item.record.observation_id: item
        for item in observation_memory.for_subject(request.subject_reference)
    }
    selected: list[WeeklyBriefItem] = []
    seen_observations: set[str] = set()
    seen_content: set[str] = set()
    for candidate in candidates:
        if len(selected) == 3:
            break
        observation = observations.get(candidate.observation_id)
        if observation is None or candidate.observation_id in seen_observations:
            continue
        if observation.record.content_fingerprint in seen_content:
            continue
        authority = observation.reuse_authority
        if (
            authority.rights_status is not ObservationRightsStatus.PERMITTED
            or authority.access_status is not ObservationAccessStatus.ACCESSIBLE
            or authority.scope is not ObservationReuseScope.GLOBAL_PUBLIC
            or (
                authority.applicable_subject_ids
                and request.subject_reference not in authority.applicable_subject_ids
            )
            or (
                authority.applicable_purposes
                and "weekly-brief" not in authority.applicable_purposes
            )
        ):
            continue
        decision = evaluate_currentness(observation, as_of=now, policy=currentness_policy)
        if decision.current.value != "CURRENT":
            continue
        summary = _observation_summary(observation)
        if summary is None:
            continue
        selected.append(
            WeeklyBriefItem(
                observation_id=observation.record.observation_id,
                source_ref=observation.record.source_ref,
                observed_at=observation.record.observed_at,
                content_fingerprint=observation.record.content_fingerprint,
                condition=decision.current,
                observation_summary=summary,
                why_may_matter=candidate.why_may_matter.strip(),
                unknowns=tuple(item.strip() for item in candidate.unknowns),
            )
        )
        seen_observations.add(candidate.observation_id)
        seen_content.add(observation.record.content_fingerprint)

    items = tuple(selected)
    issue = WeeklyBriefIssue(
        issue_id=issue_id,
        request_id=request_id,
        subject_reference=request.subject_reference,
        issue_version=issue_version,
        composition_policy_id=composition_policy_id,
        composition_policy_version=composition_policy_version,
        created_at=now,
        kind=(
            WeeklyBriefIssueKind.MATERIAL_CHANGES
            if items
            else WeeklyBriefIssueKind.NO_MATERIAL_CHANGE
        ),
        items=items,
        evidence_fingerprint=evidence_fingerprint(items),
    )
    if drafts:
        issue = apply_interpretation_draft(issue, drafts)
    store.put_issue(issue)
    return issue


def apply_interpretation_draft(
    issue: WeeklyBriefIssue,
    drafts: tuple[InterpretationDraft, ...],
) -> WeeklyBriefIssue:
    """A model may edit only the explicitly interpretive field, never evidence."""
    by_id = {draft.observation_id: draft for draft in drafts}
    if set(by_id) - {item.observation_id for item in issue.items}:
        raise ValueError("draft cannot introduce evidence or an unobserved development")
    items = tuple(
        replace(
            item,
            why_may_matter=(
                by_id[item.observation_id].why_may_matter.strip()
                if item.observation_id in by_id
                else item.why_may_matter
            ),
        )
        for item in issue.items
    )
    return replace(issue, items=items, evidence_fingerprint=evidence_fingerprint(items))


def approve_issue(
    *,
    store: WeeklyBriefStore,
    grant: AdminAuthorizationGrant,
    issue_id: str,
    now: datetime,
) -> WeeklyBriefApproval:
    _require_reviewer(grant)
    if store.get_issue(issue_id) is None:
        raise LookupError(issue_id)
    approval = WeeklyBriefApproval(
        issue_id=issue_id,
        reviewer_principal_id=str(grant.principal_id),
        approved_at=now,
    )
    store.put_approval(approval)
    return approval


def deliver_issue(
    *,
    store: WeeklyBriefStore,
    acquisition_store: AcquisitionStore,
    integration_service: AdminIntegrationService,
    credential_resolver: CredentialResolver,
    provider: WeeklyBriefDeliveryProvider,
    issue_id: str,
    delivery_id: str,
    integration_id: str,
    environment: IntegrationEnvironment,
    now: datetime,
) -> WeeklyBriefDelivery:
    issue = store.get_issue(issue_id)
    if issue is None:
        raise LookupError(issue_id)
    if store.get_approval(issue_id) is None:
        raise PermissionError("weekly brief requires human approval before delivery")
    request = _request_snapshot(acquisition_store, issue.request_id)
    if not request.delivery_eligible:
        raise PermissionError("weekly brief recipient is no longer delivery eligible")

    integration_service.require_connection(
        integration_id=integration_id,
        environment=environment,
        now=now,
        required_scopes=frozenset({"email:send"}),
        credential_resolver=credential_resolver,
    )
    existing_deliveries = store.deliveries_for_issue(issue_id)
    same_delivery = next(
        (item for item in existing_deliveries if item.delivery_id == delivery_id),
        None,
    )
    if same_delivery is not None:
        return same_delivery
    if existing_deliveries:
        raise ValueError("weekly brief issue already delivered")

    provider_message_ref = provider.send(
        recipient_email=request.professional_email,
        issue=issue,
        delivery_id=delivery_id,
    )
    delivery = WeeklyBriefDelivery(
        delivery_id=delivery_id,
        issue_id=issue_id,
        delivered_at=now,
        integration_id=integration_id,
        provider_message_ref=provider_message_ref,
    )
    store.put_delivery(delivery)
    return delivery


def append_correction(
    *,
    store: WeeklyBriefStore,
    grant: AdminAuthorizationGrant,
    correction_id: str,
    issue_id: str,
    reason: str,
    note: str,
    now: datetime,
) -> WeeklyBriefCorrection:
    _require_reviewer(grant)
    if store.get_issue(issue_id) is None:
        raise LookupError(issue_id)
    correction = WeeklyBriefCorrection(
        correction_id=correction_id,
        issue_id=issue_id,
        occurred_at=now,
        actor_principal_id=str(grant.principal_id),
        reason=reason.strip(),
        note=note.strip(),
    )
    store.put_correction(correction)
    return correction


def reconstruct_issue(*, store: WeeklyBriefStore, issue_id: str) -> WeeklyBriefReconstruction:
    issue = store.get_issue(issue_id)
    if issue is None:
        raise LookupError(issue_id)
    return WeeklyBriefReconstruction(
        issue=issue,
        approval=store.get_approval(issue_id),
        deliveries=store.deliveries_for_issue(issue_id),
        corrections=store.corrections_for_issue(issue_id),
    )
