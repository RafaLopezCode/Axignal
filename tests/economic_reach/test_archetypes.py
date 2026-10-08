"""Falsify the garden against business archetypes (spec 058).

Each test is one sentence of the mandate: reach is per delivery channel, operating ≠
expansion ≠ exposure, UNKNOWN is never FALSE, and the world stays global.
"""

from __future__ import annotations

from datetime import timedelta

from application.economic_reach.exposure import (
    DriverEvent,
    DriverKind,
    ExposureScope,
    assess_exposure,
)
from application.economic_reach.model import ClaimBinding, DeliveryMode, ReachBasis
from application.economic_reach.relevance import Family, Outcome, RelevanceScope, assess_demand
from application.observation_intelligence.catalog import eu_nuts
from application.observation_intelligence.contracts import EvidenceRef, geo
from domain.xignal import XignalEpistemicState as State
from tests.economic_reach.harness import T0, demand, model, page

MADRID, TOLEDO, SEVILLA = eu_nuts("ES30"), eu_nuts("ES425"), eu_nuts("ES618")
VALENCIA, HAMBURG, CANARIAS = eu_nuts("ES523"), eu_nuts("DE600"), eu_nuts("ES70")
NOW = T0 + timedelta(hours=1)


def _judgment(decision, capability_id, family):  # type: ignore[no-untyped-def]
    channel = next(c for c in decision.channels if c.capability_id == capability_id)
    return next(j for j in channel.judgments if j.family is family)


def test_local_hairdresser_world_events_outside_the_garden_are_not_opportunities() -> None:
    m = model(
        "org:salon",
        (
            page(
                "org:salon",
                "https://salon.example.com/",
                "Peluquería en nuestro salón en Madrid. Cortes y color con cita previa.",
            ),
        ),
        {"hair": ("peluqueria", "cortes")},
    )
    hamburg = assess_demand(m, demand("tender:hamburg", HAMBURG, "hair"), as_of=NOW)
    assert hamburg.scope is RelevanceScope.OUTSIDE_XEED_REACH and not hamburg.surfaced
    geo_judgment = _judgment(hamburg, "hair", Family.GEOGRAPHIC_ECONOMIC_REACH)
    # Not evidenced there; never FALSE about the world or the business.
    assert geo_judgment.outcome is Outcome.UNRESOLVED and geo_judgment.state is State.UNKNOWN
    madrid = assess_demand(m, demand("tender:madrid", MADRID, "hair"), as_of=NOW)
    assert madrid.scope is RelevanceScope.OPERATING_REACH and madrid.surfaced


def test_language_school_same_capability_two_channels_two_reaches() -> None:
    m = model(
        "org:school",
        (
            page(
                "org:school",
                "https://school.example.com/",
                "Clases de inglés presenciales en nuestra academia en Madrid. "
                "Clases de inglés online en toda España.",
            ),
        ),
        {"english": ("ingles",)},
    )
    sevilla = assess_demand(m, demand("training:sevilla", SEVILLA, "english"), as_of=NOW)
    by_mode = {c.mode: c.scope for c in sevilla.channels}
    assert by_mode[DeliveryMode.PROVIDER_PREMISES] is RelevanceScope.OUTSIDE_XEED_REACH
    assert by_mode[DeliveryMode.REMOTE] is RelevanceScope.OPERATING_REACH
    assert sevilla.scope is RelevanceScope.OPERATING_REACH  # relevant through the online channel
    onsite_only = assess_demand(
        m,
        demand(
            "onsite:sevilla",
            SEVILLA,
            "english",
            required_modes=frozenset({DeliveryMode.PROVIDER_PREMISES}),
        ),
        as_of=NOW,
    )
    assert onsite_only.scope is RelevanceScope.OUTSIDE_XEED_REACH
    germany = assess_demand(m, demand("training:de", geo("EU/DE"), "english"), as_of=NOW)
    assert germany.scope is RelevanceScope.UNRESOLVED_REACH  # remote ≠ global: unknown, bounded


