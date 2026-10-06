"""Three Xeeds whose capabilities, markets and questions differ."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.observation_intelligence import (
    EvidenceCoverageMap,
    MarketRole,
    MarketScope,
    XeedObservationContext,
    derive_families,
    detect_capabilities,
    geo,
)
from domain.xignal import XignalEpistemicState

AS_OF = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)
OBSERVED = XignalEpistemicState.OBSERVED
POTENTIAL = XignalEpistemicState.POTENTIAL

HOMEPAGES = {
    "xeed:solartec": (
        "Solartec Levante. Somos una empresa valenciana especializada en instalaciones "
        "fotovoltaicas de autoconsumo para industria y administraciones públicas. "
        "También ejecutamos instalaciones eléctricas en baja tensión."
    ),
    "xeed:frionord": (
        "FrioNord. Spécialiste du froid industriel pour l'agroalimentaire : conception, "
        "installation et maintenance de chambres froides."
    ),
    "xeed:panapp": (
        "PanApp. Descarga nuestra app y pide el pan de tu barrio antes de salir de casa."
    ),
    "xeed:airtech": (
        "AirTech Systems. Industrial HVAC design, installation and maintenance for hospitals, "
        "laboratories and logistics centres."
    ),
}

MARKETS = {
    "xeed:solartec": (
        MarketScope(geo("EU/ES"), frozenset({MarketRole.PUBLIC_BUYERS, MarketRole.PRIVATE_BUSINESSES}), OBSERVED),
        MarketScope(geo("EU/FR"), frozenset({MarketRole.PUBLIC_BUYERS}), POTENTIAL),
    ),
    "xeed:frionord": (
        MarketScope(
            geo("EU/FR"),
            frozenset({MarketRole.PRIVATE_BUSINESSES, MarketRole.PUBLIC_BUYERS}),
            OBSERVED,
            buyer_segments=("food manufacturing",),
        ),
    ),
    "xeed:airtech": (MarketScope(geo("US"), frozenset({MarketRole.PUBLIC_BUYERS, MarketRole.PRIVATE_BUSINESSES}), OBSERVED),),
    "xeed:panapp": (MarketScope(geo("EU/ES"), frozenset({MarketRole.CONSUMERS}), OBSERVED),),
}  # fmt: skip


def context_for(
    xeed_id: str, *, markets: tuple[MarketScope, ...] | None = None
) -> tuple[XeedObservationContext, EvidenceCoverageMap]:
    """Generalist observation of the homepage, then the context routing may use."""

    observed_at = AS_OF - timedelta(hours=1)
    capabilities = detect_capabilities(
        text=HOMEPAGES[xeed_id],
        observation_id=f"obs:{xeed_id}:homepage",
        source_ref=f"https://{xeed_id.split(':')[1]}.example/",
        observed_at=observed_at,
    )
    coverage = EvidenceCoverageMap(max_age=timedelta(days=30))
    for market in markets or MARKETS[xeed_id]:
        coverage.record(
            question_id="what-does-it-offer",
            market=market.geography,
            source_id="official-public-website",
            evidence_ids=(f"obs:{xeed_id}:homepage",),
            observed_at=observed_at,
        )
    context = XeedObservationContext(
        xeed_id=xeed_id,
        as_of=AS_OF,
        capabilities=capabilities,
        families=derive_families(capabilities),
        markets=markets or MARKETS[xeed_id],
    )
    return context, coverage
