"""Reaching the website the subscriber named, without stretching what it means.

Found in a real-company sample: a bare domain that only serves ``www.`` (its TLS
certificate does not cover the apex) was reported as an unavailable website, and a site
that redirects to another domain was reported as blocked by access rules. The ``www.``
host is the same DNS domain, so it is tried once; another domain could be another
organization, so it is never followed and is named for what it is.
"""

from __future__ import annotations

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
