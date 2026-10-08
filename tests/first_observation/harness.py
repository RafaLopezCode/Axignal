"""Controlled world for spec 063 E2E: six very different businesses, no network.

Only the network-facing ports are replaced (website GETs, the TED search adapter and
the System One provider). Identity admission, the portfolio, entitlements, jobs, leases,
Observation Memory, the projection and the HTTP facade are the real composition.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.first_observation.service import FetchedResource
from application.observation_intelligence.contracts import (
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
    geo,
)
from application.observation_intelligence.findings import ProcurementRecord, SourceFindings
from application.observation_intelligence.strategy import ObservationAction
from application.observation_runtime.replay import matches
from application.semantic_layer.cascade import CascadePolicy, SemanticCascade
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion
from application.semantic_layer.ledger import JEV_1_13_PRICE, CostLedger, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from application.subscriber_identity.runtime import SystemClock
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from tests.integration.test_subscriber_composition import _ControlledOidc, _settings
from tests.semantic_layer.fakes import FakeSystemOne
from tools.runtime.first_observation import FirstObservationOverrides
from tools.runtime.subscriber_composition import build_subscriber_facade

NOW = datetime.now(UTC)


def _ld(payload: object) -> str:
    return f'<script type="application/ld+json">{json.dumps(payload)}</script>'


# A. Solar installer in Spain: lexicon capability, declared Spanish address, TED demand.
SOLAR_ES = "https://solaria-norte.example.com/"
# B. Language school in Arkansas: no JSON-LD; location only in prose; no US source.
SCHOOL_AR = "https://littlerock-languages.example.com/"
# C. Digital SaaS serving globally from Ireland: schema.org SoftwareApplication.
SAAS_IE = "https://ledgerly.example.com/"
# D. Local bakery in France: schema.org Bakery, nothing a tender usually buys.
BAKERY_FR = "https://boulangerie-lune.example.com/"
# E. A site that gives no usable evidence.
PLACEHOLDER = "https://soon.example.com/"
# F. Known canonical Organization: registry records this website.
KNOWN = "https://www.solartec.example.com/"
# Robots forbid everything.
FORBIDDEN = "https://private-robots.example.com/"

PAGES: dict[str, str] = {
    SOLAR_ES: (
        '<html lang="es"><head><title>Solaria Norte | Instalaciones fotovoltaicas</title>'
        '<meta name="description" content="Diseñamos e instalamos sistemas de autoconsumo '
        'fotovoltaico para empresas y ayuntamientos.">'
        + _ld({"@context": "https://schema.org", "@type": "Organization", "name": "Solaria Norte",
               "legalName": "Solaria Norte SL",
               "address": {"@type": "PostalAddress", "addressLocality": "Madrid",
                           "addressCountry": "ES"}})
        + "</head><body><h1>Energía solar para empresas</h1>"
        "<p>Instalaciones fotovoltaicas de autoconsumo en naves industriales y edificios "
        'públicos.</p><a href="/servicios">Servicios</a></body></html>'
    ),
    SCHOOL_AR: (
        '<html lang="en"><head><title>Little Rock Language Studio</title>'
        '<meta name="description" content="Spanish and French classes for adults and kids.">'
        "</head><body><h1>Learn a language with native teachers</h1>"
        "<p>Spanish and French classes for adults and kids in our studio.</p>"
        "<p>Visit us in Little Rock, Arkansas.</p>"
        '<a href="/about">About us</a> <a href="/courses">Courses</a>'
        '<a href="/blog/2024/tips">Tips</a></body></html>'
    ),
    SCHOOL_AR + "courses": (
        "<html><head><title>Courses</title></head><body><h1>Courses</h1>"
        "<p>Group courses, private lessons and corporate language training.</p></body></html>"
    ),
    SCHOOL_AR + "about": (
        "<html><head><title>About</title></head><body><h1>About us</h1>"
        "<p>Founded in 2015 by language teachers.</p></body></html>"
    ),
    SAAS_IE: (
        '<html lang="en"><head><title>Ledgerly — invoicing software</title>'
        '<meta name="description" content="Cloud invoicing and bookkeeping software for small '
        'businesses worldwide.">'
        + _ld([{"@context": "https://schema.org", "@type": "SoftwareApplication",
                "name": "Ledgerly", "applicationCategory": "BusinessApplication"},
               {"@context": "https://schema.org", "@type": "Organization", "name": "Ledgerly",
                "address": {"@type": "PostalAddress", "addressLocality": "Dublin",
                            "addressCountry": "IE"}}])
        + '<link rel="alternate" hreflang="de" href="/de/"><link rel="alternate" hreflang="fr" '
        'href="/fr/"></head><body><h1>Invoicing that runs itself</h1>'
        "<p>Used by teams in 40 countries.</p></body></html>"
    ),
    BAKERY_FR: (
        '<html lang="fr"><head><title>Boulangerie de la Lune</title>'
        + _ld({"@context": "https://schema.org", "@type": "Bakery",
               "name": "Boulangerie de la Lune",
               "address": {"@type": "PostalAddress", "addressLocality": "Lyon",
                           "addressCountry": "FR"}})
        + "</head><body><h1>Pain au levain</h1><p>Pain, viennoiseries et gâteaux chaque matin."
        "</p></body></html>"
    ),
    PLACEHOLDER: "<html><head><title>Coming soon</title></head><body><h1>Coming soon</h1></body></html>",
    KNOWN: (
        '<html lang="es"><head><title>Solartec Energía</title>'
        + _ld({"@context": "https://schema.org", "@type": "Organization",
               "name": "Solartec Energía", "legalName": "Solartec Energía SL",
               "address": {"@type": "PostalAddress", "addressCountry": "ES"}})
        + "</head><body><h1>Solartec</h1><p>Instalaciones fotovoltaicas de autoconsumo para "
        "industria y administraciones públicas.</p></body></html>"
    ),
    FORBIDDEN: "<html><body><p>Instalaciones fotovoltaicas.</p></body></html>",
}  # fmt: skip
ROBOTS: dict[str, str] = {
    "https://private-robots.example.com": "User-agent: *\nDisallow: /\n",
}


class SiteWorld:
    """In-process public web: counts every GET and can fail on demand."""

    def __init__(self) -> None:
        self.requests: list[str] = []
        self.fail_next: set[str] = set()

    def fetch(self, url: str, *, slot: str) -> FetchedResource:
        self.requests.append(url)
        if url in self.fail_next:
            self.fail_next.discard(url)
            raise OSError("controlled transport failure")
        origin = url.split("/robots.txt")[0] if url.endswith("/robots.txt") else None
        if origin is not None:
            body_text = ROBOTS.get(origin)
            return self._resource(url, 404 if body_text is None else 200, "text/plain", body_text)
        page = PAGES.get(url)
        return self._resource(url, 404 if page is None else 200, "text/html; charset=utf-8", page)

    @staticmethod
    def _resource(url: str, status: int, kind: str, text: str | None) -> FetchedResource:
        body = None if text is None else text.encode("utf-8")
        return FetchedResource(
            requested_url=url,
            final_url=url,
            observed_at=NOW,
            status=status,
            content_type=kind,
            body=body,
            content_fingerprint=None if body is None else "sha256:" + hashlib.sha256(body).hexdigest(),
            artifact_ref=None if body is None else "artifact:" + hashlib.sha256(body).hexdigest()[:16],
            requests=1,
            failure=None if status == 200 else f"http_{status}",
        )  # fmt: skip


TENDERS = (
    ProcurementRecord(
        record_id="801234-2026",
        source_id="ted-search-v3",
        kind=SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
        title="Instalación fotovoltaica de autoconsumo en edificios municipales",
        buyer_name="Ayuntamiento de Getafe",
        places=(geo("EU/ES/ES3/ES30/ES300"),),
        demand_codes=(TaxonomyCode("CPV", "09332000"),),
        published_at=NOW - timedelta(days=4),
        source_url="https://ted.europa.eu/en/notice/-/detail/801234-2026",
        deadline=(NOW + timedelta(days=25)).date().isoformat(),
    ),
)


class TedWorld:
    """Stand-in for the TED adapter: the source's own exact criteria, counted."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings:
        self.queries.append(action.action_id)
        records = tuple(r for r in TENDERS if matches(r, action.query))
        return SourceFindings(
            source_id=source.source_id,
            retrieved_at=NOW,
            requests=1,
            amount_microunits=0,
            latency_ms=40,
            records=records,
            total_available=len(records),
            failure=None,
        )


