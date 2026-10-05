"""Internal attention inventory in FR-30's existing read-model database.

Catalog bindings reference already-canonical identity authority. Submitted names
and URLs cannot create that authority, organization business facts or source rights.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from domain.identity import OrganizationId
from domain.organizations.model import Organization
from pipeline.entity_resolution.resolver import (
    ExactNameResolver,
    ResolutionCandidate,
    ResolutionStatus,
)
from tools.runtime.first_proof import FirstProofInsufficientEvidence, FirstProofService


def attention_target(uri: str) -> str:
    parsed = urlsplit(uri.strip())
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.port not in (None, 443)
        or parsed.path not in ("", "/")
        or "." not in host
        or host.endswith((".localhost", ".local", ".internal"))
    ):
        raise ValueError("PUBLIC_HTTPS_ORGANIZATION_ROOT_REQUIRED")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("PUBLIC_HOSTNAME_REQUIRED")
    return f"https://{host}/"


@dataclass(frozen=True)
class CanonicalObservationTarget:
    organization: Organization
    target_uri: str
    identity_authority_ref: str

    def __post_init__(self) -> None:
        if attention_target(self.target_uri) != self.target_uri:
            raise ValueError("catalog target must be normalized")
        if not self.identity_authority_ref.strip():
            raise ValueError("catalog requires existing canonical identity authority")


def load_observation_catalog(
    path: Path | None, host: str
) -> tuple[CanonicalObservationTarget, ...]:
    targets = [
        CanonicalObservationTarget(
            Organization(OrganizationId("org:axignal"), "AXIGNAL"),
            attention_target(f"https://{host}/"),
            "legacy-fr30:org:axignal",
        )
    ]
    if path is not None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("canonical source catalog must be a list")
        for item in raw:
            if not isinstance(item, dict) or set(item) != {
                "organizationId",
                "canonicalName",
                "targetUri",
                "identityAuthorityRef",
            }:
                raise ValueError("invalid canonical source binding")
            if not all(isinstance(value, str) and value.strip() for value in item.values()):
                raise ValueError("catalog values must be non-empty strings")
            targets.append(
                CanonicalObservationTarget(
                    Organization(OrganizationId(item["organizationId"]), item["canonicalName"]),
                    attention_target(item["targetUri"]),
                    item["identityAuthorityRef"],
                )
            )
    if len({item.organization.id for item in targets}) != len(targets):
        raise ValueError("duplicate canonical organization catalog binding")
    if len({item.target_uri for item in targets}) != len(targets):
        raise ValueError("duplicate catalog source binding")
    return tuple(targets)


class OrganizationAttention:
    """One existing internal tenant; per-principal reading selection, no billing.

    No commercial tenant authority is inferred from an Admin/browser role.
    The HTTP composition supplies an already-verified Admin authorization grant.
    """

    def __init__(
        self, proof: FirstProofService, catalog: tuple[CanonicalObservationTarget, ...]
    ) -> None:
        self.proof = proof
        self.catalog = catalog
        self._lock = threading.RLock()
        self._resolver = ExactNameResolver(
            ResolutionCandidate(str(t.organization.id), t.organization.canonical_name)
            for t in catalog
        )
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS organization_attention_attempts (
              sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL,
              requested_name TEXT NOT NULL, target_uri TEXT NOT NULL, state TEXT NOT NULL,
              organization_id TEXT, projection_id TEXT, occurred_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS organization_attention_selection (
              principal_id TEXT PRIMARY KEY, attention_id TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS organization_attention_leases (
              attention_id TEXT PRIMARY KEY, lease_token TEXT NOT NULL,
              operation_key TEXT NOT NULL, acquired_at TEXT NOT NULL,
              expires_at TEXT NOT NULL)""")
        # Adopt accepted legacy FR-30 self-observation only. General runs must have
        # an explicit inventory record and cannot become a global default.
        prior = proof.store.latest()
        organization = None if prior is None else prior.get("organization")
        if (
            prior is not None
            and isinstance(organization, dict)
            and organization.get("id") == "org:axignal"
            and not any(item["organizationId"] == "org:axignal" for item in self._entries())
        ):
            target = next(t for t in catalog if t.organization.id == "org:axignal")
            context = prior.get("context")
            if isinstance(context, dict):
                self._append(
                    self._id(target.target_uri),
                    "AXIGNAL",
                    target.target_uri,
                    "LIVE",
                    target,
                    str(context["id"]),
                )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.proof.store.path)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _id(target: str) -> str:
        return "attention:" + hashlib.sha256(target.encode()).hexdigest()[:24]

    def _claim_lease(self, identifier: str, operation_key: str) -> str | None:
        now = self.proof.clock()
        if now.tzinfo is None:
            raise ValueError("attention lease clock must be timezone-aware")
        expires_at = now + timedelta(seconds=60)
        token = f"lease:{uuid.uuid4().hex}"
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT lease_token, expires_at FROM organization_attention_leases "
                "WHERE attention_id=?",
                (identifier,),
            ).fetchone()
            if row is not None:
                existing_expires = datetime.fromisoformat(str(row["expires_at"]))
                if existing_expires > now:
                    return None
                db.execute(
                    "DELETE FROM organization_attention_leases WHERE attention_id=?",
                    (identifier,),
                )
            db.execute(
                """INSERT INTO organization_attention_leases
                (attention_id,lease_token,operation_key,acquired_at,expires_at)
                VALUES (?,?,?,?,?)""",
                (
                    identifier,
                    token,
                    operation_key,
                    now.isoformat(),
                    expires_at.isoformat(),
                ),
            )
        return token

    def _release_lease(self, identifier: str, token: str) -> None:
        with self._connect() as db:
            db.execute(
                "DELETE FROM organization_attention_leases WHERE attention_id=? AND lease_token=?",
                (identifier, token),
            )

    def _owns_lease(self, identifier: str, token: str) -> bool:
        now = self.proof.clock()
        if now.tzinfo is None:
            raise ValueError("attention lease clock must be timezone-aware")
        with self._connect() as db:
            row = db.execute(
                "SELECT lease_token, expires_at FROM organization_attention_leases "
                "WHERE attention_id=?",
                (identifier,),
            ).fetchone()
        return (
            row is not None
            and str(row["lease_token"]) == token
            and datetime.fromisoformat(str(row["expires_at"])) > now
        )

    def _active_lease_ids(self) -> frozenset[str]:
        now = self.proof.clock()
        if now.tzinfo is None:
            raise ValueError("attention lease clock must be timezone-aware")
        with self._connect() as db:
            rows = db.execute(
                "SELECT attention_id, expires_at FROM organization_attention_leases"
            ).fetchall()
        return frozenset(
            str(row["attention_id"])
            for row in rows
            if datetime.fromisoformat(str(row["expires_at"])) > now
        )

    def _append(
        self,
        identifier: str,
        name: str,
        target: str,
        state: str,
        canonical: CanonicalObservationTarget | None = None,
        context: str | None = None,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO organization_attention_attempts
              (id,requested_name,target_uri,state,organization_id,projection_id,occurred_at)
              VALUES (?,?,?,?,?,?,?)""",
                (
                    identifier,
                    name,
                    target,
                    state,
                    None if canonical is None else str(canonical.organization.id),
                    context,
                    self.proof.clock().isoformat(),
                ),
            )

    def _entries(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("""SELECT * FROM organization_attention_attempts WHERE sequence IN
              (SELECT MAX(sequence) FROM organization_attention_attempts GROUP BY id) ORDER BY sequence""").fetchall()
        active_leases = self._active_lease_ids()
        by_id = {str(t.organization.id): t for t in self.catalog}
        entries = []
        for row in rows:
            canonical = by_id.get(row["organization_id"])
            state = row["state"]
            if row["organization_id"] is not None and (
                canonical is None or canonical.target_uri != row["target_uri"]
            ):
                state = "AUTHORIZATION_REVOKED"
            if state == "PLANTING" and row["id"] not in active_leases:
                state = "RUN_INTERRUPTED"  # only an unleased run is interrupted
            entries.append(
                {
                    "id": row["id"],
                    "requestedLabel": row["requested_name"],
                    "name": None if canonical is None else canonical.organization.canonical_name,
                    "organizationId": row["organization_id"],
                    "targetUri": row["target_uri"],
                    "state": state,
                    "projectionContextId": row["projection_id"],
                }
            )
        return entries

    def selected(self, principal: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT attention_id FROM organization_attention_selection WHERE principal_id=?",
                (principal,),
            ).fetchone()
        entries = self._entries()
        if row is not None:
            return next((e for e in entries if e["id"] == row[0]), None)
        return next(
            (e for e in entries if e["organizationId"] == "org:axignal" and e["state"] == "LIVE"),
            None,
        )

    def inventory(self, principal: str, *, can_observe: bool) -> dict[str, object]:
        with self._lock:
            selected = self.selected(principal)
            return {
                "accessMode": "INTERNAL_ADMIN",
                "canObserve": can_observe,
                "selectedId": None if selected is None else selected["id"],
                "organizations": self._entries(),
                "available": [
                    {"name": t.organization.canonical_name, "targetUri": t.target_uri}
                    for t in self.catalog
                ],
            }

    def projection(self, principal: str) -> dict[str, object] | None:
        selected = self.selected(principal)
        if selected is None or selected["state"] == "AUTHORIZATION_REVOKED":
            return None
        context = selected["projectionContextId"]
        return None if context is None else self.proof.current_projection(xeed_id=context)

    def select(self, principal: str, identifier: str) -> dict[str, object]:
        with self._lock:
            entry = next((e for e in self._entries() if e["id"] == identifier), None)
            if (
                entry is None
                or entry["state"] == "AUTHORIZATION_REVOKED"
                or entry["projectionContextId"] is None
            ):
                raise ValueError("FOCUS_NOT_AVAILABLE")
            projection = self.proof.current_projection(xeed_id=entry["projectionContextId"])
            if projection is None:
                raise ValueError("FOCUS_NOT_AVAILABLE")
            with self._connect() as db:
                db.execute(
                    "INSERT INTO organization_attention_selection VALUES (?,?) ON CONFLICT(principal_id) DO UPDATE SET attention_id=excluded.attention_id",
                    (principal, identifier),
                )
            return projection

    def add(
        self, principal: str, name: str, uri: str, *, reobserve: bool = False
    ) -> dict[str, object]:
        name = name.strip()
        if not name or len(name) > 200 or len(uri) > 2048:
            raise ValueError("INVALID_ATTENTION_REQUEST")
        target = attention_target(uri)
        identifier = self._id(target)

        with self._lock:
            existing = next((e for e in self._entries() if e["id"] == identifier), None)
            result = self._resolver.resolve_identity(name)
            canonical = next(
                (
                    t
                    for t in self.catalog
                    if t.target_uri == target
                    and result.status is ResolutionStatus.RESOLVED
                    and result.candidate is not None
                    and str(t.organization.id) == result.candidate.organization_id
                ),
                None,
            )
            if canonical is None:
                if existing and existing["projectionContextId"]:
                    raise ValueError("IDENTITY_MISMATCH")
                self._append(identifier, name, target, "IDENTITY_UNRESOLVED")
                return {"state": "IDENTITY_UNRESOLVED", "attentionId": identifier}
            if not reobserve and existing and existing["projectionContextId"]:
                return self.select(principal, identifier)

            old_context = None if existing is None else existing["projectionContextId"]
            operation_key = "reobserve" if reobserve else "observe"
            lease_token = self._claim_lease(identifier, operation_key)
            if lease_token is None:
                if existing and existing["projectionContextId"]:
                    projection = self.proof.current_projection(
                        xeed_id=existing["projectionContextId"]
                    )
                    if projection is not None:
                        return projection
                return {"state": "PLANTING", "attentionId": identifier}

            self._append(identifier, name, target, "PLANTING", canonical, old_context)

        try:
            projection = self.proof.observe_resolved(
                label=f"Observation of {canonical.organization.canonical_name}",
                target_uri=target,
                organization=canonical.organization,
            )
        except FirstProofInsufficientEvidence:
            with self._lock:
                self._append(
                    identifier, name, target, "INSUFFICIENT_EVIDENCE", canonical, old_context
                )
            raise
        except Exception:
            with self._lock:
                self._append(identifier, name, target, "RUNTIME_FAILURE", canonical, old_context)
            raise
        else:
            context = projection.get("context")
            assert isinstance(context, dict)
            with self._lock:
                if not self._owns_lease(identifier, lease_token):
                    raise ValueError("RUN_LEASE_LOST")
                self._append(identifier, name, target, "LIVE", canonical, str(context["id"]))
            return self.select(principal, identifier)
        finally:
            self._release_lease(identifier, lease_token)

    def reobserve(self, principal: str, identifier: str) -> dict[str, object]:
        entry = next((e for e in self._entries() if e["id"] == identifier), None)
        if entry is None or entry["state"] == "AUTHORIZATION_REVOKED":
            raise ValueError("FOCUS_NOT_AVAILABLE")
        return self.add(
            principal, entry["name"] or entry["requestedLabel"], entry["targetUri"], reobserve=True
        )

    def record_legacy(self, principal: str, projection: dict[str, object]) -> None:
        target = next(t for t in self.catalog if t.organization.id == "org:axignal")
        context = projection.get("context")
        if not isinstance(context, dict):
            raise ValueError("INVALID_RUNTIME_CONTEXT")
        identifier = self._id(target.target_uri)
        self._append(identifier, "AXIGNAL", target.target_uri, "LIVE", target, str(context["id"]))
        self.select(principal, identifier)
