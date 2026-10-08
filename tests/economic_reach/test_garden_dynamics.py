"""The garden over time, against noise, and as a research budget (spec 058)."""

from __future__ import annotations

from datetime import timedelta

from application.economic_reach.relevance import Family, RelevanceScope, assess_demand
from application.economic_reach.research import worth_observing
from application.observation_intelligence.catalog import eu_nuts
from application.observation_intelligence.contracts import Band, QuerySpec, geo
from application.observation_intelligence.strategy import ActionPriority, ObservationAction
from domain.xignal import XignalEpistemicState as State
from tests.economic_reach.harness import T0, DemandEvent, demand, model, page

MADRID, SEVILLA, VALENCIA = eu_nuts("ES30"), eu_nuts("ES618"), eu_nuts("ES523")
HOME = "https://installer.example.com/"
TERMS = {"hvac": ("climatizacion",)}


def test_event_naming_a_broader_place_is_unknown_not_outside() -> None:
    m = model("org:i", (page("org:i", HOME, "Instalamos climatización en Madrid."),), TERMS)
    at = T0 + timedelta(hours=1)
    national = DemandEvent("national", (geo("EU/ES"),), ("hvac",), deadline="2026-12-31")
    assert assess_demand(m, national, as_of=at).scope is RelevanceScope.UNRESOLVED_REACH
    getafe = DemandEvent(
        "getafe", (geo("EU/ES"), eu_nuts("ES300")), ("hvac",), deadline="2026-12-31"
    )
    assert assess_demand(m, getafe, as_of=at).scope is RelevanceScope.OPERATING_REACH
    cordoba = DemandEvent(
        "cordoba", (geo("EU/ES"), eu_nuts("ES613")), ("hvac",), deadline="2026-12-31"
    )
    assert assess_demand(m, cordoba, as_of=at).scope is RelevanceScope.OUTSIDE_XEED_REACH


def test_garden_evolves_without_rewriting_its_history() -> None:
    t0 = page("org:i", HOME, "Instalamos climatización en Madrid.", at=T0)
    t1 = page(
        "org:i",
        HOME.replace(".com/", ".com/empleo"),
        "Nueva delegación en Valencia. Buscamos técnicos de climatización en Valencia.",
        at=T0 + timedelta(days=10),
    )
    t4 = page(
        "org:i",
        HOME,
        "Damos servicio de climatización en toda España.",
        at=T0 + timedelta(days=200),
        n=2,
    )
    history = (t0, t1, t4)

    def scope(at, place):  # type: ignore[no-untyped-def]
        garden = model(
            "org:i", tuple(p for p in history if p.record.observed_at <= at), TERMS, at=at
        )
        return assess_demand(
            garden, demand("e", place, "hvac", deadline="2027-12-31"), as_of=at
        ), garden

    at0 = T0 + timedelta(hours=1)
    d0, g0 = scope(at0, VALENCIA)
    assert d0.scope is RelevanceScope.OUTSIDE_XEED_REACH
    d1, g1 = scope(T0 + timedelta(days=11), VALENCIA)
    assert d1.scope is RelevanceScope.PLAUSIBLE_EXPANSION and g1.fingerprint != g0.fingerprint
    # t2: the Madrid statement aged past the policy: still the garden, no longer current.
    d2, _ = scope(T0 + timedelta(days=70), MADRID)
    madrid = next(
        j for c in d2.channels for j in c.judgments if j.family is Family.GEOGRAPHIC_ECONOMIC_REACH
    )
    assert d2.scope is RelevanceScope.OPERATING_REACH
    assert (madrid.state, madrid.reason) == (State.POTENTIAL, "REACH_SUPPORT_NOT_CURRENT")
    # t4: the website now states national service; the newer statement replaces the older.
    d4, g4 = scope(T0 + timedelta(days=201), SEVILLA)
    assert d4.scope is RelevanceScope.OPERATING_REACH
    # History is derivable at any earlier cut: t0's garden is still Madrid only.
    again, g0_again = scope(at0, SEVILLA)
    assert (
        again.scope is RelevanceScope.OUTSIDE_XEED_REACH and g0_again.fingerprint == g0.fingerprint
    )
    assert len({g0.fingerprint, g1.fingerprint, g4.fingerprint}) == 3


