"""Reaching the website the subscriber named, without stretching what it means.

Found in a real-company sample: a bare domain that only serves ``www.`` (its TLS
certificate does not cover the apex) was reported as an unavailable website, and a site
that redirects to another domain was reported as blocked by access rules. The ``www.``
host is the same DNS domain, so it is tried once; another domain could be another
organization, so it is never followed and is named for what it is.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from application.first_observation.contracts import RunLedger
from application.first_observation.service import (
    TLS_NOT_VERIFIED,
    FetchedResource,
    FirstObservationService,
)
from application.first_observation.site import language_entry_link, read_page

NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)
HOME = (
    "<html lang='en'><head><title>Apex Ventilation</title>"
    "<meta name='description' content='Ventilation systems for tunnels.'></head>"
    "<body><h1>Apex</h1><p>Ventilation systems for tunnels and mining.</p></body></html>"
)


def _resource(
    url: str, status: int | None, body: str | None, failure: str | None = None
) -> FetchedResource:
    data = None if body is None else body.encode("utf-8")
    return FetchedResource(
        requested_url=url,
        final_url=url,
        observed_at=NOW,
        status=status,
        content_type="text/html; charset=utf-8" if body and "<html" in body else "text/plain",
        body=data,
        content_fingerprint=None if data is None else "sha256:test",
        artifact_ref=None,
        requests=0 if status is None else 1,
        failure=failure,
    )


class Web:
    def __init__(self, answers: dict[str, FetchedResource]) -> None:
        self.answers = answers
        self.requests: list[str] = []

    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> FetchedResource:
        self.requests.append(url)
        return self.answers.get(url, _resource(url, 404, None, "http_404"))


class Sites:
    def __init__(self) -> None:
        self.saved: list[Any] = []

    def site(self, origin: str) -> None:
        return None

    def save_site(self, reading: Any) -> None:
        self.saved.append(reading)


def _service(web: Web) -> FirstObservationService:
    return FirstObservationService(
        fetcher=web,
        sites=Sites(),
        research=None,  # type: ignore[arg-type]
        seeds=None,  # type: ignore[arg-type]
        cascade_factory=lambda: None,
        clock=lambda: NOW,
    )


def test_a_bare_domain_that_does_not_answer_is_read_on_its_www_host_once() -> None:
    web = Web({
        "https://www.apex.example/robots.txt": _resource("https://www.apex.example/robots.txt", 200, "User-agent: *\nAllow: /\n"),
        "https://www.apex.example/": _resource("https://www.apex.example/", 200, HOME),
    })  # fmt: skip
    web.answers["https://apex.example/robots.txt"] = _resource(
        "https://apex.example/robots.txt", None, None, "SENSOR:SSLCertVerificationError"
    )
    ledger = RunLedger()

    reading = _service(web).read_site("apex.example", NOW, ledger)

    assert reading.failure is None
    assert reading.pages and reading.pages[0].url == "https://www.apex.example/"
    assert "RETRIED:WWW_HOST" in ledger.decisions
    assert web.requests[:2] == [
        "https://apex.example/robots.txt",
        "https://www.apex.example/robots.txt",
    ]


def test_no_www_retry_when_the_bare_domain_answered() -> None:
    web = Web({})
    web.answers["https://down.example/robots.txt"] = _resource(
        "https://down.example/robots.txt", 503, None, "http_503"
    )

    reading = _service(web).read_site("down.example", NOW, RunLedger())

    assert reading.failure == "ROBOTS_UNAVAILABLE"
    assert web.requests == ["https://down.example/robots.txt"]


def test_a_redirect_to_another_domain_is_named_and_never_followed() -> None:
    web = Web({})
    web.answers["https://moved.example/robots.txt"] = _resource(
        "https://moved.example/robots.txt", 301, None, "redirect_policy_rejected"
    )

    reading = _service(web).read_site("moved.example", NOW, RunLedger())

    assert reading.failure == "REDIRECTS_TO_ANOTHER_SITE"
    assert not reading.pages
    assert web.requests == ["https://moved.example/robots.txt"]


def test_a_certificate_that_cannot_be_verified_is_named_and_never_relaxed() -> None:
    # Found in the sample: a server without its intermediate certificate, on both hosts.
    web = Web({})
    for host in ("certs.example", "www.certs.example"):
        web.answers[f"https://{host}/robots.txt"] = _resource(
            f"https://{host}/robots.txt", None, None, TLS_NOT_VERIFIED
        )

    reading = _service(web).read_site("certs.example", NOW, RunLedger())

    assert reading.failure == TLS_NOT_VERIFIED
    assert not reading.pages


SPLASH = (
    "<html lang='es-ES'><head><title>Bienvenido | Welcome | Bem-vindo</title></head><body>"
    "<a href='/cl/'>Chile</a><a href='/es/'>España</a><a href='/pt/'>Portugal</a>"
    "<a href='/us/'>USA</a></body></html>"
)


def test_a_language_selector_home_is_read_through_its_matching_version() -> None:
    # Found in the sample: a homepage that only offers countries says nothing of the
    # activity; the version in the page's own language is read instead.
    web = Web({
        "https://splash.example/robots.txt": _resource("https://splash.example/robots.txt", 200, "User-agent: *\nAllow: /\n"),
        "https://splash.example": _resource("https://splash.example/", 200, SPLASH),
        "https://splash.example/es/": _resource("https://splash.example/es/", 200, HOME),
    })  # fmt: skip
    ledger = RunLedger()

    reading = _service(web).read_site("splash.example", NOW, ledger)

    assert [page.url for page in reading.pages] == [
        "https://splash.example/",
        "https://splash.example/es/",
    ]
    assert "FETCHED:LANGUAGE_ENTRY" in ledger.decisions


def test_a_page_with_a_couple_of_language_links_is_not_a_selector() -> None:
    page = read_page(
        url="https://two.example/",
        html="<html lang='es'><body><a href='/en/'>EN</a><a href='/fr/'>FR</a></body></html>",
        observed_at=NOW,
        content_fingerprint="sha256:test",
        artifact_ref=None,
    )
    assert language_entry_link(page) is None


def test_the_fetcher_names_an_unverifiable_certificate() -> None:
    from types import SimpleNamespace

    from pipeline.first_observation.http_fetcher import GovernedSiteFetcher

    class Sensor:
        def observe(self, request: object, policy: object) -> SimpleNamespace:
            return SimpleNamespace(
                final_uri="https://certs.example/robots.txt", retrieved_at=NOW, http_status=None,
                content_type=None, body_artifact_ref=None, body_fingerprint=None,
                raw_observation_ref=None, peer_ips=(),
                failure_state="transport_error:SSLCertVerificationError",
            )  # fmt: skip

    fetcher = GovernedSiteFetcher(sensor=Sensor(), artifacts=None)  # type: ignore[arg-type]
    fetched = fetcher.fetch("https://certs.example/robots.txt", slot="robots")
    assert fetched.failure == TLS_NOT_VERIFIED and fetched.status is None


def test_a_redirect_to_the_same_brand_on_another_domain_is_read_once_and_said() -> None:
    from dataclasses import replace

    moved = replace(
        _resource("https://impression.co.uk/robots.txt", 301, None, "redirect_policy_rejected"),
        redirected_to="https://www.impressiondigital.com/robots.txt",
    )
    web = Web({
        "https://impression.co.uk/robots.txt": moved,
        "https://www.impressiondigital.com/robots.txt": _resource(
            "https://www.impressiondigital.com/robots.txt", 200, "User-agent: *\nAllow: /\n"),
        "https://www.impressiondigital.com/": _resource("https://www.impressiondigital.com/", 200, HOME),
    })  # fmt: skip
    ledger = RunLedger()

    reading = _service(web).read_site("impression.co.uk", NOW, ledger)

    assert reading.failure is None
    assert reading.pages[0].url == "https://www.impressiondigital.com/"
    assert "FOLLOWED:SAME_BRAND_REDIRECT" in ledger.decisions


def test_a_redirect_to_another_brand_is_still_never_followed() -> None:
    from dataclasses import replace

    from application.first_observation.service import same_brand

    moved = replace(
        _resource("https://acme.example/robots.txt", 301, None, "redirect_policy_rejected"),
        redirected_to="https://www.bigholding.example/acme",
    )
    web = Web({"https://acme.example/robots.txt": moved})
    reading = _service(web).read_site("acme.example", NOW, RunLedger())
    assert reading.failure == "REDIRECTS_TO_ANOTHER_SITE"
    assert web.requests == ["https://acme.example/robots.txt"]
    assert same_brand("https://alan.com", "https://alan.eu/")
    assert not same_brand("https://ab.com", "https://abacus.com/")  # too short to tell


class ArchiveWeb(Web):
    """Robots allow, the live homepage refuses us, the Internet Archive holds a capture."""

    def __init__(self, capture: str | None) -> None:
        super().__init__({})
        self.capture = capture

    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> FetchedResource:
        self.requests.append(url)
        if url.endswith("/robots.txt"):
            return _resource(url, 200, "User-agent: *\nAllow: /\n")
        if url.startswith("https://web.archive.org/cdx/"):
            rows = [["timestamp", "original"]] + (
                [[self.capture, "https://walled.example/"]] if self.capture else []
            )
            return _resource(url, 200, json.dumps(rows))
        if url.startswith("https://web.archive.org/web/"):
            return _resource(url, 200, HOME)
        return _resource(url, 403, None, "http_403")


def test_a_walled_homepage_is_read_from_a_recent_archive_capture_dated_as_such() -> None:
    web = ArchiveWeb("20261001093000")
    ledger = RunLedger()
    reading = _service(web).read_site("walled.example", NOW, ledger)
    assert reading.failure is None and len(reading.pages) == 1
    page = reading.pages[0]
    assert page.url == "https://web.archive.org/web/20261001093000id_/https://walled.example/"
    assert page.observed_at.isoformat().startswith("2026-10-01T09:30")
    assert page.signals["archivedFrom"].rstrip("/") == "https://walled.example"
    assert "READ:ARCHIVED_HOMEPAGE" in ledger.decisions
    assert "from=20260415" in next(u for u in web.requests if "/cdx/" in u)  # 180 days


def test_without_a_recent_capture_the_homepage_stays_unavailable() -> None:
    reading = _service(ArchiveWeb(None)).read_site("walled.example", NOW, RunLedger())
    assert reading.failure == "HOMEPAGE_UNAVAILABLE"


def test_robots_refusal_is_never_routed_around_through_the_archive() -> None:
    web = Web({"https://closed.example/robots.txt": _resource(
        "https://closed.example/robots.txt", 200, "User-agent: *\nDisallow: /\n")})  # fmt: skip
    reading = _service(web).read_site("closed.example", NOW, RunLedger())
    assert reading.failure == "ROBOTS_DISALLOWED"
    assert not any("archive.org" in u for u in web.requests)


class FlakyIndexWeb(ArchiveWeb):
    """The CDX index is temporarily offline; the availability service answers."""

    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> FetchedResource:
        if url.startswith("https://web.archive.org/cdx/"):
            self.requests.append(url)
            return _resource(url, 503, None, "http_503")
        if url.startswith("https://archive.org/wayback/available"):
            self.requests.append(url)
            body = {"archived_snapshots": {"closest": {
                "available": True, "status": "200", "timestamp": "20261005120000"}}}  # fmt: skip
            return _resource(url, 200, json.dumps(body))
        return super().fetch(url, slot=slot, retain_body=retain_body)


def test_an_offline_archive_index_falls_back_to_its_availability_service() -> None:
    ledger = RunLedger()
    reading = _service(FlakyIndexWeb("unused")).read_site("walled.example", NOW, ledger)
    assert reading.failure is None
    assert reading.pages[0].url.startswith("https://web.archive.org/web/20261005120000id_/")
    assert {"ARCHIVE:INDEX_UNAVAILABLE", "READ:ARCHIVED_HOMEPAGE"} <= set(ledger.decisions)


def test_its_customers_page_is_read_when_no_page_shows_its_clients() -> None:
    # Golden set 2026-10-14: 25 of 30 organizations showed no client on the pages read,
    # while many keep them on a customers or case-studies page, often as unlabeled logos.
    from application.own_site import own_site_discoveries

    home = HOME.replace("</body>", "<a href='/customers'>Customers</a></body>")
    customers = (
        "<html><body><h2>Trusted by our customers</h2>"
        "<img src='/logos/hp-logo.svg'><img src='/img/logo_coca-cola_white@2x.png'>"
        "<img title='Deutsche Bahn' src='/x.png'><img aria-label='Repsol' src='/y.svg'>"
        "<img src='/assets/a1b2c3d4e5f6.svg'></body></html>"
    )
    web = Web({
        "https://apex.example/robots.txt": _resource("https://apex.example/robots.txt", 200, "User-agent: *\nAllow: /\n"),
        "https://apex.example": _resource("https://apex.example/", 200, home),
        "https://apex.example/customers": _resource("https://apex.example/customers", 200, customers),
    })  # fmt: skip
    ledger = RunLedger()
    reading = _service(web).read_site("apex.example", NOW, ledger)
    assert "FETCHED:CUSTOMERS" in ledger.decisions
    clients = [
        d.statement for d in own_site_discoveries(reading.pages) if d.code == "CLIENT_DECLARED"
    ]
    assert clients == ["Hp", "Coca Cola", "Deutsche Bahn", "Repsol"]  # a hash names nobody


def test_no_customers_page_is_read_when_the_pages_read_already_show_clients() -> None:
    wall = "".join(f"<img alt='{n}'>" for n in ("Iberdrola", "Repsol", "Ferrovial"))
    home = HOME.replace(
        "</body>", f"<h2>Our clients</h2>{wall}<a href='/customers'>Customers</a></body>"
    )
    web = Web({
        "https://apex.example/robots.txt": _resource("https://apex.example/robots.txt", 200, "User-agent: *\nAllow: /\n"),
        "https://apex.example": _resource("https://apex.example/", 200, home),
    })  # fmt: skip
    ledger = RunLedger()
    _service(web).read_site("apex.example", NOW, ledger)
    assert "https://apex.example/customers" not in web.requests
