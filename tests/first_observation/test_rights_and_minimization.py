"""CTO review of PR #174: content rights, retention and evaluator input minimization.

ADR-0015: public visibility and robots.txt are not authority to reuse or retain content;
raw text retention is not automatic. ADR-0090 §5: evaluator input needs input rights and
person-free state. ADR-0047: provider confidence is not a probability of truth.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.first_observation.rights import NoContentRights
from application.source_acquisition import SourceObservation
from pipeline.first_observation.http_fetcher import GovernedSiteFetcher
from pipeline.source_acquisition import ContentAddressedArtifactStore
from tests.first_observation import harness
from tests.first_observation.harness import (
    KNOWN,
    SCHOOL_AR,
    SOLAR_ES,
    World,
    build,
    registered_rights,
    runtime,
)
from tests.first_observation.test_first_observation_e2e import (
    SOLARTEC,
    _attend,
    _pending_id,
    _view,
    discoveries,
)
from tests.organization_admission.registry_fixture import ControlledRegistry, entity


def _site_row(tmp_path: Path, origin: str) -> dict[str, Any]:
    with sqlite3.connect(tmp_path / "first-observation.sqlite3") as db:
        (reading,) = db.execute("SELECT reading FROM fo_sites WHERE origin=?", (origin,)).fetchone()
    return dict(json.loads(reading))


def test_without_rights_the_private_observation_works_and_nothing_is_kept_or_sent(
    tmp_path: Path,
) -> None:
    world = World()
    facade = build(tmp_path, world, rights=NoContentRights())
    token, _ = _attend(facade, tmp_path, "subject:no-rights", SOLAR_ES)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    # Legitimate private observation still answers the subscriber who asked.
    assert view["state"] == "FIRST_PROOF_READY" and discoveries(view, "ACTIVITY")
    assert "NOT_SHARED:CONTENT_RIGHTS_UNKNOWN" in view["_ledger"]["decisions"]
    # World-level store keeps fingerprints and robots, never page content.
    stored = _site_row(tmp_path, SOLAR_ES)
    assert stored["sharedUntil"] is None
    assert all(p["text"] == "" and p["title"] == "" for p in stored["pages"])
    assert stored["pages"][0]["contentFingerprint"].startswith("sha256:")
    # No raw body was asked to be retained.
    assert world.sites.retained and not any(world.sites.retained)
    # Another tenant cannot reuse content that may not be shared: it is fetched again.
    before = len(world.sites.requests)
    second, _ = _attend(facade, tmp_path, "subject:no-rights-2", SOLAR_ES)
    runtime(facade).drain()
    assert len(world.sites.requests) > before
    assert discoveries(_view(facade, second, _pending_id(facade, second)), "ACTIVITY")


def test_without_input_rights_no_page_text_reaches_the_semantic_provider(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world, rights=registered_rights(provider_input=False))
    token, _ = _attend(facade, tmp_path, "subject:no-input", SCHOOL_AR)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert world.judge.calls == []
    assert "SKIPPED:SEMANTIC:PROVIDER_INPUT_RIGHTS_UNKNOWN" in view["_ledger"]["decisions"]


def test_a_registry_verified_website_without_rights_is_never_seeded(tmp_path: Path) -> None:
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    registry = ControlledRegistry(
        [entity(artifacts, legal_name="Solartec Energía SL", lei_value=SOLARTEC, websites=(KNOWN,))]
    )
    world = World()
    facade = build(tmp_path, world, identity_source=registry, rights=NoContentRights())
    token, added = _attend(facade, tmp_path, "subject:verified-no-rights", KNOWN)
    runtime(facade).drain()
    view = _view(facade, token, str(added["focusId"]))
    assert view["target"]["identityLink"] == "REGISTRY_VERIFIED"
    assert "PRIVATE_PATH:CONTENT_RIGHTS_UNKNOWN" in view["_ledger"]["decisions"]
    with sqlite3.connect(tmp_path / "observation-memory.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 0


def test_lost_rights_purge_shared_content_before_any_reuse(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)  # rights registered
    _attend(facade, tmp_path, "subject:rights-1", SOLAR_ES)
    runtime(facade).drain()
    assert _site_row(tmp_path, SOLAR_ES)["pages"][0]["text"]  # shared under rights
    runtime(facade).service._rights = NoContentRights()  # the operator withdraws the basis
    token, _ = _attend(facade, tmp_path, "subject:rights-2", SOLAR_ES)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    decisions = view["_ledger"]["decisions"]
    assert "PURGED:SHARED_CONTENT:RIGHTS_NOT_PERMITTED" in decisions
    assert "REUSED:SITE_READING_CURRENT" not in decisions
    assert _site_row(tmp_path, SOLAR_ES)["pages"][0]["text"] == ""


def test_retention_expires_shared_text_and_private_citations(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:expiry", SOLAR_ES)
    runtime(facade).drain()
    # Even with reuse rights, the service never persists duplicate raw HTTP bodies.
    assert world.sites.retained and not any(world.sites.retained)
    pending = _pending_id(facade, token)
    assert any(d["excerpt"] for d in _view(facade, token, pending)["discoveries"])
    purged = runtime(facade).store.purge(now=datetime.now(UTC) + timedelta(days=400))
    assert purged == {"siteReadings": 1, "proofs": 1}
    assert _site_row(tmp_path, SOLAR_ES)["pages"][0]["text"] == ""
    expired = _view(facade, token, pending)
    assert expired["contentExpiredAt"] and not any(d["excerpt"] for d in expired["discoveries"])
    # Expired shared content is never reused: the next reader fetches again.
    assert runtime(facade).service._sites.site(SOLAR_ES).content_retained is False


class _Sensor:
    def __init__(self, artifacts: ContentAddressedArtifactStore) -> None:
        self.artifacts = artifacts

    def observe(self, request: Any, policy: Any) -> SourceObservation:
        body = self.artifacts.put_bytes(b"<html><body><p>Raw page</p></body></html>")
        envelope = self.artifacts.put_json({"request": request.request_id})
        return SourceObservation(
            request_id=request.request_id, subject_id=request.subject_id,
            observation_slot=request.observation_slot, requested_uri=request.target_uri,
            final_uri=request.target_uri, retrieved_at=datetime.now(UTC), http_status=200,
            content_type="text/html", body_fingerprint="sha256:x", body_artifact_ref=body,
            raw_observation_ref=envelope, observation_fingerprint="sha256:y",
            instrument_ref="test", policy_id=policy.policy_id,
            policy_fingerprint=policy.fingerprint, redirect_chain=(request.target_uri,),
            peer_ips=("192.0.2.1",), failure_state=None,
        )  # fmt: skip


def test_the_governed_fetcher_discards_raw_bodies_unless_retention_is_permitted(
    tmp_path: Path,
) -> None:
    artifacts = ContentAddressedArtifactStore(tmp_path / "fo-artifacts")
    fetcher = GovernedSiteFetcher(sensor=_Sensor(artifacts), artifacts=artifacts)  # type: ignore[arg-type]
    kept = fetcher.fetch("https://example.com/", slot="website", retain_body=True)
    assert kept.body and kept.requests == 1
    body_files = [p for p in (tmp_path / "fo-artifacts").rglob("*") if p.is_file()]
    assert len(body_files) == 2  # body + envelope
    dropped = fetcher.fetch("https://example.com/", slot="website", retain_body=False)
    assert dropped.body  # usable in memory for this run only
    remaining = [p for p in (tmp_path / "fo-artifacts").rglob("*") if p.is_file()]
    assert len(remaining) == 1  # only the metadata envelope survives


def test_evaluator_state_is_minimized_and_excludes_pages_about_people(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setitem(
        harness.PAGES,
        SCHOOL_AR + "about",
        "<html><head><title>About</title></head><body><h1>About us</h1>"
        "<p>Founded by John Smith and Dr. Ana García in 2015.</p>"
        "<p>Write to john.smith@littlerock-languages.example.com or call +1 501 555 0100.</p>"
        "</body></html>",
    )
    world = World()
    facade = build(tmp_path, world)
    _attend(facade, tmp_path, "subject:minimize", SCHOOL_AR)
    runtime(facade).drain()
    (batch,) = world.judge.calls
    state = json.dumps(batch.state, ensure_ascii=False)
    for personal in ("John Smith", "García", "john.smith@", "555 0100"):
        assert personal not in state, personal
    assert "arkansas" in state.casefold() and "little rock" in state.casefold()
    assert "Alicia" not in state and "Beatriz" not in state
    assert SCHOOL_AR not in state  # no URL/host passed to the evaluator


def test_provider_confidence_never_reaches_the_subscriber(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:confidence", SCHOOL_AR)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    (activity,) = discoveries(view, "ACTIVITY")
    assert "confidence" not in activity["detail"] and activity["detail"]["model"] == "jev-1.13.0"
    # The authorized trace keeps the provider's original value.
    tenant = str(facade.identity.authenticate(token).tenant_id)
    stored = runtime(facade).store.proof(tenant, _pending_id(facade, token))
    (traced,) = [d for d in stored["discoveries"] if d["kind"] == "ACTIVITY"]
    assert traced["detail"]["confidence"] > 0.6


def test_single_word_names_and_url_usernames_are_never_sent_to_evaluator(
    tmp_path: Path, monkeypatch
) -> None:
    from application.first_observation.activity import _state, minimize
    from application.first_observation.site import read_page

    assert "Alicia" not in minimize("Nuestro equipo incluye a Alicia para asistencia.")
    assert "Beatriz" not in minimize("Our consultant Beatriz handles support.")
    assert "alice" not in minimize("Please write to alice@example.com")
    page = read_page(
        url="https://personal.example.com/users/alicia?email=alice@example.com",
        html=(
            "<html><head><title>Beatriz Ruiz's classes</title></head>"
            "<body><p>Classes offered by Alicia. "
            "Call 555 0100, write to alice@example.com.</p></body></html>"
        ),
        observed_at=datetime.now(UTC),
        content_fingerprint="test",
        artifact_ref=None,
    )
    raw = json.dumps(_state(page.url, [page]), ensure_ascii=False).casefold()
    for forbidden in ("alicia", "beatriz", "ruiz", "personal.example", "alice@", "555 0100"):
        assert forbidden not in raw, forbidden
    assert "classes" in raw


def test_registry_rights_respect_path_and_currentness() -> None:
    from dataclasses import replace

    from application.economic_discovery.observation_reuse import ReusePurpose
    from application.first_observation.rights import RegisteredContentRights
    from application.source_acquisition import SourceTargetRule
    from domain.evidence.epistemics import Currentness
    from tests.first_observation.harness import registered_rights

    policy = registered_rights()
    grant = policy.rights_for(SOLAR_ES, now=datetime.now(UTC)).entry
    assert grant is not None
    narrowed = replace(
        grant,
        targets=(SourceTargetRule("solaria-norte.example.com", "/permitted/", ("https",)),),
    )
    restricted = RegisteredContentRights((narrowed,), provider_input=frozenset({grant.source_id}))
    now = datetime.now(UTC)
    assert restricted.rights_for(
        "https://solaria-norte.example.com/permitted/a", now=now
    ).reuse_permitted
    assert not restricted.rights_for(
        "https://solaria-norte.example.com/unrelated", now=now
    ).reuse_permitted
    assert not restricted.rights_for(
        "https://solaria-norte.example.com/permittedness", now=now
    ).reuse_permitted
    assert (
        not RegisteredContentRights((replace(narrowed, currentness=Currentness.UNKNOWN),))
        .rights_for("https://solaria-norte.example.com/permitted/a", now=now)
        .reuse_permitted
    )
    assert (
        not RegisteredContentRights(
            (replace(narrowed, allowed_purposes=(ReusePurpose.HISTORICAL_REFERENCE,)),)
        )
        .rights_for("https://solaria-norte.example.com/permitted/a", now=now)
        .reuse_permitted
    )


def test_memory_raw_content_is_retired_but_history_envelope_remains(tmp_path: Path) -> None:
    from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
    from tests.first_observation.harness import KNOWN
    from tests.first_observation.test_first_observation_e2e import SOLARTEC
    from tests.organization_admission.registry_fixture import ControlledRegistry, entity

    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    registry = ControlledRegistry(
        [entity(artifacts, legal_name="Solartec Energía SL", lei_value=SOLARTEC, websites=(KNOWN,))]
    )
    facade = build(tmp_path, World(), identity_source=registry)
    _attend(facade, tmp_path, "subject:memory-ttl", KNOWN)
    runtime(facade).drain()
    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    with sqlite3.connect(tmp_path / "observation-memory.sqlite3") as db:
        before = db.execute(
            "SELECT observation_id, raw_content FROM observations WHERE observation_id LIKE 'fo:%'"
        ).fetchall()
    assert before and any(content for _, content in before)
    result = memory.purge_first_observation_content(
        now=datetime.now(UTC) + timedelta(days=400),
        retain_until=lambda source, observed: observed + timedelta(days=30),
    )
    assert result == len(before)
    with sqlite3.connect(tmp_path / "observation-memory.sqlite3") as db:
        after = db.execute(
            "SELECT observation_id, raw_content, raw_artifact_ref FROM observations WHERE observation_id LIKE 'fo:%'"
        ).fetchall()
    assert [row[0] for row in after] == [row[0] for row in before]
    assert all(content == "" and ref is None for _, content, ref in after)


def test_runtime_purge_withdraws_canonical_raw_after_rights_revocation(tmp_path: Path) -> None:
    from tests.first_observation.harness import KNOWN
    from tests.first_observation.test_first_observation_e2e import SOLARTEC
    from tests.organization_admission.registry_fixture import ControlledRegistry, entity

    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    registry = ControlledRegistry(
        [entity(artifacts, legal_name="Solartec Energía SL", lei_value=SOLARTEC, websites=(KNOWN,))]
    )
    facade = build(tmp_path, World(), identity_source=registry)
    _attend(facade, tmp_path, "subject:revoke", KNOWN)
    observing = runtime(facade)
    observing.drain()
    with sqlite3.connect(tmp_path / "observation-memory.sqlite3") as db:
        assert (
            db.execute(
                "SELECT count(*) FROM observations WHERE observation_id LIKE 'fo:%' AND raw_content != ''"
            ).fetchone()[0]
            > 0
        )
    observing.service._rights = NoContentRights()
    count = observing.purge()
    assert count["canonicalRaw"] > 0
    with sqlite3.connect(tmp_path / "observation-memory.sqlite3") as db:
        assert (
            db.execute(
                "SELECT count(*) FROM observations WHERE observation_id LIKE 'fo:%' AND raw_content != ''"
            ).fetchone()[0]
            == 0
        )


def test_operator_rights_revocation_is_live_and_fails_closed(tmp_path: Path) -> None:
    from tools.runtime.first_observation import RIGHTS_FILE_KEY, load_content_rights

    file = tmp_path / "website-rights.json"
    file.write_text(
        json.dumps(
            [
                {
                    "host": "solaria-norte.example.com",
                    "rightsBasis": "controlled fixture approval",
                    "rawRetentionDays": 30,
                    "metadataRetentionDays": 60,
                    "providerInput": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    policy = load_content_rights({RIGHTS_FILE_KEY: str(file)})
    now = datetime.now(UTC)
    assert policy.rights_for(SOLAR_ES, now=now).reuse_permitted
    assert policy.rights_for(SOLAR_ES, now=now).provider_input
    file.write_text("[]", encoding="utf-8")
    assert not policy.rights_for(SOLAR_ES, now=now).reuse_permitted
    file.write_text("{broken", encoding="utf-8")
    assert not policy.rights_for(SOLAR_ES, now=now).reuse_permitted
    file.unlink()
    assert not policy.rights_for(SOLAR_ES, now=now).reuse_permitted
