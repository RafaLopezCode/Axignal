"""The reach model's fingerprint is a total order, with or without empty claim fields.

Found on the biocultor.com canary (2026-10-17): once a web-anchored subject reached the
canonical projection path (#302), two reach claims that differed only in a missing delivery
mode made the fingerprint raise TypeError, so the observation failed and was retried forever.
"""

from __future__ import annotations

from datetime import UTC, datetime

from application.economic_reach.model import (
    CapabilityReach,
    ClaimBinding,
    DeliveryMode,
    EconomicOperatingModel,
    ReachBasis,
    ReachClaim,
)
from application.observation_intelligence.contracts import EvidenceRef, TaxonomyCode
from domain.evidence.epistemics import Currentness

NOW = datetime(2026, 10, 17, tzinfo=UTC)
EVIDENCE = EvidenceRef("fo:1", "https://biocultor.example.com/", "Envío a toda España.", NOW)


def _claim(mode: DeliveryMode | None) -> ReachClaim:
    return ReachClaim(
        geography=TaxonomyCode("GEO", "EU/ES"),
        basis=next(iter(ReachBasis)),
        binding=next(iter(ClaimBinding)),
        evidence=EVIDENCE,
        currentness=Currentness.CURRENT,
        mode=mode,
    )


def _model(*claims: ReachClaim) -> EconomicOperatingModel:
    reach = CapabilityReach("fertilisers-soil-amendments", "Fertilisers", (), claims, ())
    return EconomicOperatingModel("org:web:x", (reach,), (), ("fo:1",))


def test_claims_with_and_without_a_mode_have_a_stable_fingerprint() -> None:
    with_mode, without = _claim(next(iter(DeliveryMode))), _claim(None)
    first = _model(with_mode, without).fingerprint  # raised TypeError before
    assert first == _model(without, with_mode).fingerprint  # order of evidence never matters


def test_rows_without_empty_fields_keep_their_previous_order() -> None:
    from application.economic_reach.model import _total_order

    rows: list[list[object]] = [["b", 2, True], ["a", 3, False], ["a", 1, True]]
    assert sorted(rows, key=_total_order) == sorted(rows)  # stored fingerprints stay valid
