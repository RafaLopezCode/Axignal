"""SQLite authority for Principal-owned UI preferences."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from application.subscriber_profile.service import Profile, ProfileConflict
from domain.identity import PrincipalId


class SqliteProfileStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS principal_ui_profile (principal TEXT PRIMARY KEY, version INTEGER NOT NULL, locale TEXT, avatar BLOB)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _profile(row: sqlite3.Row | None) -> Profile:
        return (
            Profile() if row is None else Profile(int(row["version"]), row["locale"], row["avatar"])
        )

    def read(self, principal: PrincipalId) -> Profile:
        with self._connect() as db:
            return self._profile(
                db.execute(
                    "SELECT * FROM principal_ui_profile WHERE principal=?", (principal,)
                ).fetchone()
            )

    def write(
        self,
        principal: PrincipalId,
        expected: int,
        *,
        locale: str | None = None,
        avatar: bytes | None = None,
        field: str,
    ) -> Profile:
        if field not in {"locale", "avatar"}:
            raise ValueError("invalid preference")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = self._profile(
                db.execute(
                    "SELECT * FROM principal_ui_profile WHERE principal=?", (principal,)
                ).fetchone()
            )
            if current.version != expected:
                raise ProfileConflict("profile changed")
            updated = Profile(
                expected + 1,
                locale if field == "locale" else current.locale,
                avatar if field == "avatar" else current.avatar,
            )
            db.execute(
                "INSERT INTO principal_ui_profile VALUES (?,?,?,?) ON CONFLICT(principal) DO UPDATE SET version=excluded.version, locale=excluded.locale, avatar=excluded.avatar",
                (principal, updated.version, updated.locale, updated.avatar),
            )
            return updated
