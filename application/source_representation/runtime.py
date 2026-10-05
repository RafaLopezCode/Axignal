"""Deterministic compilation of derived document representation into rich state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from application.economic_discovery import StateChange
from application.source_representation.contracts import (
    DocumentRepresentation,
    RichStateDatum,
    RichSubjectState,
)


def _state_fingerprint(subject_id: str, data: tuple[RichStateDatum, ...]) -> str:
    payload = {
        "subject_id": subject_id,
        "data": [
            {
                "name": item.name,
                "value": item.value,
                "observation_id": item.observation_id,
                "representation_id": item.representation_id,
                "source_ref": item.source_ref,
                "observed_at": item.observed_at.isoformat(),
                "supporting_span": asdict(item.supporting_span) if item.supporting_span else None,
            }
            for item in data
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def representation_state_data(
    representation: DocumentRepresentation,
    *,
    observation_slot: str,
) -> tuple[RichStateDatum, ...]:
    """Expose explicit document semantics without inventing business facts."""

    if not observation_slot.strip():
        raise ValueError("observation slot is required")
    prefix = f"document.{observation_slot}"
    values: list[tuple[str, str]] = [
        (f"{prefix}.visible_text", representation.visible_text),
        (f"{prefix}.visible_text_fingerprint", representation.visible_text_fingerprint),
        (f"{prefix}.media_type", representation.media_type),
        (f"{prefix}.charset", representation.charset),
    ]
    if representation.title:
        values.append((f"{prefix}.title", representation.title))
    if representation.language:
        values.append((f"{prefix}.language", representation.language))
    if representation.description:
        values.append((f"{prefix}.description", representation.description))
    if representation.canonical_uri:
        values.append((f"{prefix}.canonical_uri", representation.canonical_uri))
    if representation.structured_data:
        values.append((f"{prefix}.structured_data", "\n".join(representation.structured_data)))

    return tuple(
        RichStateDatum(
            name=name,
            value=value,
            observation_id=representation.observation_id,
            representation_id=representation.representation_id,
            source_ref=representation.source_ref,
            observed_at=representation.observed_at,
            supporting_span=(
                representation.text_representation().span(0, len(value))
                if name == f"{prefix}.visible_text"
                else None
            ),
        )
        for name, value in values
    )


def compile_rich_subject_state(
    *,
    subject_id: str,
    contributions: tuple[RichStateDatum, ...],
) -> RichSubjectState:
    """Select latest deterministic contribution per field while retaining provenance."""

    if not subject_id.strip():
        raise ValueError("rich-state subject is required")
    latest: dict[str, RichStateDatum] = {}
    for item in sorted(
        contributions,
        key=lambda value: (
            value.observed_at,
            value.observation_id,
            value.representation_id,
            value.name,
        ),
    ):
        latest[item.name] = item
    selected = tuple(latest[name] for name in sorted(latest))
    return RichSubjectState(
        subject_id=subject_id,
        data=selected,
        fingerprint=_state_fingerprint(subject_id, selected),
    )


def rich_state_change(
    previous: RichSubjectState,
    current: RichSubjectState,
) -> StateChange | None:
    """Describe semantic state delta for dependency-aware Brain reevaluation."""

    if previous.subject_id != current.subject_id:
        raise ValueError("rich-state diff cannot mix subjects")
    if previous.fingerprint == current.fingerprint:
        return None
    previous_by_name = {item.name: item for item in previous.data}
    current_by_name = {item.name: item for item in current.data}
    changed = frozenset(
        name
        for name in previous_by_name.keys() | current_by_name.keys()
        if previous_by_name.get(name) != current_by_name.get(name)
    )
    if not changed:
        return None
    return StateChange(
        subject_id=current.subject_id,
        changed_fields=changed,
        previous_fingerprint=previous.fingerprint,
        current_fingerprint=current.fingerprint,
    )
