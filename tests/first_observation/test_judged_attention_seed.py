"""A confident judged activity may choose where the autonomous loop looks (spec 079, CTO 2026-10-16).

Found on the canary: biocultor.com, an SME only Jev can read (CPV division 77 at 0.91), could
not start the daily loop because a judged activity never seeded attention and a web-anchored
Focus never handed its reading over. Both stay POTENTIAL attention, never a fact.
"""

from __future__ import annotations

from typing import Any

from application.first_observation.derived import JUDGED_SEED_MIN_CONFIDENCE, derived_capabilities
from pipeline.entity_resolution.web_subjects import web_subject_id

WEB = str(web_subject_id("biocultor.example.com"))


def _proof(method: str, confidence: float | None, *, link: str = "SUBSCRIBER_DIRECTED",
           organization: str = WEB, codes: list[list[str]] | None = None) -> dict[str, Any]:  # fmt: skip
    return {
        "target": {"kind": "FOCUS", "identityLink": link, "organizationId": organization},
        "capabilities": [{
            "method": method, "confidence": confidence, "capabilityId": "landscaping-gardening",
            "label": "Landscaping", "state": "POTENTIAL",
            "demandCodes": [["CPV", "77310000"]] if codes is None else codes,
            "basis": {"observationId": "o", "sourceRef": "https://biocultor.example.com/",
                      "excerpt": "Mantenimiento de zonas verdes.", "observedAt": "2026-10-16T12:00:00+00:00"},
        }],
    }  # fmt: skip


def test_a_confident_judgment_with_demand_codes_seeds_attention() -> None:
    (seed,) = derived_capabilities(_proof("SEMANTIC_JUDGMENT", 0.91), WEB)
    assert seed.capability_id == "landscaping-gardening" and seed.state.value == "POTENTIAL"


def test_doubt_or_no_routing_never_seeds() -> None:
    low = JUDGED_SEED_MIN_CONFIDENCE - 0.01
    assert derived_capabilities(_proof("SEMANTIC_JUDGMENT", low), WEB) == ()
    assert derived_capabilities(_proof("SEMANTIC_JUDGMENT", None), WEB) == ()
    assert derived_capabilities(_proof("SEMANTIC_JUDGMENT", 0.95, codes=[]), WEB) == ()


def test_only_registry_verified_or_web_anchored_proofs_hand_over() -> None:
    assert derived_capabilities(_proof("LEXICON", None), WEB)  # web subject, its own website
    canonical = "org:id:abc"
    # A website merely directed for a canonical Organization does not hand over (ADR-0091 §3).
    assert derived_capabilities(_proof("LEXICON", None, organization=canonical), canonical) == ()
    verified = _proof("LEXICON", None, link="REGISTRY_VERIFIED", organization=canonical)
    assert derived_capabilities(verified, canonical)
