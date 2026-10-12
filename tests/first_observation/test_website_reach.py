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
from application.first_observation.service import FetchedResource, FirstObservationService

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
