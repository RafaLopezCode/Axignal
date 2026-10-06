"""Compile real opportunity-loop output into subscriber-safe cognitive facts.

The adapter preserves the source observation and the capability observation as
separate bases. It never turns a candidate into an observed relationship.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.observation_reuse import ReusePurpose
from application.observation_intelligence.contracts import (
    AdoptionStatus,
    CapabilityHypothesis,
    EvidenceRef,
    MarketRole,
    OpportunityFamily,
    RightsStatus,
    XeedObservationContext,
)
from application.observation_intelligence.coverage import CoverageState, EvidenceCoverageMap
from application.observation_intelligence.human import (
    FindingLine,
    HumanObservationBrief,
    build_brief,
)
from application.observation_intelligence.loop import LoopResult, LoopStep, OpportunityCandidate
from application.observation_intelligence.registry import SourceRegistry
from application.observation_intelligence.strategy import ObservationStrategy
from application.xeed_access.organization_reader import AuthorizedXeedOrganization
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState

_CURRENTNESS_ORDER = {
    Currentness.CURRENT: 0,
    Currentness.STALE: 1,
    Currentness.HISTORICAL: 2,
    Currentness.UNKNOWN: 3,
}


class SubscriberOpportunityProjectionError(ValueError):
    """An opportunity cannot be safely bound to this authorized projection."""


@dataclass(frozen=True, slots=True)
class SubscriberOpportunityProjection:
    tenant_id: str
    xeed_id: str
    organization_id: str
    projection_id: str
    as_of: datetime
    cognition: dict[str, object]

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.tenant_id, self.xeed_id, self.organization_id, self.projection_id)
        ):
            raise SubscriberOpportunityProjectionError("projection identity is required")
        if self.as_of.tzinfo is None:
            raise SubscriberOpportunityProjectionError("projection time must be timezone-aware")
        opportunities = self.cognition.get("opportunities")
        sources = self.cognition.get("sources")
        signals = self.cognition.get("signals")
        if not isinstance(opportunities, list) or not isinstance(sources, list):
            raise SubscriberOpportunityProjectionError("cognition collections are required")
        if not isinstance(signals, list):
            raise SubscriberOpportunityProjectionError("cognition signals are required")
        if not opportunities:
            raise SubscriberOpportunityProjectionError("at least one opportunity is required")


def _safe_public_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return bool(
            parsed.scheme == "https"
            and parsed.hostname
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        return False


def _effective_currentness(
    left: Currentness,
    right: Currentness,
) -> Currentness:
    return max((left, right), key=_CURRENTNESS_ORDER.__getitem__)


def _finding_pairs(*, brief: HumanObservationBrief, result: LoopResult) -> dict[str, FindingLine]:
    """Pair the human finding with its candidate in the family-preserving order."""
    pairs: dict[str, FindingLine] = {}
    cards = {card.family: card for card in brief.cards}
    for family in OpportunityFamily:
        candidates = [item for item in result.candidates if item.opportunity_family is family]
        card = cards.get(family)
        findings = () if card is None else card.findings
        if len(candidates) != len(findings):
            raise SubscriberOpportunityProjectionError(
                "human brief findings do not match LoopResult candidate identities"
            )
        for candidate, finding in zip(candidates, findings, strict=True):
            pairs[candidate.candidate_id] = finding
    return pairs


def _capability_for(
    candidate: OpportunityCandidate, context: XeedObservationContext
) -> CapabilityHypothesis | None:
    by_id = {item.capability_id: item for item in context.capabilities}
    searched_for = next(
        (
            reason.split(":", 1)[1]
            for reason in candidate.why_looked
            if reason.startswith("XEED_CAPABILITY:")
        ),
        None,
    )
    capability_id = (
        searched_for if searched_for in candidate.capability_ids else candidate.capability_ids[0]
    )
    return by_id.get(capability_id)


def _authorized_basis(
    *,
    candidate: OpportunityCandidate,
    context: XeedObservationContext,
    organization_id: str,
    observations: tuple[tuple[GovernedObservation, Currentness], ...],
) -> tuple[EvidenceRef, Currentness] | None:
    capability = _capability_for(candidate, context)
    if capability is None or not capability.basis:
        return None
    datum = capability.basis[0]
    for observation, currentness in observations:
        record = observation.record
        authority = observation.reuse_authority
        if (
            record.observation_id == datum.observation_id
            and record.source_ref == datum.source_ref
            and record.observed_at == datum.observed_at
            and record.subject_id == organization_id
            and record.observed_at <= context.as_of
            and authority.rights_status is ObservationRightsStatus.PERMITTED
            and authority.access_status is ObservationAccessStatus.ACCESSIBLE
            and authority.scope is ObservationReuseScope.GLOBAL_PUBLIC
            and organization_id in authority.applicable_subject_ids
            and ReusePurpose.HISTORICAL_REFERENCE.value in authority.applicable_purposes
            and authority.provenance_ref is not None
            and observation.raw_content is not None
            and datum.excerpt in observation.raw_content
        ):
            return datum, currentness
    return None


def _candidate_step(candidate: OpportunityCandidate, result: LoopResult) -> LoopStep | None:
    action_id = next(
        (
            reason.removeprefix("ACTION:")
            for reason in candidate.why_looked
            if reason.startswith("ACTION:")
        ),
        None,
    )
    return next(
        (step for step in result.steps if step.action.action_id == action_id),
        None,
    )


def _coverage_currentness(
    *,
    candidate: OpportunityCandidate,
    result: LoopResult,
    coverage: EvidenceCoverageMap,
    as_of: datetime,
) -> Currentness:
    step = _candidate_step(candidate, result)
    if step is None:
        return Currentness.UNKNOWN
    entry = coverage.entry(step.action.question_id, step.action.market)
    if (
        entry is None
        or candidate.record.record_id not in entry.evidence_ids
        or step.action.source_id not in entry.searched_sources
    ):
        return Currentness.UNKNOWN
    state = coverage.state(step.action.question_id, step.action.market, as_of=as_of)
    return {
        CoverageState.OBSERVED_CURRENT: Currentness.CURRENT,
        CoverageState.STALE: Currentness.STALE,
        CoverageState.SEARCHED_NO_EVIDENCE: Currentness.UNKNOWN,
        CoverageState.UNKNOWN: Currentness.UNKNOWN,
    }[state]


def project_observation_opportunities(
    *,
    authorized_context: AuthorizedXeedOrganization,
    context: XeedObservationContext,
    strategy: ObservationStrategy,
    result: LoopResult,
    coverage: EvidenceCoverageMap,
    observations: tuple[tuple[GovernedObservation, Currentness], ...],
    registry: SourceRegistry | None = None,
) -> SubscriberOpportunityProjection | None:
    """Build cognition opportunities only from this focus and admitted provenance."""
    if not isinstance(authorized_context, AuthorizedXeedOrganization):
        raise SubscriberOpportunityProjectionError("authorized Observation Focus context required")
    xeed = authorized_context.authorized_xeed.xeed
    organization = authorized_context.organization
    if context.xeed_id != xeed.id or strategy.xeed_id != xeed.id or result.xeed_id != xeed.id:
        raise SubscriberOpportunityProjectionError(
            "LoopResult, strategy and context must match the authorized Observation Focus"
        )
    if strategy.as_of != context.as_of:
        raise SubscriberOpportunityProjectionError("strategy and observation context time differ")
    if organization.id != xeed.organization_id:
        raise SubscriberOpportunityProjectionError("authorized Organization binding is invalid")

    registry = registry or SourceRegistry()
    for candidate in result.candidates:
        if candidate.xeed_id != xeed.id:
            raise SubscriberOpportunityProjectionError("candidate belongs to another focus")
        if candidate.epistemic_state is XignalEpistemicState.OBSERVED:
            raise SubscriberOpportunityProjectionError("opportunity candidate cannot be OBSERVED")
        try:
            registry.get(candidate.record.source_id)
        except KeyError as error:
            raise SubscriberOpportunityProjectionError(
                "candidate source is not registered"
            ) from error
    brief = build_brief(
        context=context,
        strategy=strategy,
        result=result,
        coverage=coverage,
        registry=registry,
    )
    findings = _finding_pairs(brief=brief, result=result)
    output_as_of = max((context.as_of, *(item.observed_at for item in result.candidates)))
    source_rows: list[dict[str, object]] = []
    opportunities: list[dict[str, object]] = []
    signals: list[dict[str, str]] = []
    for candidate in result.candidates:
        try:
            source = registry.get(candidate.record.source_id)
        except KeyError:
            continue
        if (
            candidate.record.kind not in source.capabilities
            or not source.covers(candidate.market)
            or not any(
                candidate.market.within(market.geography)
                and MarketRole.PUBLIC_BUYERS in market.roles
                for market in context.markets
            )
            or not any(place.within(candidate.market) for place in candidate.record.places)
        ):
            continue
        if (
            not source.routable
            or source.adoption is not AdoptionStatus.ADOPTED
            or source.rights is not RightsStatus.REUSE_DOCUMENTED
            or not _safe_public_url(candidate.record.source_url)
        ):
            # Unsupported provenance means no subscriber-visible opportunity.
            continue
        basis = _authorized_basis(
            candidate=candidate,
            context=context,
            organization_id=organization.id,
            observations=observations,
        )
        if basis is None:
            continue
        capability_datum, capability_currentness = basis
        capability = _capability_for(candidate, context)
        if capability is None:
            continue
        finding = findings[candidate.candidate_id]
        step = _candidate_step(candidate, result)
        if (
            step is None
            or step.action.source_id != candidate.record.source_id
            or step.action.market != candidate.market
            or candidate.record.kind not in step.action.query.capabilities
        ):
            continue
        looked = (
            (brief.why_we_looked[result.steps.index(step)],)
            if step is not None and step in result.steps
            else ()
        )
        demand_currentness = _coverage_currentness(
            candidate=candidate,
            result=result,
            coverage=coverage,
            as_of=output_as_of,
        )
        currentness = _effective_currentness(capability_currentness, demand_currentness)
        source_id = f"opportunity-evidence:{candidate.record.record_id}"
        if any(
            source_id == observation.record.observation_id
            for observation, _currentness in observations
        ):
            # The demand source namespace must never shadow a distinct observation.
            continue
        source_rows.append(
            {
                "id": source_id,
                "title": candidate.record.title,
                "observedAt": candidate.observed_at.isoformat(),
                "currentness": demand_currentness.value,
                "currentnessEvaluatedAt": output_as_of.isoformat(),
                "instrument": f"{source.source_id}@{source.version}",
                "limitation": "; ".join(
                    (
                        *source.scope_limitations,
                        "A published demand record or buyer name does not establish a relationship, customer or commercial fit.",
                    )
                ),
                "sourceRef": candidate.record.source_url,
                "provenanceRef": candidate.record.record_id,
            }
        )
        code = candidate.matched_codes[0]
        unknowns = list(candidate.missing_context)
        if currentness is not Currentness.CURRENT:
            unknowns.append("Supporting source currentness is not established as current.")
        opportunities.append(
            {
                "id": candidate.candidate_id,
                "familyId": "demand",
                "opportunityFamily": candidate.opportunity_family.value,
                "title": candidate.record.title,
                "buyer": candidate.record.buyer_name,
                "market": candidate.market.code,
                "form": candidate.demand_form,
                "deadline": candidate.record.deadline,
                "epistemic": (
                    candidate.epistemic_state.value
                    if currentness is Currentness.CURRENT
                    else XignalEpistemicState.UNKNOWN.value
                ),
                "capability": {
                    "label": capability.label,
                    "excerpt": capability_datum.excerpt,
                    "sourceId": capability_datum.observation_id,
                },
                "demand": {
                    "label": candidate.record.title,
                    "code": code.code,
                    "sourceId": source_id,
                },
                "known": [
                    {"label": "Published demand title", "value": candidate.record.title},
                    *(
                        {"label": "Matched demand code", "value": item.code}
                        for item in candidate.matched_codes
                    ),
                ],
                "unknown": list(dict.fromkeys(unknowns)),
                "whyPotential": finding.why,
                "whyLooked": list(looked),
                "observedAt": candidate.observed_at.isoformat(),
                "currentness": currentness.value,
                "currentnessEvaluatedAt": output_as_of.isoformat(),
                "matchBasis": list(candidate.match_basis),
            }
        )
        signals.append({"id": candidate.candidate_id, "familyId": "demand"})

    if not opportunities:
        return None
    source_rows.sort(key=lambda item: str(item["id"]))
    opportunities.sort(key=lambda item: (str(item["observedAt"]), str(item["id"])))
    signals.sort(key=lambda item: item["id"])
    payload: dict[str, object] = {
        "asOf": output_as_of.isoformat(),
        "sources": source_rows,
        "signals": signals,
        "opportunities": opportunities,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    projection_id = "opportunity-projection:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return SubscriberOpportunityProjection(
        tenant_id=xeed.tenant_id,
        xeed_id=xeed.id,
        organization_id=organization.id,
        projection_id=projection_id,
        as_of=output_as_of,
        cognition=payload,
    )
