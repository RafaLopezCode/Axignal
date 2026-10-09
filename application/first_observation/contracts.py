"""Contracts of the First Observation loop (spec 063). Operational state, never truth."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from application.first_observation.site import PageReading, RobotsReading

POLICY_VERSION = "first-observation-value-policy.v1"


class TargetKind(StrEnum):
    FOCUS = "FOCUS"
    PENDING = "PENDING"


class IdentityLink(StrEnum):
    """How the observed website relates to the canonical Organization (if any)."""

    REGISTRY_VERIFIED = "REGISTRY_VERIFIED"
    SUBSCRIBER_DIRECTED = "SUBSCRIBER_DIRECTED"
    IDENTITY_PENDING = "IDENTITY_PENDING"
    #: A registry records this website for a different Organization: never observed as it.
    WEBSITE_OF_ANOTHER_ORGANIZATION = "WEBSITE_OF_ANOTHER_ORGANIZATION"


@dataclass(frozen=True, slots=True)
class AttentionTarget:
    """Where a subscriber directed attention. Private; never an Organization."""

    tenant_id: str
    principal_id: str
    target_ref: str
    kind: TargetKind
    website: str | None
    name: str | None
    organization_id: str | None
    identity_link: IdentityLink

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.principal_id.strip():
            raise ValueError("attention target needs its authorized principal and tenant")
        if not self.target_ref.strip():
            raise ValueError("attention target needs a reference")
        if (self.kind is TargetKind.FOCUS) != (self.organization_id is not None):
            raise ValueError("only a Focus target carries a canonical Organization")

    def to_wire(self) -> dict[str, object]:
        return {
            "tenantId": self.tenant_id,
            "principalId": self.principal_id,
            "targetRef": self.target_ref,
            "kind": self.kind.value,
            "website": self.website,
            "name": self.name,
            "organizationId": self.organization_id,
            "identityLink": self.identity_link.value,
        }

    @staticmethod
    def from_wire(raw: Mapping[str, Any]) -> AttentionTarget:
        return AttentionTarget(
            tenant_id=str(raw["tenantId"]),
            principal_id=str(raw["principalId"]),
            target_ref=str(raw["targetRef"]),
            kind=TargetKind(str(raw["kind"])),
            website=None if raw["website"] is None else str(raw["website"]),
            name=None if raw["name"] is None else str(raw["name"]),
            organization_id=None if raw["organizationId"] is None else str(raw["organizationId"]),
            identity_link=IdentityLink(str(raw["identityLink"])),
        )


class JobState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ObservationJob:
    job_id: str
    target: AttentionTarget
    state: JobState
    attempts: int
    created_at: datetime
    lease_token: str | None = None


@dataclass(frozen=True, slots=True)
class SiteReading:
    """World-level reading of one website origin. Shared by every tenant."""

    origin: str
    observed_at: datetime
    robots: RobotsReading | None
    pages: tuple[PageReading, ...]
    failure: str | None = None
    unchanged_streak: int = 0

    @property
    def fingerprint(self) -> str:
        return "|".join(page.content_fingerprint for page in self.pages) or "none"

    def to_wire(self) -> dict[str, object]:
        return {
            "origin": self.origin,
            "observedAt": self.observed_at.isoformat(),
            "robots": None
            if self.robots is None
            else {"text": self.robots.text, "observedAt": self.robots.observed_at.isoformat()},
            "pages": [page.to_wire() for page in self.pages],
            "failure": self.failure,
            "unchangedStreak": self.unchanged_streak,
        }

    @staticmethod
    def from_wire(raw: Mapping[str, Any]) -> SiteReading:
        robots = raw.get("robots")
        return SiteReading(
            origin=str(raw["origin"]),
            observed_at=datetime.fromisoformat(str(raw["observedAt"])),
            robots=None
            if robots is None
            else RobotsReading(
                None if robots["text"] is None else str(robots["text"]),
                datetime.fromisoformat(str(robots["observedAt"])),
            ),
            pages=tuple(PageReading.from_wire(p) for p in raw["pages"]),
            failure=None if raw.get("failure") is None else str(raw["failure"]),
            unchanged_streak=int(raw.get("unchangedStreak", 0)),
        )


class CostBasis(StrEnum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    VENDOR_PUBLISHED = "VENDOR_PUBLISHED"
    OPERATOR_CONFIGURED = "OPERATOR_CONFIGURED"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class RunLedger:
    """What one job spent and avoided. Counts are measured; money keeps its basis."""

    http_requests: int = 0
    http_bytes: int = 0
    source_requests: int = 0
    source_cache_hits: int = 0
    site_reuse_hits: int = 0
    requests_avoided: int = 0
    jev_calls: int = 0
    jev_input_tokens: int = 0
    jev_tokens_basis: CostBasis = CostBasis.MEASURED
    jev_memory_hits: int = 0
    jev_usd: str | None = None
    jev_usd_basis: CostBasis = CostBasis.UNKNOWN
    luna_calls: int = 0
    luna_usd: str | None = None
    luna_usd_basis: CostBasis = CostBasis.OPERATOR_CONFIGURED
    source_paid_microunits: int = 0
    source_paid_basis: CostBasis = CostBasis.VENDOR_PUBLISHED
    elapsed_ms: int = 0
    decisions: list[str] = field(default_factory=list)

    def decide(self, reason: str) -> None:
        if len(self.decisions) < 64:
            self.decisions.append(reason)

    def to_wire(self) -> dict[str, object]:
        return {
            "httpRequests": {"value": self.http_requests, "basis": "MEASURED"},
            "httpBytes": {"value": self.http_bytes, "basis": "MEASURED"},
            "sourceRequests": {"value": self.source_requests, "basis": "MEASURED"},
            "sourceCacheHits": {"value": self.source_cache_hits, "basis": "MEASURED"},
            "siteReuseHits": {"value": self.site_reuse_hits, "basis": "MEASURED"},
            "requestsAvoided": {"value": self.requests_avoided, "basis": "ESTIMATED"},
            "jevCalls": {"value": self.jev_calls, "basis": "MEASURED"},
            "jevInputTokens": {
                "value": self.jev_input_tokens,
                "basis": self.jev_tokens_basis.value,
            },
            "jevMemoryHits": {"value": self.jev_memory_hits, "basis": "MEASURED"},
            "jevUsd": {"value": self.jev_usd, "basis": self.jev_usd_basis.value},
            "lunaCalls": {"value": self.luna_calls, "basis": "MEASURED"},
            "lunaUsd": {"value": self.luna_usd, "basis": self.luna_usd_basis.value},
            "sourcePaidMicrounits": {
                "value": self.source_paid_microunits,
                "basis": self.source_paid_basis.value,
            },
            "elapsedMs": {"value": self.elapsed_ms, "basis": "MEASURED"},
            "decisions": list(self.decisions),
            "policyVersion": POLICY_VERSION,
        }


class ObservationState(StrEnum):
    """Subscriber-facing state, derived from what actually happened."""

    OBSERVATION_DISABLED = "OBSERVATION_DISABLED"
    QUEUED = "QUEUED"
    OBSERVING_PUBLIC_PRESENCE = "OBSERVING_PUBLIC_PRESENCE"
    FIRST_PROOF_READY = "FIRST_PROOF_READY"
    NOT_ENOUGH_CAPABILITY_EVIDENCE = "NOT_ENOUGH_CAPABILITY_EVIDENCE"
    NO_PUBLIC_WEBSITE = "NO_PUBLIC_WEBSITE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    CAPACITY_REQUIRED = "CAPACITY_REQUIRED"
    OBSERVATION_FAILED = "OBSERVATION_FAILED"


class DiscoveryKind(StrEnum):
    PUBLIC_PRESENCE = "PUBLIC_PRESENCE"
    ACTIVITY = "ACTIVITY"
    DECLARED_LOCATION = "DECLARED_LOCATION"
    DECLARED_SERVICE_AREA = "DECLARED_SERVICE_AREA"
    LANGUAGES = "LANGUAGES"
    WEB_REPRESENTATION = "WEB_REPRESENTATION"
    REPRESENTATION_GAP = "REPRESENTATION_GAP"
    IDENTITY_HINT = "IDENTITY_HINT"
    DEMAND = "DEMAND"
    SIGNIFICANT_UNKNOWN = "SIGNIFICANT_UNKNOWN"


@dataclass(frozen=True, slots=True)
class Discovery:
    """One evidence-backed statement for the subscriber, or a grounded UNKNOWN."""

    kind: DiscoveryKind
    code: str
    statement: str
    epistemic_state: str
    source_url: str | None
    excerpt: str | None
    observed_at: datetime | None
    detail: Mapping[str, object] = field(default_factory=dict)

    def to_wire(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "code": self.code,
            "statement": self.statement,
            "epistemicState": self.epistemic_state,
            "sourceUrl": self.source_url,
            "excerpt": self.excerpt,
            "observedAt": None if self.observed_at is None else self.observed_at.isoformat(),
            "detail": dict(self.detail),
        }


@dataclass(frozen=True, slots=True)
class FirstProof:
    target: AttentionTarget
    state: ObservationState
    ready: bool
    discoveries: tuple[Discovery, ...]
    attention_scopes: tuple[tuple[str, tuple[str, ...]], ...]
    capabilities: tuple[Mapping[str, object], ...]
    site_fingerprint: str | None
    ledger: Mapping[str, object]
    judged: Mapping[str, str]
    observed_at: datetime
    next_due_at: datetime | None

    def to_wire(self) -> dict[str, object]:
        return {
            "target": self.target.to_wire(),
            "state": self.state.value,
            "firstProofReady": self.ready,
            "discoveries": [d.to_wire() for d in self.discoveries],
            "attentionScopes": [
                {"jurisdiction": code, "roles": list(roles), "epistemicState": "POTENTIAL"}
                for code, roles in self.attention_scopes
            ],
            "capabilities": [dict(c) for c in self.capabilities],
            "siteFingerprint": self.site_fingerprint,
            "ledger": dict(self.ledger),
            "judged": dict(self.judged),
            "observedAt": self.observed_at.isoformat(),
            "nextDueAt": None if self.next_due_at is None else self.next_due_at.isoformat(),
            "authority": "OPERATIONAL_NOT_CANONICAL",
        }


def summarize(discoveries: Sequence[Discovery]) -> dict[str, int]:
    out: dict[str, int] = {}
    for discovery in discoveries:
        out[discovery.kind.value] = out.get(discovery.kind.value, 0) + 1
    return out
