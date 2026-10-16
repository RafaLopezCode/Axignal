"""Mentioning is not offering: the lexicon's trap corpus (flywheel, 2026-10-16).

A shop selling worm-humus fertiliser was read as a solar installer from "huerto urbano,
autoconsumo y jardinería", and offered photovoltaic tenders. Every false activity found is
added to the fixture as a trap; real offers must keep being read.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.observation_intelligence.understanding import detect_capabilities

CORPUS = json.loads(
    (Path(__file__).parent / "fixtures" / "lexicon_traps.json").read_text(encoding="utf-8")
)


def _read(sentence: str) -> list[str]:
    found = detect_capabilities(text=sentence, observation_id="trap", source_ref="https://x.example/",
                                observed_at=datetime(2026, 10, 16, tzinfo=UTC))  # fmt: skip
    return [h.capability_id for h in found]


@pytest.mark.parametrize(("origin", "sentence"), CORPUS["traps"])
def test_a_mention_establishes_no_activity(origin: str, sentence: str) -> None:
    assert _read(sentence) == [], origin


@pytest.mark.parametrize(("capability", "sentence"), CORPUS["offers"])
def test_a_real_offer_is_still_read(capability: str, sentence: str) -> None:
    assert capability in _read(sentence)
