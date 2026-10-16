"""Spec 075 US2: a lexicon activity is established only when the site offers it.

The mechanism is general: one versioned CHOICE question per lexicon activity, over
AXIGNAL's controlled vocabulary, page kinds and anonymous page ids (ADR-0090 as
amended). Python composes: OFFERED or no usable judgment keeps the activity (the latter
marked UNVERIFIED); MENTIONED and USED_INTERNALLY are kept as negative classifications.
No organization or domain is special-cased: the fake provider below decides only from
the controlled words in the state.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from application.first_observation.activity import ActivityMethod, deterministic_activity
from application.first_observation.activity_verification import (
    ACTIVITY_OFFERED,
    PageKind,
    Verdict,
    compose,
    interpret_verification,
    page_kind,
    plan_verification,
)
from application.first_observation.site import PageReading, read_page
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion
from application.semantic_layer.ledger import JEV_1_13_PRICE, CostLedger, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from tests.first_observation import harness
from tests.first_observation.harness import World, build, jev_rule, registered_rights, runtime
from tests.first_observation.test_first_observation_e2e import (
    _attend,
    _pending_id,
    _view,
    discoveries,
)
from tests.semantic_layer.fakes import FakeSystemOne

GUARDS = "https://guardia-norte.example.com/"
GUARDS_HOME = (
    "<html lang='en'><head><title>Guardia Norte | Security guard services</title>"
    "<meta name='description' content='Manned guarding and alarm monitoring for companies "
    "and public buildings in Spain.'></head><body><h1>Security guard services</h1>"
    "<p>Our guarding services protect offices, warehouses and events across Spain.</p>"
    # securitas.com's own wording (no "we use" cue, which the lexicon now drops by itself):
    "<p>Guardia Norte protects digital assets by adopting a secure software development "
    "lifecycle and security controls. Contact Marta Ibáñez at marta@guardia-norte.example.com."
    "</p></body></html>"
)


def _words(batch: SemanticBatch) -> set[str]:
    around = [w for m in batch.state["mentions"] for w in m["around"]]  # type: ignore[union-attr]
    return {w for text in around for w in str(text).split()}


def offered_rule(batch: SemanticBatch, question: SemanticQuestion) -> tuple[str, float]:
    """Decides from controlled words only: an internal practice is not an offer."""
    if question.question_id != ACTIVITY_OFFERED.question_id:
        return jev_rule(batch, question)
    return ("USED_INTERNALLY", 0.9) if "lifecycle" in _words(batch) else ("OFFERED", 0.9)


def _verification_batches(world: World) -> list[SemanticBatch]:
    return [
        b for b in world.judge.calls if b.questions[0].question_id == ACTIVITY_OFFERED.question_id
    ]


def _observe(
    tmp_path: Path, world: World, subject: str = "subject:guards", **kwargs: Any
) -> dict[str, Any]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    facade = build(tmp_path, world, **kwargs)
    token, _ = _attend(facade, tmp_path, subject, GUARDS)
    runtime(facade).drain()
    return _view(facade, token, _pending_id(facade, token))


@pytest.fixture(autouse=True)
def _guards_site(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(harness.PAGES, GUARDS, GUARDS_HOME)


def _codes(view: dict[str, Any]) -> set[str]:
    return {d["code"] for d in discoveries(view, "ACTIVITY")}


def test_lexicon_alone_reads_an_internal_practice_as_an_activity() -> None:
    """The measured defect, reproduced deterministically (no model)."""
    page = _page(GUARDS, GUARDS_HOME)
    found = {f.activity_id for f in deterministic_activity([page])}
    assert "software-development" in found and "security-guarding" in found


def test_an_internal_practice_is_rejected_and_kept_as_a_negative_classification(
    tmp_path: Path,
) -> None:
    world = World(judge=FakeSystemOne(offered_rule))
    view = _observe(tmp_path, world, activity_verification=True)
    codes = _codes(view)
    assert "software-development" not in codes
    assert "security-guarding" in codes  # what the site offers stays established
    (kept,) = [d for d in discoveries(view, "ACTIVITY") if d["code"] == "security-guarding"]
    assert kept["detail"]["verification"] == "OFFERED"
    ledger = view["_ledger"]
    decisions = ledger["decisions"]
    assert "RAN:SEMANTIC:activity_offered" in decisions
    assert "ACTIVITY_REJECTED:software-development:USED_INTERNALLY" in decisions
    assert "ACTIVITY_VERIFIED:security-guarding:OFFERED" in decisions
    # Negative classification: inspectable in the trace, never silently deleted.
    (rejected,) = [
        v for v in ledger["activityVerifications"] if v["activityId"] == "software-development"
    ]
    assert rejected["verdict"] == "USED_INTERNALLY" and rejected["established"] is False
    assert rejected["pageKinds"] == ["HOME"] and rejected["model"] == "jev-1.13.0"
    assert rejected["questionVersion"] == "1" and rejected["nonAuthoritative"] is True
    # The trace is operator state: the subscriber sees only what was established.
    assert "activityVerifications" not in json.dumps(
        {k: v for k, v in view.items() if k != "_ledger"}
    )


def test_an_offered_activity_is_kept_and_marked_verified(tmp_path: Path) -> None:
    world = World(judge=FakeSystemOne(lambda b, q: ("OFFERED", 0.92)
                                      if q.question_id == "activity_offered" else jev_rule(b, q)))  # fmt: skip
    view = _observe(tmp_path, world, activity_verification=True)
    assert "software-development" in _codes(view)
    assert all(d["detail"]["verification"] == "OFFERED" for d in discoveries(view, "ACTIVITY"))


def test_without_a_usable_judgment_the_lexicon_result_stands_unverified(tmp_path: Path) -> None:
    # Disabled by policy (the default until measured, FR-008).
    off = World(judge=FakeSystemOne(offered_rule))
    view = _observe(tmp_path / "off", off)
    assert "software-development" in _codes(view)
    assert all(d["detail"]["verification"] == "UNVERIFIED" for d in discoveries(view, "ACTIVITY"))
    assert "SKIPPED:ACTIVITY_VERIFICATION:DISABLED" in view["_ledger"]["decisions"]
    assert not _verification_batches(off) and view["_ledger"]["activityVerifications"] == []
    # Semantic layer off.
    layer_off = _observe(tmp_path / "layer", World(), activity_verification=True, semantic=False)
    assert "software-development" in _codes(layer_off)
    assert (
        "ACTIVITY_UNVERIFIED:software-development:LAYER_DISABLED"
        in layer_off["_ledger"]["decisions"]
    )
    # The provider stays uncertain (the harness answers UNCLEAR at 0.5).
    unsure = _observe(tmp_path / "unsure", World(), activity_verification=True)
    assert "software-development" in _codes(unsure)
    assert "ACTIVITY_UNVERIFIED:software-development:UNCERTAIN" in unsure["_ledger"]["decisions"]
    # The provider fails.
    failing = World(judge=FakeSystemOne(offered_rule, fail="TIMEOUT"))
    failed = _observe(tmp_path / "fail", failing, activity_verification=True)
    assert "software-development" in _codes(failed)
    assert "ACTIVITY_UNVERIFIED:software-development:TIMEOUT" in failed["_ledger"]["decisions"]


def test_without_rights_the_public_sentence_and_page_kinds_leave_never_people(
    tmp_path: Path,
) -> None:
    world = World(judge=FakeSystemOne(offered_rule))
    view = _observe(
        tmp_path, world, activity_verification=True,
        rights=registered_rights(provider_input=False),
    )  # fmt: skip
    assert "SEMANTIC_INPUT:PUBLIC_TEXT:NO_SITE_CONTENT_RIGHTS" in view["_ledger"]["decisions"]
    batches = _verification_batches(world)
    assert batches
    for batch in batches:
        state = batch.state
        assert set(state) == {"representation", "site", "activity", "pagesRead", "mentions"}
        assert state["site"] == "[site]"
        for page in [*state["pagesRead"], *state["mentions"]]:  # type: ignore[misc]
            assert re.fullmatch(r"\[page-\d+\]", page["page"])
            assert page["kind"] in PageKind.__members__
        raw = json.dumps(state, ensure_ascii=False).casefold()
        for private in ("marta", "ibáñez", "@", "example.com", "http"):
            assert private not in raw, private


def test_identical_states_are_not_asked_twice(tmp_path: Path) -> None:
    world = World(judge=FakeSystemOne(offered_rule))
    facade = build(tmp_path, world, activity_verification=True)
    _first, _ = _attend(facade, tmp_path, "subject:guards-1", GUARDS)
    runtime(facade).drain()
    asked = len(_verification_batches(world))
    assert asked
    second, _ = _attend(facade, tmp_path, "subject:guards-2", GUARDS)
    runtime(facade).drain()
    assert len(_verification_batches(world)) == asked  # judgment memory answered
    view = _view(facade, second, _pending_id(facade, second))
    assert "software-development" not in _codes(view)
    assert "ACTIVITY_REJECTED:software-development:USED_INTERNALLY" in view["_ledger"]["decisions"]


# --- units --------------------------------------------------------------------------


def _page(url: str, html: str) -> PageReading:
    return read_page(
        url=url, html=html, observed_at=datetime.now(UTC), content_fingerprint="t",
        artifact_ref=None,
    )  # fmt: skip


@pytest.mark.parametrize(
    ("url", "title", "kind"),
    [
        ("https://a.example/", "", PageKind.HOME),
        ("https://a.example/en/", "", PageKind.HOME),
        ("https://a.example/es-es", "", PageKind.HOME),
        ("https://a.example/servicios/limpieza", "", PageKind.SERVICE),
        ("https://a.example/en/what-we-do", "", PageKind.SERVICE),
        ("https://a.example/about-us", "", PageKind.ABOUT),
        ("https://a.example/quienes-somos", "", PageKind.ABOUT),
        ("https://a.example/privacy-policy", "", PageKind.LEGAL),
        ("https://a.example/aviso-legal", "", PageKind.LEGAL),
        ("https://a.example/careers/engineer", "", PageKind.CAREERS),
        ("https://a.example/trabaja-con-nosotros", "", PageKind.CAREERS),
        ("https://a.example/news/2026/award", "", PageKind.NEWS),
        ("https://a.example/p/123", "Our services", PageKind.SERVICE),
        ("https://a.example/p/123", "", PageKind.OTHER),
    ],
)
def test_page_kind_is_deterministic_from_path_then_title(
    url: str, title: str, kind: PageKind
) -> None:
    html = f"<html><head><title>{title}</title></head><body><p>x</p></body></html>"
    assert page_kind(_page(url, html)) is kind


def _cascade(judge: FakeSystemOne, memory: InMemoryJudgmentMemory) -> SemanticCascade:
    return SemanticCascade(
        judge=judge,
        ledger=CostLedger(prices=(JEV_1_13_PRICE,)),
        budget=SemanticBudget(max_system_one_input_tokens=50_000),
        memory=memory,
    )


def test_state_names_the_kind_of_every_page_where_the_activity_appears() -> None:
    pages = [
        _page(GUARDS, GUARDS_HOME),
        _page(GUARDS + "careers/developer",
              "<html><head><title>Join</title></head><body><p>We are hiring for our "
              "software development team in Bilbao.</p></body></html>"),
        _page(GUARDS + "privacy",
              "<html><head><title>Privacy</title></head><body><p>Our software development "
              "partners process data under contract.</p></body></html>"),
    ]  # fmt: skip
    findings = deterministic_activity(pages)
    requests = {r.finding.activity_id: r for r in plan_verification(GUARDS, pages, findings)}
    software = requests["software-development"]
    assert software.page_kinds == ("CAREERS", "HOME", "LEGAL")
    assert [p["kind"] for p in software.batch.state["pagesRead"]] == [  # type: ignore[union-attr]
        "HOME", "CAREERS", "LEGAL",
    ]  # fmt: skip
    # Schema.org self-declarations are not verified here; only lexicon matches are.
    assert all(r.finding.method is ActivityMethod.LEXICON for r in requests.values())


def test_a_new_question_version_is_a_memory_miss() -> None:
    pages = [_page(GUARDS, GUARDS_HOME)]
    requests = plan_verification(GUARDS, pages, deterministic_activity(pages))
    judge, memory = FakeSystemOne(offered_rule), InMemoryJudgmentMemory()
    now = datetime.now(UTC)
    first = _cascade(judge, memory).run([r.batch for r in requests], now=now)
    calls = len(judge.calls)
    _cascade(judge, memory).run([r.batch for r in requests], now=now)
    assert len(judge.calls) == calls  # same state, same question: remembered
    bumped = replace(ACTIVITY_OFFERED, version="2")
    _cascade(judge, memory).run(
        [SemanticBatch(r.batch.batch_id, r.batch.state, (bumped,)) for r in requests], now=now
    )
    assert len(judge.calls) == calls + len(requests)  # a new version is judged again
    verdicts = {v.activity_id: v.verdict for v in interpret_verification(requests, first)}
    assert verdicts["software-development"] is Verdict.USED_INTERNALLY


def test_composition_keeps_unclear_and_unknown_and_drops_only_rejections() -> None:
    pages = [_page(GUARDS, GUARDS_HOME)]
    findings = deterministic_activity(pages)
    requests = plan_verification(GUARDS, pages, findings)
    unknown = interpret_verification(requests, None, unavailable="LAYER_DISABLED")
    assert {v.verdict for v in unknown} == {Verdict.UNKNOWN}
    assert [f.activity_id for f in compose(findings, unknown)] == [f.activity_id for f in findings]
    assert {f.verification for f in compose(findings, unknown)} == {"UNVERIFIED"}
    unclear = tuple(replace(v, verdict=Verdict.UNCLEAR, reason=None) for v in unknown)
    assert len(compose(findings, unclear)) == len(findings)
    mentioned = tuple(replace(v, verdict=Verdict.MENTIONED) for v in unknown)
    assert compose(findings, mentioned) == ()
