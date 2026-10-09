"""Current content delivery, independent of economic admission and temporal truth.

Only an already authorized projection enters this boundary. Source-linked text is
withdrawn in a copy, including materialized duplicates; facts and history stay stored.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessMetadata,
    ObservationAccessStatus,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from domain.evidence.epistemics import Currentness


class ContentAccess(StrEnum):
    PERMITTED = "PERMITTED"
    WITHHELD = "WITHHELD"
    UNKNOWN = "UNKNOWN"


class CurrentContentRights(Protocol):
    def decision(self, metadata: ObservationAccessMetadata) -> ContentAccess:
        """Decide at the live clock; a historical read must not rewind rights."""
        ...


@dataclass(frozen=True, slots=True)
class RecordedContentRights:
    """Compatibility for non-live sources; managed website grants need a resolver."""

    def decision(self, metadata: ObservationAccessMetadata) -> ContentAccess:
        if metadata.record.observation_id.startswith("fo:") or (
            metadata.record.source_type == "PUBLIC_WEBSITE"
            and (metadata.reuse_authority.provenance_ref or "").startswith(
                "source-registry:website:"
            )
        ):
            return ContentAccess.UNKNOWN
        return recorded_content_access(metadata)


def recorded_content_access(metadata: ObservationAccessMetadata) -> ContentAccess:
    authority = metadata.reuse_authority
    if authority.provenance_ref is None:
        return ContentAccess.UNKNOWN
    if (
        authority.scope is not ObservationReuseScope.GLOBAL_PUBLIC
        or authority.access_status is not ObservationAccessStatus.ACCESSIBLE
        or metadata.record.subject_id not in authority.applicable_subject_ids
        or "HISTORICAL_REFERENCE" not in authority.applicable_purposes
    ):
        return ContentAccess.WITHHELD
    status = authority.rights_status
    return (
        ContentAccess.PERMITTED
        if status is ObservationRightsStatus.PERMITTED
        else ContentAccess.WITHHELD
        if status is ObservationRightsStatus.PROHIBITED
        else ContentAccess.UNKNOWN
    )


def content_reusable_history(
    history: tuple[tuple[GovernedObservation, Currentness], ...],
    rights: CurrentContentRights,
) -> tuple[tuple[GovernedObservation, Currentness], ...]:
    """Current permission to reuse raw content; canonical storage remains untouched."""
    return tuple(
        (item, state)
        for item, state in history
        if rights.decision(ObservationAccessMetadata(item.record, item.reuse_authority))
        is ContentAccess.PERMITTED
    )


WITHHELD_TEXT = "Source text is unavailable under current content rights."
_TEXT_KEYS = frozenset(
    {
        "excerpt",
        "excerpt_or_summary",
        "quote",
        "quotation",
        "raw_content",
        "content",
        "label",
        "title",
        "statement",
        "interpretation",
        "reason",
        "summary",
        "description",
    }
)
_REFERENCE_KEYS = frozenset(
    {
        "sourceRef",
        "source_ref",
        "provenanceRef",
        "rights_basis_ref",
        "observation_ref",
        "observationId",
        "sourceId",
        "id",
        "url",
        "sourceUrl",
        "evidence_ref",
        "datum_ref",
        "observedAt",
        "observed_at",
        "as_of",
        "content_fingerprint",
        "representation_fingerprint",
    }
)


def deliver_evidence_content(
    projection: dict[str, object],
    *,
    metadata_for: Callable[[str], ObservationAccessMetadata | None],
    rights: CurrentContentRights,
) -> dict[str, object]:
    """Deliver old and new snapshots through one source-bound content decision.

    Descriptors in economic evidence and cognitive source rows retain source identity.
    Missing metadata for a registered FO reference fails closed. Exact copied excerpts
    are also withdrawn from legacy untagged explanation fields. Explicit independent
    source context overrides that inherited taint; no cross-source blocklist is used.
    """
    result = deepcopy(projection)
    decisions: dict[str, ContentAccess] = {}
    refs: dict[tuple[str, str], str] = {}
    source_ids: dict[str, set[str]] = {}
    quotes: set[str] = set()

    def decide(identifier: str) -> ContentAccess:
        if identifier not in decisions:
            metadata = metadata_for(identifier)
            if metadata is not None:
                decisions[identifier] = rights.decision(metadata)
                refs[(metadata.record.source_ref, metadata.record.observed_at.isoformat())] = (
                    identifier
                )
                source_ids.setdefault(metadata.record.source_ref, set()).add(identifier)
            else:
                # Source-derived demand rows are authorized by the existing registry
                # projector, not stored as ObservationMemory records. Their existing
                # rights path is unchanged; this is not a new source authorization.
                decisions[identifier] = (
                    ContentAccess.PERMITTED
                    if identifier.startswith("opportunity-evidence:")
                    else ContentAccess.UNKNOWN
                )
        return decisions[identifier]

    # First register identities, including narrative sourceRef resolution.
    def identities(value: Any) -> None:
        if isinstance(value, dict):
            identifier = value.get("observation_ref") or value.get("observationId")
            identifier = identifier or value.get("sourceId")
            if not identifier and "sourceRef" in value:
                identifier = value.get("id")
            if isinstance(identifier, str) and identifier:
                decide(identifier)
                source = value.get("source_ref") or value.get("sourceRef")
                if isinstance(source, str):
                    observed = value.get("observed_at") or value.get("observedAt")
                    if isinstance(observed, str):
                        refs[(source, observed)] = identifier
                    source_ids.setdefault(source, set()).add(identifier)
            for child in value.values():
                identities(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                identities(child)

    identities(result)

    def source_id(value: dict[str, Any]) -> str | None:
        for key in ("observation_ref", "observationId", "sourceId", "id"):
            identifier = value.get(key)
            if isinstance(identifier, str) and identifier in decisions:
                return identifier
        source = value.get("source_ref") or value.get("sourceRef")
        if not isinstance(source, str):
            return None
        observed = value.get("observed_at") or value.get("observedAt")
        if isinstance(observed, str):
            exact = refs.get((source, observed))
            if exact is not None:
                return exact
        candidates = source_ids.get(source, set())
        # An undated legacy copy never borrows a later observation's permission.
        denied = [i for i in sorted(candidates) if decide(i) is not ContentAccess.PERMITTED]
        return denied[0] if denied else next(iter(candidates), None)

    def collect(value: Any, inherited: str | None = None) -> None:
        if isinstance(value, dict):
            identifier = source_id(value) or inherited
            denied = identifier is not None and decide(identifier) is not ContentAccess.PERMITTED
            field_name = value.get("name") or value.get("field_name") or value.get("field")
            if (
                denied
                and isinstance(field_name, str)
                and field_name.rsplit(".", 1)[-1] == "excerpt"
            ):
                text = value.get("value")
                if isinstance(text, str) and text:
                    quotes.add(text)
            for key, child in value.items():
                if (
                    denied
                    and key.rsplit(".", 1)[-1]
                    in {"excerpt", "excerpt_or_summary", "quote", "quotation"}
                    and isinstance(child, str)
                    and child
                ):
                    quotes.add(child)
                collect(child, identifier)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child, inherited)

    collect(result)

    def clean(value: Any, inherited: str | None = None, key: str = "") -> Any:
        if key in {"organization", "context"}:
            return deepcopy(value)  # Already resolved canonical identity / authorized attention.
        if isinstance(value, dict):
            identifier = source_id(value) or inherited
            access = None if identifier is None else decide(identifier)
            denied = access is not None and access is not ContentAccess.PERMITTED
            demand = value.get("demand")
            demand_id = demand.get("sourceId") if isinstance(demand, dict) else None
            cleaned = {
                k: clean(
                    v,
                    demand_id
                    if k in {"title", "buyer", "known", "demand"}
                    and isinstance(demand_id, str)
                    and demand_id in decisions
                    else identifier,
                    k,
                )
                for k, v in value.items()
            }
            if denied and access is not None:
                # Excerpts are content, not normalized economic values or provenance.
                field_name = value.get("name") or value.get("field_name") or value.get("field")
                if isinstance(field_name, str) and field_name.rsplit(".", 1)[-1] == "excerpt":
                    cleaned["value"] = None
                for k in value:
                    kind = k.rsplit(".", 1)[-1]
                    if kind not in _TEXT_KEYS:
                        continue
                    normalized_label = k == "label" and "sourceId" in value and "excerpt" in value
                    source_reference = value[k] == value.get("sourceRef") or value[k] == value.get(
                        "source_ref"
                    )
                    if isinstance(value[k], str) and not normalized_label and not source_reference:
                        cleaned[k] = WITHHELD_TEXT
                cleaned["contentAccess"] = access.value
            capability = cleaned.get("capability")
            if isinstance(capability, dict) and capability.get("contentAccess") in {
                ContentAccess.WITHHELD.value,
                ContentAccess.UNKNOWN.value,
            }:
                # This explanation quotes the capability, whereas demand is a separate source.
                cleaned["whyPotential"] = WITHHELD_TEXT
            return cleaned
        if isinstance(value, list):
            return [clean(v, inherited, key) for v in value]
        if isinstance(value, tuple):
            return tuple(clean(v, inherited, key) for v in value)
        if (
            isinstance(value, str)
            and key not in _REFERENCE_KEYS
            and (inherited is None or decide(inherited) is not ContentAccess.PERMITTED)
        ):
            for quote in sorted(quotes, key=len, reverse=True):
                value = value.replace(quote, WITHHELD_TEXT)
        return value

    return dict(clean(result))
