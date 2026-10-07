"""The evidence AXENT may reason over: one authorized subscriber reading, flattened.

The corpus is built only from the reading the subscriber runtime returned
after re-checking membership, tenant and Xeed. There is no global index: what
is not in this reading does not exist for this turn. Every item keeps its
epistemic state, currentness, observation time and provenance, and its text is
sanitized as untrusted data (observed pages may contain instructions).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from application.observation_runtime.families import (
    FAMILY_POLICIES,
    EntryTarget,
    ObservationFamily,
)

MAX_TEXT_CHARS = 280

_F = ObservationFamily
#: Families whose entry point is the organization's own website (canonical policy).
WEBSITE_FAMILIES = frozenset(
    family
    for family, policy in FAMILY_POLICIES.items()
    if any(entry.target is EntryTarget.WEBSITE for entry in policy.entry_points)
)


class EvidenceKind(StrEnum):
    OPPORTUNITY = "OPPORTUNITY"
    CAPABILITY = "CAPABILITY"
    OBSERVATION = "OBSERVATION"
    SIGNAL = "SIGNAL"
    CHANGE = "CHANGE"
    #: Not evidence of anything: an explicit statement of what is not known.
    GAP = "GAP"


_INJECTION = re.compile(
    r"(ignore|disregard|olvida|ignora)\s+(all\s+|the\s+|las\s+|todas\s+)?(previous|prior|above|anteriores|instrucciones)"
    r"|\b(system|assistant)\s*:|</?\s*(system|evidence|question|tenant_context)\s*>|you are now|eres ahora",
    re.IGNORECASE,
)
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def sanitize(text: str, limit: int = MAX_TEXT_CHARS) -> tuple[str, bool]:
    """Untrusted text → one bounded line of data. Returns (text, looked like instructions)."""

    flat = _CONTROL.sub(" ", unicodedata.normalize("NFC", text))
    flat = re.sub(r"\s+", " ", flat).strip()
    suspicious = bool(_INJECTION.search(flat))
    # Delimiters of the prompt structure can never appear inside evidence.
    flat = flat.replace("<", "‹").replace(">", "›").replace("```", "'''")  # noqa: RUF001
    if len(flat) > limit:
        flat = flat[: limit - 1].rstrip() + "…"
    return flat, suspicious


_WORD = re.compile(r"[\w]+", re.UNICODE)


def fold(text: str) -> str:
    """Lowercase without accents, for matching only (never shown)."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def terms(text: str) -> frozenset[str]:
    return frozenset(w for w in _WORD.findall(fold(text)) if len(w) > 2)


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    item_id: str
    kind: EvidenceKind
    families: frozenset[ObservationFamily]
    text: str
    epistemic: str
    currentness: str
    observed_at: datetime | None
    source_ref: str | None
    source_label: str | None
    geographies: tuple[str, ...] = ()
    limits: tuple[str, ...] = ()
    #: The observed text looked like instructions; it stays data, flagged.
    untrusted_instructions: bool = False

    @property
    def terms(self) -> frozenset[str]:
        return terms(" ".join((self.text, *self.limits, *self.geographies)))

    def fingerprint_payload(self) -> tuple[object, ...]:
        return (
            self.item_id,
            self.kind.value,
            self.text,
            self.epistemic,
            self.currentness,
            None if self.observed_at is None else self.observed_at.isoformat(),
            self.source_ref,
            self.limits,
        )


@dataclass(frozen=True, slots=True)
class AuthorizedCorpus:
    tenant_id: str
    xeed_id: str
    organization_id: str
    organization_name: str
    as_of: datetime
    items: tuple[EvidenceItem, ...]

    @property
    def dependency_fingerprint(self) -> str:
        """Meaning/currentness, without the changing read cut or private scope."""
        payload = [
            self.organization_id,
            [i.fingerprint_payload() for i in self.items if i.kind is not EvidenceKind.GAP],
        ]
        return hashlib.sha256(json.dumps(payload, default=str, sort_keys=True).encode()).hexdigest()

    @property
    def fingerprint(self) -> str:
        """Changes whenever evidence, its currentness or the day of the cut changes."""
        # Item currentness carries the temporal state; the cut counts only to the day.
        payload: list[object] = [self.tenant_id, self.xeed_id, self.as_of.date().isoformat()]
        payload += [[str(v) for v in i.fingerprint_payload()] for i in self.items]
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _str(value: object) -> str:
    return value if isinstance(value, str) else ""


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, dict) else {}


