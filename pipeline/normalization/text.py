"""Deterministic text normalization helpers.

Doctrine: MASTER §14.
"""

from __future__ import annotations

import re

from domain.identity import identity_name_key

_WHITESPACE = re.compile(r"\s+")


def normalize_whitespace(value: str) -> str:
    """Collapse runs of whitespace and strip the ends."""

    return _WHITESPACE.sub(" ", value).strip()


def normalize_name(value: str) -> str:
    """Normalize an exact identity key without discarding accents or scripts."""
    return identity_name_key(value)
