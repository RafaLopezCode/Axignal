from application.economic_discovery.research_value import (
    ResearchValueContext,
    ResearchValueDisposition,
    ResearchValuePolicy,
    ResearchValueReason,
    ResearchValueSignal,
    decide_research_value,
)


def _policy() -> ResearchValuePolicy:
    return ResearchValuePolicy(
        policy_id="research-value",
        version="1",
        research_signals=frozenset(
            {
                ResearchValueSignal.MATERIALITY,
                ResearchValueSignal.DECISION_IMPACT,
                ResearchValueSignal.REUSE_POTENTIAL,
                ResearchValueSignal.FRESHNESS_NEED,
            }
        ),
    )


def _context(
    *,
    signals: frozenset[ResearchValueSignal] = frozenset(),
    rights: bool = True,
    capability: bool = True,
    budget: bool | None = True,
    no_progress: bool = False,
) -> ResearchValueContext:
    return ResearchValueContext(
        subject_id="org:1",
        state_fingerprint="state:1",
        dimension_id="reputation",
        missing_requirements=("document.reviews.visible_text",),
        value_signals=signals,
        rights_permit=rights,
        capability_available=capability,
        budget_permits=budget,
        known_source_available=False,
        no_progress_observed=no_progress,
    )


def test_low_value_gap_is_retained_unknown_without_research() -> None:
    decision = decide_research_value(context=_context(), policy=_policy())

    assert decision.disposition is ResearchValueDisposition.RETAIN_UNKNOWN
    assert decision.reason_codes == (ResearchValueReason.NO_VALUE_SIGNAL,)


def test_material_gap_can_research_now_when_governance_allows() -> None:
    decision = decide_research_value(
        context=_context(signals=frozenset({ResearchValueSignal.MATERIALITY})),
        policy=_policy(),
    )

    assert decision.disposition is ResearchValueDisposition.RESEARCH_NOW
    assert decision.reason_codes == (ResearchValueReason.MATERIALITY,)


def test_rights_denial_blocks_research_even_when_material() -> None:
    decision = decide_research_value(
        context=_context(
            signals=frozenset({ResearchValueSignal.MATERIALITY}),
            rights=False,
        ),
        policy=_policy(),
    )

    assert decision.disposition is ResearchValueDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS
    assert decision.reason_codes == (ResearchValueReason.RIGHTS_DENIED,)


def test_unknown_budget_defers_instead_of_guessing_zero_cost() -> None:
    decision = decide_research_value(
        context=_context(
            signals=frozenset({ResearchValueSignal.DECISION_IMPACT}),
            budget=None,
        ),
        policy=_policy(),
    )

    assert decision.disposition is ResearchValueDisposition.DEFER
    assert decision.reason_codes == (ResearchValueReason.BUDGET_UNKNOWN,)


def test_no_progress_defers_repeated_research() -> None:
    decision = decide_research_value(
        context=_context(
            signals=frozenset({ResearchValueSignal.REUSE_POTENTIAL}),
            no_progress=True,
        ),
        policy=_policy(),
    )

    assert decision.disposition is ResearchValueDisposition.DEFER
    assert decision.reason_codes == (ResearchValueReason.NO_PROGRESS,)


def test_decision_is_replay_stable() -> None:
    first = decide_research_value(
        context=_context(signals=frozenset({ResearchValueSignal.FRESHNESS_NEED})),
        policy=_policy(),
    )
    second = decide_research_value(
        context=_context(signals=frozenset({ResearchValueSignal.FRESHNESS_NEED})),
        policy=_policy(),
    )

    assert first == second
    assert first.context_fingerprint == second.context_fingerprint
