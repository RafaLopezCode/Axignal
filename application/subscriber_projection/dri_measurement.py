"""Narrow public single-page representation measurement for subscriber output."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.economic_discovery.first_vertical_e2e import MaterializedEconomicSource
from domain.evidence.epistemics import Currentness
from domain.organizations.model import Organization

DRI_INSTRUMENT_REF = "axignal.public-page-representation"
DRI_INSTRUMENT_VERSION = "1.0.0"


class PageMeasureState(StrEnum):
    PRESENT = "PRESENT"
    MEASURED_ABSENCE_WITHIN_SCOPE = "MEASURED_ABSENCE_WITHIN_SCOPE"
    NOT_MEASURED = "NOT_MEASURED"
    NON_INFORMATIVE = "NON_INFORMATIVE"


class ContextRecommendationState(StrEnum):
    CONTEXT_REQUIRED = "CONTEXT_REQUIRED"


@dataclass(frozen=True, slots=True)
class RepresentationGapContextRecommendation:
    """A conditional human-review prompt, not an inferred remediation plan."""

    state: ContextRecommendationState

    def to_wire(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "condition": (
                "Only if this exact public page is intended to identify the Organization and "
                "the expected public brand name matches the name compared by this instrument."
            ),
            "requiredContext": {
                "pagePurpose": "UNKNOWN",
                "expectedPublicBrandName": "UNKNOWN",
            },
            "recommendedAction": (
                "If a responsible person confirms both conditions, consider reviewing the page "
                "title with the responsible team."
            ),
            "actionMode": "HUMAN_REVIEW_ONLY",
            "performanceBenefit": "NOT_ESTABLISHED",
        }


@dataclass(frozen=True, slots=True)
class PageRepresentationMeasurement:
    instrument_ref: str
    instrument_version: str
    surface: str
    resource_ref: str
    source_ref: str
    source_policy_ref: str
    source_policy_version: str
    source_rights_ref: str | None
    source_rights_status: str
    source_access_status: str
    source_reuse_scope: str
    retention_policy_ref: str | None
    robots_policy_ref: str | None
    representation_ref: str
    representation_fingerprint: str
    representation_version: str
    normalization_version: str
    observed_at: datetime
    geography: str
    language: str
    device_context: str
    eligible_sample_count: int
    informative_sample_count: int
    currentness: Currentness
    fields: tuple[tuple[str, PageMeasureState, str | None], ...]
    uncertainty: str
    human_meaning: str
    gap: dict[str, object] | None

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise ValueError("page measurement time must be timezone-aware")
        if self.eligible_sample_count != 1:
            raise ValueError("single-page instrument must retain exactly one eligible sample")
        if not 0 <= self.informative_sample_count <= self.eligible_sample_count:
            raise ValueError("page measurement informative sample is outside its denominator")

    def to_wire(self) -> dict[str, object]:
        result: dict[str, object] = {
            "kind": "DRI_PUBLIC_PAGE_REPRESENTATION",
            "instrument": {"ref": self.instrument_ref, "version": self.instrument_version},
            "surface": self.surface,
            "resourceRef": self.resource_ref,
            "source": {
                "ref": self.source_ref,
                "policyRef": self.source_policy_ref,
                "policyVersion": self.source_policy_version,
                "rightsBasisRef": self.source_rights_ref,
                "rightsStatus": self.source_rights_status,
                "accessStatus": self.source_access_status,
                "reuseScope": self.source_reuse_scope,
                "retentionPolicyRef": self.retention_policy_ref,
                "robotsPolicyRef": self.robots_policy_ref,
            },
            "representation": {
                "ref": self.representation_ref,
                "fingerprint": self.representation_fingerprint,
                "representationVersion": self.representation_version,
                "normalizationVersion": self.normalization_version,
            },
            "observedAt": self.observed_at.isoformat(),
            "conditions": {
                "geography": self.geography,
                "language": self.language,
                "deviceContext": self.device_context,
            },
            "sample": {
                "eligible": self.eligible_sample_count,
                "informative": self.informative_sample_count,
            },
            "currentness": self.currentness.value,
            "fields": [
                {"name": name, "state": state.value, "value": value}
                for name, state, value in self.fields
            ],
            "uncertainty": self.uncertainty,
            "humanMeaning": self.human_meaning,
            "scopeLimit": (
                "One authorized public page only. This is not search, generative, social, "
                "whole-Organization presence, SEO/GEO quality, or causal evidence."
            ),
        }
        if self.gap is not None:
            result["representationGap"] = self.gap
        return result


def _field_state(value: str | None, *, measurable: bool) -> PageMeasureState:
    if not measurable:
        return PageMeasureState.NOT_MEASURED
    if value is not None and value.strip():
        return PageMeasureState.PRESENT
    return PageMeasureState.MEASURED_ABSENCE_WITHIN_SCOPE


def measure_public_page_representation(
    *,
    source: MaterializedEconomicSource,
    organization: Organization,
) -> PageRepresentationMeasurement:
    """Describe a single acquired page; never infer broader digital visibility."""
    authorization = source.authorization
    representation = source.representation
    if authorization.request.subject_id != organization.id:
        raise ValueError("DRI page measurement must target the authorized Organization")
    text_measured = representation.visibility_resolved
    title_state = _field_state(representation.title, measurable=True)
    description_state = _field_state(representation.description, measurable=True)
    language_state = _field_state(representation.language, measurable=True)
    visible_text_state = (
        PageMeasureState.PRESENT
        if text_measured and representation.visible_text.strip()
        else PageMeasureState.NON_INFORMATIVE
        if text_measured
        else PageMeasureState.NOT_MEASURED
    )
    structured_state = _field_state("\n".join(representation.structured_data), measurable=True)
    normalized_title = " ".join((representation.title or "").casefold().split())
    normalized_name = " ".join(organization.canonical_name.casefold().split())
    # The page-title detector uses captured title metadata, not rendered body
    # visibility. CSS visibility uncertainty limits visible_text only.
    title_name_state = (
        PageMeasureState.PRESENT
        if normalized_title and normalized_name in normalized_title
        else PageMeasureState.MEASURED_ABSENCE_WITHIN_SCOPE
    )
    fields = (
        ("page_title", title_state, representation.title),
        ("page_description", description_state, representation.description),
        ("declared_language", language_state, representation.language),
        ("visible_text", visible_text_state, None),
        ("structured_data", structured_state, str(len(representation.structured_data))),
        (
            "canonical_organization_name_in_page_title",
            title_name_state,
            organization.canonical_name if title_name_state is PageMeasureState.PRESENT else None,
        ),
    )
    gap: dict[str, object] | None = None
    if title_name_state is PageMeasureState.MEASURED_ABSENCE_WITHIN_SCOPE:
        gap = {
            "type": "INXIGHT_REPRESENTATION_GAP",
            "state": "MEASURED_ABSENCE_WITHIN_SCOPE",
            "expectedPhrase": organization.canonical_name,
            "measuredField": "canonical_organization_name_in_page_title",
            "scope": "exact captured public page title",
            "cause": "UNKNOWN",
            "notEstablished": [
                "search visibility",
                "generative visibility",
                "social visibility",
                "whole-Organization representation",
                "SEO/GEO quality or cause",
            ],
            "contextRecommendation": RepresentationGapContextRecommendation(
                ContextRecommendationState.CONTEXT_REQUIRED
            ).to_wire(),
        }
        human_meaning = (
            "The captured page title does not contain the canonical Organization name. "
            "This single-page measurement does not establish why or how the Organization "
            "appears in search or AI-generated answers."
        )
    elif title_name_state is PageMeasureState.PRESENT:
        human_meaning = (
            "The captured page title contains the canonical Organization name. "
            "This describes one page only and does not establish broader digital visibility."
        )
    else:
        human_meaning = (
            "The captured page representation was not informative enough to measure whether "
            "its title contains the canonical Organization name."
        )
    resource_ref = representation.canonical_uri or authorization.request.target_uri
    return PageRepresentationMeasurement(
        instrument_ref=DRI_INSTRUMENT_REF,
        instrument_version=DRI_INSTRUMENT_VERSION,
        surface="PUBLIC_WEB_PAGE",
        resource_ref=resource_ref,
        source_ref=representation.source_ref,
        source_policy_ref=authorization.dispatch_policy.policy_id,
        source_policy_version=authorization.dispatch_policy.policy_version,
        source_rights_ref=authorization.reuse_authority.provenance_ref,
        representation_ref=representation.representation_id,
        representation_fingerprint=representation.fingerprint,
        observed_at=representation.observed_at,
        geography="UNKNOWN",
        language=representation.language or "UNKNOWN",
        device_context="UNKNOWN",
        eligible_sample_count=1,
        informative_sample_count=(
            1 if title_name_state is not PageMeasureState.NOT_MEASURED else 0
        ),
        currentness=authorization.reuse_authority.currentness,
        source_rights_status=authorization.reuse_authority.rights_status.value,
        source_access_status=authorization.reuse_authority.access_status.value,
        source_reuse_scope=authorization.reuse_authority.scope.value,
        retention_policy_ref=authorization.reuse_authority.retention_policy_ref,
        robots_policy_ref=authorization.reuse_authority.robots_policy_ref,
        representation_version=representation.representation_version,
        normalization_version=representation.normalization_version,
        fields=fields,
        uncertainty=(
            "One acquired page is the entire sample. Page metadata and visible text can be "
            "incomplete or unrepresentative; no other surface or discovery instrument ran."
        ),
        human_meaning=human_meaning,
        gap=gap,
    )
