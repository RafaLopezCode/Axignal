"""Minute 0 (CTO, 2026-10-17): a fresh observation queues its background readings at once.

Baseline on 14 real agencies: reputation 1/14, economics 0/14, context 0/14 at the first
reading, because AI visibility, press, boards, sector and regulation were only requested
when someone read the view, then measured on the background loop's next turn.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.first_observation.harness import SOLAR_ES, World, build, runtime
from tests.integration.test_organization_admission_e2e import _add, _pilot


class GeoSpy:
    def __init__(self) -> None:
        self.requested: list[Any] = []

    def measurement(self, subject: Any) -> None:
        return None

    def request(self, subject: Any) -> None:
        self.requested.append(subject)

    def run(self) -> int:
        return 0


def test_a_fresh_observation_queues_ai_visibility_without_waiting_for_a_read(
    tmp_path: Path,
) -> None:
    facade = build(tmp_path, World())
    rt = runtime(facade)
    spy = GeoSpy()
    rt._geo = spy
    token, _tenant = _pilot(facade, tmp_path, "subject:minute-zero")
    added = _add(facade, token, "add:minute-zero", SOLAR_ES)
    assert added.status == 200
    assert rt.drain() == 1
    # Nobody has read the view yet: the observation itself queued the measurement.
    assert len(spy.requested) == 1
    subject = spy.requested[0]
    assert subject.name  # a Focus added by its website alone still has a name to ask about
    assert rt._wake.is_set()
    # Wikidata/Wikipedia (economics, organization), job boards and buyers run on the source
    # thread: it is woken too, instead of waiting up to ten minutes.
    assert rt._sources_wake.is_set()
