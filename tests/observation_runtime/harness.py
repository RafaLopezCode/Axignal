"""Controlled world for multi-day autonomous observation tests.

The clock, the public web and the TED corpus are all under test control. The
TED stand-in is the existing offline fixture behind the real TED adapter, so
expert queries, parsing and candidate derivation are the production code.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.observation_intelligence import (
    MarketRole,
    MarketScope,
    XeedObservationContext,
    derive_families,
    detect_capabilities,
    geo,
)
from application.observation_runtime import (
    ObservationFamily,
    PublicWebsiteAcquirer,
    RecomputationRequest,
    RecomputeTrigger,
    XeedAttention,
    procurement_acquirers,
)
from application.source_acquisition.contracts import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
    SourceTargetRule,
)
from domain.xignal import XignalEpistemicState
from pipeline.observation_intelligence import TedSearchAdapter
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from tests.observation_intelligence.ted_fixture import CORPUS, FixtureTedTransport, _notice

DAY_1 = datetime(2026, 10, 6, 5, 0, tzinfo=UTC)
XEED = "xeed:solartec"
SITE = "https://solartec.example/"
HOMEPAGE = (
    "Solartec Levante. Somos una empresa valenciana especializada en instalaciones "
    "fotovoltaicas de autoconsumo para industria y administraciones públicas. "
    "También ejecutamos instalaciones eléctricas en baja tensión."
)
#: A second award by the same buyer makes it recurring (the base corpus has one each).
RECURRING_AWARD = _notice(
    "650006-2026", "can-standard", "Ampliación de autoconsumo en edificios provinciales",
    "Diputación de Valencia", ["ESP", "ES523"], ["09332000"], "2026-08-30",
    winner="Solar Mediterránea SA",
)  # fmt: skip
#: Published on day 17 by the recurring buyer, in a region revealed by awards.
NEW_CALL = _notice(
    "720301-2026", "cn-standard", "Instalación fotovoltaica en mercados municipales",
    "Diputación de Valencia", ["ESP", "ES523"], ["09332000"], "2026-10-22", "2026-11-30",
)  # fmt: skip


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def at_day(self, day: int, hour: int = 5) -> datetime:
        self.now = DAY_1.replace(hour=hour) + timedelta(days=day - 1)
        return self.now


@dataclass
class FakeWeb:
    """The public web as seen by the governed sensor: one body per URL, or a failure."""

    clock: Clock
    pages: dict[str, str] = field(default_factory=dict)
    down: set[str] = field(default_factory=set)
    requests: Counter[str] = field(default_factory=Counter)

    def observe(self, request: SourceRequest, policy: SourceDispatchPolicy) -> SourceObservation:
        url = request.target_uri
        self.requests[url] += 1
        body = self.pages.get(url)
        failure = "connection_failed" if url in self.down else None
        status = None if failure else (200 if body is not None else 404)
        fingerprint = None if body is None or failure else hashlib.sha256(body.encode()).hexdigest()
        # Like the real sensor envelope, the observation includes when it was retrieved.
        observed = hashlib.sha256(
            f"{url}|{status}|{fingerprint}|{self.clock().isoformat()}".encode()
        ).hexdigest()
        return SourceObservation(
            request_id=request.request_id,
            subject_id=request.subject_id,
            observation_slot=request.observation_slot,
            requested_uri=url,
            final_uri=url,
            retrieved_at=self.clock(),
            http_status=status,
            content_type=None if status is None else "text/html",
            body_fingerprint=fingerprint,
            body_artifact_ref=None if fingerprint is None else f"artifact:{fingerprint[:16]}",
            raw_observation_ref=f"raw:{observed[:16]}",
            observation_fingerprint=observed,
            instrument_ref="fake-web-sensor/1",
            policy_id=request.policy_id,
            policy_fingerprint=request.policy_fingerprint,
            redirect_chain=(url,),
            peer_ips=() if status is None else ("203.0.113.10",),
            failure_state=failure,
            policy_version=request.policy_version,
        )


class CountingTed(FixtureTedTransport):
    def __init__(self) -> None:
        super().__init__(corpus=(*CORPUS, RECURRING_AWARD))

    def publish(self, notice: dict[str, Any]) -> None:
        self.corpus = (*self.corpus, notice)


@dataclass
class Downstream:
    """Brain work behind the runtime, with the cost model of the existing reuse path.

    Material change: one semantic extraction plus every family dimension.
    Currentness transition: no extraction, only freshness-dependent dimensions.
    The scheduler never reaches this port except through these requests.
    """

    requests: list[RecomputationRequest] = field(default_factory=list)
    semantic_extractions: int = 0
    structured_evaluations: int = 0
    dimensions_per_family: int = 2

    def recompute(self, request: RecomputationRequest) -> None:
        self.requests.append(request)
        if request.family is ObservationFamily.DEMAND:
            return  # deterministic candidate projection; no model involved
        if request.trigger is RecomputeTrigger.MATERIAL_CHANGE:
            self.semantic_extractions += 1
            self.structured_evaluations += self.dimensions_per_family
        else:
            self.structured_evaluations += 1


ATTENTION = (
    XeedAttention(
        xeed_id=XEED,
        organization_name="Solartec Levante",
        website=SITE,
        markets=(
            MarketScope(
                geo("EU/ES"),
                frozenset({MarketRole.PUBLIC_BUYERS, MarketRole.PRIVATE_BUSINESSES}),
                XignalEpistemicState.OBSERVED,
            ),
        ),
    ),
)


def website_policy(url: str) -> SourceDispatchPolicy | None:
    if not url.startswith("https://solartec.example/"):
        return None
    return SourceDispatchPolicy(
        policy_id="public-web-solartec",
        disposition=DispatchDisposition.ALLOW,
        decision_basis="registered public homepage policy",
        targets=(SourceTargetRule("solartec.example"),),
        max_redirects=0,
    )


def context_for(attention: XeedAttention, as_of: datetime) -> XeedObservationContext | None:
    capabilities = detect_capabilities(
        text=HOMEPAGE,
        observation_id=f"obs:{attention.xeed_id}:homepage",
        source_ref=SITE,
        observed_at=DAY_1,
    )
    return XeedObservationContext(
        xeed_id=attention.xeed_id,
        as_of=as_of,
        capabilities=capabilities,
        families=derive_families(capabilities),
        markets=attention.markets,
    )


@dataclass
class World:
    root: Path
    clock: Clock
    web: FakeWeb
    ted: CountingTed
    downstream: Downstream

    def store(self) -> SqliteObservationRuntimeStore:
        """A fresh handle on the same file: what a restarted process would open."""
        return SqliteObservationRuntimeStore(self.root / "runtime.sqlite3")

    def acquirers(self) -> dict[str, Any]:
        memory = SqliteObservationMemory(self.root / "observation-memory.sqlite3")
        acquirers: dict[str, Any] = dict(
            procurement_acquirers(
                {"ted-search-v3": TedSearchAdapter(self.ted, clock=self.clock)},
                contexts=context_for,
            )
        )
        acquirers["official-public-website"] = PublicWebsiteAcquirer(
            sensor=self.web, policy_for=website_policy, memory=memory
        )
        return acquirers


def world(root: Path) -> World:
    clock = Clock(DAY_1)
    web = FakeWeb(
        clock,
        pages={
            SITE: f"<html><body>{HOMEPAGE}</body></html>",
            "https://solartec.example/robots.txt": "User-agent: *\nAllow: /\n",
            "https://solartec.example/sitemap.xml": "<urlset><url><loc>/</loc></url></urlset>",
        },
    )
    return World(root, clock, web, CountingTed(), Downstream())