def test_two_capabilities_of_one_organization_never_contaminate_each_other() -> None:
    m = model(
        "org:hvac",
        (
            page(
                "org:hvac",
                "https://hvac.example.com/",
                "Instalamos climatización industrial en Madrid y Toledo. "
                "Software de monitorización energética disponible en España.",
            ),
        ),
        {"hvac": ("climatizacion",), "monitoring": ("software", "monitorizacion")},
    )
    hvac, monitoring = m.reach_for("hvac"), m.reach_for("monitoring")
    assert hvac and monitoring
    assert {c.geography for c in hvac.claims if c.binding is ClaimBinding.CAPABILITY} == {
        MADRID,
        TOLEDO,
    }
    assert {c.geography for c in monitoring.claims if c.binding is ClaimBinding.CAPABILITY} == {
        geo("EU/ES")
    }
    sevilla_hvac = assess_demand(m, demand("hvac:sevilla", SEVILLA, "hvac"), as_of=NOW)
    sevilla_soft = assess_demand(m, demand("soft:sevilla", SEVILLA, "monitoring"), as_of=NOW)
    assert sevilla_hvac.scope is RelevanceScope.OUTSIDE_XEED_REACH
    assert sevilla_soft.scope is RelevanceScope.OPERATING_REACH


def test_installer_logistics_and_regulation_are_explicit_not_assumed() -> None:
    m = model(
        "org:hvac",
        (
            page(
                "org:hvac",
                "https://hvac.example.com/",
                "Instalamos climatización en Madrid. Empresa instaladora certificada ISO 9001.",
            ),
        ),
        {"hvac": ("climatizacion", "instaladora")},
    )
    madrid = assess_demand(
        m,
        demand("hvac:madrid", MADRID, "hvac", required_certifications=("ISO 9001", "RITE")),
        as_of=NOW,
    )
    assert madrid.scope is RelevanceScope.OPERATING_REACH
    logistics = _judgment(madrid, "hvac", Family.LOGISTICS_FEASIBILITY)
    assert (logistics.outcome, logistics.state) == (Outcome.UNRESOLVED, State.UNKNOWN)  # not false
    regulation = [
        j for c in madrid.channels for j in c.judgments if j.family is Family.REGULATORY_ELIGIBILITY
    ]
    assert {j.reason for j in regulation} == {
        "QUALIFICATION_STATED:ISO 9001",
        "QUALIFICATION_UNOBSERVED:RITE",
    }
    assert "LOGISTICS_FEASIBILITY:hvac" in madrid.unknowns


def test_withdrawn_qualification_blocks_a_reachable_event_without_deleting_it() -> None:
    from application.economic_discovery.observation_memory import (
        ObservationFieldState,
        ObservedField,
    )

    m = model(
        "org:hvac",
        (
            page(
                "org:hvac",
                "https://hvac.example.com/",
                "Instalamos climatización en Madrid.",
                fields=(ObservedField("certification", "RITE", ObservationFieldState.WITHDRAWN),),
            ),
        ),
        {"hvac": ("climatizacion",)},
    )
    event = demand("hvac:madrid", MADRID, "hvac", required_certifications=("RITE",))
    decision = assess_demand(m, event, as_of=NOW)
    assert decision.scope is RelevanceScope.NOT_ACTIONABLE and not decision.surfaced
    blocked = _judgment(decision, "hvac", Family.REGULATORY_ELIGIBILITY)
    assert (blocked.outcome, blocked.state) == (Outcome.INCOMPATIBLE, State.OBSERVED)
    assert event.places == (MADRID,)  # the observed demand itself is untouched


def test_manufacturer_ships_to_stated_markets_with_customs_unknown() -> None:
    m = model(
        "org:factory",
        (
            page(
                "org:factory",
                "https://factory.example.com/",
                "Fábrica en Zaragoza. Exportamos válvulas industriales a Francia, Alemania y Portugal. "
                "Nuestros proveedores de acero están en China.",
            ),
        ),
        {"valves": ("valvulas",)},
    )
    valves = m.reach_for("valves")
    assert valves and DeliveryMode.SHIPPED in valves.mode_values()
    # The factory is premises, not a market; China is supply exposure, not a market.
    assert {c.geography for c in valves.claims if c.basis is ReachBasis.STATED_SERVICE_AREA} == {
        geo("EU/FR"),
        geo("EU/DE"),
        geo("EU/PT"),
    }
    hamburg = assess_demand(m, demand("valves:hamburg", HAMBURG, "valves"), as_of=NOW)
    assert hamburg.scope is RelevanceScope.OPERATING_REACH
    assert (
        _judgment(hamburg, "valves", Family.MARKET_ACCESS_FEASIBILITY).reason
        == "CUSTOMS_AND_TAX_UNOBSERVED"
    )
    assert any(p.channel.value == "SUPPLY_INPUTS" for p in m.exposure)