def jev_rule(batch: SemanticBatch, question: SemanticQuestion) -> tuple[str, float]:
    text = json.dumps(batch.state, ensure_ascii=False).lower()
    qid = question.question_id
    teaching = "classes" in text or "courses" in text
    if qid == "fo_operating_business":
        return ("false", 0.9) if "coming soon" in text else ("true", 0.95)
    if qid == "fo_isic_section":
        return ("P", 0.91) if teaching else ("UNCLEAR", 0.7)
    if qid == "fo_naics_sector":
        return ("61", 0.88) if teaching else ("UNCLEAR", 0.7)
    if qid == "fo_cpv_division":
        return ("80", 0.84) if teaching else ("UNCLEAR", 0.7)
    if qid == "fo_customer_type":
        return ("CONSUMERS", 0.8)
    if qid == "fo_delivery_mode":
        return ("PREMISES", 0.82)
    if qid == "fo_operating_location":
        return ("US/US-AR", 0.9) if "US/US-AR" in question.labels else ("NONE_STATED", 0.7)
    return (question.labels[-1], 0.5)


@dataclass
class World:
    sites: SiteWorld = field(default_factory=SiteWorld)
    ted: TedWorld = field(default_factory=TedWorld)
    judge: FakeSystemOne = field(default_factory=lambda: FakeSystemOne(jev_rule))
    memory: InMemoryJudgmentMemory = field(default_factory=InMemoryJudgmentMemory)

    def cascade(self) -> SemanticCascade:
        return SemanticCascade(
            judge=self.judge,
            ledger=CostLedger(prices=(JEV_1_13_PRICE,)),
            budget=SemanticBudget(max_system_one_input_tokens=12_000),
            policy=CascadePolicy(),
            memory=self.memory,
        )


