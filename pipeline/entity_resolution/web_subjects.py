"""Web-anchored subjects (ADR-0087 amendment 2026-10-16): attention, never legal identity.

An organization a subscriber wants observed whose legal identity no registry can resolve is
anchored to its public website: ``org:web:<sha256(domain)>``. This operational store holds only
the domain, the locator first given and when it was anchored. It is not the canonical
Organization store and never AXIGLAND; nothing here is a FAXT. Two Tenants observing the same
domain share one subject, as they share a canonical Organization.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from domain.identity import WEB_SUBJECT_PREFIX, OrganizationId, is_web_subject
from domain.organizations.model import Organization


def web_subject_id(domain: str) -> OrganizationId:
    key = domain.strip().lower().removeprefix("www.")
    return OrganizationId(WEB_SUBJECT_PREFIX + hashlib.sha256(key.encode("utf-8")).hexdigest())


class SqliteWebSubjectStore:
    def __init__(self, path: Path, *, read_only: bool = False) -> None:
        self.path, self._read_only = path, read_only
        if not read_only:
            path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as db:
                db.execute(
                    """CREATE TABLE IF NOT EXISTS web_subjects (
                        organization_id TEXT PRIMARY KEY,
                        domain TEXT NOT NULL UNIQUE,
                        locator TEXT NOT NULL,
                        anchored_at TEXT NOT NULL
                    )"""
                )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        uri = f"file:{self.path.as_posix()}{'?mode=ro' if self._read_only else ''}"
        connection = sqlite3.connect(uri, uri=True, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _readable(self) -> bool:
        return not self._read_only or self.path.is_file()

    def ensure(self, domain: str, locator: str, now: datetime) -> Organization:
        """The subject for this domain, anchored now if it was not (idempotent)."""
        if self._read_only:
            raise PermissionError("web subject store is read-only")
        key = domain.strip().lower().removeprefix("www.")
        organization_id = web_subject_id(key)
        with self._connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO web_subjects VALUES (?,?,?,?)",
                (organization_id, key, locator[:2048], now.isoformat()),
            )
        return Organization(id=organization_id, canonical_name=key)

    def domain_of(self, organization_id: str) -> str | None:
        if not is_web_subject(organization_id) or not self._readable():
            return None
        with self._connect() as db:
            row = db.execute(
                "SELECT domain FROM web_subjects WHERE organization_id = ?", (organization_id,)
            ).fetchone()
        return None if row is None else str(row[0])

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        domain = self.domain_of(organization_id)
        return None if domain is None else Organization(id=organization_id, canonical_name=domain)

    def organization_by_domain(self, domain: str) -> OrganizationId | None:
        if not self._readable():
            return None
        key = domain.strip().lower().removeprefix("www.")
        with self._connect() as db:
            row = db.execute(
                "SELECT organization_id FROM web_subjects WHERE domain = ?", (key,)
            ).fetchone()
        return None if row is None else OrganizationId(str(row[0]))


class CanonicalOrWebSubjects:
    """Reads a Focus's organization: canonical Organizations from the canonical store,
    web-anchored subjects from theirs. Every other canonical operation is the canonical
    store's own (a web subject can never be admitted, bound or written there)."""

    def __init__(self, canonical: Any, subjects: SqliteWebSubjectStore) -> None:
        self._canonical, self._subjects = canonical, subjects

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        if is_web_subject(organization_id):
            return self._subjects.get_organization(organization_id)
        result: Organization | None = self._canonical.get_organization(organization_id)
        return result

    def websites_for(self, organization_id: OrganizationId) -> tuple[str, ...]:
        if is_web_subject(organization_id):
            domain = self._subjects.domain_of(organization_id)
            return () if domain is None else (domain,)
        result: tuple[str, ...] = self._canonical.websites_for(organization_id)
        return result

    def organization_by_domain(self, domain: str) -> OrganizationId | None:
        # A registry-attested website always wins over a web anchor of the same domain.
        canonical: OrganizationId | None = self._canonical.organization_by_domain(domain)
        return canonical if canonical is not None else self._subjects.organization_by_domain(domain)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._canonical, name)