def test_saas_digital_is_not_global() -> None:
    m = model(
        "org:saas",
        (
            page(
                "org:saas",
                "https://saas.example.com/",
                "Software de facturación en la nube disponible en España y Portugal.",
            ),
        ),
        {"billing": ("facturacion",)},
    )
    assert (
        assess_demand(m, demand("it:es", SEVILLA, "billing"), as_of=NOW).scope
        is RelevanceScope.OPERATING_REACH
    )
    germany = assess_demand(m, demand("it:de", geo("EU/DE"), "billing"), as_of=NOW)
    assert germany.scope is RelevanceScope.UNRESOLVED_REACH
    assert _judgment(germany, "billing", Family.MARKET_ACCESS_FEASIBILITY).state is State.UNKNOWN
    silent = model(
        "org:saas2",
        (page("org:saas2", "https://saas2.example.com/", "Software de facturación en la nube."),),
        {"billing": ("facturacion",)},
    )
    assert (
        assess_demand(silent, demand("it:es2", SEVILLA, "billing"), as_of=NOW).scope
        is RelevanceScope.UNRESOLVED_REACH
    )


def test_ecommerce_explicit_exclusion_is_observed_negative_evidence() -> None:
    m = model(
        "org:shop",
        (
            page(
                "org:shop",
                "https://shop.example.com/",
                "Envíos de cerámica a toda España excepto Canarias.",
            ),
        ),
        {"ceramics": ("ceramica",)},
    )
    assert (
        assess_demand(m, demand("c:sev", SEVILLA, "ceramics"), as_of=NOW).scope
        is RelevanceScope.OPERATING_REACH
    )
    canarias = assess_demand(m, demand("c:can", CANARIAS, "ceramics"), as_of=NOW)
    assert canarias.scope is RelevanceScope.OUTSIDE_XEED_REACH
    excluded = _judgment(canarias, "ceramics", Family.GEOGRAPHIC_ECONOMIC_REACH)
    assert (excluded.outcome, excluded.state) == (Outcome.INCOMPATIBLE, State.OBSERVED)


def test_consultancy_remote_and_onsite_and_restaurant_supply_exposure() -> None:
    consultancy = model(
        "org:consult",
        (
            page(
                "org:consult",
                "https://consult.example.com/",
                "Consultoría estratégica presencial en Madrid. Consultoría remota por videoconferencia en toda Europa.",
            ),
        ),
        {"strategy": ("consultoria",)},
    )
    paris = assess_demand(consultancy, demand("c:paris", eu_nuts("FR101"), "strategy"), as_of=NOW)
    assert paris.scope is RelevanceScope.OPERATING_REACH
    assert {c.mode for c in paris.channels if c.scope is RelevanceScope.OPERATING_REACH} == {
        DeliveryMode.REMOTE
    }
    restaurant = model(
        "org:food",
        (
            page(
                "org:food",
                "https://food.example.com/",
                "Restaurante en Madrid: cocina de mercado en nuestro restaurante. "
                "Trabajamos con proveedores locales de producto fresco.",
            ),
        ),
        {"dining": ("restaurante", "cocina")},
    )
    shock = assess_exposure(
        restaurant,
        DriverEvent(
            "supply:shock",
            DriverKind.SUPPLY_DISRUPTION,
            EvidenceRef("obs:n", "https://news.example.com/", "x", T0),
        ),
    )
    assert shock.scope is ExposureScope.EXPOSURE


