"""Synthetic acceptance cases for conditioned public-offer understanding.

These fixtures exercise interpretation contracts, not real-world evaluator quality.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from application.first_observation.contracts import RunLedger, SiteReading
from application.first_observation.rights import ContentRights
from application.first_observation.site import (
    DeclaredAddress,
    DeclaredIdentifier,
    PageReading,
    read_page,
)
from application.first_observation.understanding import compare, measure, public_report
from application.semantic_layer.cascade import CascadePolicy, SemanticCascade
from application.semantic_layer.contracts import BatchResult, SemanticAnswer
from application.semantic_layer.ledger import JEV_1_13_PRICE, CostLedger, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from tests.semantic_layer.fakes import FakeReasoning, FakeSystemOne

NOW = datetime(2026, 10, 9, 12, tzinfo=UTC)
BASE = "https://manolo.example.com/"
RIGHTS = ContentRights(provider_input=True, public_offer_input=True, decided_at=NOW)


def _page(url: str, html: str, *, language: str | None = "en") -> PageReading:
    if language:
        html = html.replace("<html>", f'<html lang="{language}">', 1)
    return read_page(
        url=url,
        html=html,
        observed_at=NOW,
        content_fingerprint="sha256:" + hashlib.sha256((url + html).encode()).hexdigest(),
        artifact_ref=None,
    )


def _site(
    *pages: PageReading, coverage: str = "BOUNDED_COMPLETE", failure: str | None = None
) -> SiteReading:
    return SiteReading(
        origin=BASE,
        observed_at=NOW,
        robots=None,
        pages=tuple(pages),
        failure=failure,
        perception_coverage=coverage,
    )


def _citation_for(batch: Any, phrase: str) -> str:
    quotations = batch.state["quotations"]
    for item in quotations:
        if phrase.casefold() in item["text"].casefold():
            return str(item["id"])
    raise AssertionError(f"synthetic fixture did not expose citation containing {phrase!r}")


def _rule(
    decisions: Mapping[str, str | Callable[[Any], str]],
) -> Callable[[Any, Any], tuple[str, float]]:
    def decide(batch: Any, question: Any) -> tuple[str, float]:
        if question.question_id == "pu_control_positive":
            return "true", 0.99
        if question.question_id == "pu_control_negative":
            return "false", 0.99
        value = decisions.get(question.question_id, "UNKNOWN")
        return (value(batch) if callable(value) else value), 0.99

    return decide


def _cascade(
    decisions: Mapping[str, str | Callable[[Any], str]],
    *,
    fail: str | None = None,
    budget: int = 12_000,
    memory: InMemoryJudgmentMemory | None = None,
    model: str = "jev-1.13.0",
) -> tuple[SemanticCascade, FakeSystemOne]:
    judge = FakeSystemOne(_rule(decisions), fail=fail)
    judge.model = model
    cascade = SemanticCascade(
        judge=judge,
        ledger=CostLedger(prices=(JEV_1_13_PRICE,)),
        budget=SemanticBudget(max_system_one_input_tokens=budget),
        policy=CascadePolicy(),
        memory=memory,
    )
    return cascade, judge


def _measure(
    site: SiteReading | None,
    decisions: Mapping[str, str | Callable[[Any], str]],
    *,
    rights: ContentRights = RIGHTS,
    rights_for: Callable[[str], ContentRights] | None = None,
    cascade: SemanticCascade | None = None,
    fail: str | None = None,
    budget: int = 12_000,
    ledger: RunLedger | None = None,
) -> tuple[dict[str, Any], FakeSystemOne | None]:
    if cascade is None:
        cascade, judge = _cascade(decisions, fail=fail, budget=budget)
    else:
        judge = cascade.judge if isinstance(cascade.judge, FakeSystemOne) else None
    report = measure(
        site,
        now=NOW,
        rights=rights,
        rights_for=rights_for or (lambda _url: rights),
        cascade_factory=lambda: cascade,
        ledger=ledger or RunLedger(),
        token_budget=budget,
    )
    return report, judge


def _states(report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(item["dimension"]): item for item in report["dimensions"]}


def test_minimal_manolo_has_evidence_backed_offer_strength_and_conditional_omission() -> None:
    page = _page(
        BASE,
        "<html><head><title>Taller de Manolo</title></head><body>"
        "<h1>Hola, soy Manolo</h1><p>Reparamos zapatos.</p></body></html>",
    )
    choices: dict[str, str | Callable[[Any], str]] = {
        "pu_offer": lambda batch: _citation_for(batch, "Reparamos zapatos."),
        "pu_audience": "NOT_STATED",
        "pu_outcome": "NOT_STATED",
    }

    report, judge = _measure(_site(page), choices)

    assert report["status"] == "MEASURED"
    dimensions = _states(report)
    assert dimensions["offer"]["state"] == "STRENGTH"
    assert dimensions["offer"]["citationIds"] == [
        _citation_for(judge.calls[0], "Reparamos zapatos.")  # type: ignore[union-attr]
    ]
    assert dimensions["audience"]["state"] == "CONSTRUCTIVE_GAP"
    assert dimensions["audience"]["proposal"] == "MAKE_AUDIENCE_EXPLICIT_IF_INTENDED"
    assert dimensions["outcome"]["state"] == "CONSTRUCTIVE_GAP"
    assert "CONDITIONED_NOT_CANONICAL" in report["authority"]
    assert report["trace"] and all(item["answer"]["distribution"] for item in report["trace"])
    assert "confidence" not in json.dumps(public_report(report, now=NOW)).casefold()


def test_clear_offer_audience_and_outcome_need_no_invented_critique() -> None:
    page = _page(
        BASE,
        "<html><head><title>Manolo Shoe Repair</title></head><body>"
        "<h1>We repair shoes for households.</h1>"
        "<p>Our repairs help shoes last longer.</p></body></html>",
    )
    report, _ = _measure(
        _site(page),
        {
            "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
            "pu_audience": lambda batch: _citation_for(batch, "households"),
            "pu_outcome": lambda batch: _citation_for(batch, "last longer"),
        },
    )

    assert report["status"] == "MEASURED"
    assert {item["state"] for item in report["dimensions"]} == {"STRENGTH"}
    assert all(item["proposal"] is None for item in report["dimensions"])


def test_incomplete_acquisition_never_turns_not_stated_into_a_gap() -> None:
    page = _page(BASE, "<html><body><p>Reparamos zapatos.</p></body></html>")
    report, _ = _measure(
        _site(page, coverage="NOT_STATED"),
        {"pu_offer": "NOT_STATED", "pu_audience": "NOT_STATED", "pu_outcome": "NOT_STATED"},
    )

    assert report["status"] == "MEASURED"
    assert report["coverage"] == "NOT_STATED"
    assert all(item["state"] == "UNCERTAIN" for item in report["dimensions"])
    assert all(item["cause"] == "OBSERVATION_MISS" for item in report["dimensions"])
    assert all(item["proposal"] is None for item in report["dimensions"])


@pytest.mark.parametrize(
    ("fail", "wrong_control"),
    [("provider unavailable", False), (None, True)],
    ids=("provider-failure", "failed-positive-control"),
)
def test_provider_failure_or_failed_control_is_instrument_error_not_company_gap(
    fail: str | None, wrong_control: bool
) -> None:
    page = _page(BASE, "<html><body><p>Reparamos zapatos.</p></body></html>")
    cascade: SemanticCascade | None = None
    if wrong_control:
        judge = FakeSystemOne(
            lambda _batch, question: (
                "false"
                if question.question_id == "pu_control_positive"
                else "false"
                if question.question_id == "pu_control_negative"
                else "NOT_STATED",
                0.99,
            )
        )
        cascade = SemanticCascade(
            judge=judge,
            ledger=CostLedger(prices=(JEV_1_13_PRICE,)),
            budget=SemanticBudget(max_system_one_input_tokens=12_000),
        )
    report, _ = _measure(
        _site(page),
        {"pu_offer": "NOT_STATED", "pu_audience": "NOT_STATED", "pu_outcome": "NOT_STATED"},
        fail=fail,
        cascade=cascade,
    )

    assert report["status"] == "NON_INFORMATIVE"
    assert report["cause"] == "INSTRUMENT_ERROR"
    assert all(item["proposal"] is None for item in report["dimensions"])


def test_conflicting_pages_remain_unresolved_with_both_exact_sources() -> None:
    first = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")
    second_url = BASE + "services"
    second = _page(second_url, "<html><body><p>We do not offer shoe repair.</p></body></html>")
    report, judge = _measure(
        _site(first, second),
        {
            "pu_offer": "CONFLICTING",
            "pu_audience": "NOT_STATED",
            "pu_outcome": "NOT_STATED",
        },
    )

    assert report["status"] == "MEASURED"
    offer = _states(report)["offer"]
    assert offer["state"] == "UNRESOLVED"
    assert offer["cause"] == "CONTRADICTION"
    assert offer["proposal"] == "RECONCILE_STATEMENTS_IF_SAME_CURRENT_OFFER"
    assert {citation["url"] for citation in report["citations"]} >= {BASE, second_url}
    assert {citation["id"] for citation in report["citations"]}.issubset(offer["citationIds"])
    assert judge is not None and all(item["answer"]["distribution"] for item in report["trace"])


def test_content_change_is_comparable_but_model_language_and_source_drift_are_not() -> None:
    first_page = _page(
        BASE, '<html><body><p lang="en">We repair shoes for households.</p></body></html>'
    )
    changed_page = _page(
        BASE,
        '<html><body><p lang="en">We repair shoes for households and help them last longer.</p></body></html>',
    )
    choices = {
        "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
        "pu_audience": lambda batch: _citation_for(batch, "households"),
        "pu_outcome": "NOT_STATED",
    }
    first, _ = _measure(_site(first_page), choices)
    changed, _ = _measure(_site(changed_page), choices)
    model_cascade, _ = _cascade(choices, model="jev-next")
    model_changed, _ = _measure(_site(changed_page), choices, cascade=model_cascade)
    language_page = _page(
        BASE,
        "<html><body><p>Nous réparons les chaussures des familles.</p></body></html>",
        language="fr",
    )
    language_changed, _ = _measure(_site(language_page), choices)
    source_changed, _ = _measure(
        _site(changed_page, _page(BASE + "about", "<html><body><p>About.</p></body></html>")),
        choices,
    )

    assert compare(changed, first)["state"] == "COMPARABLE"
    assert (
        compare(changed, first)["meaning"]
        == "INTERPRETATION_CHANGE_NOT_PROVEN_BUSINESS_IMPROVEMENT"
    )
    assert compare(model_changed, first)["state"] == "NOT_COMPARABLE"
    assert compare(language_changed, first)["state"] == "NOT_COMPARABLE"
    assert compare(source_changed, first)["state"] == "NOT_COMPARABLE"


def test_same_strength_with_a_different_selected_quote_reports_basis_change() -> None:
    page = _page(
        BASE,
        "<html><body><p>We repair shoes for households.</p>"
        "<p>We restore leather boots for households.</p></body></html>",
    )
    previous, _ = _measure(
        _site(page),
        {
            "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
            "pu_audience": lambda batch: _citation_for(batch, "households"),
            "pu_outcome": "NOT_STATED",
        },
    )
    current, _ = _measure(
        _site(page),
        {
            "pu_offer": lambda batch: _citation_for(batch, "restore leather boots"),
            "pu_audience": lambda batch: _citation_for(batch, "households"),
            "pu_outcome": "NOT_STATED",
        },
    )

    assert _states(previous)["offer"]["state"] == "STRENGTH"
    assert _states(current)["offer"]["state"] == "STRENGTH"
    compared = compare(current, previous)
    [change] = [item for item in compared["changes"] if item["dimension"] == "offer"]

    def quote_text(values: Any) -> set[str]:
        return {value if isinstance(value, str) else str(value["quote"]) for value in values}

    assert change["kind"] == "INTERPRETATION_BASIS_CHANGED"
    assert quote_text(change["beforeQuotations"]) == {"We repair shoes for households."}
    assert quote_text(change["afterQuotations"]) == {"We restore leather boots for households."}


def test_remeasurement_one_hour_later_does_not_create_a_false_change() -> None:
    page = _page(
        BASE,
        "<html><body><p>We repair shoes for households.</p></body></html>",
    )
    decisions = {
        "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
        "pu_audience": lambda batch: _citation_for(batch, "households"),
        "pu_outcome": "NOT_STATED",
    }
    previous, _ = _measure(_site(page), decisions)
    current = deepcopy(previous)
    current["reportId"] = "synthetic-later-report-id"
    current["measuredAt"] = (NOW + timedelta(hours=1)).isoformat()

    compared = compare(current, previous)

    assert compared["state"] == "COMPARABLE"
    assert compared["changes"] == []


def test_report_expiry_uses_the_earliest_page_specific_rights_deadline() -> None:
    from application.first_observation.rights import RegisteredContentRights
    from tools.runtime.first_observation import website_rights_entry

    home_entry = website_rights_entry(
        host="manolo.example.com",
        basis="synthetic home-page offer permission",
        raw_retention_days=90,
        metadata_retention_days=120,
    )
    linked_entry = website_rights_entry(
        host="services.manolo.example.com",
        basis="synthetic linked-page offer permission",
        raw_retention_days=7,
        metadata_retention_days=30,
    )
    policy = RegisteredContentRights(
        (home_entry, linked_entry),
        provider_input=frozenset({home_entry.source_id, linked_entry.source_id}),
        public_offer_input=frozenset({home_entry.source_id, linked_entry.source_id}),
    )
    home_rights = policy.rights_for(BASE, now=NOW)
    linked_url = "https://services.manolo.example.com/services"
    linked_rights = policy.rights_for(linked_url, now=NOW)
    pages = (
        _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>"),
        _page(linked_url, "<html><body><p>We restore leather boots.</p></body></html>"),
    )
    report, _ = _measure(
        _site(*pages),
        {
            "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
            "pu_audience": lambda batch: _citation_for(batch, "households"),
            "pu_outcome": "NOT_STATED",
        },
        rights=home_rights,
        rights_for=lambda url: policy.rights_for(url, now=NOW),
    )

    expected_expiry = min(home_rights.private_until(NOW), linked_rights.private_until(NOW))
    assert report["status"] == "MEASURED"
    assert datetime.fromisoformat(report["contentExpiresAt"]) == expected_expiry
    # The 7-day linked page bounds the whole report; 30 days is only the no-entry default.
    assert expected_expiry == NOW + timedelta(days=7)


def test_rights_denied_skips_judge_and_unsafe_contact_quotes_are_not_sent() -> None:
    contact_page = _page(
        BASE,
        "<html><body><p>We repair shoes.</p>"
        "<p>Contact hello@manolo.example or call +34 600 123 456.</p></body></html>",
    )
    decisions = {"pu_offer": lambda batch: _citation_for(batch, "repair shoes")}
    denied, judge = _measure(
        _site(contact_page), decisions, rights=ContentRights(provider_input=False, decided_at=NOW)
    )

    assert denied["cause"] == "PROVIDER_INPUT_NOT_AUTHORIZED"
    assert denied["status"] == "NOT_MEASURED"
    assert judge is not None and judge.calls == []

    report, judge = _measure(
        _site(contact_page), {**decisions, "pu_audience": "NOT_STATED", "pu_outcome": "NOT_STATED"}
    )
    assert judge is not None and len(judge.calls) == 1
    state = json.dumps(judge.calls[0].state, ensure_ascii=False).casefold()
    assert "hello@manolo.example" not in state
    assert "+34 600 123 456" not in state
    assert report["coverage"] == "INCOMPLETE"
    assert _states(report)["audience"]["cause"] == "OBSERVATION_MISS"
    assert _states(report)["audience"]["proposal"] is None


def test_routing_only_rights_do_not_authorize_public_offer_text_input() -> None:
    page = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")
    routing_only = ContentRights(
        provider_input=True,
        public_offer_input=False,
        decided_at=NOW,
    )

    report, judge = _measure(_site(page), {"pu_offer": "NOT_STATED"}, rights=routing_only)

    assert report["status"] == "NOT_MEASURED"
    assert report["cause"] == "PROVIDER_INPUT_NOT_AUTHORIZED"
    assert judge is not None and judge.calls == []
    assert report["sourceRights"][0]["providerInput"] is True
    assert report["sourceRights"][0]["publicOfferInput"] is False


def test_denied_linked_page_purpose_blocks_entire_provider_batch_and_records_basis() -> None:
    from application.first_observation.rights import RegisteredContentRights
    from tools.runtime.first_observation import website_rights_entry

    entry = website_rights_entry(
        host="manolo.example.com",
        basis="synthetic governed offer-text permission",
        raw_retention_days=30,
        metadata_retention_days=90,
    )
    home = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")
    linked_url = BASE + "services"
    linked = _page(linked_url, "<html><body><p>We restore leather boots.</p></body></html>")
    granted_policy = RegisteredContentRights(
        (entry,),
        provider_input=frozenset({entry.source_id}),
        public_offer_input=frozenset({entry.source_id}),
    )
    granted = granted_policy.rights_for(BASE, now=NOW)
    linked_denied = ContentRights(
        entry=entry,
        provider_input=True,
        public_offer_input=False,
        decided_at=NOW,
    )

    report, judge = _measure(
        _site(home, linked),
        {"pu_offer": lambda batch: _citation_for(batch, "repair shoes")},
        rights=granted,
        rights_for=lambda url: (
            linked_denied if url == linked_url else granted_policy.rights_for(url, now=NOW)
        ),
    )

    assert report["status"] == "NOT_MEASURED"
    assert report["cause"] == "PROVIDER_INPUT_NOT_AUTHORIZED"
    assert judge is not None and judge.calls == []
    rights_by_url = {item["url"]: item for item in report["sourceRights"]}
    assert rights_by_url[BASE]["publicOfferInput"] is True
    assert rights_by_url[linked_url]["publicOfferInput"] is False
    assert rights_by_url[BASE]["basisRef"] == granted.basis_ref
    assert rights_by_url[linked_url]["basisRef"] == granted.basis_ref


def test_low_confidence_offer_interpretation_remains_uncertain_without_critique() -> None:
    page = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")

    def low_confidence(batch: Any, question: Any) -> tuple[str, float]:
        if question.question_id == "pu_control_positive":
            return "true", 0.99
        if question.question_id == "pu_control_negative":
            return "false", 0.99
        if question.question_id == "pu_offer":
            return _citation_for(batch, "repair shoes"), 0.51
        return "NOT_STATED", 0.99

    judge = FakeSystemOne(low_confidence)
    cascade = SemanticCascade(
        judge=judge,
        ledger=CostLedger(prices=(JEV_1_13_PRICE,)),
        budget=SemanticBudget(max_system_one_input_tokens=12_000),
    )
    report, _ = _measure(_site(page), {}, cascade=cascade)

    offer = _states(report)["offer"]
    assert report["status"] == "MEASURED"
    assert offer["state"] == "UNCERTAIN"
    assert offer["proposal"] is None
    trace = next(item for item in report["trace"] if item["questionId"] == "pu_offer")
    distribution = trace["answer"]["distribution"]
    assert distribution[trace["answer"]["selected"]] == 0.51
    public = public_report(report, now=NOW)
    assert "trace" not in public
    assert "distribution" not in json.dumps(public).casefold()


def test_partial_dimension_answer_outside_choice_contract_is_instrument_error() -> None:
    page = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")

    class OutsideOfferChoice(FakeSystemOne):
        def judge(self, batch: Any) -> BatchResult:
            result = super().judge(batch)
            answers = []
            for item in result.answers:
                if item.question_id == "pu_offer":
                    item = SemanticAnswer(
                        question_id=item.question_id,
                        primitive=item.primitive,
                        source=item.source,
                        evaluator=item.evaluator,
                        model=item.model,
                        distribution=(
                            *item.distribution[:-1],
                            ("OUTSIDE_CHOICE_SPACE", item.distribution[-1][1]),
                        ),
                        selected=item.selected,
                        confidence=item.confidence,
                    )
                answers.append(item)
            return BatchResult(
                result.batch_id,
                result.evaluator,
                result.model,
                tuple(answers),
                result.usage,
                result.latency_ms,
            )

    judge = OutsideOfferChoice(
        _rule(
            {
                "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
                "pu_audience": "NOT_STATED",
                "pu_outcome": "NOT_STATED",
            }
        )
    )
    cascade = SemanticCascade(
        judge=judge,
        ledger=CostLedger(prices=(JEV_1_13_PRICE,)),
        budget=SemanticBudget(max_system_one_input_tokens=12_000),
    )
    report, _ = _measure(_site(page), {}, cascade=cascade)

    assert report["status"] == "MEASURED"  # valid controls; one invalid dimension only
    offer = _states(report)["offer"]
    assert offer["state"] == "UNCERTAIN"
    assert offer["cause"] == "INSTRUMENT_ERROR"
    assert offer["proposal"] is None
    offer_trace = next(item for item in report["trace"] if item["questionId"] == "pu_offer")
    assert offer_trace["resolution"] == "FAILED"
    assert offer_trace["reason"] == "ANSWER_OUTSIDE_CONTRACT"


def test_person_schema_identity_and_contact_content_are_excluded_with_incomplete_coverage() -> None:
    person = _page(
        BASE + "team",
        '<html><head><script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"Person","name":"Manolo Ruiz",'
        '"identifier":"person-id-4321","email":"manolo@example.test",'
        '"telephone":"+34 600 123 456","address":{"@type":"PostalAddress",'
        '"streetAddress":"Calle Privada 7","addressLocality":"Madrid"}}'
        "</script></head><body><p>Manolo Ruiz, phone +34 600 123 456.</p></body></html>",
    )
    person = replace(
        person,
        names=("Manolo Ruiz",),
        identifiers=(DeclaredIdentifier("PERSON_ID", "person-id-4321"),),
        addresses=(DeclaredAddress("ES", None, "Madrid"),),
    )
    offer = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")
    assert "Person" in person.schema_types
    assert person.identifiers and person.addresses and person.names
    decisions = {
        "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
        "pu_audience": "NOT_STATED",
        "pu_outcome": "NOT_STATED",
    }

    report, judge = _measure(_site(person, offer), decisions)

    assert report["status"] == "MEASURED"
    assert report["coverage"] == "INCOMPLETE"
    assert judge is not None and len(judge.calls) == 1
    state = json.dumps(judge.calls[0].state, ensure_ascii=False).casefold()
    for private in (
        "manolo ruiz",
        "person-id-4321",
        "manolo@example.test",
        "+34 600 123 456",
        "calle privada 7",
        "madrid",
        "team",
    ):
        assert private not in state
    assert "we repair shoes for households" in state
    assert all(
        not any(token in item["quote"].casefold() for token in ("manolo", "person-id", "600 123"))
        for item in report["citations"]
    )
    audience = _states(report)["audience"]
    assert audience["state"] == "UNCERTAIN"
    assert audience["cause"] == "OBSERVATION_MISS"
    assert audience["proposal"] is None


def test_public_offer_never_escalates_to_reasoning_even_if_caller_marks_question_escalable() -> (
    None
):
    page = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")

    def uncertain_offer(batch: Any, question: Any) -> tuple[str, float]:
        if question.question_id == "pu_control_positive":
            return "true", 0.99
        if question.question_id == "pu_control_negative":
            return "false", 0.99
        if question.question_id == "pu_offer":
            return _citation_for(batch, "repair shoes"), 0.51
        return "NOT_STATED", 0.99

    judge = FakeSystemOne(uncertain_offer)
    reasoning = FakeReasoning(lambda _question: "NOT_STATED")
    cascade = SemanticCascade(
        judge=judge,
        ledger=CostLedger(prices=(JEV_1_13_PRICE,)),
        budget=SemanticBudget(max_system_one_input_tokens=12_000, max_reasoning_calls=5),
        policy=CascadePolicy(escalable=frozenset({"pu_offer"})),
        escalation=reasoning,
    )
    report, _ = _measure(_site(page), {}, cascade=cascade)

    assert not reasoning.calls
    assert _states(report)["offer"]["state"] == "UNCERTAIN"
    assert _states(report)["offer"]["proposal"] is None


def test_budget_failure_abstains_and_does_not_create_a_gap() -> None:
    page = _page(BASE, "<html><body><p>Reparamos zapatos.</p></body></html>")
    report, judge = _measure(
        _site(page),
        {"pu_offer": "NOT_STATED", "pu_audience": "NOT_STATED", "pu_outcome": "NOT_STATED"},
        budget=0,
    )

    assert report["status"] == "NOT_MEASURED"
    assert report["cause"] == "BUDGET_EXHAUSTED"
    assert report["dimensions"] == []
    assert judge is not None and judge.calls == []


def test_exact_judgment_reuse_is_traced_and_not_counted_as_an_independent_replica() -> None:
    page = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")
    memory = InMemoryJudgmentMemory()
    choices = {
        "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
        "pu_audience": lambda batch: _citation_for(batch, "households"),
        "pu_outcome": "NOT_STATED",
    }
    cascade, judge = _cascade(choices, memory=memory)
    first, _ = _measure(_site(page), choices, cascade=cascade)
    second, _ = _measure(_site(page), choices, cascade=cascade)

    assert first["execution"] == "EVALUATED"
    assert second["execution"] == "EXACT_JUDGMENT_REUSE"
    assert len(judge.calls) == 1
    assert second["conditions"]["sampleSize"] == 1
    assert second["conditions"]["replicaPolicy"] == "ONE_EXECUTION_OR_EXACT_JUDGMENT_REUSE"
    assert second["trace"] and all(item["reused"] for item in second["trace"])


def test_public_projection_marks_stale_and_expired_without_leaking_expired_citations() -> None:
    page = _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")
    report, _ = _measure(
        _site(page),
        {
            "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
            "pu_audience": lambda batch: _citation_for(batch, "households"),
            "pu_outcome": "NOT_STATED",
        },
    )

    stale = public_report(report, now=NOW + timedelta(days=8))
    expired = public_report(report, now=NOW + timedelta(days=31))
    assert stale["currentness"] == "STALE"
    assert stale["citations"]
    assert expired["status"] == "NOT_MEASURED"
    assert expired["cause"] == "CONTENT_EXPIRED"
    assert expired["currentness"] == "EXPIRED"
    assert expired["citations"] == []
    assert expired["dimensions"] == []
