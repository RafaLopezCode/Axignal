"""World query cache: one source query per day pays once, every Focus reuses it.

Wraps a live source adapter with the autonomous runtime's findings ledger (the same
records T12 replays). A complete, same-day retrieval whose query covers the new one is
replayed through the source's own criteria; otherwise the live adapter is called and
its complete result recorded. Public procurement records only; never tenant context.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from application.observation_intelligence.contracts import SourceDescriptor
from application.observation_intelligence.findings import SourceFindings
from application.observation_intelligence.loop import SourceObservationPort
from application.observation_intelligence.strategy import ObservationAction
from application.observation_runtime.replay import (
    FindingsLedger,
    RecordedFindings,
    covers,
    matches,
)


class SharedFindingsPort:
    def __init__(
        self,
        live: SourceObservationPort,
        ledger: FindingsLedger,
        *,
        clock: Callable[[], datetime],
        fresh_for: timedelta = timedelta(hours=24),
    ) -> None:
        self._live = live
        self._ledger = ledger
        self._clock = clock
        self._fresh_for = fresh_for
        self.hits = 0
        self.live_requests = 0

    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings:
        now = self._clock()
        recorded = [
            item
            for item in self._ledger.recorded_findings(source.source_id)
            if item.complete
            and covers(item.query, action.query)
            and now - item.findings.retrieved_at <= self._fresh_for
        ]
        if recorded:
            latest = max(recorded, key=lambda item: item.findings.retrieved_at)
            self.hits += 1
            return SourceFindings(
                source_id=source.source_id,
                retrieved_at=latest.findings.retrieved_at,  # never fresher than observed
                requests=0,
                amount_microunits=0,
                latency_ms=0,
                records=tuple(r for r in latest.findings.records if matches(r, action.query)),
                total_available=None,
                failure=None,
            )
        findings = self._live.observe(action, source)
        self.live_requests += findings.requests
        # Only real retrievals are recorded: an index answer (0 requests) is not a source
        # response with the source's own matching semantics.
        if findings.failure is None and findings.requests > 0:
            self._ledger.record_findings(RecordedFindings(source.source_id, action.query, findings))
        return findings
