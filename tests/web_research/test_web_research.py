"""Governed web research (spec 098): the index proposes, AXIGNAL reads and verifies."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from application.first_observation.service import FetchedResource
from application.web_research import (
    ResearchSubject,
    WebHit,
    candidates,
    check_page,
    plan,
    registrable_label,
    research_discoveries,
)
from pipeline.web_search.deepseek import DeepSeekSearch
from tools.runtime.web_research import WebResearchRunner, web_research_from_values

NOW = datetime(2026, 10, 18, 9, tzinfo=UTC)
VELASCA = ResearchSubject(
    names=("Velasca",), domain="velasca.com", language="it", activity_terms=("scarpe",)
)


def hit(url: str, rerank: float | None = 2.0, title: str = "Velasca recensioni") -> WebHit:
    return WebHit(url=url, title=title, site_name=None, rerank=rerank, indexed_date="2026-05-01")


def test_plan_asks_reviews_recent_pages_and_sector_rules_in_its_language() -> None:
    queries = plan(VELASCA, today=date(2026, 10, 18))
    assert [q.purpose for q in queries] == ["REPUTATION", "REPUTATION", "CONTEXT"]
    assert queries[0].query == '"Velasca" recensioni -site:velasca.com'
    assert "after:2025-10-18" in queries[1].query
    assert queries[2].query.startswith('"scarpe" normativa lang:it')
    assert all(len(q.query) <= 128 for q in queries)


def test_no_activity_words_means_no_context_query() -> None:
    subject = ResearchSubject(names=("Velasca",), domain="velasca.com", language="it")
    assert [q.purpose for q in plan(subject, today=date(2026, 10, 18))] == [
        "REPUTATION",
        "REPUTATION",
    ]


def test_own_same_brand_and_social_pages_are_never_reputation() -> None:
    hits = [
        hit("https://www.velasca.com/it/shop"),
        hit("https://blog.velasca.com/post"),
        hit("https://velascawomen.com/"),  # a same-brand domain is its own channel
        hit("https://www.instagram.com/velasca/"),
        hit("https://play.google.com/store/apps/details?id=com.velasca"),
        hit("https://www.smysecret.com/politica-de-privacidad"),
        hit("https://it.trustpilot.com/review/velasca.com"),
        hit("https://www.corriere.it/economia/velasca", rerank=1.6),
        hit("https://example.org/low", rerank=0.3),  # below the index's relevance floor
    ]
    kept = [h.url for h in candidates(hits, VELASCA, purpose="REPUTATION")]
    assert kept == [
        "https://it.trustpilot.com/review/velasca.com",
        "https://www.corriere.it/economia/velasca",
    ]


def test_registrable_label_handles_second_level_domains() -> None:
    assert registrable_label("www.velascawomen.com") == "velascawomen"
    assert registrable_label("news.bbc.co.uk") == "bbc"


def test_a_page_supports_only_what_its_own_text_says() -> None:
    supported = check_page(
        "https://www.corriere.it/a", title="Le scarpe di Velasca", text="Intro. Velasca apre a Parigi.",
        links=["https://www.velasca.com/"], needles=["velasca"], own_domain="velasca.com",
        read_at=NOW.isoformat(),
    )  # fmt: skip
    assert supported.state == "SUPPORTED"
    assert supported.links_to_website
    assert supported.excerpt is not None and "Velasca apre a Parigi" in supported.excerpt
    homonym_free = check_page(
        "https://x.it/a", title="Scarpe da uomo", text="Nessun nome qui.", links=[],
        needles=["velasca"], own_domain="velasca.com", read_at=NOW.isoformat(),
    )  # fmt: skip
    assert homonym_free.state == "NOT_SUPPORTED"


def test_accented_names_are_found_in_the_page_text() -> None:
    check = check_page(
        "https://elcomercio.es/a", title="Ampliación en Gijón", text="La empresa Zitrón amplía su planta.",
        links=[], needles=["zitron"], own_domain="zitron.com", read_at=NOW.isoformat(),
    )  # fmt: skip
    assert check.state == "SUPPORTED"
    assert check.excerpt is not None and "Zitrón amplía" in check.excerpt


def result_with(pages: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {"instrument": {"search": "fake"}, "researchedAt": NOW.isoformat(), "pages": list(pages)}


def page(
    url: str, purpose: str, state: str = "SUPPORTED", title: str = "Velasca"
) -> dict[str, object]:
    return {"url": url, "state": state, "title": title, "excerpt": "… Velasca …", "purpose": purpose,
            "readAt": NOW.isoformat(), "siteName": None, "indexedDate": None}  # fmt: skip


def test_findings_are_potential_with_page_and_excerpt_and_reviews_apart() -> None:
    found = research_discoveries(
        result_with([
            page("https://it.trustpilot.com/review/velasca.com", "REPUTATION"),
            page("https://www.corriere.it/a", "REPUTATION"),
            page("https://x.it/unsupported", "REPUTATION", state="NOT_SUPPORTED"),
            page("https://www.mimit.gov.it/norma", "CONTEXT", title="Normativa calzature"),
        ]),
        own_domain="velasca.com",
    )  # fmt: skip
    assert [(d["kind"], d["code"]) for d in found] == [
        ("MENTION", "REVIEW_PAGE"),
        ("MENTION", "WEB_MENTION"),
        ("CONTEXT_SIGNAL", "WEB_SECTOR_SOURCE"),
    ]
    assert all(
        d["epistemicState"] == "POTENTIAL" and d["sourceUrl"] and d["excerpt"] for d in found
    )
    context = found[2]["detail"]
    assert isinstance(context, dict) and context["notAboutThisOrganization"] is True


def test_another_entity_judgment_withholds_the_page() -> None:
    found = research_discoveries(
        result_with([page("https://a.fr/bioculteur", "REPUTATION", title="Bioculteur à Lyon"),
                     page("https://b.es/biocultor", "REPUTATION", title="Biocultor humus")]),
        own_domain="biocultor.com",
        attribution=lambda title: ("ANOTHER_ENTITY", "jev") if "Lyon" in title else ("ABOUT_IT", "jev"),
    )  # fmt: skip
    assert [d["sourceUrl"] for d in found] == ["https://b.es/biocultor"]
    detail = found[0]["detail"]
    assert isinstance(detail, dict) and detail["attributionBy"] == "jev"
    assert detail["withheldAsAnotherEntity"] == 1


def test_deepseek_adapter_keeps_no_summary_or_content_and_hides_the_key(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("sk-test\n", encoding="utf-8")
    sent: list[tuple[str, Mapping[str, str], bytes]] = []

    def transport(url: str, headers: Mapping[str, str], body: bytes) -> bytes:
        sent.append((url, headers, body))
        return json.dumps({"results": [
            {"url": "https://a.es/x#1", "title": "T", "site_name": "A", "rerank_score": 1.7,
             "date": "2026-05-01T10:00:00", "summary": "model text", "content": "page"},
            {"title": "no url"},
        ]}).encode()  # fmt: skip

    hits = DeepSeekSearch(key, transport=transport).search("q" * 300, count=99)
    assert hits == [WebHit("https://a.es/x", "T", "A", 1.7, "2026-05-01")]
    url, headers, body = sent[0]
    assert url.endswith("/v1/tools/search") and headers["Authorization"] == "Bearer sk-test"
    payload = json.loads(body)
    assert len(payload["query"]) == 128 and payload["count"] == 20


class FakeSearch:
    instrument = "fake-search"

    def __init__(self, answers: Mapping[str, Sequence[WebHit]]) -> None:
        self.answers = answers
        self.calls: list[str] = []

    def search(self, query: str, *, count: int) -> Sequence[WebHit]:
        self.calls.append(query)
        return self.answers.get(query, ())


class FakeFetcher:
    def __init__(self, pages: Mapping[str, tuple[int, str]]) -> None:
        self.pages = pages
        self.fetched: list[str] = []

    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> FetchedResource:
        self.fetched.append(url)
        status, html = self.pages.get(url, (404, ""))
        return FetchedResource(
            requested_url=url, final_url=url, observed_at=NOW, status=status,
            content_type="text/html; charset=utf-8", body=html.encode(), content_fingerprint="f",
            artifact_ref=None, requests=1,
        )  # fmt: skip


def test_runner_reads_pages_itself_shares_searches_and_records_cost(tmp_path: Path) -> None:
    queries = plan(VELASCA, today=NOW.date())
    search = FakeSearch({
        queries[0].query: [hit("https://www.corriere.it/a"), hit("https://blocked.it/b")],
        queries[2].query: [hit("https://www.mimit.gov.it/norma", title="Scarpe")],
    })  # fmt: skip
    fetcher = FakeFetcher({
        "https://www.corriere.it/a": (200, "<title>Velasca a Parigi</title><p>Velasca apre.</p>"),
        "https://blocked.it/robots.txt": (200, "User-agent: *\nDisallow: /"),
        "https://www.mimit.gov.it/norma": (200, "<title>Norme</title><p>Le scarpe e la normativa.</p>"),
    })  # fmt: skip
    runner = WebResearchRunner(
        search, fetcher, tmp_path / "r.sqlite3", usd_per_request=0.00075, clock=lambda: NOW
    )
    runner.request(VELASCA)
    assert runner.result(VELASCA) is None  # never searched on the read path
    assert runner.run() == 1
    result = runner.result(VELASCA)
    assert result is not None
    states = {str(p["url"]): p["state"] for p in result["pages"]}  # type: ignore[union-attr]
    assert states == {
        "https://www.corriere.it/a": "SUPPORTED",
        "https://blocked.it/b": "ROBOTS_DISALLOWED",
        "https://www.mimit.gov.it/norma": "SUPPORTED",
    }
    assert "https://blocked.it/b" not in fetcher.fetched  # robots.txt decides
    assert result["cost"] == {"paidSearches": 2, "usd": 0.0015}  # the empty answer is free
    # Another organization with the same activity reuses the sector search.
    other = ResearchSubject(
        names=("Altra",), domain="altra.it", language="it", activity_terms=("scarpe",)
    )
    runner.request(other)
    runner.run()
    assert search.calls.count(queries[2].query) == 1


def test_daily_cap_keeps_research_queued(tmp_path: Path) -> None:
    search = FakeSearch({q.query: [hit("https://x.it/a")] for q in plan(VELASCA, today=NOW.date())})
    runner = WebResearchRunner(
        search, FakeFetcher({}), tmp_path / "r.sqlite3", usd_per_request=0.00075,
        clock=lambda: NOW, max_searches_per_day=1,
    )  # fmt: skip
    runner.request(VELASCA)
    assert runner.run() == 0
    assert runner.result(VELASCA) is None
    assert runner.spent_today() == (1, 0.00075)


def test_off_unless_enabled_and_key_mounted(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("sk", encoding="utf-8")
    fetcher = FakeFetcher({})
    assert web_research_from_values({}, tmp_path, fetcher) is None
    assert (
        web_research_from_values({"AXIGNAL_DEEPSEEK_API_KEY_FILE": str(key)}, tmp_path, fetcher)
        is None
    )
    enabled = {"AXIGNAL_WEB_RESEARCH_ENABLED": "true", "AXIGNAL_DEEPSEEK_API_KEY_FILE": str(key)}
    assert web_research_from_values(enabled, tmp_path, fetcher) is not None
    missing = {**enabled, "AXIGNAL_DEEPSEEK_API_KEY_FILE": str(tmp_path / "none")}
    assert web_research_from_values(missing, tmp_path, fetcher) is None


def test_activity_words_come_from_the_proof_and_need_no_country() -> None:
    from tools.runtime.first_observation import _activity_words

    view: dict[str, object] = {
        "target": {"website": "https://www.biocultor.com/"},
        "attentionScopes": [{"jurisdiction": "EU/ES"}],
        "discoveries": [],
    }  # the public view carries no capabilities nor published contact
    proof = {
        "publishedContact": {"language": "es"},
        "capabilities": [{"capabilityId": "fertilisers-soil-amendments",
                          "basis": {"excerpt": "Fabricamos humus de lombriz."}}],
    }  # fmt: skip
    assert _activity_words(view) == ("biocultor.com", "ES", "es", ())
    assert _activity_words(view, proof) == ("biocultor.com", "ES", "es", ("humus de lombriz",))
    no_country = {**view, "attentionScopes": [],
                  "discoveries": [{"kind": "LANGUAGES", "detail": {"languages": ["it-IT"]}}]}  # fmt: skip
    assert _activity_words(no_country) == ("biocultor.com", None, "it", ())
    assert _activity_words({"target": {}}) is None


def test_one_page_in_two_language_subdomains_is_read_once() -> None:
    hits = [
        hit("https://empresaexterior.com/i/velasca/"),
        hit("https://gl.empresaexterior.com/i/velasca", rerank=1.5),
    ]
    assert [h.url for h in candidates(hits, VELASCA, purpose="REPUTATION")] == [
        "https://empresaexterior.com/i/velasca/"
    ]


ARTICLE = """<html><head><title>{title}</title>
<meta property="article:published_time" content="2026-04-07T08:00:00+02:00"></head>
<body><nav><a href="/">Inicio</a> <a href="/marcas">Marcas</a></nav>
<article><h1>{title}</h1>
<p>{body} El sector dental vive un año de cambios y las cadenas revisan sus planes de
expansión en toda España, con nuevas aperturas previstas para el próximo ejercicio.</p>
<p>Los analistas consultados creen que la consolidación continuará durante los próximos
trimestres, mientras los fondos buscan nuevas oportunidades en el mercado sanitario.</p>
</article>
<footer>Nuestros socios: Vitaldent, Sanitas, Adeslas, DKV y otras marcas.</footer>
</body></html>"""


def test_main_text_and_date_decide_a_mention() -> None:
    from pipeline.web_search.article import read_article

    about = ARTICLE.format(
        title="OTPP nombra presidente", body="Vitaldent nombra nuevo presidente."
    )
    reading = read_article(about, "https://www.expansion.com/a")
    assert reading is not None and reading.published == "2026-04-07"
    assert "Vitaldent nombra" in reading.text and "Nuestros socios" not in reading.text
    footer_only = ARTICLE.format(title="Planes del sector", body="Las cadenas preparan su año.")
    other = read_article(footer_only, "https://example.es/b")
    assert other is not None
    check = check_page(
        "https://example.es/b", title="Planes del sector", text=other.text, links=[],
        needles=["vitaldent"], own_domain="vitaldent.com", read_at=NOW.isoformat(),
        published=other.published,
    )  # fmt: skip
    assert check.state == "NOT_SUPPORTED"  # named only in the footer's brand list


def test_findings_carry_the_publication_date() -> None:
    found = research_discoveries(
        result_with(
            [{**page("https://www.corriere.it/a", "REPUTATION"), "published": "2026-04-07"}]
        ),
        own_domain="velasca.com",
    )
    detail = found[0]["detail"]
    assert isinstance(detail, dict) and detail["publishedAt"] == "2026-04-07"


def test_a_date_stamped_when_served_is_not_a_publication_date() -> None:
    check = check_page(
        "https://www.reviews.io/r/1", title="Review on Velasca - March 2026", text="Velasca shoes.",
        links=[], needles=["velasca"], own_domain="velasca.com", read_at=NOW.isoformat(),
        published=NOW.date().isoformat(),
    )  # fmt: skip
    assert check.state == "SUPPORTED" and check.published is None


def test_identity_research_asks_the_country_word_and_needs_one_verified_identifier() -> None:
    subject = ResearchSubject(names=("Goiko",), domain="goiko.com", language="es", country="ES")
    queries = plan(subject, today=NOW.date())
    assert queries[-1].purpose == "IDENTITY" and queries[-1].query == '"Goiko" CIF -site:goiko.com'
    assert not [
        q
        for q in plan(
            ResearchSubject(names=("Velasca",), domain="velasca.com", language="it", country="IT"),
            today=NOW.date(),
        )
        if q.purpose == "IDENTITY"
    ]  # no verifiable identifier for Italy yet
    one = check_page(
        "https://www.einforma.com/goiko", title="Goiko Grill SL", text="Goiko Grill SL. CIF: B82846825. Madrid.",
        links=[], needles=["goiko"], own_domain="goiko.com", read_at=NOW.isoformat(), require_identifier=True,
    )  # fmt: skip
    assert one.state == "SUPPORTED" and one.identifiers == (("ES_CIF", "B82846825"),)
    assert one.excerpt is not None and "B82846825" in one.excerpt
    listing = check_page(
        "https://dir.example/es", title="Empresas Goiko", needles=["goiko"], own_domain="goiko.com",
        text="Goiko. CIF B82846825. Otra SA CIF A28015865. Tercera SL CIF B-82846825. Cuarta SIREN 552 100 554",
        links=[], read_at=NOW.isoformat(), require_identifier=True,
    )  # fmt: skip
    assert listing.state == "NOT_SUPPORTED"  # a list of companies says nothing about which
    none = check_page(
        "https://x.es/a", title="Goiko", text="Goiko abre en Valencia.", links=[], needles=["goiko"],
        own_domain="goiko.com", read_at=NOW.isoformat(), require_identifier=True,
    )  # fmt: skip
    assert none.state == "NOT_SUPPORTED"
    found = research_discoveries(
        result_with([{**page("https://www.einforma.com/goiko", "IDENTITY", title="Goiko Grill SL"),
                      "identifiers": [["ES_CIF", "B82846825"]]}]),
        own_domain="goiko.com",
    )  # fmt: skip
    assert [(d["kind"], d["code"], d["statement"], d["epistemicState"]) for d in found] == [
        ("IDENTITY_HINT", "IDENTIFIER_IN_DIRECTORY", "B82846825", "POTENTIAL")
    ]


def test_without_its_own_words_the_classified_activity_frames_the_sector_research() -> None:
    subject = ResearchSubject(names=("Bombas",), domain="bombas.com", language="en",
                              activity_terms=("Retail trade",), activity_from_label=True)  # fmt: skip
    context = [q for q in plan(subject, today=NOW.date()) if q.purpose == "CONTEXT"]
    assert (
        context[0].query.startswith('"Retail trade" regulation') and "lang:" not in context[0].query
    )


def test_patent_databases_are_not_sector_context() -> None:
    hits = [hit("https://eureka.patsnap.com/patent/CN224316339U", title="Air damper"),
            hit("https://patents.google.com/patent/X", title="Damper"),
            hit("https://www.boe.es/norma", title="Norma")]  # fmt: skip
    assert [h.url for h in candidates(hits, VELASCA, purpose="CONTEXT")] == [
        "https://www.boe.es/norma"
    ]
