"""Canonical terminology is documented and not corrupted in source."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TERMINOLOGY = REPO_ROOT / "docs/architecture/TERMINOLOGY.md"

CANONICAL_TERMS = ["AXIGNAL", "AXIGLAND", "AXENT", "XIGNAL", "FAXT", "INXIGHT", "PATHX"]
FORBIDDEN_IDENTIFIERS = ["EconomicPath", "CompanyProfile", "ClaimedCompany"]


def test_terminology_document_defines_every_canonical_term() -> None:
    body = TERMINOLOGY.read_text(encoding="utf-8")
    missing = [term for term in CANONICAL_TERMS if term not in body]
    assert missing == []


def test_source_layers_do_not_use_forbidden_identifiers() -> None:
    offenders: list[str] = []
    for layer in ("domain", "pipeline", "cognition"):
        for path in (REPO_ROOT / layer).rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for identifier in FORBIDDEN_IDENTIFIERS:
                if re.search(rf"\b{identifier}\b", source):
                    offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}: {identifier}")
    assert offenders == []
