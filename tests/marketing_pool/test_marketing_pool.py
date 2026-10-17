"""Marketing pool: discover → study → qualify → draft; staff approve; send; opt out forever."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from application.first_observation.service import _published_contact
from application.first_observation.site import read_page
from application.marketing_pool.personas import PERSONAS, best_persona
from application.marketing_pool.policy import Channel, channel_for, market
from application.marketing_pool.prospect import accept_draft, findings, gate, recipient
from cognition.jobs.model import JobKind
from pipeline.marketing_pool.discovery import OverpassDiscovery, WikidataDiscovery
from pipeline.marketing_pool.smtp import OutgoingMessage
from pipeline.marketing_pool.sqlite_store import Candidate, SqliteMarketingPool
from tools.runtime.first_observation import public_view
from tools.runtime.marketing_pool import MarketingPoolRunner, Operator

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def _d(kind: str, code: str, statement: str, state: str = "OBSERVED", **detail: Any) -> dict:
    return {
        "kind": kind, "code": code, "statement": statement, "epistemicState": state,
        "sourceUrl": f"https://source.example/{code.lower()}", "detail": detail,
    }  # fmt: skip


VIEW = {
    "state": "FIRST_PROOF_READY",
    "observedAt": NOW.isoformat(),
    "discoveries": [
        _d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED", "Acme SEO — search engine agency"),
        _d("ACTIVITY", "seo-services", "SEO and AI search consulting for retailers"),
        _d(
            "GENERATIVE_VISIBILITY",
            "AI_NOT_NAMED_FOR_CATEGORY",
            "0/2",
            competitorsNamed=["Rival SEO"],
        ),
        _d("REPRESENTATION_GAP", "AUDIT:LLMS_TXT", "LLMS_TXT", "POTENTIAL", value=False),
        _d("MENTION", "PRESS_MENTION", "Quoted in The Daily on a client launch"),
        _d("DEMAND", "TED:123", "Open call for digital marketing services", "POTENTIAL"),
        _d("SIGNIFICANT_UNKNOWN", "IDENTITY_NOT_VERIFIED", "No registry", "UNKNOWN"),
    ],
}


def test_the_site_reader_keeps_the_addresses_a_site_publishes() -> None:
    html = (
        '<html lang="de-DE"><body><a href="mailto:Hallo@Agentur.de?subject=x">Mail</a>'
        '<script type="application/ld+json">{"@type":"Organization","name":"A",'
        '"contactPoint":{"email":"mailto:kontakt@agentur.de"}}</script></body></html>'
    )
    page = read_page(url="https://agentur.de/", html=html, observed_at=NOW,
                     content_fingerprint="f", artifact_ref=None)  # fmt: skip
    assert page.signals["emails"] == ["hallo@agentur.de", "kontakt@agentur.de"]
    assert _published_contact([page]) == {
        "emails": ["hallo@agentur.de", "kontakt@agentur.de"], "language": "de",
        "page": "https://agentur.de/",
    }  # fmt: skip


def test_published_contact_never_reaches_a_subscriber_view() -> None:
    proof = {"target": {"kind": "FOCUS", "website": "w", "name": "n", "identityLink": "x"},
             "state": "FIRST_PROOF_READY", "discoveries": [],
             "publishedContact": {"emails": ["info@x.com"]}}  # fmt: skip
    assert "publishedContact" not in (public_view(proof, None) or {})


def test_only_a_role_address_on_its_own_domain_is_chosen() -> None:
    emails = ["jane.doe@acme.com", "noreply@acme.com", "info@other.com", "info@acme.com",
              "hello@acme.com"]  # fmt: skip
    assert recipient(emails, "acme.com") == "hello@acme.com"
    assert recipient(["jane.doe@acme.com", "privacy@acme.com"], "acme.com") is None


def test_findings_are_sourced_lead_families_first_and_gated() -> None:
    chosen, words = best_persona("SEO and AI search consulting", "B2B_CONSULTANCY")
    assert chosen is not None and chosen.id == "SEO_GEO_AGENCY" and "seo" in words
    selected = findings(VIEW, chosen.lead_families)
    assert [f.family for f in selected][:3] == ["presence", "presence", "reputation"]
    assert all(f.state != "UNKNOWN" and f.source for f in selected)
    assert gate(selected) is None
    assert gate(selected[:2]) == "TOO_FEW_EVIDENCED_FINDINGS"


def test_a_draft_must_cite_findings_and_carry_no_links_of_its_own() -> None:
    selected = findings(VIEW, ("presence",))
    body = "We observed your agency from the outside. " * 8
    good = {"subject": "What AXIGNAL observes", "body": body, "findings_used": [1, 2],
            "cards": [{"index": 1, "text": "AI assistants did not name it"},
                      {"index": 2, "text": "An open call matches its services"}]}  # fmt: skip
    assert accept_draft(good, selected) is not None
    assert accept_draft({**good, "findings_used": [1]}, selected) is None
    assert accept_draft({**good, "body": body + " see https://x.com"}, selected) is None


def test_channel_policy_is_conservative() -> None:
    assert channel_for("US")[0] is Channel.EMAIL
    assert channel_for("ES")[0] is Channel.HOLD and channel_for("DE")[0] is Channel.HOLD
    assert channel_for("ZZ")[0] is Channel.HOLD


def test_open_registries_are_parsed_into_candidates() -> None:
    osm = {"elements": [
        {"type": "node", "id": 1, "tags": {"name": "Acme", "website": "acme.com"}},
        {"type": "node", "id": 2, "tags": {"name": "", "website": "https://x.com"}},
    ]}  # fmt: skip
    found = OverpassDiscovery(lambda r, t: json.dumps(osm).encode()).find(PERSONAS[0], market("US"))
    assert [(c.name, c.website, c.source_ref) for c in found] == [
        ("Acme", "https://acme.com", "osm:node/1")
    ]
    wikidata = {"results": {"bindings": [
        {"o": {"value": "http://www.wikidata.org/entity/Q1"}, "oLabel": {"value": "Big Co"},
         "site": {"value": "https://big.example/"}},
        {"o": {"value": "http://www.wikidata.org/entity/Q2"}, "oLabel": {"value": "Q2"},
         "site": {"value": "https://q2.example/"}},
    ]}}  # fmt: skip
    found = WikidataDiscovery(lambda r, t: json.dumps(wikidata).encode()).find(
        PERSONAS[0], market("US")
    )
    assert [c.source_ref for c in found] == ["wikidata:Q1"]


class _Source:
    name = "FAKE"

    def __init__(self, candidates: list[Candidate]) -> None:
        self.candidates = candidates

    def find(self, persona: Any, market: Any) -> list[Candidate]:
        return self.candidates if market.iso == "US" and persona.id == "SEO_GEO_AGENCY" else []


class _Sender:
    sender_address = "hola@axignal.com"

    def __init__(self) -> None:
        self.sent: list[OutgoingMessage] = []

    def send(self, message: OutgoingMessage) -> str:
        self.sent.append(message)
        return "<id@axignal.com>"


def _runner(tmp_path: Path, clock: list[datetime], sender: _Sender) -> MarketingPoolRunner:
    store = SqliteMarketingPool(tmp_path / "pool.sqlite3")
    studies: dict[str, str] = {}

    def study(ref: str, website: str, name: str) -> str:
        studies[ref] = website
        return "QUEUED"

    def study_result(ref: str) -> tuple[dict | None, dict]:
        if ref not in studies:
            return None, {}
        domain = ref.removeprefix("pool:")
        return VIEW, {"emails": [f"hello@{domain}"], "language": "en"}

    def complete(job: Any) -> Any:
        assert job.kind is JobKind.OUTREACH_DRAFT
        assert "[1] presence" in job.context["user"]
        body = "We observed your agency from the outside, as an auditor would. " * 4
        return SimpleNamespace(payload={"answer": {
            "subject": "What AXIGNAL observes about you", "body": body,
            "findings_used": [1, 3],
            "cards": [{"index": 1, "text": "AI assistants did not name it in 2 answers"},
                      {"index": 3, "text": "Its site states its services in prose only"}]}})  # fmt: skip

    return MarketingPoolRunner(
        store,
        (
            _Source(
                [
                    Candidate(
                        "Acme SEO",
                        "https://www.acme.com/",
                        "US",
                        "SEO_GEO_AGENCY",
                        "FAKE",
                        "osm:node/1",
                    ),
                    Candidate(
                        "Acme again",
                        "http://acme.com",
                        "US",
                        "SEO_GEO_AGENCY",
                        "FAKE",
                        "osm:node/2",
                    ),
                ]
            ),
        ),
        study=study,
        study_result=study_result,
        complete=complete,
        model="m",
        operator=Operator("Rafael López", "Calle 1, Toledo", "https://axignal.com", "CEO"),
        sender=sender,
        clock=lambda: clock[0],
    )


def test_end_to_end_once_per_organization_approved_by_staff(tmp_path: Path) -> None:
    clock, sender = [NOW], _Sender()
    runner = _runner(tmp_path, clock, sender)
    assert runner.tick() == {"discovered": 1, "studying": 1, "concluded": 1, "sent": 0}
    prospect = runner.store.get("acme.com")
    assert prospect is not None and prospect["state"] == "DRAFTED"
    assert prospect["detail"]["recipient"] == "hello@acme.com"
    html = runner.html(prospect) or ""
    assert "What AXIGNAL observes about you" in html and "CEO, Axignal.com" in html
    assert "/email/observer-laptop-480.png" in html and "/r/" in html

    assert runner.send_approved() == 0  # nothing leaves without staff approval
    assert runner.decide("acme.com", "APPROVE", actor="founder")
    assert runner.send_approved() == 1
    message = sender.sent[0]
    assert message.to == "hello@acme.com" and message.html
    assert "Rafael López\nCEO, Axignal.com" in message.body
    assert message.body.startswith("For the attention of the head of SEO at Acme SEO\n\n")
    assert "For the attention of the head of SEO at Acme SEO" in message.html
    assert runner.reading(str(runner.store.get("acme.com")["detail"]["token"])) is not None

    token = message.unsubscribe_url.rsplit("/", 1)[1]
    assert "/api/marketing/unsubscribe/" in message.unsubscribe_url
    assert runner.unsubscribe(token)
    assert runner.store.get("acme.com")["state"] == "SUPPRESSED"
    assert runner.store.is_suppressed("hello@acme.com")
    clock[0] = NOW + timedelta(days=60)  # rediscovered later: never added again
    assert runner.discover() == 0 and runner.store.get("acme.com")["state"] == "SUPPRESSED"


def test_held_markets_are_studied_but_never_sent(tmp_path: Path) -> None:
    clock, sender = [NOW], _Sender()
    runner = _runner(tmp_path, clock, sender)
    runner.store.add([Candidate("Agencia", "https://agencia.es", "ES", "SEO_GEO_AGENCY",
                                "FAKE", "osm:node/9")], now=NOW)  # fmt: skip
    runner.tick()
    held = runner.store.get("agencia.es")
    assert held is not None and held["state"] == "HELD"
    assert held["reason"] == "CHANNEL_POLICY_HOLD" and held["detail"]["draft"]
    assert not runner.decide("agencia.es", "APPROVE", actor="founder")
    assert all(m.to != "hello@agencia.es" for m in sender.sent)


def test_platform_pages_are_not_an_organization_website() -> None:
    from pipeline.marketing_pool.sqlite_store import domain_of

    assert domain_of("https://www.facebook.com/acme") is None
    assert domain_of("https://acme.business.site/") is None
    assert domain_of("https://www.acme.co.uk/") == "acme.co.uk"


def test_a_persona_needs_its_own_site_and_one_word_only_when_registry_backed() -> None:
    assert best_persona("We are a branding studio", None) == (None, ())
    chosen, _ = best_persona("We are a branding studio", "DIGITAL_MARKETING_AGENCY")
    assert chosen is not None and chosen.id == "DIGITAL_MARKETING_AGENCY"
    assert best_persona("Our strategy for growth", "B2B_CONSULTANCY") == (None, ())


def test_addresses_written_as_text_are_kept_too() -> None:
    html = "<html><body><p>Write to info@studio.fr for projects.</p></body></html>"
    page = read_page(url="https://studio.fr/", html=html, observed_at=NOW,
                     content_fingerprint="f", artifact_ref=None)  # fmt: skip
    assert page.signals["emails"] == ["info@studio.fr"]


def test_a_failed_search_is_retried_the_next_day_not_in_a_month(tmp_path: Path) -> None:
    class Failing:
        name = "FAKE"
        calls = 0

        def find(self, persona: Any, market: Any) -> list[Candidate]:
            Failing.calls += 1
            raise TimeoutError

    clock = [NOW]
    runner = _runner(tmp_path, clock, _Sender())
    runner._sources = (Failing(),)
    assert runner.discover() == 0 and runner.discover() == 0
    assert Failing.calls == 2  # the next search in the rotation, not the failed one again
    clock[0] = NOW + timedelta(days=1, minutes=1)
    runner.discover()
    assert Failing.calls == 3


def test_the_salutation_names_a_role_never_a_person() -> None:
    from application.marketing_pool.prospect import salutation

    assert salutation("es", "DIGITAL_MARKETING_AGENCY", "Acme") == (
        "A la atención del responsable de marketing de Acme"
    )
    assert salutation("de", "REPUTATION_PR_AGENCY", "Acme") == (
        "Zu Händen der Leitung Kommunikation, Acme"
    )
    assert salutation("xx", "B2B_CONSULTANCY", "Acme").startswith("For the attention")


def test_a_campaign_takes_the_budget_then_the_pool_returns_to_automatic(
    tmp_path: Path,
) -> None:
    clock, sender = [NOW], _Sender()
    runner = _runner(tmp_path, clock, sender)
    runner.store.add([Candidate("Auto", "https://auto.example", "US", "SEO_GEO_AGENCY",
                                "FAKE", "osm:node/7")], now=NOW)  # fmt: skip
    campaign = runner.create_campaign(
        name="SEO US", personas=["SEO_GEO_AGENCY"], countries=["US"], target=1,
        ends_on=None, actor="claude:rafael",
    )  # fmt: skip
    assert runner.discover() == 1  # the campaign's search, not the automatic rotation
    assert runner.store.get("acme.com")["campaign_id"] == campaign
    assert runner.start_studies() == 1  # only the campaign's prospect
    assert runner.store.get("auto.example")["state"] == "DISCOVERED"
    runner.collect()
    view = runner.campaign_view()[0]
    assert view["state"] == "COMPLETED" and view["progress"]["drafted"] == 1
    assert runner.start_studies() == 1  # back to automatic mode
    assert runner.store.get("auto.example")["state"] == "STUDYING"


def test_campaigns_are_validated_and_cancelled_by_staff(tmp_path: Path) -> None:
    import pytest

    runner = _runner(tmp_path, [NOW], _Sender())
    for bad in (
        {"personas": ["NOPE"], "countries": ["US"], "target": 5},
        {"personas": ["SEO_GEO_AGENCY"], "countries": ["ZZ"], "target": 5},
        {"personas": ["SEO_GEO_AGENCY"], "countries": ["US"], "target": 0},
    ):
        with pytest.raises(ValueError):
            runner.create_campaign(name="x", ends_on=None, actor="a:b", **bad)
    with pytest.raises(ValueError):
        runner.create_campaign(name="x", personas=["SEO_GEO_AGENCY"], countries=["US"],
                               target=5, ends_on="2026-01-01", actor="a:b")  # fmt: skip
    campaign = runner.create_campaign(name="x", personas=["SEO_GEO_AGENCY"],
                                      countries=["US"], target=5, ends_on=None,
                                      actor="a:b")  # fmt: skip
    assert runner.cancel_campaign(campaign, actor="founder")
    assert not runner.cancel_campaign(campaign, actor="founder")
    assert runner.active_campaigns() == []


def test_the_automatic_pool_favours_what_has_qualified(tmp_path: Path) -> None:
    from tools.runtime.marketing_pool import _rate

    assert _rate((10, 8)) > _rate(None) > _rate((10, 0))
