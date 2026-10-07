"""Private operator preparation for pilot testing, never subscriber access."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class PilotAccountsConflict(ValueError):
    """Preparation changed since the operator loaded it."""


@dataclass(frozen=True, slots=True)
class PilotAccounts:
    a: str = ""
    b: str = ""
    revision: int = 0
    saved_by: str | None = None
    saved_at: datetime | None = None

    @property
    def authorized_for_test(self) -> bool:
        return bool(self.a and self.b)


class PilotAccountsStore(Protocol):
    def read(self) -> PilotAccounts: ...

    def append(self, accounts: PilotAccounts, *, expected_revision: int) -> PilotAccounts: ...


def save_pilot_accounts(
    store: PilotAccountsStore,
    *,
    a: str,
    b: str,
    expected_revision: int,
    actor: str,
    now: datetime,
) -> PilotAccounts:
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("invalid preparation revision")
    if not actor.strip() or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("current operator and time required")
    values = []
    for value in (a, b):
        if not isinstance(value, str):
            raise ValueError("account address must be text")
        value = value.strip()
        if value and (
            len(value) > 254
            or not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", value)
            or any(ord(char) < 32 for char in value)
        ):
            raise ValueError("invalid account address")
        values.append(value)
    if values[0] and values[0].casefold() == values[1].casefold():
        raise ValueError("test accounts must be distinct")
    return store.append(
        PilotAccounts(values[0], values[1], expected_revision + 1, actor, now),
        expected_revision=expected_revision,
    )