def test_world_noise_is_retained_but_only_the_garden_reaches_the_xeed() -> None:
    salon = model(
        "org:salon",
        (
            page(
                "org:salon", "https://salon.example.com/", "Peluquería en nuestro salón en Madrid."
            ),
        ),
        {"hair": ("peluqueria",)},
    )
    regions = [
        "ES300",
        "ES613",
        "ES523",
        "ES511",
        "ES618",
        "ES243",
        "ES213",
        "DE600",
        "DE300",
        "FR101",
        "PT170",
        "ES412",
        "ES521",
        "ES620",
        "ES700",
        "ES424",
        "ES425",
        "ES111",
        "ES120",
        "ES130",
    ]
    world = tuple(
        DemandEvent(
            f"event:{n}", (eu_nuts(regions[n % len(regions)]),), ("hair",), deadline="2026-12-31"
        )
        for n in range(100)
    )
    decisions = [assess_demand(salon, event, as_of=T0 + timedelta(hours=1)) for event in world]
    surfaced = [d for d in decisions if d.surfaced]
    assert len(world) == 100 and len(decisions) == 100  # nothing deleted, every event judged
    assert len(surfaced) == 5 and {d.scope for d in surfaced} == {RelevanceScope.OPERATING_REACH}
    assert all(
        e.places[0].within(MADRID) for e, d in zip(world, decisions, strict=True) if d.surfaced
    )
    assert sum(d.scope is RelevanceScope.OUTSIDE_XEED_REACH for d in decisions) == 95


def _action(market, capability_id):  # type: ignore[no-untyped-def]
    return ObservationAction(
        action_id=f"a:{market.code}:{capability_id}",
        question_id="q",
        market=market,
        source_id="ted-search-v3",
        query=QuerySpec(demand_codes=(), geographies=(market,), capabilities=frozenset()),
        priority=ActionPriority(Band.HIGH, Band.HIGH, Band.HIGH, Band.LOW),
        reasons=(),
        depth=0,
        reobserve_after=timedelta(days=7),
        capability_id=capability_id,
    )


def test_research_is_spent_only_where_the_garden_makes_it_useful() -> None:
    salon = model(
        "org:salon",
        (
            page(
                "org:salon", "https://salon.example.com/", "Peluquería en nuestro salón en Madrid."
            ),
        ),
        {"hair": ("peluqueria",)},
    )
    assert worth_observing(_action(geo("EU/ES"), "hair"), salon)  # overlaps Madrid
    assert not worth_observing(_action(geo("EU/DE"), "hair"), salon)  # pure noise for a salon
    assert worth_observing(_action(geo("EU/DE"), None), salon)  # capability-agnostic question
    remote = model(
        "org:school",
        (page("org:school", "https://school.example.com/", "Clases de inglés online en Madrid."),),
        {"english": ("ingles",)},
    )
    assert worth_observing(_action(geo("EU/DE"), "english"), remote)  # remote: growth stays open
    unknown = model(
        "org:new",
        (page("org:new", "https://new.example.com/", "Climatización industrial."),),
        {"hvac": ("climatizacion",)},
    )
    assert worth_observing(_action(geo("EU/DE"), "hvac"), unknown)  # unknown reach: never pruned


def test_only_contributing_evidence_is_a_dependency_of_the_garden() -> None:
    reach_page = page("org:i", HOME, "Instalamos climatización en Madrid.")
    blog = page("org:i", HOME + "blog", "Nuestro equipo celebró su aniversario.")
    garden = model("org:i", (reach_page, blog), TERMS)
    assert garden.evidence_ids == (reach_page.record.observation_id,)
