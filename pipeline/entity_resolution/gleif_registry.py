"""Bounded GLEIF LEI lookup. Produces claims; admission remains outside this adapter."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
import unicodedata
import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from application.organization_admission.locator import (
    AttentionLocator,
    LeiIdentifier,
    parse_locator,
)
from application.organization_admission.registry_record import RegistryAttestation, registry_record
from application.organization_admission.service import (
    RegistryIdentityRecord,
    RegistryLookup,
    RegistryLookupStatus,
)
from application.source_acquisition import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceRequest,
    SourceTargetRule,
)
from domain.identity import identity_name_key
from domain.representation import text_fingerprint
from pipeline.source_acquisition import ContentAddressedArtifactStore
from pipeline.source_acquisition.http_sensor import HttpSourceSensor

PARSER = "gleif-lei-json/1"
RIGHTS = "https://www.gleif.org/en/meta/lei-data-terms-of-use"
BASE = "https://api.gleif.org/api/v1/lei-records/"
POLICY = SourceDispatchPolicy(
    policy_id="gleif-lei-registry-v1",
    disposition=DispatchDisposition.ALLOW,
    decision_basis=f"052-T006; GLEIF LEI/LE-RD CC0-1.0; {RIGHTS}; exact LEI only",
    targets=(SourceTargetRule("api.gleif.org", "/api/v1/lei-records"),),
    timeout_ms=5000,
    max_response_bytes=262144,
    max_redirects=0,
)
#: Candidate search (spec 052 amendment, audit 2026-10-12): suggestions for a person to
#: choose from, never an admission. Same host, same CC0 rights, same shared rate limit.
SEARCH_BASE = "https://api.gleif.org/api/v1/"
SEARCH_POLICY = SourceDispatchPolicy(
    policy_id="gleif-lei-candidates-v1",
    disposition=DispatchDisposition.ALLOW,
    decision_basis=f"GLEIF LEI/LE-RD CC0-1.0; {RIGHTS}; name candidates for subscriber choice",
    targets=(
        SourceTargetRule("api.gleif.org", "/api/v1/autocompletions"),
        SourceTargetRule("api.gleif.org", "/api/v1/lei-records"),
    ),
    timeout_ms=5000,
    max_response_bytes=524288,
    max_redirects=0,
)
_LEI_VALUE = re.compile(r"[A-Z0-9]{18}[0-9]{2}")
_LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RegistryCandidate:
    """One current LEI holder a person may recognize. Not an identity decision."""

    lei: str
    legal_name: str
    country: str | None
    city: str | None

    def to_wire(self) -> dict[str, str | None]:
        return {
            "lei": self.lei,
            "legalName": self.legal_name,
            "country": self.country,
            "city": self.city,
        }


def _candidate(item: dict[str, Any], now: datetime) -> RegistryCandidate | None:
    """A record only if it is current: ACTIVE entity, ISSUED and unexpired registration."""
    lei = item.get("id")
    attributes = _object(item.get("attributes"))
    entity = _object(attributes.get("entity"))
    registration = _object(attributes.get("registration"))
    name = _object(entity.get("legalName")).get("name")
    if not isinstance(lei, str) or not _LEI_VALUE.fullmatch(lei) or not isinstance(name, str):
        return None
    if not name.strip() or len(name) > 512 or any(c in name for c in "<>"):
        return None
    if entity.get("status") != "ACTIVE" or registration.get("status") != "ISSUED":
        return None
    try:
        if _date(registration.get("nextRenewalDate")) <= now:
            return None
    except ValueError:
        return None
    address = entity.get("legalAddress")
    address = address if isinstance(address, dict) else {}
    country = address.get("country") if isinstance(address.get("country"), str) else None
    city = address.get("city") if isinstance(address.get("city"), str) else None
    return RegistryCandidate(lei, name.strip(), country, city)


class _RecordArtifacts:
    def __init__(self, artifacts: ContentAddressedArtifactStore) -> None:
        self.artifacts = artifacts

    def put_bytes(self, data: bytes) -> str:
        return self.artifacts.put_bytes(data)

    def put_json(self, value: object) -> str:
        if not isinstance(value, dict):
            raise ValueError("registry artifact must be an object")
        return self.artifacts.put_json(value)


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("non-JSON numeric constant")


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("expected object")
    return value


def _date(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("expected timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("expected timezone")
    return parsed.astimezone(UTC)


def parse_record(payload: bytes, *, lei: str, now: datetime) -> tuple[str, datetime]:
    """One exact, active, currently renewed record; no name search or website claim."""
    if not payload or len(payload) > POLICY.max_response_bytes:
        raise ValueError("invalid response size")
    envelope = _object(
        json.loads(
            payload.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_invalid_constant
        )
    )
    if "errors" in envelope:
        raise ValueError("error envelope")
    data = _object(envelope.get("data"))
    attributes = _object(data.get("attributes"))
    if data.get("type") != "lei-records" or data.get("id") != lei or attributes.get("lei") != lei:
        raise ValueError("record identifier mismatch")
    entity = _object(attributes.get("entity"))
    name = _object(entity.get("legalName")).get("name")
    if (
        not isinstance(name, str)
        or not name.strip()
        or len(name) > 512
        or any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} for c in name)
        or any(c in name for c in "<>")
        or lei in name
    ):
        raise ValueError("invalid legal name")
    registration = _object(attributes.get("registration"))
    renewal = _date(registration.get("nextRenewalDate"))
    updated = _date(registration.get("lastUpdateDate"))
    if entity.get("status") != "ACTIVE" or registration.get("status") != "ISSUED":
        raise ValueError("record not current")
    if updated > now or renewal <= now or updated >= renewal:
        raise ValueError("record dates not current")
    return name, min(now + timedelta(hours=1), renewal)


class GLEIFRegistryIdentitySource:
    """Global LEI-holder coverage, one HTTP request, no pagination or retries.

    Shared operational SQLite limits 30 attempts/minute and 500/day across workers.
    Only successful immutable responses are reusable, at most one hour and never
    beyond renewal. Failure/absence is not cached as truth.
    """

    def __init__(
        self,
        *,
        sensor: HttpSourceSensor,
        artifacts: ContentAddressedArtifactStore,
        database: Path,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.sensor, self.artifacts, self.database = sensor, artifacts, database
        self.clock = clock or (lambda: datetime.now(UTC))
        with sqlite3.connect(database) as db:
            db.execute("CREATE TABLE IF NOT EXISTS gleif_attempts (at TEXT NOT NULL)")
            db.execute(
                "CREATE TABLE IF NOT EXISTS gleif_cache (lei TEXT PRIMARY KEY, body TEXT NOT NULL, metadata TEXT NOT NULL, observed_at TEXT NOT NULL, expires_at TEXT NOT NULL, parser TEXT NOT NULL, rights TEXT NOT NULL)"
            )

    def _reserve(self, now: datetime) -> bool:
        with sqlite3.connect(self.database, timeout=5) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM gleif_cache WHERE expires_at<=?", (now.isoformat(),))
            db.execute(
                "DELETE FROM gleif_attempts WHERE at<?", ((now - timedelta(days=1)).isoformat(),)
            )
            minute = db.execute(
                "SELECT count(*) FROM gleif_attempts WHERE at>?",
                ((now - timedelta(minutes=1)).isoformat(),),
            ).fetchone()[0]
            day = db.execute("SELECT count(*) FROM gleif_attempts").fetchone()[0]
            if minute >= 30 or day >= 500:
                return False
            db.execute("INSERT INTO gleif_attempts VALUES (?)", (now.isoformat(),))
        return True

    def _record(
        self, lei: str, name: str, observed: datetime, body: str, metadata: str
    ) -> RegistryIdentityRecord:
        # Deterministic field extraction from the retained JSON; no invented website.
        legal = f"LEI {lei} legalName: {name}"
        registration = f"lei: {lei}"
        document = legal + "\n" + registration
        record = registry_record(
            document=document,
            source_ref=BASE + lei,
            observed_at=observed,
            artifacts=_RecordArtifacts(self.artifacts),
            identifier=("LEI", "GLEIF", lei),
            attestations=(
                RegistryAttestation("legal_identity", name, legal, lei, "legalName", name),
                RegistryAttestation(
                    "registration", f"LEI|GLEIF|{lei}", registration, lei, "lei", lei
                ),
            ),
        )
        requests = []
        for request in record.requests:
            representation = request.evidence.representation
            assert representation is not None
            surface = self.artifacts.put_json(
                {"text": document, "body": body, "observation": metadata, "parser": PARSER}
            )
            representation = replace(
                representation,
                source_artifact_ref=body,
                source_content_fingerprint=text_fingerprint(
                    self.artifacts.read(body).decode("utf-8")
                ),
                source_observation_artifact_ref=metadata,
                source_observation_fingerprint=metadata,
                artifact_ref=surface,
                representation_version=PARSER,
                normalization_version=PARSER,
                observation_id=f"observation:gleif:{metadata}",
            )
            claim = request.evidence.grounded_claim
            assert claim is not None
            claim = replace(
                claim, supporting_span=representation.unique_span(claim.supporting_excerpt)
            )
            requests.append(
                replace(
                    request,
                    evidence=replace(
                        request.evidence,
                        source="GLEIF Global LEI Repository",
                        representation=representation,
                        grounded_claim=claim,
                    ),
                )
            )
        return RegistryIdentityRecord(requests[0], (requests[1],))

    # ---- candidates by name (search; never an admission by itself) --------------------
    def _get_json(self, url: str, slot: str, now: datetime) -> Any:
        if not self._reserve(now):
            raise RuntimeError("LOCAL_LIMIT")
        observation = self.sensor.observe(
            SourceRequest(
                request_id="gleif-search:" + uuid.uuid4().hex,
                subject_id="registry:lei-search",
                observation_slot=slot,
                target_uri=url,
                source_type="REGISTRY_SEARCH",
                policy_id=SEARCH_POLICY.policy_id,
                policy_fingerprint=SEARCH_POLICY.fingerprint,
                policy_version=SEARCH_POLICY.policy_version,
            ),
            SEARCH_POLICY,
        )
        if observation.http_status != 200 or observation.body_artifact_ref is None:
            raise RuntimeError("SEARCH_UNAVAILABLE")
        if (observation.content_type or "").split(";", 1)[0].strip().lower() not in {
            "application/json",
            "application/vnd.api+json",
        }:
            raise RuntimeError("SEARCH_NOT_JSON")
        payload = self.artifacts.read(observation.body_artifact_ref)
        if len(payload) > SEARCH_POLICY.max_response_bytes:
            raise ValueError("invalid response size")
        return json.loads(
            payload.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_invalid_constant
        )

    def candidates(
        self, query: str, *, prefer_country: str | None = None, limit: int = 5
    ) -> tuple[RegistryCandidate, ...]:
        """Current LEI holders whose names match a query, for a person to choose from.

        Two bounded requests (GLEIF autocompletion, then those records' details) under the
        shared rate limit. Only ACTIVE entities with an ISSUED, unexpired registration are
        returned. A candidate is a suggestion: identity is admitted only from the LEI the
        subscriber then chooses, through the normal exact lookup.
        """
        text = " ".join(unicodedata.normalize("NFC", query).split())
        if len(text) < 2 or len(text) > 120:
            return ()
        now = self.clock().astimezone(UTC)
        completions = _object(
            self._get_json(
                f"{SEARCH_BASE}autocompletions?field=fulltext&q={quote(text)}",
                "registry-search",
                now,
            )
        ).get("data")
        if not isinstance(completions, list):
            raise ValueError("autocompletion data")
        leis: list[str] = []
        for item in completions[:20]:
            relation = _object(_object(_object(item).get("relationships")).get("lei-records"))
            lei = _object(relation.get("data")).get("id")
            if isinstance(lei, str) and _LEI_VALUE.fullmatch(lei) and lei not in leis:
                leis.append(lei)
        if not leis:
            return ()
        details = _object(
            self._get_json(
                f"{SEARCH_BASE}lei-records?filter[lei]={','.join(leis[:20])}&page[size]=20",
                "registry-candidates",
                now,
            )
        ).get("data")
        if not isinstance(details, list):
            raise ValueError("record data")
        found: dict[str, RegistryCandidate] = {}
        for item in details:
            candidate = _candidate(_object(item), now)
            if candidate is not None:
                found[candidate.lei] = candidate
        ranked = [found[lei] for lei in leis if lei in found]
        key = identity_name_key(text)
        ranked.sort(
            key=lambda c: (
                identity_name_key(c.legal_name) != key,
                prefer_country is not None and c.country != prefer_country.upper(),
            )
        )
        return tuple(ranked[:limit])

    def _lookup_exact_name(self, name: str) -> RegistryLookup:
        """A name alone is admitted only when it is exactly one current legal name."""
        key = identity_name_key(name)
        exact = [
            c for c in self.candidates(name, limit=20) if identity_name_key(c.legal_name) == key
        ]
        if not exact:
            return RegistryLookup(RegistryLookupStatus.NOT_FOUND)
        records: list[RegistryIdentityRecord] = []
        for candidate in exact[:2]:
            found = self.lookup(AttentionLocator(identifier=LeiIdentifier(candidate.lei)))
            if found.status is not RegistryLookupStatus.FOUND:
                return RegistryLookup(RegistryLookupStatus.UNAVAILABLE)
            records.extend(found.records)
        return RegistryLookup(RegistryLookupStatus.FOUND, tuple(records))

    def lookup(self, locator: AttentionLocator) -> RegistryLookup:
        started = time.monotonic()
        category = "NO_HTTP"
        outcome = RegistryLookup(RegistryLookupStatus.UNAVAILABLE)
        try:
            identifier = locator.identifier
            if identifier is None and locator.domain is None and locator.name:
                category = "NAME"
                outcome = self._lookup_exact_name(locator.name)
                return outcome
            if identifier is None or identifier.scheme != "LEI" or identifier.authority != "GLEIF":
                # A website alone is not covered by GLEIF: UNKNOWN, never global absence.
                # With an LEI, the record is read by its LEI; whether the website named
                # alongside it may stand is decided by admission, not by this adapter.
                return outcome
            lei = identifier.value
            if parse_locator("LEI " + lei).identifier != identifier:
                return outcome
            current = self.clock()
            if current.tzinfo is None:
                return outcome
            now = current.astimezone(UTC)
            with sqlite3.connect(self.database) as db:
                cached = db.execute(
                    "SELECT body,metadata,observed_at FROM gleif_cache WHERE lei=? AND expires_at>? AND observed_at<=? AND parser=? AND rights=?",
                    (lei, now.isoformat(), now.isoformat(), PARSER, RIGHTS),
                ).fetchone()
            if cached is not None:
                body, metadata, observed_text = cached
                provenance = _object(json.loads(self.artifacts.read(metadata)))
                if (
                    provenance.get("body"),
                    provenance.get("parser"),
                    provenance.get("rights"),
                    provenance.get("observed_at"),
                    provenance.get("resource"),
                ) != (body, PARSER, RIGHTS, observed_text, BASE + lei):
                    return outcome
                observed = _date(observed_text)
                name, _ = parse_record(self.artifacts.read(body), lei=lei, now=now)
                outcome = RegistryLookup(
                    RegistryLookupStatus.FOUND, (self._record(lei, name, observed, body, metadata),)
                )
                return outcome
            if not self._reserve(now):
                category = "LOCAL_LIMIT"
                return outcome
            observation = self.sensor.observe(
                SourceRequest(
                    request_id="gleif:" + uuid.uuid4().hex,
                    subject_id="registry:lei:" + lei,
                    observation_slot="registry-identity",
                    target_uri=BASE + lei,
                    source_type="REGISTRY_RECORD",
                    policy_id=POLICY.policy_id,
                    policy_fingerprint=POLICY.fingerprint,
                    policy_version=POLICY.policy_version,
                ),
                POLICY,
            )
            status = observation.http_status
            category = "NO_RESPONSE" if status is None else f"{status // 100}xx"
            if (observation.content_type or "").split(";", 1)[0].strip().lower() not in {
                "application/json",
                "application/vnd.api+json",
            }:
                return outcome
            if observation.final_uri != BASE + lei or len(observation.redirect_chain) != 1:
                return outcome
            if (
                status == 404
                and observation.failure_state == "http_404"
                and observation.body_artifact_ref
            ):
                error = _object(
                    json.loads(
                        self.artifacts.read(observation.body_artifact_ref).decode("utf-8"),
                        object_pairs_hook=_unique,
                        parse_constant=_invalid_constant,
                    )
                )
                errors = error.get("errors")
                if (
                    "data" not in error
                    and isinstance(errors, list)
                    and len(errors) == 1
                    and _object(errors[0]).get("status") == "404"
                ):
                    outcome = RegistryLookup(RegistryLookupStatus.NOT_FOUND)
                return outcome
            if observation.failure_state or status != 200 or observation.body_artifact_ref is None:
                return outcome
            body = observation.body_artifact_ref
            if observation.body_fingerprint != "sha256:" + self.artifacts.digest(body):
                return outcome
            observed = observation.retrieved_at
            if observed > now + timedelta(seconds=POLICY.timeout_ms / 1000 + 1) or observed < now:
                return outcome
            name, expires = parse_record(self.artifacts.read(body), lei=lei, now=observed)
            metadata = self.artifacts.put_json(
                {
                    "provider": "GLEIF",
                    "authority": "REGISTRY",
                    "resource": BASE + lei,
                    "query_identifier": lei,
                    "observed_at": observed.isoformat(),
                    "body": body,
                    "http_observation": observation.raw_observation_ref,
                    "parser": PARSER,
                    "license": "CC0-1.0",
                    "rights": RIGHTS,
                    "expires_at": expires.isoformat(),
                }
            )
            record = self._record(lei, name, observed, body, metadata)
            with sqlite3.connect(self.database) as db:
                db.execute(
                    "INSERT OR REPLACE INTO gleif_cache VALUES (?,?,?,?,?,?,?)",
                    (
                        lei,
                        body,
                        metadata,
                        observed.isoformat(),
                        expires.isoformat(),
                        PARSER,
                        RIGHTS,
                    ),
                )
            outcome = RegistryLookup(RegistryLookupStatus.FOUND, (record,))
            return outcome
        except (
            ValueError,
            TypeError,
            KeyError,
            OSError,
            RuntimeError,
            sqlite3.Error,
            RecursionError,
        ):
            return outcome
        finally:
            _LOG.info(
                "registry_lookup provider=GLEIF lookup_type=LEI outcome=%s latency_ms=%s http_category=%s records=%s parser=%s",
                outcome.status.value,
                round((time.monotonic() - started) * 1000),
                category,
                len(outcome.records),
                PARSER,
            )