def build(
    tmp_path: Path,
    world: World,
    *,
    enabled: bool = True,
    semantic: bool = True,
    identity_source: Any = None,
) -> Any:
    facade = build_subscriber_facade(
        _settings(tmp_path, pilot=True),
        tmp_path,
        observation_memory=SqliteObservationMemory(tmp_path / "observation-memory.sqlite3"),
        reuse_policy=ObservationReusePolicy("subscriber-read", "051-v1"),
        temporal_policy=TemporalCurrentnessPolicy(
            "subscriber-currentness", "051-v1", timedelta(days=7), timedelta(days=30)
        ),
        code_sha="test-code-sha",
        clock=SystemClock(),
        identity_source=identity_source,
        first_observation_overrides=FirstObservationOverrides(
            enabled=enabled,
            worker="manual",
            fetcher=world.sites,
            source_ports={"ted-search-v3": world.ted},
            cascade_factory=world.cascade if semantic else (lambda: None),
        ),
    )
    facade.identity.auth._provider = _ControlledOidc()
    return facade


def runtime(facade: Any) -> Any:
    return facade.workflow._trigger.first_observation


def discoveries(view: Mapping[str, Any], kind: str) -> list[dict[str, Any]]:
    return [d for d in view["discoveries"] if d["kind"] == kind]


def codes(view: Mapping[str, Any]) -> set[str]:
    return {str(d["code"]) for d in view["discoveries"]}
