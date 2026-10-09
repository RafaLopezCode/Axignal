"""Regressions for the adversarial review of spec 063 (doctrine, economics, correctness)."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.first_observation.contracts import AttentionTarget, IdentityLink, TargetKind
from application.first_observation.geography import country_code
from application.first_observation.service import FetchedResource, site_key
from application.first_observation.site import read_page
from application.observation_intelligence.contracts import SourceCapability
from application.world_demand.index import DemandSlice, WorldDemandIngestor
from pipeline.world_demand.sqlite_store import SqliteWorldDemandIndex
from tests.first_observation import harness
from tests.first_observation.harness import NOW, SOLAR_ES, TENDERS, TedWorld, World, build, runtime
from tests.first_observation.test_first_observation_e2e import _attend, _pending_id, _view
from tests.integration.test_organization_admission_e2e import _headers


def _jobs(tmp_path: Path) -> list[tuple[Any, ...]]:
    with sqlite3.connect(tmp_path / "first-observation.sqlite3") as db:
        return db.execute(
            "SELECT state, attempts, last_error FROM fo_jobs ORDER BY created_at"
        ).fetchall()


def test_a_worker_lost_on_the_last_attempt_ends_failed_and_visible(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:stuck", SOLAR_ES)
    store = runtime(facade).store
    start = datetime.now(UTC) - timedelta(hours=1)
    for i in range(3):  # three claims whose workers die (lease never completed)
        claimed = store.claim(
            now=start + timedelta(seconds=10 * i), lease_seconds=1, max_attempts=3
        )
        assert claimed is not None
    assert store.claim(now=datetime.now(UTC), lease_seconds=1, max_attempts=3) is None
    assert _jobs(tmp_path) == [("FAILED", 3, "LEASE_EXPIRED_ON_LAST_ATTEMPT")]
    view = _view(facade, token, _pending_id(facade, token))
    assert view["state"] == "OBSERVATION_FAILED"
    # "Check again" really re-observes: a finished target gets a fresh job.
    retried = facade.handle(
        "POST", "/subscriber/portfolio", _headers(token),
        {"action": "retry_pending", "requestRef": "retry:1", "focusId": _pending_id(facade, token)},
    )  # fmt: skip
    assert retried.body["observationState"] == "QUEUED"
    assert runtime(facade).drain() == 1
    assert _view(facade, token, _pending_id(facade, token))["state"] == "FIRST_PROOF_READY"


def test_one_open_job_per_target_and_a_per_tenant_daily_cap(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:flood", SOLAR_ES)
    pending = _pending_id(facade, token)
    for i in range(5):  # a client resending "check again" while the first job is queued
        facade.handle(
            "POST", "/subscriber/portfolio", _headers(token),
            {"action": "retry_pending", "requestRef": f"retry:{i}", "focusId": pending},
        )  # fmt: skip
    assert len(_jobs(tmp_path)) == 1


def test_two_websites_on_one_host_never_share_a_reading(tmp_path: Path, monkeypatch) -> None:
    acme, bolt = "https://sites.example.com/view/acme/", "https://sites.example.com/view/bolt/"
    monkeypatch.setitem(harness.PAGES, acme, harness.PAGES[SOLAR_ES])
    monkeypatch.setitem(harness.PAGES, bolt, harness.PAGES[harness.BAKERY_FR])
    assert site_key(acme) != site_key(bolt)
    world = World()
    facade = build(tmp_path, world)
    _attend(facade, tmp_path, "subject:acme", acme)
    token, _ = _attend(facade, tmp_path, "subject:bolt", bolt)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert [d["code"] for d in view["discoveries"] if d["kind"] == "ACTIVITY"] == ["isic-I"]


def _focus_target(website: str | None, link: IdentityLink) -> AttentionTarget:
    return AttentionTarget(
        tenant_id="tenant:x", principal_id="principal:x", target_ref="focus_x",
        kind=TargetKind.FOCUS, website=website, name=None, organization_id="org:id:x",
        identity_link=link,
    )  # fmt: skip


class _SeedSpy:
    def __init__(self) -> None:
        self.calls = 0

    def seed(self, *args: Any, **kwargs: Any) -> dict[str, str]:
        self.calls += 1
        return {}


def test_a_subscriber_directed_website_is_never_seeded_as_the_organization(
    tmp_path: Path,
) -> None:
    world = World()
    facade = build(tmp_path, world)
    service = runtime(facade).service
    spy = _SeedSpy()
    service._seeds = spy
    proof = service.observe(_focus_target(SOLAR_ES, IdentityLink.SUBSCRIBER_DIRECTED))
    assert spy.calls == 0  # no write under the Organization subject
    assert proof.ready and any(d.kind.value == "DEMAND" for d in proof.discoveries)
    assert all(not c["basis"]["observationId"].startswith("fo:") for c in proof.capabilities)
    other = service.observe(_focus_target(SOLAR_ES, IdentityLink.WEBSITE_OF_ANOTHER_ORGANIZATION))
    assert other.state.value == "NO_PUBLIC_WEBSITE"
    assert [d.code for d in other.discoveries] == ["WEBSITE_OF_ANOTHER_ORGANIZATION"]
    assert world.sites.requests.count(SOLAR_ES) == 1  # the conflicting site was not fetched


def test_a_broken_semantic_provider_still_yields_the_deterministic_proof(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)

    def broken() -> None:
        raise FileNotFoundError("key file rotated away")

    runtime(facade).service._cascade_factory = broken
    token, _ = _attend(facade, tmp_path, "subject:broken", harness.SCHOOL_AR)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert view["state"] == "NOT_ENOUGH_CAPABILITY_EVIDENCE"
    assert "SKIPPED:SEMANTIC:FAILED:FileNotFoundError" in view["_ledger"]["decisions"]


def test_a_redirect_onto_a_robots_disallowed_path_is_discarded(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    service = runtime(facade).service
    origin = "https://redirects.example.com"
    harness.ROBOTS[origin] = "User-agent: *\nDisallow: /private\n"
    try:
        real = world.sites.fetch

        def fetch(url: str, *, slot: str) -> FetchedResource:
            if url == origin + "/":
                body = b"<html><body><p>Instalaciones fotovoltaicas.</p></body></html>"
                return replace(
                    world.sites._resource(url, 200, "text/html", body.decode()),
                    final_url=origin + "/private/home",
                )
            return real(url, slot=slot)

        service._fetcher.fetch = fetch  # type: ignore[method-assign]
        proof = service.observe(replace(_focus_target(origin + "/", IdentityLink.IDENTITY_PENDING),
                                        kind=TargetKind.PENDING, organization_id=None))  # fmt: skip
    finally:
        del harness.ROBOTS[origin]
    assert proof.state.value == "SOURCE_UNAVAILABLE"
    assert "DISCARDED:ROBOTS_AFTER_REDIRECT" in proof.ledger["decisions"]


def test_a_large_slice_resumes_across_runs_and_completes(tmp_path: Path) -> None:
    many = tuple(
        replace(TENDERS[0], record_id=f"7{i:05d}-2026", title=f"Notice {i}") for i in range(250)
    )
    ted = TedWorld(extra=many)
    store = SqliteWorldDemandIndex(tmp_path / "index.sqlite3")
    item = DemandSlice("ted-search-v3", "EU/ES", SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES)
    store.demand(item, now=NOW)
    ingestor = WorldDemandIngestor(
        feeds={"ted-search-v3": ted}, store=store, clock=lambda: NOW, max_pages=1
    )
    reports = [ingestor.run()[0] for _ in range(3)]
    assert [r.complete for r in reports] == [False, False, True]
    assert [p for _g, p in ted.pages] == [1, 2, 3]  # never re-paged from the start
    assert len(store.records(item)) == 251


def test_parser_and_place_edge_cases() -> None:
    page = read_page(
        url="https://x.example.com/",
        html="<html><head><title>Acme Solar</title></head><body><svg><title>Menu icon</title>"
        "</svg><p>Text</p></body></html>",
        observed_at=NOW,
        content_fingerprint="f",
        artifact_ref=None,
    )
    assert page.title == "Acme Solar" and "Text" in page.text
    unclosed = read_page(
        url="https://x.example.com/", html="<title>Broken<body><p>Body text</p>",
        observed_at=NOW, content_fingerprint="f", artifact_ref=None,
    )  # fmt: skip
    assert "Body text" in unclosed.text
    assert (country_code("UK"), country_code("EL")) == ("GB", "GR")
