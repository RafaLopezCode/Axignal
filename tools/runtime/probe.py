"""Durable persistence probe using production Observation/Learning adapters.

The probe always uses a dedicated probe directory. It never writes business or
subscriber data into the runtime's live memories.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.economic_discovery.observation_memory import GovernedObservation
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory


def run_probe(*, probe_dir: Path, code_sha: str) -> dict[str, object]:
    code_sha = code_sha.strip()
    if not code_sha or code_sha == "UNKNOWN":
        raise ValueError("runtime persistence probe requires an exact code SHA")
    probe_dir = probe_dir.expanduser().resolve()
    probe_dir.mkdir(parents=True, exist_ok=True)
    # Stable sentinel time makes the SHA-scoped probe payload replay-idempotent.
    # Runtime execution time is intentionally not persisted as economic evidence.
    now = datetime(2000, 1, 1, tzinfo=UTC)
    short_sha = code_sha[:16]
    subject_id = f"runtime-probe:{short_sha}"
    observation_id = f"obs:runtime-probe:{short_sha}"
    event_id = f"learn:runtime-probe:{short_sha}"

    observation = GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id=subject_id,
            source_ref="urn:axignal:runtime-persistence-probe",
            source_type="RUNTIME_PROBE",
            observed_at=now,
            content_fingerprint=f"sha256:runtime-probe:{short_sha}",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content="AXIGNAL isolated runtime persistence probe",
        fields=(),
    )
    learning = LearningEvent(
        event_id=event_id,
        kind=LearningEventKind.BOOTSTRAP,
        outcome=LearningOutcome.COMPLETED,
        occurred_at=now,
        subject_id=subject_id,
        xeed_id=None,
        activity_ref=f"runtime-probe:{short_sha}",
        policy_id="runtime-persistence-probe",
        policy_version="1",
        code_sha=code_sha,
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint=f"runtime-probe-input:{short_sha}",
        output_fingerprint=f"runtime-probe-output:{short_sha}",
        reason_code="PRODUCTION_PERSISTENCE_PROBE",
        before_state_fingerprint=f"runtime-probe-state-before:{short_sha}",
        after_state_fingerprint=f"runtime-probe-state-after:{short_sha}",
        replay=LearningReplayReference.non_replayable(
            "ISOLATED_RUNTIME_PROBE",
            code_sha=code_sha,
        ),
        cost=LearningCost(),
        yield_=LearningYield(state_fields_changed=1),
    )

    observation_db = probe_dir / "observation-memory.sqlite3"
    learning_db = probe_dir / "learning-memory.sqlite3"
    first_observation = SqliteObservationMemory(observation_db).append(observation)
    first_learning = SqliteLearningMemory(learning_db).append(learning)

    observation_reopened = SqliteObservationMemory(observation_db).for_subject(subject_id)
    learning_reopened = SqliteLearningMemory(learning_db).get(event_id)
    if observation_reopened != (observation,):
        raise RuntimeError("observation persistence probe failed after reopen")
    if learning_reopened != learning:
        raise RuntimeError("learning persistence probe failed after reopen")

    return {
        "status": "ok",
        "code_sha": code_sha,
        "probe_scope": "isolated-non-business-data",
        "observation_append": "created" if first_observation else "idempotent-replay",
        "learning_append": "created" if first_learning else "idempotent-replay",
        "observation_reopen": "ok",
        "learning_reopen": "ok",
    }


def main() -> None:
    raw_dir = os.getenv("AXIGNAL_PROBE_DIR", "").strip()
    code_sha = os.getenv("AXIGNAL_CODE_SHA", "").strip()
    if not raw_dir:
        raise SystemExit("AXIGNAL_PROBE_DIR is required")
    payload = run_probe(probe_dir=Path(raw_dir), code_sha=code_sha)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
