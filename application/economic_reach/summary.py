"""What a person needs to read about the garden: where it serves, where it may grow,
what affects it, and what is not known yet. Structure only; copy belongs to the UI/AXENT.
"""

from __future__ import annotations

from datetime import timedelta

from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.economic_reach.model import (
    CapabilityReach,
    ClaimBinding,
    EconomicOperatingModel,
    Polarity,
    ReachBasis,
)
from application.observation_intelligence.catalog import CAPABILITY_LEXICON
from domain.evidence.epistemics import Currentness

#: Unresolved-reach candidates shown per projection when some reach is known: a bounded
#: exploration frontier, so growth stays discoverable without flooding the Xeed.
EXPLORATION_LIMIT = 3

#: Reach statements age like other public page evidence read by subscribers.
GARDEN_TEMPORAL_POLICY = TemporalCurrentnessPolicy(
    policy_id="economic-garden-currentness",
    version="058-v1",
    stale_after=timedelta(days=90),
    historical_after=timedelta(days=365),
)

LEXICON_TERMS: dict[str, tuple[str, ...]] = {
    entry.capability_id: entry.terms for entry in CAPABILITY_LEXICON
}


def _places(
    reach: CapabilityReach, basis: tuple[ReachBasis, ...], *, include: bool = True
) -> list[dict[str, object]]:
    return sorted(
        (
            {
                "geography": claim.geography.code,
                "mode": None if claim.mode is None else claim.mode.value,
                "stated": claim.binding is ClaimBinding.CAPABILITY,
                "current": claim.currentness is Currentness.CURRENT,
                "evidence": claim.evidence.observation_id,
            }
            for claim in reach.claims
            if claim.basis in basis and (claim.polarity is Polarity.INCLUDED) is include
        ),
        key=str,
    )


def garden_summary(model: EconomicOperatingModel) -> dict[str, object]:
    capabilities = [
        {
            "capabilityId": reach.capability_id,
            "label": reach.label,
            "deliveryModes": sorted(mode.value for mode in reach.mode_values()),
            "operating": _places(reach, (ReachBasis.STATED_SERVICE_AREA, ReachBasis.PREMISES)),
            "expansion": _places(reach, (ReachBasis.EXPANSION_SIGNAL,)),
            "excluded": _places(reach, (ReachBasis.STATED_SERVICE_AREA,), include=False),
            "unknown": [
                item
                for item, missing in (
                    ("DELIVERY_MODE", not reach.modes),
                    ("OPERATING_REACH", not reach.claims),
                )
                if missing
            ],
        }
        for reach in model.capabilities
    ]
    return {
        "operatingModelFingerprint": model.fingerprint,
        "capabilities": capabilities,
        "exposureChannels": sorted({path.channel.value for path in model.exposure}),
        "evidence": list(model.evidence_ids),
    }