def _item(
    item_id: str,
    kind: EvidenceKind,
    families: Iterable[ObservationFamily],
    text: str,
    *,
    epistemic: str,
    currentness: str,
    observed_at: datetime | None,
    source_ref: str | None,
    source_label: str | None,
    geographies: tuple[str, ...] = (),
    limits: Iterable[str] = (),
) -> EvidenceItem:
    clean, suspicious = sanitize(text)
    clean_limits = tuple(dict.fromkeys(sanitize(limit, 160)[0] for limit in limits if limit))
    label = None if source_label is None else sanitize(source_label, 120)[0]
    return EvidenceItem(
        item_id=item_id,
        kind=kind,
        families=frozenset(families),
        text=clean,
        epistemic=epistemic or "UNKNOWN",
        currentness=currentness or "UNKNOWN",
        observed_at=observed_at,
        source_ref=source_ref or None,
        source_label=label,
        geographies=geographies,
        limits=clean_limits[:3],
        untrusted_instructions=suspicious,
    )


def corpus_from_reading(
    *,
    tenant_id: str,
    projection: Mapping[str, Any],
    as_of: datetime,
    coverage: Iterable[tuple[ObservationFamily, str, str]] = (),
) -> AuthorizedCorpus:
    """Flatten one authorized subscriber reading (and optional family coverage) into items.

    ``coverage`` rows are (family, currentness, reason) for families the
    observation runtime could not observe; they become GAP items.
    """

    organization = _dict(projection.get("organization"))
    context = _dict(projection.get("context"))
    cognition = _dict(projection.get("cognition"))
    sources = {_str(s.get("id")): s for s in map(_dict, _list(cognition.get("sources")))}
    signal_family = {
        _str(s.get("id")): _str(s.get("familyId"))
        for s in map(_dict, _list(cognition.get("signals")))
    }
    items: list[EvidenceItem] = []

    for raw in map(_dict, _list(cognition.get("opportunities"))):
        demand_source = sources.get(_str(_dict(raw.get("demand")).get("sourceId")), {})
        market = _str(raw.get("market"))
        parts = [_str(raw.get("title"))]
        if raw.get("buyer"):
            parts.append(f"buyer: {_str(raw.get('buyer'))}")
        if market:
            parts.append(f"market: {market}")
        if raw.get("deadline"):
            parts.append(f"deadline: {_str(raw.get('deadline'))[:10]}")
        if raw.get("whyPotential"):
            parts.append(_str(raw.get("whyPotential")))
        items.append(
            _item(
                _str(raw.get("id")),
                EvidenceKind.OPPORTUNITY,
                (_F.DEMAND,),
                "; ".join(p for p in parts if p),
                epistemic=_str(raw.get("epistemic")),
                currentness=_str(raw.get("currentness")),
                observed_at=_time(raw.get("observedAt")),
                source_ref=_str(demand_source.get("sourceRef")) or None,
                source_label=_str(demand_source.get("instrument")) or None,
                geographies=(market,) if market else (),
                limits=[_str(u) for u in _list(raw.get("unknown"))],
            )
        )
        capability = _dict(raw.get("capability"))
        capability_source = sources.get(_str(capability.get("sourceId")), {})
        if capability.get("excerpt"):
            items.append(
                _item(
                    f"capability:{_str(capability.get('sourceId'))}:{_str(capability.get('label'))}",
                    EvidenceKind.CAPABILITY,
                    (_F.VALUE, _F.ORGANIZATION),
                    f"{_str(capability.get('label'))}: “{_str(capability.get('excerpt'))}”",
                    # A capability read on the organization's own page is a declaration.
                    epistemic="DECLARED",
                    currentness=_str(capability_source.get("currentness")),
                    observed_at=_time(capability_source.get("observedAt")),
                    source_ref=_str(capability_source.get("sourceRef")) or None,
                    source_label=_str(capability_source.get("title")) or None,
                    limits=(
                        "A declaration on its own website is evidence of the claim, not of the capability.",
                    ),
                )
            )

    for source_id, raw in sources.items():
        if source_id.startswith("opportunity-evidence:"):
            continue  # already carried by its opportunity
        items.append(
            _item(
                f"source:{source_id}",
                EvidenceKind.OBSERVATION,
                WEBSITE_FAMILIES,
                f"Public page observed: {_str(raw.get('title'))}",
                epistemic="OBSERVED",
                currentness=_str(raw.get("currentness")),
                observed_at=_time(raw.get("observedAt")),
                source_ref=_str(raw.get("sourceRef")) or None,
                source_label=_str(raw.get("title")) or None,
                limits=(_str(raw.get("limitation")),),
            )
        )

    for raw in map(_dict, _list(projection.get("nodes"))):
        node_id = _str(raw.get("id"))
        family = signal_family.get(node_id)
        families = (_F(family),) if family in {f.value for f in _F} else ()
        steps = [_dict(s) for s in _list(_dict(raw.get("evidenceNarrative")).get("steps"))]
        source_ref = next(
            (_str(s.get("sourceRef")) for s in steps if s.get("sourceRef")), ""
        ) or next(iter(_list(raw.get("sourceRefs"))), "")
        items.append(
            _item(
                node_id,
                EvidenceKind.SIGNAL,
                families,
                f"{_str(raw.get('title'))}. {_str(raw.get('interpretation'))} {_str(raw.get('whyAttention'))}",
                epistemic=_str(raw.get("epistemicState")),
                currentness=_str(raw.get("currentness")),
                observed_at=_time(raw.get("observedAt")),
                source_ref=str(source_ref) or None,
                source_label=None,
                limits=[_str(u) for u in _list(raw.get("unknowns"))]
                or [_str(raw.get("uncertainty"))],
            )
        )

    for index, raw in enumerate(map(_dict, _list(_dict(projection.get("today")).get("items")))):
        items.append(
            _item(
                f"change:today:{index}:{_str(raw.get('xignalId'))}",
                EvidenceKind.CHANGE,
                (_F.ACTIVITY,),
                f"{_str(raw.get('whatChanged'))}. {_str(raw.get('whyItMatters'))}",
                epistemic="OBSERVED",
                currentness="CURRENT",
                observed_at=_time(raw.get("observedAt")),
                source_ref=None,
                source_label=None,
            )
        )
    for raw in map(_dict, _list(_dict(projection.get("temporalHistory")).get("items"))):
        if raw.get("normalizedStateChanged") is True:
            items.append(
                _item(
                    f"change:{_str(raw.get('observationId'))}",
                    EvidenceKind.CHANGE,
                    (_F.ACTIVITY, *WEBSITE_FAMILIES),
                    f"The observed public page changed compared with the previous observation ({_str(raw.get('sourceRef'))}).",
                    epistemic="OBSERVED",
                    currentness=_str(raw.get("currentness")),
                    observed_at=_time(raw.get("observedAt")),
                    source_ref=_str(raw.get("sourceRef")) or None,
                    source_label=None,
                )
            )

    representation = _dict(projection.get("digitalRepresentation"))
    if representation.get("state") == "NOT_MEASURED":
        reason = _dict(representation.get("reason")).get("explanation") or representation.get(
            "reason"
        )
        items.append(
            _item(
                "gap:digital-representation",
                EvidenceKind.GAP,
                (_F.PRESENCE,),
                "No condition-bound measurement of search or generative visibility exists yet.",
                epistemic="UNKNOWN",
                currentness="UNKNOWN",
                observed_at=None,
                source_ref=None,
                source_label=None,
                limits=(_str(reason),),
            )
        )
    for family, currentness, reason in coverage:
        items.append(
            _item(
                f"gap:coverage:{family.value}",
                EvidenceKind.GAP,
                (family,),
                f"{family.value}: not observed — {reason}",
                epistemic="UNKNOWN",
                currentness=currentness,
                observed_at=None,
                source_ref=None,
                source_label=None,
                limits=(reason,),
            )
        )

    unique: dict[str, EvidenceItem] = {}
    for item in items:
        if item.item_id and item.item_id not in unique:
            unique[item.item_id] = item
    return AuthorizedCorpus(
        tenant_id=tenant_id,
        xeed_id=_str(context.get("id")),
        organization_id=_str(organization.get("id")),
        organization_name=sanitize(_str(organization.get("name")), 120)[0],
        as_of=as_of,
        items=tuple(i for i in unique.values() if i.observed_at is None or i.observed_at <= as_of),
    )
