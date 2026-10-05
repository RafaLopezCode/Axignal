"""Deterministic synthetic scenarios for the local HFX-01 UX laboratory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    GroundedClaim,
    SourceAuthority,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import FaxtId, XeedId
from domain.xeed.knowledge_reference import XeedFaxtReference
from tests.support.grounding import with_synthetic_representation
from tests.support.hfx01_demo import Hfx01Demo
from tests.support.hfx01_server import serialize_projection

SCENARIOS = ("SYNTHETIC_SPARSE", "SYNTHETIC_NOMINAL", "SYNTHETIC_DENSE", "SYNTHETIC_EDGE_CASES")

_NOMINAL_FACTS = (
    ("capability", "renewable energy equipment makers", EpistemicState.CORROBORATED),
    ("DEVELOPS_CAPABILITY", "precision ceramic machining", EpistemicState.DECLARED),
    ("capability", "Northern Europe", EpistemicState.OBSERVED),
    ("SUPPORTS_STANDARD", "ISO 14001", EpistemicState.STALE),
    ("HAS_PRODUCT", "thermal control assemblies", EpistemicState.OBSERVED),
    ("capability", "delivery lead-time varies by region", EpistemicState.INFERRED),
)

_DENSE_FACTS = (
    ("capability", "rail electrification suppliers", EpistemicState.CORROBORATED),
    ("DEVELOPS_CAPABILITY", "multi-axis finishing", EpistemicState.DECLARED),
    ("capability", "Central Europe", EpistemicState.OBSERVED),
    ("SUPPORTS_STANDARD", "ISO 14001", EpistemicState.STALE),
    ("HAS_PRODUCT", "thermal control assemblies", EpistemicState.OBSERVED),
    ("capability", "lead times vary by region", EpistemicState.INFERRED),
    ("capability", "pilot production line", EpistemicState.OBSERVED),
    ("capability", "materials traceability requirements", EpistemicState.DECLARED),
    ("capability", "supplier qualification window", EpistemicState.INFERRED),
    ("capability", "capacity expansion announcements", EpistemicState.STALE),
    ("capability", "medical instrumentation makers", EpistemicState.CORROBORATED),
    ("DEVELOPS_CAPABILITY", "low-volume alloy forming", EpistemicState.DECLARED),
    ("capability", "East Asia", EpistemicState.OBSERVED),
    ("HAS_PRODUCT", "sealed sensor housings", EpistemicState.OBSERVED),
)

_EDGE_CASE_FACTS = (
    (
        "capability",
        "Donaudampfschifffahrtselektrizitätenhauptbetriebswerkbaugesellschaft",
        EpistemicState.DECLARED,
    ),
    ("capability", "精密部品の製造", EpistemicState.OBSERVED),
    ("capability", "تصنيع المكوّنات الدقيقة", EpistemicState.CORROBORATED),
    ("capability", "Fabricación de componentes de precisión", EpistemicState.STALE),
    ("capability", "[presentation-empty-label fixture]", EpistemicState.DECLARED),
    ("capability", "Optional detail intentionally absent", EpistemicState.OBSERVED),
    ("capability", "An isolated synthetic information object", EpistemicState.INFERRED),
    (
        "capability",
        "A long label for checking narrow panels and wrap behavior",
        EpistemicState.OBSERVED,
    ),
    ("capability", "Región de prueba", EpistemicState.DECLARED),
)

_EDGE_TYPES = ("supports", "observes", "compares", "intersects")
_EDGE_EPISTEMIC_STATES = (
    "OBSERVED",
    "CORROBORATED",
    "INFERRED",
    "POTENTIAL",
    "STALE",
    "CONTRADICTED",
    "HISTORICAL",
    "UNKNOWN",
)


def _extra_facts(demo: Hfx01Demo, facts: tuple[tuple[str, str, EpistemicState], ...]) -> None:
    for index, (predicate, value, epistemic_state) in enumerate(facts, start=1):
        faxt_id = FaxtId(f"lab-faxt-{index:02d}")
        authority = (
            SourceAuthority.CERTIFIER
            if predicate == "SUPPORTS_STANDARD"
            else SourceAuthority.OFFICIAL_WEB
        )
        subject_id = f"synthetic-opaque-subject-{index:02d}"
        claim = f"{subject_id} {predicate} {value}"
        evidence = with_synthetic_representation(
            Evidence(
                id=f"lab-evidence-{index:02d}",
                source="synthetic://axignal-ux-laboratory",
                source_type="test",
                reference=f"synthetic://scenario/{index:02d}",
                extracted_claim=claim,
                observed_at=datetime(2026, 9, 1, tzinfo=UTC),
                authority=authority,
                observation_subject_id=subject_id,
                grounded_claim=GroundedClaim(
                    subject_id=subject_id,
                    predicate=predicate,
                    object_or_value=value,
                    subject_mention=subject_id,
                    predicate_mention=predicate,
                    object_mention=value,
                    supporting_excerpt=claim,
                ),
            )
        )
        currentness = (Currentness.CURRENT, Currentness.STALE, Currentness.UNKNOWN)[index % 3]
        faxt = FAXT.create(
            faxt_id=faxt_id,
            subject_id=subject_id,
            predicate=predicate,
            object_or_value=value,
            evidence=evidence,
            decision=EvidenceAdmission.admit_claim(
                AdmissionRequest(
                    evidence=evidence,
                    subject_id=subject_id,
                    predicate=predicate,
                    object_or_value=value,
                    claim_proposition=evidence.extracted_claim,
                )
            ),
            epistemic_state=epistemic_state,
            currentness=currentness,
        )
        demo.knowledge.add_faxt(faxt)
        demo.knowledge.add_reference(XeedFaxtReference(XeedId("xeed-demo-a"), faxt_id))


def _edges(scenario: str, object_ids: list[str]) -> list[dict[str, str]]:
    if scenario == "SYNTHETIC_SPARSE":
        return []
    if scenario == "SYNTHETIC_NOMINAL":
        pairs = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (3, 6), (4, 7), (5, 8)]
    elif scenario == "SYNTHETIC_DENSE":
        # Twenty-four edges exercise normal, cross-region, long-distance and
        # high-degree drawing without turning the fixture into random noise.
        pairs = [(0, index) for index in range(1, 9)] + [
            (1, 3),
            (1, 4),
            (2, 5),
            (2, 6),
            (3, 7),
            (4, 8),
            (5, 9),
            (6, 10),
            (7, 11),
            (8, 12),
            (9, 13),
            (10, 14),
            (11, 15),
            (12, 16),
            (13, 4),
            (14, 2),
        ]
    else:
        pairs = [(0, 1), (0, 2), (0, 3), (2, 4), (4, 5), (6, 7), (8, 9)]
    edges = []
    for index, (source_index, target_index) in enumerate(pairs):
        if source_index < len(object_ids) and target_index < len(object_ids):
            edges.append(
                {
                    "id": f"synthetic-edge-{index + 1:02d}",
                    "source": object_ids[source_index],
                    "target": object_ids[target_index],
                    "type": _EDGE_TYPES[index % len(_EDGE_TYPES)],
                    "epistemicState": _EDGE_EPISTEMIC_STATES[index % len(_EDGE_EPISTEMIC_STATES)],
                    "syntheticFixture": True,
                }
            )
    return edges


def _scenario_state(scenario: str) -> dict[str, Any]:
    contexts = {
        "SYNTHETIC_SPARSE": ["Fictional demo context"],
        "SYNTHETIC_NOMINAL": [
            "Asterion focus",
            "Market scan",
            "Supplier landscape",
            *(f"Synthetic Xeed {index:03d}" for index in range(1, 99)),
        ],
        "SYNTHETIC_DENSE": [f"Synthetic context {index:02d}" for index in range(1, 9)],
        "SYNTHETIC_EDGE_CASES": [
            "Kontext mit einem außergewöhnlich langen Namen für die Darstellung",
            "試験用コンテキスト",
            "سياق تجريبي",
            "Contexto de prueba",
        ],
    }[scenario]
    axent = {
        "SYNTHETIC_SPARSE": {
            "moves": [
                {
                    "label": "Why does this matter?",
                    "copyKey": "navigation.whyMatters",
                    "available": False,
                }
            ],
            "messages": [],
            "composerEnabled": False,
        },
        "SYNTHETIC_NOMINAL": {
            "moves": [
                {
                    "label": "Why does this matter?",
                    "copyKey": "navigation.whyMatters",
                    "available": True,
                },
                {
                    "label": "Compare regions",
                    "copyKey": "fixture.compareRegions",
                    "available": False,
                },
                {
                    "label": "What remains unverified?",
                    "copyKey": "fixture.whatUnverified",
                    "available": False,
                },
            ],
            "messages": [
                {"role": "you", "text": "Which capability is most relevant to this view?"},
                {
                    "role": "axent",
                    "text": "Synthetic fixture response: this panel can present contextual guidance; no reasoning service was called.",
                },
            ],
            "composerEnabled": True,
            "placeholderKey": "fixture.composerPlaceholder",
            "reply": "Synthetic fixture response. No model or provider was called.",
        },
        "SYNTHETIC_DENSE": {
            "moves": [
                {
                    "label": "Why does this matter?",
                    "copyKey": "navigation.whyMatters",
                    "available": True,
                },
                {
                    "label": "Compare regions",
                    "copyKey": "fixture.compareRegions",
                    "available": True,
                },
                {
                    "label": "Explain simply",
                    "copyKey": "navigation.explainSimply",
                    "available": True,
                },
                {
                    "label": "What remains unverified?",
                    "copyKey": "fixture.whatUnverified",
                    "available": False,
                },
            ],
            "messages": [
                {"role": "axent", "text": "Synthetic long transcript fixture. " * 42},
                {"role": "you", "text": "Synthetic long user input fixture. " * 18},
                {"role": "axent", "text": "Synthetic long response fixture. " * 56},
            ],
            "composerEnabled": True,
            "placeholderKey": "fixture.composerPlaceholder",
            "reply": "Synthetic fixture response. No model or provider was called.",
        },
        "SYNTHETIC_EDGE_CASES": {
            "moves": [
                {"label": "¿Qué cambia?", "available": True},
                {"label": "Vergleich anzeigen", "available": False},
                {"label": "説明を表示", "available": True},
                {"label": "اشرح ببساطة", "available": False},
            ],
            "messages": [
                {
                    "role": "axent",
                    "text": "Synthetic multilingual fixture: prueba · Prüfung · 試験 · اختبار.",
                }
            ],
            "composerEnabled": True,
            "placeholder": "Ask in a test language · synthetic only",
            "reply": "Synthetic fixture response. No model or provider was called.",
        },
    }[scenario]
    for fixture in (*axent["moves"], *axent["messages"]):
        fixture["syntheticFixture"] = True
    return {
        "scenario": scenario,
        "disclosure": "SYNTHETIC UX LAB · FICTIONAL TEST DATA · NOT CANONICAL",
        "fixtureClass": "CANONICAL_CONTRACT_BACKED_SYNTHETIC",
        "contexts": [{"label": label, "syntheticFixture": True} for label in contexts],
        "contextSearch": scenario
        in {"SYNTHETIC_NOMINAL", "SYNTHETIC_DENSE", "SYNTHETIC_EDGE_CASES"},
        "accountLabel": None,
        "accountLabelKey": "fixture.accountLabel" if scenario != "SYNTHETIC_EDGE_CASES" else None,
        "governanceAvailable": scenario in {"SYNTHETIC_NOMINAL", "SYNTHETIC_DENSE"},
        "edges": [],
        "timeline": [],
        "moves": axent["moves"],
        "messages": axent["messages"],
        "composerEnabled": axent["composerEnabled"],
        "composerPlaceholder": axent.get("placeholder", ""),
        "composerPlaceholderKey": axent.get("placeholderKey"),
        "fixtureReply": axent.get("reply", ""),
    }


def build_scenario(scenario: str) -> dict[str, Any]:
    """Build an explicitly synthetic, deterministic presentation payload."""

    if scenario not in SCENARIOS:
        raise ValueError("unsupported synthetic UX scenario")
    facts = {
        "SYNTHETIC_SPARSE": (),
        "SYNTHETIC_NOMINAL": _NOMINAL_FACTS,
        "SYNTHETIC_DENSE": _DENSE_FACTS,
        "SYNTHETIC_EDGE_CASES": _EDGE_CASE_FACTS,
    }[scenario]
    name = (
        "Asterion Works · fictional lab"
        if scenario != "SYNTHETIC_SPARSE"
        else "Northwind Materials (synthetic demo)"
    )
    demo = Hfx01Demo(name)
    _extra_facts(demo, facts)
    payload = serialize_projection(demo.selected_demo_projection())
    lab = _scenario_state(scenario)
    payload["context"]["label"] = lab["contexts"][0]["label"]
    object_ids = [payload["organization"]["id"], *(node["id"] for node in payload["nodes"])]
    for index, message in enumerate(lab["messages"]):
        message["scope"] = {
            "xeedId": payload["context"]["id"],
            "objectId": payload["organization"]["id"],
            "objectKind": "ORGANIZATION",
            "label": payload["organization"]["name"],
        }
        message["occurredAt"] = f"2026-09-01T12:{index:02d}:00+00:00"
    for node in payload["nodes"]:
        node["syntheticFixture"] = True
        node["fixtureClass"] = "CANONICAL_CONTRACT_BACKED_SYNTHETIC"
    payload["organization"]["syntheticFixture"] = True
    payload["organization"]["fixtureClass"] = "CANONICAL_CONTRACT_BACKED_SYNTHETIC"
    lab["edges"] = _edges(scenario, object_ids)
    lab["timeline"] = (
        [
            {"label": "Synthetic checkpoint 1", "syntheticFixture": True},
            {"label": "Synthetic checkpoint 2", "syntheticFixture": True},
        ]
        if scenario in {"SYNTHETIC_NOMINAL", "SYNTHETIC_DENSE"}
        else []
    )
    lab["initialHistory"] = (
        object_ids[: min(len(object_ids), 12)]
        if scenario == "SYNTHETIC_EDGE_CASES"
        else [object_ids[0]]
    )
    lab["initialFocus"] = lab["initialHistory"][-1]
    lab["presentationOverrides"] = {
        "epistemicState": {
            "faxt-demo-a2": "POTENTIAL",
            "lab-faxt-01": "UNKNOWN",
        }
        if scenario == "SYNTHETIC_EDGE_CASES"
        else {},
        "currentness": {},
    }
    lab["scenarioObjectCount"] = len(object_ids)
    lab["presentationOnlyFixtures"] = [
        "relationship edges",
        "timeline",
        "AXENT transcript",
        "sidebar contexts",
    ]
    payload["realityLevel"] = "SYNTHETIC_PRESENTATION_LAB"
    payload["uxLab"] = lab
    return payload
