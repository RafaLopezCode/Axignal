"""Bounded retry worker for durable subscriber billing reconciliation."""

from __future__ import annotations

from datetime import datetime

from application.admin_billing.retry_policy import ReconciliationRetryPolicy
from application.admin_billing.subscriber_reconciliation import (
    SubscriberPurchaseReconciler,
)
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore


class SubscriberReconciliationWorker:
    def __init__(
        self,
        *,
        store: SqliteSubscriberBillingStore,
        reconciler: SubscriberPurchaseReconciler,
        maximum_attempts: int = 8,
    ) -> None:
        if type(maximum_attempts) is not int or not 1 <= maximum_attempts <= 20:
            raise ValueError("maximum attempts must be between 1 and 20")
        self._store = store
        self._reconciler = reconciler
        self._retry_policy = ReconciliationRetryPolicy(maximum_attempts=maximum_attempts)

    def run_due(self, *, now: datetime, limit: int = 20) -> tuple[str, ...]:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("worker clock must be timezone-aware")
        completed: list[str] = []
        for retry in self._store.pending_retries(now, limit=limit):
            operation_ref = str(retry["operation_ref"])
            safe_refs = retry["safe_refs"]
            if not isinstance(safe_refs, dict):
                continue
            stored_count = retry.get("attempt_count")
            if type(stored_count) is not int or stored_count < 0:
                continue
            intent_ref = safe_refs.get("intent_ref")
            attempt = (
                self._store.get_attempt_by_intent(intent_ref)
                if isinstance(intent_ref, str)
                else None
            )
            if attempt is None:
                self._store.enqueue_retry(
                    operation_ref=operation_ref,
                    next_attempt_at=None,
                    attempt_count=stored_count,
                    disposition="DLQ",
                    failure_code="ATTEMPT_NOT_FOUND",
                    safe_refs={"intent_ref": str(intent_ref or "")[:200]},
                )
                continue
            count = stored_count + 1
            try:
                result = self._reconciler.reconcile_attempt(
                    attempt.tenant_id, attempt.request_ref, now=now
                )
            except Exception as exc:
                dead = self._retry_policy.is_dead(count)
                self._store.enqueue_retry(
                    operation_ref=operation_ref,
                    next_attempt_at=None if dead else now + self._retry_policy.failure_delay(count),
                    attempt_count=count,
                    disposition="DLQ" if dead else "RETRY",
                    failure_code=type(exc).__name__[:80],
                    safe_refs={
                        "tenant_ref": str(attempt.tenant_id),
                        "intent_ref": attempt.intent_ref,
                    },
                )
                continue
            if result.value == "COMPLETE":
                self._store.enqueue_retry(
                    operation_ref=operation_ref,
                    next_attempt_at=None,
                    attempt_count=count,
                    disposition="COMPLETE",
                    failure_code="NONE",
                    safe_refs={
                        "tenant_ref": str(attempt.tenant_id),
                        "intent_ref": attempt.intent_ref,
                    },
                )
                completed.append(attempt.intent_ref)
            elif result.value in {"UNKNOWN", "MISMATCH"}:
                dead = self._retry_policy.is_dead(count)
                self._store.enqueue_retry(
                    operation_ref=operation_ref,
                    next_attempt_at=None
                    if dead
                    else now + self._retry_policy.unknown_outcome_delay,
                    attempt_count=count,
                    disposition="DLQ" if dead else "RETRY",
                    failure_code=result.value,
                    safe_refs={
                        "tenant_ref": str(attempt.tenant_id),
                        "intent_ref": attempt.intent_ref,
                    },
                )
        return tuple(completed)
