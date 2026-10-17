"""A specific activity routes demand before a section reading does (self-check 2026-10-17).

Found on novonordisk.com: the schema.org reading "Manufacturing" (isic-C) routed all of
CPV division 33, so a pharmaceutical maker was offered cardiac-ablation devices and
anaesthesia equipment beside its own pharmaceutical calls.
"""

from __future__ import annotations

from datetime import UTC, datetime

from application.first_observation.activity import (
    ActivityFinding,
    ActivityMethod,
    prefer_specific_routing,
)
from application.observation_intelligence.contracts import TaxonomyCode

NOW = datetime(2026, 10, 17, tzinfo=UTC)


def _finding(activity: str, *codes: str) -> ActivityFinding:
    return ActivityFinding(activity_id=activity, label=activity, method=ActivityMethod.LEXICON,
                           page_url="https://x.example/", excerpt="x", observed_at=NOW,
                           demand_codes=tuple(TaxonomyCode("CPV", c) for c in codes))  # fmt: skip


def test_a_section_yields_its_broad_routing_to_a_specific_activity() -> None:
    pharma, section = _finding("pharmaceuticals", "33600000"), _finding("isic-C", "33000000")
    kept = {f.activity_id: f for f in prefer_specific_routing([pharma, section])}
    assert kept["pharmaceuticals"].demand_codes == pharma.demand_codes
    assert kept["isic-C"].demand_codes == ()  # still a reading, no longer a route


def test_a_section_alone_still_routes() -> None:
    # Unknown is never narrowed to nothing: without a specific activity the section routes.
    (section,) = prefer_specific_routing([_finding("isic-C", "33000000")])
    assert section.demand_codes
    unrouted = _finding("pharmaceuticals")
    assert prefer_specific_routing([unrouted, _finding("isic-C", "33000000")])[1].demand_codes
