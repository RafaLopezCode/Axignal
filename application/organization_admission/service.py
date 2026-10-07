"""Subscriber attention → governed Organization identity (spec 052, ADR-0087).

A subscriber locator only directs attention. This service decides, deterministically,
whether that attention points at an Organization AXIGLAND already admitted, at one an
independent identity source attests well enough to admit now, or at nothing yet:

    locator → canonical index (identifier → website → exact name)
            → otherwise an independent registry source
            → EvidenceAdmission (REGISTRY only) → canonical store (atomic, unique keys)

Models, subscriber text and email never decide. No first match wins; ambiguity and
conflict are terminal states, and UNKNOWN stays pending instead of becoming false.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Protocol

from application.organization_admission.locator import (
    AttentionLocator,
    LocatorError,
    parse_locator,
    public_domain,
)
from application.subscriber_portfolio.models import (
    OrganizationIdentityPending,
    OrganizationIdentityRejected,
    OrganizationResolution,
)
from domain.evidence.admission import (
    AdmissionDecision,
    AdmissionRequest,
    EvidenceAdmission,
    EvidenceAdmissionError,
)
from domain.identity import IdentityBindingAuthority, OrganizationId, identity_name_key
from domain.identity_binding import (
    GovernedIdentityBinding,
    IdentityBindingAdmission,
    IdentityBindingRequest,
)
from domain.organizations.model import Organization
from domain.representation import RepresentationSpan


class AdmissionStatus(StrEnum):
    RESOLVED_EXISTING = "RESOLVED_EXISTING"
    ADMITTED_NEW = "ADMITTED_NEW"
    IDENTITY_PENDING = "IDENTITY_PENDING"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICT = "CONFLICT"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True, slots=True)
class AdmissionOutcome:
    """Inspectable decision. ``reason_code`` is stable and never echoes the input."""

    status: AdmissionStatus
    reason_code: str
    organization: Organization | None = None
    candidate_count: int = 0

    def __post_init__(self) -> None:
        resolved = self.status in (AdmissionStatus.RESOLVED_EXISTING, AdmissionStatus.ADMITTED_NEW)
        if resolved != (self.organization is not None):
            raise ValueError("only a resolved outcome carries an Organization")


def registration_value(scheme: str, authority: str, value: str) -> str:
    """Object of an admitted ``registration`` claim: ``SCHEME|AUTHORITY|VALUE``."""

    return f"{scheme.strip().upper()}|{authority.strip().upper()}|{value.strip()}"


def parse_registration(value: str) -> tuple[str, str, str]:
    parts = value.split("|")
    if len(parts) != 3 or not all(part.strip() for part in parts):
        raise ValueError("registration must be SCHEME|AUTHORITY|VALUE")
    scheme, authority, raw = (part.strip() for part in parts)
    scheme = scheme.upper()
    return scheme, authority.upper(), raw.upper() if scheme == "LEI" else raw


def organization_id_for(scheme: str, authority: str, value: str) -> OrganizationId:
    """Deterministic canonical id from a verified registry identifier.

    Two sources, processes or replays that admit the same registered entity converge
    on one OrganizationId; the store's uniqueness constraints do the rest.
    """

    key = "|".join(parse_registration(registration_value(scheme, authority, value)))
    return OrganizationId("org:id:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:32])


@dataclass(frozen=True, slots=True)
class RegistryIdentityRecord:
    """Propositions one registry record attests, each grounded in that record.

    ``legal_name`` is ``legal_identity``; ``registrations`` are ``registration``
    claims (``SCHEME|AUTHORITY|VALUE``); ``official_websites`` are registry-recorded
    corporate websites. All share one subject. Nothing here is admitted yet.
    """

    legal_name: AdmissionRequest
    registrations: tuple[AdmissionRequest, ...]
    official_websites: tuple[AdmissionRequest, ...] = ()

    @property
    def requests(self) -> tuple[AdmissionRequest, ...]:
        return (self.legal_name, *self.registrations, *self.official_websites)

    @property
    def subject_id(self) -> str:
        return self.legal_name.subject_id


class RegistryLookupStatus(StrEnum):
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class RegistryLookup:
    status: RegistryLookupStatus
    records: tuple[RegistryIdentityRecord, ...] = ()


class RegistryIdentitySource(Protocol):
    """Independent identity source (a registry). Never the subscriber, never a model."""

    def lookup(self, locator: AttentionLocator) -> RegistryLookup: ...


class UnavailableRegistrySource:
    """No governed registry source is configured: identity stays pending (UNKNOWN)."""

    def lookup(self, locator: AttentionLocator) -> RegistryLookup:
        del locator
        return RegistryLookup(RegistryLookupStatus.UNAVAILABLE)


class IdentityConflictError(Exception):
    """Admission would bind a key already held by another identity; nothing is written."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class AdmittedProposition:
    request: AdmissionRequest
    decision: AdmissionDecision


