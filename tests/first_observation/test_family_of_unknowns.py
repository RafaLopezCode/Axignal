"""Every grounded unknown the service emits belongs to a family (spec 093).

Found by the census of real readings (2026-10-17): LOCATION_NOT_DECLARED belonged to none,
so a family summary could not say Markets had a known gap.
"""

from __future__ import annotations

import re
from pathlib import Path

from application.first_observation.families import BY_UNKNOWN_CODE, family_of

ROOT = Path(__file__).resolve().parents[2]


def test_location_not_declared_is_a_markets_unknown() -> None:
    unknown = {"kind": "SIGNIFICANT_UNKNOWN", "code": "LOCATION_NOT_DECLARED"}
    assert family_of(unknown) == "markets"


def test_every_unknown_code_the_service_emits_has_a_family() -> None:
    source = (ROOT / "application" / "first_observation" / "service.py").read_text(encoding="utf-8")
    emitted = set(re.findall(r'unknown\(\s*"([A-Z_]+)"', source))
    assert emitted, "the service names its grounded unknowns"
    assert emitted <= set(BY_UNKNOWN_CODE), sorted(emitted - set(BY_UNKNOWN_CODE))


def test_the_web_places_the_same_unknowns() -> None:
    web = (ROOT / "apps" / "web" / "experience" / "lib" / "observation-families.ts").read_text(
        encoding="utf-8"
    )
    block = web[web.index("const BY_UNKNOWN_CODE") :]
    block = block[block.index("{") :]
    block = block[: block.index("};")]
    assert set(re.findall(r"\b([A-Z_]{4,}):", block)) == set(BY_UNKNOWN_CODE)
