"""Single retry and DLQ policy for subscriber billing reconciliation.

The inline checkout reconciliation and the durable worker must sentence
attempts identically: diverging thresholds or delays would let one path
dead-letter an attempt the other still retries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

MAXIMUM_ATTEMPTS_BOUND = 20


@dataclass(frozen=True, slots=True)
class ReconciliationRetryPolicy:
    maximum_attempts: int = 8
    base_delay: timedelta = timedelta(seconds=60)
    maximum_delay: timedelta = timedelta(hours=6)
    exponential_cap: int = 10
    unknown_outcome_delay: timedelta = timedelta(seconds=300)

    def __post_init__(self) -> None:
        if not 1 <= self.maximum_attempts <= MAXIMUM_ATTEMPTS_BOUND:
            raise ValueError(f"maximum attempts must be between 1 and {MAXIMUM_ATTEMPTS_BOUND}")

    def is_dead(self, attempt_count: int) -> bool:
        return attempt_count >= self.maximum_attempts

    def failure_delay(self, attempt_count: int) -> timedelta:
        exponent: int = min(attempt_count, self.exponential_cap)
        delay = self.base_delay * (2**exponent)
        return delay if delay < self.maximum_delay else self.maximum_delay


RECONCILIATION_RETRY_POLICY = ReconciliationRetryPolicy()