class CanonicalIdentityIndex(Protocol):
    """The canonical Organization store, seen from admission."""

    def organization_by_identifier(
        self, scheme: str, authority: str, value: str
    ) -> OrganizationId | None: ...
    def organization_by_domain(self, domain: str) -> OrganizationId | None: ...
    def organizations_by_name(self, name: str) -> tuple[OrganizationId, ...]: ...
    def get_organization(self, organization_id: OrganizationId) -> Organization | None: ...
    def admit(
        self,
        legal_name: AdmittedProposition,
        registrations: tuple[AdmittedProposition, ...],
        official_websites: tuple[AdmittedProposition, ...],
    ) -> tuple[OrganizationId, bool]:
        """Atomic; returns (id, created). Raises IdentityConflictError on any key clash."""


def _pending(reason: str, count: int = 0) -> AdmissionOutcome:
    return AdmissionOutcome(AdmissionStatus.IDENTITY_PENDING, reason, candidate_count=count)


class OrganizationAdmissionService:
    """Implements the subscriber portfolio's ``OrganizationResolutionPort``."""

    def __init__(self, index: CanonicalIdentityIndex, source: RegistryIdentitySource) -> None:
        self._index = index
        self._source = source

    def resolve(self, locator: str) -> OrganizationResolution:
        outcome = self.decide(locator)
        if outcome.organization is not None:
            return outcome.organization
        if outcome.status is AdmissionStatus.INVALID_INPUT:
            return OrganizationIdentityRejected(outcome.reason_code)
        # AMBIGUOUS and CONFLICT stay pending: unresolved identity is not a false one.
        return OrganizationIdentityPending(
            outcome.reason_code
            if outcome.status is AdmissionStatus.IDENTITY_PENDING
            else f"{outcome.status.value}:{outcome.reason_code}"
        )

    def decide(self, raw: str) -> AdmissionOutcome:
        try:
            locator = parse_locator(raw)
        except LocatorError as exc:
            return AdmissionOutcome(AdmissionStatus.INVALID_INPUT, exc.code)
        known = self._known(locator)
        if known is not None:
            return known
        return self._intake(locator)

    def _resolved(
        self, organization_id: OrganizationId, status: AdmissionStatus
    ) -> AdmissionOutcome:
        organization = self._index.get_organization(organization_id)
        if organization is None:
            # Topology/integrity revalidation pending: do not hand out the identity.
            return _pending("IDENTITY_REVALIDATION_REQUIRED")
        return AdmissionOutcome(status, "CANONICAL_IDENTITY", organization, 1)

    def _known(self, locator: AttentionLocator) -> AdmissionOutcome | None:
        strong: list[OrganizationId | None] = []
        if locator.identifier is not None:
            item = locator.identifier
            strong.append(
                self._index.organization_by_identifier(item.scheme, item.authority, item.value)
            )
        if locator.domain is not None:
            strong.append(self._index.organization_by_domain(locator.domain))
        by_name = self._index.organizations_by_name(locator.name) if locator.name else ()
        found = {item for item in strong if item is not None}
        if len(found) > 1:
            return AdmissionOutcome(AdmissionStatus.CONFLICT, "IDENTITY_SIGNALS_DISAGREE")
        if found:
            (organization_id,) = found
            if None in strong:
                # Every verified key supplied must be known and agree (ADR-0049).
                return _pending("PARTIAL_IDENTITY_MATCH")
            if by_name and organization_id not in by_name:
                return AdmissionOutcome(
                    AdmissionStatus.CONFLICT, "NAME_BELONGS_TO_ANOTHER_ORGANIZATION"
                )
            return self._resolved(organization_id, AdmissionStatus.RESOLVED_EXISTING)
        if strong:
            return None  # verified keys unknown to AXIGLAND: ask the independent source
        if len(by_name) == 1:
            return self._resolved(by_name[0], AdmissionStatus.RESOLVED_EXISTING)
        if len(by_name) > 1:
            return AdmissionOutcome(
                AdmissionStatus.AMBIGUOUS, "NAME_MATCHES_SEVERAL_ORGANIZATIONS", None, len(by_name)
            )
        return None

    def _intake(self, locator: AttentionLocator) -> AdmissionOutcome:
        try:
            lookup = self._source.lookup(locator)
        except Exception:  # any source failure is UNKNOWN, never an answer
            return _pending("IDENTITY_SOURCE_UNAVAILABLE")
        if lookup.status is RegistryLookupStatus.UNAVAILABLE:
            return _pending("IDENTITY_SOURCE_UNAVAILABLE")
        subjects = {record.subject_id for record in lookup.records}
        if lookup.status is RegistryLookupStatus.NOT_FOUND or not subjects:
            return _pending("NOT_FOUND_IN_IDENTITY_SOURCE")
        if len(subjects) > 1:
            return AdmissionOutcome(
                AdmissionStatus.AMBIGUOUS,
                "SOURCE_RETURNED_SEVERAL_IDENTITIES",
                None,
                len(subjects),
            )
        record = lookup.records[0]
        reason = _attestation_gap(record, locator)
        if reason is not None:
            return _pending(reason)
        prepared = prepare_admission(record)
        if prepared is None:
            return _pending("IDENTITY_EVIDENCE_NOT_ADMITTED")
        try:
            organization_id, created = self._index.admit(*prepared)
        except IdentityConflictError as exc:
            return AdmissionOutcome(AdmissionStatus.CONFLICT, exc.code)
        except (ValueError, EvidenceAdmissionError):
            # Integrity or authority refusal by the store: nothing written, still unknown.
            return _pending("IDENTITY_ADMISSION_REFUSED")
        return self._resolved(
            organization_id,
            AdmissionStatus.ADMITTED_NEW if created else AdmissionStatus.RESOLVED_EXISTING,
        )


