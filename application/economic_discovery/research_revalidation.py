"""Production research revalidation against temporal Prime authority."""

from __future__ import annotations

from datetime import datetime

from application.economic_discovery.continuous_observation import (
    ObservationWorkState,
    SharedObservationWork,
    SharedObservationWorkMemory,
)
from application.economic_discovery.observation_memory import ObservationMemory


class PrimeCurrentnessResearchRevalidator:
    """Fail closed unless the latest temporal Prime authority still owns the work."""

    def __init__(
        self,
        *,
        observation_memory: ObservationMemory,
        research_memory: SharedObservationWorkMemory,
    ) -> None:
        self._observations = observation_memory
        self._research = research_memory

    def may_run(self, work: SharedObservationWork, *, now: datetime) -> bool:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("research revalidation time must be timezone-aware")
        if work.state is not ObservationWorkState.PENDING:
            return False

        intent = work.intent
        authority = self._research.prime_authority(intent.subject_id)
        if authority is None:
            return False
        if authority.state_fingerprint != intent.state_fingerprint:
            return False
        if intent.work_key not in authority.authorized_work_keys:
            return False
        if now >= authority.valid_until:
            return False

        observations = self._observations.for_subject(intent.subject_id)
        if not observations:
            return False
        latest = max(
            observations,
            key=lambda item: (
                item.record.observed_at,
                item.record.observation_id,
            ),
        )
        latest_watermark = (
            latest.record.observed_at,
            latest.record.observation_id,
        )
        authority_watermark = (
            authority.observation_watermark_at,
            authority.observation_watermark_id,
        )
        return latest_watermark <= authority_watermark
