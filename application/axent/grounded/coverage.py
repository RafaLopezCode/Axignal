"""Why a family is UNKNOWN, read from the autonomous observation runtime's own state.

Called only after the subscriber read authorized the Xeed; the runtime state is
keyed by that same Xeed, so nothing outside the authorized scope is read.
"""

from __future__ import annotations

from datetime import datetime

from application.observation_runtime.digest import observation_digest
from application.observation_runtime.families import ObservationFamily
from application.observation_runtime.ports import ObservationRuntimeStore


def reason_code(blocked: str) -> str:
    """Runtime routing reason → the small vocabulary AXENT can explain to a person."""
    for code in ("NO_KNOWN_SOURCE", "NO_ADOPTED_SOURCE", "NO_ADAPTER"):
        if blocked.startswith(code):
            return code
    if "CAPABILITY_CONTEXT" in blocked:
        return "NO_CONTEXT"
    return "NOT_OBSERVED"


class RuntimeFamilyCoverage:
    def __init__(self, store: ObservationRuntimeStore) -> None:
        self._store = store

    def coverage(
        self, xeed_id: str, as_of: datetime
    ) -> tuple[tuple[ObservationFamily, str, str], ...]:
        digest = observation_digest(self._store, xeed_id, as_of=as_of)
        return tuple(
            (
                ObservationFamily(reading.family),
                reading.currentness,
                reason_code(reading.unknown_because[0]),
            )
            for reading in digest.families
            if reading.currentness == "UNKNOWN" and reading.unknown_because
        )