def test_oil_shock_far_away_is_exposure_never_opportunity() -> None:
    bakery = model(
        "org:bakery",
        (
            page(
                "org:bakery",
                "https://bakery.example.com/",
                "Panadería artesana en nuestra tienda en Madrid.",
            ),
        ),
        {"bread": ("panaderia",)},
    )
    oil = DriverEvent(
        "oil:me",
        DriverKind.ENERGY_PRICE,
        EvidenceRef("obs:oil", "https://news.example.com/oil", "crude up 30%", T0),
        locus=geo("ME"),
    )
    exposure = assess_exposure(bakery, oil)
    assert exposure.scope is ExposureScope.EXPOSURE and exposure.state is State.POTENTIAL
    assert exposure.explanation()["isOpportunity"] is False
    assert {p["channel"] for p in exposure.paths} == {"PREMISES_ENERGY"}
    platform = assess_exposure(
        bakery, DriverEvent("app:store", DriverKind.PLATFORM_CHANGE, oil.evidence)
    )
    assert platform.scope is ExposureScope.NOT_APPLICABLE  # no dependency on platforms observed
    rule_elsewhere = assess_exposure(
        bakery,
        DriverEvent("rule:fr", DriverKind.REGULATORY_CHANGE, oil.evidence, applies_in=geo("EU/FR")),
    )
    assert rule_elsewhere.scope is ExposureScope.NOT_APPLICABLE
    rule_here = assess_exposure(
        bakery,
        DriverEvent("rule:es", DriverKind.REGULATORY_CHANGE, oil.evidence, applies_in=geo("EU/ES")),
    )
    assert rule_here.scope is ExposureScope.EXPOSURE


def test_expansion_comes_from_own_preparatory_acts_and_stays_potential() -> None:
    m = model(
        "org:hvac",
        (
            page(
                "org:hvac",
                "https://hvac.example.com/",
                "Instalamos climatización en Madrid. Nueva delegación en Valencia. "
                "Buscamos técnicos de climatización en Valencia.",
            ),
        ),
        {"hvac": ("climatizacion",)},
    )
    valencia = assess_demand(m, demand("hvac:vlc", VALENCIA, "hvac"), as_of=NOW)
    assert valencia.scope is RelevanceScope.PLAUSIBLE_EXPANSION
    geo_judgment = _judgment(valencia, "hvac", Family.GEOGRAPHIC_ECONOMIC_REACH)
    assert (
        geo_judgment.state is State.POTENTIAL
        and "FACILITY" in geo_judgment.reason
        and "HIRING" in geo_judgment.reason
    )
    # Demand somewhere is never itself expansion evidence.
    sevilla = assess_demand(m, demand("hvac:sev", SEVILLA, "hvac"), as_of=NOW)
    assert sevilla.scope is RelevanceScope.OUTSIDE_XEED_REACH


def test_headquarters_demonym_or_brand_is_not_reach() -> None:
    m = model(
        "org:solar",
        (
            page(
                "org:solar",
                "https://solar.example.com/",
                "Solartec Levante. Somos una empresa valenciana de instalaciones fotovoltaicas.",
            ),
        ),
        {"solar": ("fotovoltaicas",)},
    )
    assert not m.has_reach_evidence
    unknown = assess_demand(m, demand("solar:mad", MADRID, "solar"), as_of=NOW)
    assert unknown.scope is RelevanceScope.UNRESOLVED_REACH  # UNKNOWN, not excluded


def test_ambiguous_mode_or_vans_do_not_prove_national_reach() -> None:
    m = model(
        "org:van",
        (
            page(
                "org:van",
                "https://van.example.com/",
                "Disponemos de furgonetas propias. Reparaciones a domicilio en Madrid.",
            ),
        ),
        {"repair": ("reparaciones",)},
    )
    national = assess_demand(m, demand("repair:sev", SEVILLA, "repair"), as_of=NOW)
    assert national.scope is RelevanceScope.OUTSIDE_XEED_REACH
    assert (
        assess_demand(m, demand("repair:mad", MADRID, "repair"), as_of=NOW).scope
        is RelevanceScope.OPERATING_REACH
    )
    assert (
        _judgment(national, "repair", Family.GEOGRAPHIC_ECONOMIC_REACH).state is not State.OBSERVED
    )
