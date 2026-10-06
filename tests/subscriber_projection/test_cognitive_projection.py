from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import GovernedObservation
from application.subscriber_projection.cognitive_projection import observation_cognition
from domain.evidence.epistemics import Currentness


def test_cognitive_source_keeps_provenance_time_and_unknown_instrument() -> None:
    now = datetime(2026, 10, 6, tzinfo=UTC)
    observation = GovernedObservation(
        ObservationRecord(
            "obs:1",
            "org:1",
            "https://example.org/",
            "OFFICIAL_WEB",
            now,
            "sha256:one",
            ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_artifact_ref="artifact:one",
    )
    payload = observation_cognition(
        ((observation, Currentness.STALE),), as_of=now, signals=(("signal:1", "presence"),)
    )
    assert payload["signals"] == [{"id": "signal:1", "familyId": "presence"}]
    sources = payload["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert source["currentness"] == "STALE"
    assert source["provenanceRef"] == "artifact:one"
    assert source["sourceRef"] == "https://example.org/"
    assert source["currentnessEvaluatedAt"] == now.isoformat()
    assert source["instrument"].startswith("UNKNOWN")
    assert (
        observation_cognition(((observation, Currentness.CURRENT),), as_of=now - timedelta(days=1))[
            "sources"
        ]
        == []
    )


def test_raw_text_alone_does_not_invent_provenance_or_a_family() -> None:
    now = datetime(2026, 10, 6, tzinfo=UTC)
    observation = GovernedObservation(
        ObservationRecord(
            "obs:1",
            "org:1",
            "https://example.org/",
            "OFFICIAL_WEB",
            now,
            "sha256:one",
            ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content="Actual raw text",
    )
    payload = observation_cognition(((observation, Currentness.UNKNOWN),), as_of=now)
    assert payload["sources"] == []
    assert payload["signals"] == []
    assert payload["opportunities"] == []
    with pytest.raises(ValueError, match="explicit accepted family"):
        observation_cognition((), as_of=now, signals=(("signal:1", "invented"),))
    with pytest.raises(ValueError, match="timezone-aware"):
        observation_cognition((), as_of=now.replace(tzinfo=None))