BINDING_POLICY = "registry-identifier-binding:v1"

PreparedAdmission = tuple[
    AdmittedProposition, tuple[AdmittedProposition, ...], tuple[AdmittedProposition, ...]
]


def prepare_admission(record: RegistryIdentityRecord) -> PreparedAdmission | None:
    """Bind and admit every proposition of a record, or nothing (None).

    The canonical store accepts only what this returns: each proposition carries the
    control plane's deterministic identity binding and an EvidenceAdmission decision.
    """

    if not record.registrations:
        return None
    try:
        identifiers = {parse_registration(item.object_or_value) for item in record.registrations}
    except ValueError:
        return None
    if record.subject_id != organization_id_for(*min(identifiers)):
        # The binding below is only valid for the id derived from the registry key.
        return None
    identifier_values = {value for _, _, value in identifiers}
    admitted: list[AdmittedProposition] = []
    for proposed in record.requests:
        request = _bound(proposed, identifier_values)
        if request is None:
            return None
        decision = EvidenceAdmission.admit_claim(request)
        if not decision.is_proposition_bound:
            return None
        admitted.append(AdmittedProposition(request, decision))
    registrations = len(record.registrations)
    return (
        admitted[0],
        tuple(admitted[1 : 1 + registrations]),
        tuple(admitted[1 + registrations :]),
    )


def _mention_span(request: AdmissionRequest, mention: str) -> RepresentationSpan | None:
    evidence = request.evidence
    claim, representation = evidence.grounded_claim, evidence.representation
    if claim is None or representation is None or claim.supporting_span is None:
        return None
    offset = claim.supporting_excerpt.find(mention)
    if offset < 0 or claim.supporting_excerpt.find(mention, offset + 1) >= 0:
        return None  # absent or repeated inside the excerpt: no ambiguous binding
    start = claim.supporting_span.start + offset
    return representation.span(start, start + len(mention))


