"""Economic Observation Intelligence Layer: routing, adaptation, stop, epistemics."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from application.observation_intelligence import (
    AdoptionEvidence,
    AdoptionRejected,
    AdoptionStatus,
    Band,
    CoverageState,
    MarketRole,
    MarketScope,
    ObservationBudget,
    OperationalLearning,
    OpportunityCandidate,
    SourceCapability,
    SourceFindings,
    SourceRegistry,
    StopPolicy,
    StopReason,
    TaxonomyCode,
    build_brief,
    build_strategy,
    geo,
    run_observation_loop,
)
from domain.xignal import XignalEpistemicState
from pipeline.observation_intelligence import TedSearchAdapter, expert_query, parse_notices
from tests.observation_intelligence.scenarios import AS_OF, OBSERVED, context_for
from tests.observation_intelligence.ted_fixture import FixtureTedTransport

BUDGET = ObservationBudget(max_requests=10, max_amount_microunits=0, max_depth=2, max_actions=10)
PROCUREMENT = {
    SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
    SourceCapability.PUBLIC_PROCUREMENT_AWARDS,
}


class _WebsiteStub:
    """The generalist website sensor is outside this slice; it adds no procurement."""

    def observe(self, action, source):  # type: ignore[no-untyped-def]
        return SourceFindings(
            source.source_id, AS_OF, requests=1, amount_microunits=0, latency_ms=0
        )


def _run(xeed_id: str, *, budget: ObservationBudget = BUDGET, stop: StopPolicy | None = None):  # type: ignore[no-untyped-def]
    context, coverage = context_for(xeed_id)
    strategy = build_strategy(context, coverage=coverage, budget=budget, stop_policy=stop)
    transport = FixtureTedTransport()
    result = run_observation_loop(
        strategy,
        context,
        adapters={
            "ted-search-v3": TedSearchAdapter(transport, clock=lambda: AS_OF),
            "official-public-website": _WebsiteStub(),
        },
        coverage=coverage,
        learning=OperationalLearning(),
    )
    return context, coverage, strategy, result, transport


def _plan(strategy):  # type: ignore[no-untyped-def]
    return {
        (a.question_id, a.market.code, a.source_id, tuple(c.code for c in a.query.demand_codes))
        for a in strategy.actions
    }


def test_different_xeeds_get_different_observation_plans() -> None:
    solar = _run("xeed:solartec")[2]
    cold = _run("xeed:frionord")[2]
    app = _run("xeed:panapp")[2]

    assert _plan(solar) != _plan(cold)
    assert {a.market.code for a in solar.actions} == {"EU/ES", "EU/FR"}
    assert {a.market.code for a in cold.actions} == {"EU/FR"}
    # Same source capability, different classification asked of it.
    assert {c.code for a in cold.actions for c in a.query.demand_codes} == {"42513000", "50730000"}
    assert "09331200" in {c.code for a in solar.actions for c in a.query.demand_codes}
    # A consumer app is never sent to public procurement.
    assert all(d.resolution.capability not in PROCUREMENT for d in app.decisions)
    assert [a.source_id for a in app.actions] == ["official-public-website"]


def test_same_capability_routes_by_jurisdiction_to_that_jurisdictions_sources() -> None:
    us_context, us_coverage = context_for("xeed:airtech")
    eu_market = (MarketScope(geo("EU/DE"), frozenset({MarketRole.PUBLIC_BUYERS}), OBSERVED),)
    eu_context, eu_coverage = context_for("xeed:airtech", markets=eu_market)
    us = build_strategy(us_context, coverage=us_coverage, budget=BUDGET)
    eu = build_strategy(eu_context, coverage=eu_coverage, budget=BUDGET)

    def resolution(strategy, capability):  # type: ignore[no-untyped-def]
        return next(
            d.resolution for d in strategy.decisions if d.resolution.capability is capability
        )

    us_awards = resolution(us, SourceCapability.PUBLIC_PROCUREMENT_AWARDS)
    assert [s for s, _ in us_awards.pending] == ["us-sam-opportunities", "us-usaspending-awards"]
    assert all("ADAPTER_NOT_BUILT" in reasons for _, reasons in us_awards.pending)
    us_opportunities = resolution(us, SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES)
    assert [s for s, _ in us_opportunities.pending] == ["us-sam-opportunities"]
    assert dict(us_opportunities.pending)["us-sam-opportunities"][-3] == "API_KEY_NOT_PROVISIONED"
    assert us.actions == ()  # pending sources are never executed
    assert {r.capability for r in us.discovery_requests} >= PROCUREMENT

    eu_opportunities = resolution(eu, SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES)
    assert [s.source_id for s in eu_opportunities.routable] == ["ted-search-v3"]
    # TED speaks CPV only: NAICS/PSC codes of the same capability are not sent to it.
    assert {c.scheme for a in eu.actions for c in a.query.demand_codes} == {"CPV"}
    partial = [r for r in eu.discovery_requests if r.reason == "PARTIAL_COVERAGE_ONLY"]
    assert {r.capability for r in partial} == PROCUREMENT
    assert {r.jurisdiction.code for r in partial} == {"EU/DE"}


def test_specialised_route_finds_what_generalist_observation_cannot() -> None:
    context, generalist_coverage = context_for("xeed:solartec")
    # Generalist observation alone: capabilities known, procurement questions UNKNOWN.
    assert {c.capability_id for c in context.capabilities} == {
        "solar-pv-installation",
        "electrical-installation",
    }
    assert (
        generalist_coverage.state("compatible-public-tenders", geo("EU/ES"), as_of=AS_OF)
        is CoverageState.UNKNOWN
    )

    _, coverage, strategy, result, transport = _run("xeed:solartec")

    found = [c.record.record_id for c in result.candidates]
    assert found == ["ted:700101-2026", "ted:700102-2026", "ted:705005-2026"]
    adaptive = [s for s in result.steps if s.action.parent_action_id is not None]
    assert [s.action.market.code for s in adaptive] == ["EU/ES/ES5/ES52"]
    assert "45261210" in {c.code for c in adaptive[0].action.query.demand_codes}
    assert adaptive[0].candidates_added == 1  # only reachable through revealed demand
    assert result.stop_reason is StopReason.SUFFICIENT_EVIDENCE
    assert result.requests == len(transport.bodies) == 7
    # One action per capability: neither capability's demand crowds out the other's.
    assert {s.action.capability_id for s in result.steps} == {
        "electrical-installation",
        "solar-pv-installation",
    }
    assert {c.match_basis for c in result.candidates} == {
        ("DIRECT_CAPABILITY_CODE",),
        ("ADJACENT_CODE_REVEALED_BY_AWARDS",),
    }
    assert {c.opportunity_family.value for c in result.candidates} == {"PUBLIC_PROCUREMENT"}
    assert all(c.epistemic_state is XignalEpistemicState.POTENTIAL for c in result.candidates)
    assert "ted:690001-2026" not in found  # closed call: demand evidence, not opportunity
    assert (
        coverage.state("compatible-public-tenders", geo("EU/FR"), as_of=AS_OF)
        is CoverageState.SEARCHED_NO_EVIDENCE
    )

    brief = build_brief(context=context, strategy=strategy, result=result, coverage=coverage)
    text = brief.render_es()
    assert brief.headline.startswith("Encontramos 3 señales de demanda plausible")
    assert "3 en contratación pública" in brief.headline
    cards = {card.family.value: card for card in brief.cards}
    # Procurement has its own card, but it is one of several ways demand is sought.
    assert cards["PUBLIC_PROCUREMENT"].status == "FINDINGS"
    assert len(cards["PUBLIC_PROCUREMENT"].findings) == 3
    assert set(cards) == {
        "PUBLIC_PROCUREMENT",
        "PUBLIC_INVESTMENT",
        "GRANTS_AND_SUBSIDIES",
        "PLANNING_AND_PERMITS",
        "PRIVATE_PROJECT_SIGNALS",
        "REGULATION_DRIVEN_DEMAND",
        "BUYER_EXPANSION_SIGNALS",
    }
    grants = cards["GRANTS_AND_SUBSIDIES"]
    assert grants.status == "NOT_YET_OBSERVABLE" and not grants.findings
    assert grants.pending_sources == ("es-bdns", "eu-funding-tenders-portal")
    assert cards["BUYER_EXPANSION_SIGNALS"].status == "NOT_YET_OBSERVABLE"
    assert brief.question.startswith("Where is there economically plausible demand")
    assert "¿Por qué AXIGNAL miró ahí?" in text
    assert "Profundizamos en ES52" in text
    assert "Todavía no sabemos: technical requirements" in text
    assert "no implica ausencia" in text
    assert "ted.europa.eu" in text


def test_naive_run_everything_baseline_spends_as_much_and_finds_less() -> None:
    *_, guided, _ = _run("xeed:solartec")
    context, coverage = context_for("xeed:solartec")
    naive_strategy = build_strategy(
        context,
        coverage=coverage,
        budget=replace(BUDGET, max_depth=0),
        stop_policy=StopPolicy(sufficient_candidates=999, max_no_gain_streak=999),
    )
    transport = FixtureTedTransport()
    naive = run_observation_loop(
        naive_strategy,
        context,
        adapters={"ted-search-v3": TedSearchAdapter(transport, clock=lambda: AS_OF)},
        coverage=coverage,
        learning=OperationalLearning(),
    )

    assert (naive.requests, len(naive.candidates)) == (8, 2)
    assert (guided.requests, len(guided.candidates)) == (7, 3)


def test_tight_budget_spends_on_the_highest_value_questions_first() -> None:
    *_, result, _ = _run("xeed:solartec", budget=replace(BUDGET, max_requests=2))

    assert result.stop_reason is StopReason.BUDGET_EXHAUSTED
    # Highest value first, and the OBSERVED market before the POTENTIAL one.
    assert [(s.action.question_id, s.action.market.code) for s in result.steps] == [
        ("compatible-public-tenders", "EU/ES"),
        ("compatible-public-tenders", "EU/ES"),
    ]
    assert {a.market.code for a in result.unexecuted_actions} == {"EU/ES", "EU/FR"}


def test_irreducible_gaps_stop_and_become_discovery_requests() -> None:
    _, _, strategy, result, _ = _run("xeed:frionord")

    assert result.stop_reason is StopReason.IRREDUCIBLE_WITH_ADOPTED_SOURCES
    assert [c.record.record_id for c in result.candidates] == ["ted:701010-2026"]
    gap = next(g for g in strategy.gaps if g.question_id == "projects-needing-capability")
    assert gap.reason == "NO_ADOPTED_SOURCE"
    assert gap.candidate_sources == ("fr-installations-classees",)


def test_reobservation_cadence_follows_source_volatility_and_relevance() -> None:
    *_, result, _ = _run("xeed:frionord")
    cadence = {(q, m): interval for q, m, interval in result.reobservation}

    # An active opportunity keeps TED daily for both questions.
    assert cadence[("compatible-public-tenders", "EU/FR")] == str(timedelta(days=1))
    assert cadence[("revealed-public-demand", "EU/FR")] == str(timedelta(days=1))
    app = _run("xeed:panapp")[2]
    assert app.actions[0].reobserve_after == timedelta(days=90)


def test_adoption_gate_and_discovered_sources_never_self_authorize() -> None:
    registry = SourceRegistry()
    evidence = AdoptionEvidence(
        rights_reference=None,
        adapter_contract_tested=False,
        live_probe_passed=False,
        cost_per_request_microunits=None,
        reliability=Band.UNKNOWN,
        reviewed_by="",
        reviewed_at=AS_OF,
    )
    with pytest.raises(AdoptionRejected) as rejected:
        registry.adopt("us-sam-opportunities", evidence)
    assert "API_KEY_NOT_PROVISIONED" in rejected.value.failures
    assert "RIGHTS_NOT_DOCUMENTED" in rejected.value.failures

    proposed = registry.propose_candidate(
        replace(
            registry.get("es-placsp"),
            source_id="us-tx-esbd",
            adoption=AdoptionStatus.ADOPTED,
            adoption_blockers=(),
        )
    )
    assert proposed.adoption is AdoptionStatus.CANDIDATE and not proposed.routable

    adopted = registry.adopt(
        "es-placsp",
        replace(
            evidence,
            rights_reference="https://example.test/reuse-terms",
            adapter_contract_tested=True,
            live_probe_passed=True,
            cost_per_request_microunits=0,
            reliability=Band.HIGH,
            reviewed_by="reviewer",
        ),
    )
    assert adopted.routable


def test_operational_learning_moves_quality_one_band_after_enough_attempts() -> None:
    learning = OperationalLearning()
    stats = learning.for_source("ted-search-v3")
    assert learning.adjusted_quality("ted-search-v3", Band.MEDIUM) == (Band.MEDIUM, None)
    stats.attempts, stats.failures = 4, 3
    assert learning.adjusted_quality("ted-search-v3", Band.HIGH) == (
        Band.MEDIUM,
        "LEARNED_LOW_YIELD",
    )
    stats.failures, stats.candidates = 0, 4
    assert learning.adjusted_quality("ted-search-v3", Band.MEDIUM) == (
        Band.HIGH,
        "LEARNED_HIGH_YIELD",
    )
    assert learning.adjusted_quality("x", Band.UNKNOWN) == (Band.UNKNOWN, None)


def test_hypotheses_and_candidates_cannot_claim_observed() -> None:
    context, _ = context_for("xeed:solartec")
    candidate = _run("xeed:solartec")[3].candidates[0]
    with pytest.raises(ValueError, match="never be OBSERVED"):
        replace(candidate, epistemic_state=XignalEpistemicState.OBSERVED)
    with pytest.raises(ValueError, match="never OBSERVED"):
        replace(context.capabilities[0], state=XignalEpistemicState.OBSERVED)
    assert isinstance(candidate, OpportunityCandidate)
    assert all(family.stability is Band.LOW for family in context.families)  # one page only


def test_ted_adapter_speaks_the_real_search_api_contract() -> None:
    # Shape observed from the live API on 2026-10-06 (values shortened).
    payload = {
        "notices": [
            {
                "publication-number": "535544-2026",
                "notice-type": "cn-standard",
                "notice-title": {
                    "hun": "Franciaország - Nagyjavítás",
                    "fra": "Travaux d'entretien",
                },
                "buyer-name": {"fra": ["OPH Cté Agglomération du Pays Ajaccien"]},
                "classification-cpv": ["45453000", "45310000", "45453000"],
                "place-of-performance": ["FRM01", "FRA", "FRM01"],
                "publication-date": "2026-08-03+02:00",
                "deadline-receipt-tender-date-lot": ["2026-09-21+02:00", "2026-09-22+02:00"],
            },
            {"publication-number": "1-2026", "notice-type": "pin-only", "notice-title": "x"},
        ],
        "totalNoticeCount": 266,
        "timedOut": False,
    }
    (record,) = parse_notices(payload)
    assert record.kind is SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
    assert record.title == "Travaux d'entretien"
    assert {p.code for p in record.places} == {"EU/FR", "EU/FR/FRM/FRM0/FRM01"}
    assert [c.code for c in record.demand_codes] == ["45310000", "45453000"]
    assert record.deadline == "2026-09-22+02:00"
    assert record.published_at.utcoffset() == timedelta(hours=2)

    context, coverage = context_for("xeed:solartec")
    action = build_strategy(context, coverage=coverage, budget=BUDGET).actions[0]
    query = expert_query(action.query)
    assert "place-of-performance IN (ESP)" in query
    assert "notice-type IN (cn-standard cn-social)" in query
    assert "deadline-receipt-tender-date-lot>=20261006" in query
    assert query.endswith("SORT BY publication-date DESC")
    region = replace(action.query, geographies=(geo("EU/ES/ES5/ES52"),))
    assert "place-of-performance IN (ES52)" in expert_query(region)


def test_source_failure_is_recorded_not_guessed() -> None:
    class _Down:
        def post(self, body):  # type: ignore[no-untyped-def]
            return 503, {}

    context, coverage = context_for("xeed:frionord")
    strategy = build_strategy(context, coverage=coverage, budget=BUDGET)
    learning = OperationalLearning()
    result = run_observation_loop(
        strategy,
        context,
        adapters={"ted-search-v3": TedSearchAdapter(_Down(), clock=lambda: AS_OF)},
        coverage=coverage,
        learning=learning,
    )
    assert {s.failure for s in result.steps} == {"HTTP_503"}
    assert result.candidates == ()
    assert learning.for_source("ted-search-v3").failures == 2
    assert (
        coverage.state("compatible-public-tenders", geo("EU/FR"), as_of=AS_OF)
        is CoverageState.UNKNOWN
    )
    assert TaxonomyCode("GEO", "EU/FR/FRM").within(geo("EU/FR"))
    assert not TaxonomyCode("GEO", "EU/FRX").within(geo("EU/FR"))
