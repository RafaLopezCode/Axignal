"""Deterministic text normalization helpers.

Doctrine: MASTER §14.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^0-9a-z]+")


def normalize_whitespace(value: str) -> str:
    """Collapse runs of whitespace and strip the ends."""

    return _WHITESPACE.sub(" ", value).strip()


def normalize_name(value: str) -> str:
    """Canonicalize a name for deterministic matching.

    Accent-fold, casefold, remove punctuation and collapse whitespace.
    """

    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(char for char in decomposed if not unicodedata.combining(char))
    folded = ascii_only.casefold()
    tokenized = _NON_ALNUM.sub(" ", folded)
    return normalize_whitespace(tokenized)