def _binding(
    request: AdmissionRequest, *, entity_id: str, mention: str, role: str
) -> GovernedIdentityBinding | None:
    """Deterministic policy binding issued by this control plane, never by the source."""

    evidence = request.evidence
    span = _mention_span(request, mention)
    if span is None or evidence.representation is None:
        return None
    decision = hashlib.sha256(f"{evidence.id}|{role}|{entity_id}".encode()).hexdigest()[:32]
    return IdentityBindingAdmission.bind(
        IdentityBindingRequest(
            entity_id=entity_id,
            mention=mention,
            mention_span=span,
            decision_id=f"binding:{decision}",
            evidence_refs=(evidence.id,),
            authority=IdentityBindingAuthority.DETERMINISTIC_POLICY,
            decided_by="organization-admission",
            # Observation time, not wall time: replays derive the same binding.
            decided_at=evidence.observed_at,
            policy_version=BINDING_POLICY,
        ),
        evidence.representation,
    )


def _bound(request: AdmissionRequest, identifier_values: set[str]) -> AdmissionRequest | None:
    """Bind the registry's own entry identifier to the derived OrganizationId.

    A registry document names its entry by its identifier, never by AXIGNAL's id. The
    subject mention must be one of the record's registered identifiers; for a
    registration claim the object mention must be exactly that identifier's value.
    """

    claim = request.evidence.grounded_claim
    if claim is None or claim.subject_mention not in identifier_values:
        return None
    subject = _binding(
        request, entity_id=request.subject_id, mention=claim.subject_mention, role="subject"
    )
    if subject is None:
        return None
    object_binding = claim.object_binding
    if request.predicate == "registration":
        if parse_registration(request.object_or_value)[2] != claim.object_mention:
            return None
        object_binding = _binding(
            request,
            entity_id=request.object_or_value,
            mention=claim.object_mention,
            role="object",
        )
        if object_binding is None:
            return None
    bound = replace(claim, subject_binding=subject, object_binding=object_binding)
    return replace(request, evidence=replace(request.evidence, grounded_claim=bound))


def _attestation_gap(record: RegistryIdentityRecord, locator: AttentionLocator) -> str | None:
    """The registry record must attest exactly what the subscriber pointed at.

    A source that returns a loosely matching record (search, fuzzy name, a different
    website) cannot make AXIGNAL admit an identity the locator did not designate.
    """

    if not record.registrations:
        return "REGISTRY_IDENTIFIER_REQUIRED"
    requests = record.requests
    if any(request.subject_id != record.subject_id for request in requests):
        return "REGISTRY_RECORD_SUBJECT_MISMATCH"
    if (
        record.legal_name.predicate != "legal_identity"
        or any(item.predicate != "registration" for item in record.registrations)
        or any(item.predicate != "official_website" for item in record.official_websites)
    ):
        return "REGISTRY_RECORD_SHAPE_INVALID"
    try:
        identifiers = {parse_registration(item.object_or_value) for item in record.registrations}
        websites = {public_domain(item.object_or_value) for item in record.official_websites}
    except (ValueError, LocatorError):
        return "REGISTRY_RECORD_SHAPE_INVALID"
    if record.subject_id != organization_id_for(*min(identifiers)):
        return "REGISTRY_RECORD_SUBJECT_MISMATCH"
    if locator.identifier is not None and (
        (locator.identifier.scheme, locator.identifier.authority, locator.identifier.value)
        not in identifiers
    ):
        return "SOURCE_RECORD_DOES_NOT_ATTEST_LOCATOR"
    if locator.domain is not None and locator.domain not in websites:
        return "SOURCE_RECORD_DOES_NOT_ATTEST_LOCATOR"
    if (
        locator.identifier is None
        and locator.domain is None
        and locator.name_key != identity_name_key(record.legal_name.object_or_value)
    ):
        # A name alone admits only an exact legal-name match: no fuzzy, no "closest".
        return "SOURCE_RECORD_DOES_NOT_ATTEST_LOCATOR"
    return None
