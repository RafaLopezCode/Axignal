"""Derive the Economic Operating Model from governed public observations (deterministic).

Rules that make the garden honest:

* only the latest observation of each source as of the cut speaks (EB-06 history keeps
  the rest; an earlier cut derives an earlier garden);
* a place becomes reach only next to an explicit cue (service area, premises, expansion,
  delivery); a bare place name — a brand, a headquarters, a demonym — never does;
* a sentence naming a capability binds the claim to that capability; a site-wide
  sentence binds to the Organization and proves no single channel (POTENTIAL);
* expansion comes only from the Organization's own preparatory acts, never from
  demand observed in a place;
* supplier geographies feed exposure (supply), never customer reach.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationFieldState,
)
from application.economic_discovery.temporal_currentness import (
    TemporalCurrentnessPolicy,
    evaluate_effective_currentness,
)
from application.economic_reach.model import (
    CHANNELS_BY_MODE,
    CapabilityReach,
    ClaimBinding,
    ConstraintClaim,
    ConstraintKind,
    DeliveryMode,
    EconomicOperatingModel,
    ExposureChannel,
    ExposurePath,
    ModeClaim,
    Polarity,
    ReachBasis,
    ReachClaim,
)
from application.economic_reach.places import find_places, normalize
from application.observation_intelligence.contracts import CapabilityHypothesis, EvidenceRef
from domain.evidence.epistemics import Currentness

CUES_VERSION = "reach-cues:2026-10-08"

_MODE_CUES: dict[DeliveryMode, tuple[str, ...]] = {
    DeliveryMode.PROVIDER_PREMISES: (
        "en nuestro centro",
        "en nuestra academia",
        "en nuestro salon",
        "en nuestra tienda",
        "en nuestro local",
        "en nuestro restaurante",
        "en nuestras instalaciones",
        "presencial",
        "visitanos",
        "at our premises",
        "in our store",
        "in our centre",
        "in our center",
        "in person",
    ),
    DeliveryMode.CUSTOMER_SITE: (
        "a domicilio",
        "en sus instalaciones",
        "instalamos",
        "nos desplazamos",
        "montaje en",
        "on-site",
        "onsite",
        "at your site",
        "we install",
        "at the customer",
    ),
    DeliveryMode.SHIPPED: (
        "envios",
        "enviamos",
        "exportamos",
        "distribuimos",
        "we ship",
        "shipping to",
        "we export",
        "delivery to",
    ),
    DeliveryMode.REMOTE: (
        "online",
        "en linea",
        "por videoconferencia",
        "a distancia",
        "remote",
        "remotely",
    ),
    DeliveryMode.DIGITAL: ("software", "saas", "plataforma en la nube", "cloud platform"),
}
_AREA_CUES = (
    "servicio en",
    "servicios en",
    "damos servicio",
    "servimos",
    "trabajamos en",
    "cubrimos",
    "en toda",
    "en todo",
    "atendemos",
    "disponible en",
    "operamos en",
    "we serve",
    "serving",
    "available in",
    "we operate in",
    "throughout",
)
_PREMISES_CUES = (
    "nuestro centro en",
    "nuestra academia en",
    "nuestro salon en",
    "nuestra tienda en",
    "nuestro local en",
    "nuestro restaurante en",
    "oficina en",
    "oficinas en",
    "sede en",
    "delegacion en",
    "fabrica en",
    "our office in",
    "located in",
    "our store in",
)
_EXPANSION_FACILITY = (
    "abriremos",
    "proxima apertura",
    "nueva oficina",
    "nueva delegacion",
    "nuevo centro",
    "nueva sede",
    "abrimos en",
    "ampliamos a",
    "expanding to",
    "opening in",
    "new office",
)
_EXPANSION_HIRING = (
    "buscamos",
    "contratamos",
    "incorporamos",
    "ofertas de empleo",
    "we are hiring",
    "hiring",
    "join our team in",
)
_EXCLUSIVE = ("solo ", "solamente", "unicamente", "exclusivamente", "only ", "exclusively")
_NEGATED = ("no enviamos", "no realizamos", "no damos servicio", "no trabajamos", "we do not")
_EXCEPT = ("excepto", "salvo", "except", "excluding")
_SUPPLY_CUES = (
    "proveedores",
    "importamos",
    "materia prima",
    "materias primas",
    "suppliers",
    "we import",
    "sourced from",
)
_CERTIFICATION = re.compile(r"\biso[ -]?(\d{4,5})\b|\b(rite)\b|\b(instalador autorizado)\b")
_SENTENCE = re.compile(r"[^.!?;\n]+")


def _has(text: str, cues: tuple[str, ...]) -> bool:
    return any(cue in text for cue in cues)


@dataclass(frozen=True, slots=True)
class _Sentence:
    text: str
    norm: str
    evidence: EvidenceRef
    currentness: Currentness


def _latest_by_source(
    observations: tuple[GovernedObservation, ...], as_of: datetime
) -> tuple[GovernedObservation, ...]:
    latest: dict[str, GovernedObservation] = {}
    for item in sorted(
        (o for o in observations if o.record.observed_at <= as_of and o.raw_content),
        key=lambda o: (o.record.observed_at, o.record.observation_id),
    ):
        latest[item.record.source_ref] = item
    return tuple(latest[key] for key in sorted(latest))


def derive_operating_model(
    *,
    organization_id: str,
    capabilities: tuple[CapabilityHypothesis, ...],
    capability_terms: Mapping[str, tuple[str, ...]],
    observations: tuple[GovernedObservation, ...],
    as_of: datetime,
    policy: TemporalCurrentnessPolicy,
) -> EconomicOperatingModel:
    """The garden as of ``as_of``: per-capability channels, reach claims and exposure."""

    if as_of.tzinfo is None:
        raise ValueError("operating model derivation time must be timezone-aware")
    sources = _latest_by_source(observations, as_of)
    sentences: list[_Sentence] = []
    for observation in sources:
        record = observation.record
        currentness = evaluate_effective_currentness(
            observation_id=record.observation_id,
            observed_at=record.observed_at,
            previous=Currentness.CURRENT,
            as_of=as_of,
            policy=policy,
        ).current
        assert observation.raw_content is not None
        for match in _SENTENCE.finditer(observation.raw_content):
            text = match.group(0).strip()
            if len(text) < 3:
                continue
            sentences.append(
                _Sentence(
                    text,
                    normalize(text),
                    EvidenceRef(record.observation_id, record.source_ref, text, record.observed_at),
                    currentness,
                )
            )

    terms = {
        capability.capability_id: tuple(
            normalize(term) for term in capability_terms.get(capability.capability_id, ())
        )
        for capability in capabilities
    }
    modes: dict[str, list[ModeClaim]] = {c.capability_id: [] for c in capabilities}
    claims: dict[str, list[ReachClaim]] = {c.capability_id: [] for c in capabilities}
    constraints: dict[str, list[ConstraintClaim]] = {c.capability_id: [] for c in capabilities}
    org_modes: list[ModeClaim] = []
    org_claims: list[ReachClaim] = []
    org_constraints: list[ConstraintClaim] = []
    exposure: list[ExposurePath] = []

    for sentence in sentences:
        named = [
            cid for cid, words in terms.items() if any(word in sentence.norm for word in words)
        ]
        binding = ClaimBinding.CAPABILITY if named else ClaimBinding.ORGANIZATION
        sentence_modes = [mode for mode, cues in _MODE_CUES.items() if _has(sentence.norm, cues)]
        found = [ModeClaim(mode, binding, sentence.evidence) for mode in sentence_modes]
        if named:
            for cid in named:
                modes[cid].extend(found)
        else:
            org_modes.extend(found)

        places = find_places(sentence.text)
        new_claims: list[ReachClaim] = []
        if places:
            if _has(sentence.norm, _EXPANSION_FACILITY) or _has(sentence.norm, _EXPANSION_HIRING):
                signal = "FACILITY" if _has(sentence.norm, _EXPANSION_FACILITY) else "HIRING"
                new_claims = [
                    ReachClaim(
                        place,
                        ReachBasis.EXPANSION_SIGNAL,
                        binding,
                        sentence.evidence,
                        sentence.currentness,
                        signal=signal,
                    )
                    for _pos, place in places
                ]
            elif _has(sentence.norm, _SUPPLY_CUES):
                # Where suppliers are is supply exposure, never where customers are served.
                exposure.append(
                    ExposurePath(
                        ExposureChannel.SUPPLY_INPUTS, None, "STATED_SUPPLY", (sentence.evidence,)
                    )
                )
            elif _has(sentence.norm, _PREMISES_CUES) and not _has(sentence.norm, _AREA_CUES):
                new_claims = [
                    ReachClaim(
                        place,
                        ReachBasis.PREMISES,
                        binding,
                        sentence.evidence,
                        sentence.currentness,
                        mode=DeliveryMode.PROVIDER_PREMISES
                        if DeliveryMode.PROVIDER_PREMISES in sentence_modes
                        else None,
                    )
                    for _pos, place in places
                ]
            elif _has(sentence.norm, _AREA_CUES) or sentence_modes:
                negated = _has(sentence.norm, _NEGATED)
                except_at = min(
                    (sentence.norm.find(cue) for cue in _EXCEPT if cue in sentence.norm),
                    default=-1,
                )
                exclusive = _has(sentence.norm, _EXCLUSIVE)
                channel_modes: list[DeliveryMode | None] = list(sentence_modes) or [None]
                for position, place in places:
                    excluded = negated or (except_at >= 0 and position > except_at)
                    for mode in channel_modes:
                        new_claims.append(
                            ReachClaim(
                                place,
                                ReachBasis.STATED_SERVICE_AREA,
                                binding,
                                sentence.evidence,
                                sentence.currentness,
                                mode=mode,
                                polarity=Polarity.EXCLUDED if excluded else Polarity.INCLUDED,
                                exclusive=exclusive and not excluded,
                            )
                        )
        elif _has(sentence.norm, _SUPPLY_CUES):
            exposure.append(
                ExposurePath(
                    ExposureChannel.SUPPLY_INPUTS, None, "STATED_SUPPLY", (sentence.evidence,)
                )
            )
        if named:
            for cid in named:
                claims[cid].extend(new_claims)
        else:
            org_claims.extend(new_claims)

        for match in _CERTIFICATION.finditer(sentence.norm):
            value = (
                f"ISO {match.group(1)}"
                if match.group(1)
                else (match.group(2) or match.group(3)).upper()
            )
            claim = ConstraintClaim(ConstraintKind.CERTIFICATION, value, binding, sentence.evidence)
            if named:
                for cid in named:
                    constraints[cid].append(claim)
            else:
                org_constraints.append(claim)

    # Structured certification fields: an explicit WITHDRAWN state is negative evidence.
    for observation in sources:
        for field in observation.fields:
            if field.name != "certification":
                continue
            org_constraints.append(
                ConstraintClaim(
                    ConstraintKind.CERTIFICATION,
                    field.value.upper(),
                    ClaimBinding.ORGANIZATION,
                    EvidenceRef(
                        observation.record.observation_id,
                        observation.record.source_ref,
                        field.value,
                        observation.record.observed_at,
                    ),
                    withdrawn=field.state
                    in (ObservationFieldState.WITHDRAWN, ObservationFieldState.MEASURED_ABSENCE),
                )
            )

    reaches: list[CapabilityReach] = []
    for capability in sorted(capabilities, key=lambda item: item.capability_id):
        cid = capability.capability_id
        reach = CapabilityReach(
            capability_id=cid,
            label=capability.label,
            modes=tuple(modes[cid]) + tuple(org_modes),
            claims=tuple(claims[cid]) + tuple(org_claims),
            constraints=tuple(constraints[cid]) + tuple(org_constraints),
        )
        reaches.append(reach)
        for mode in sorted(reach.mode_values()):
            mode_evidence = tuple(m.evidence for m in reach.modes if m.mode is mode)
            exposure.extend(
                ExposurePath(channel, cid, mode.value, mode_evidence)
                for channel in CHANNELS_BY_MODE[mode]
            )
    # Only observations that contributed something are dependencies: an unrelated page
    # changing must not invalidate the garden.
    evidence_ids = tuple(
        sorted(
            {m.evidence.observation_id for r in reaches for m in r.modes}
            | {c.evidence.observation_id for r in reaches for c in r.claims}
            | {k.evidence.observation_id for r in reaches for k in r.constraints}
            | {e.observation_id for path in exposure for e in path.evidence}
        )
    )
    return EconomicOperatingModel(
        organization_id=organization_id,
        capabilities=tuple(reaches),
        exposure=tuple(exposure),
        evidence_ids=evidence_ids,
    )
