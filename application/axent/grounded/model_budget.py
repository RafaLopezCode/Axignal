"""One bounded model attempt, with durable reservation and redacted audit."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from application.axent.grounded.answer import GroundedReasoner, ReasoningRequest, ReasoningResult
from application.axent.grounded.cost import CostRates, turn_cost


class ModelAudit(Protocol):
    def reserve(
        self,
        request: ReasoningRequest,
        *,
        now: datetime,
        provider: str,
        model: str,
        ceiling: Decimal,
    ) -> str | None: ...

    def result(self, ref: str, result: ReasoningResult, *, cost: Decimal | None) -> None: ...

    def verified(self, ref: str, *, route: str, dropped: int) -> None: ...


@dataclass
class BudgetedReasoner:
    inner: GroundedReasoner
    audit: ModelAudit
    clock: Callable[[], datetime]
    rates: CostRates
    maximum_cost: Decimal
    provider: str
    max_input_tokens: int = 16000
    max_output_tokens: int = 500
    max_prompt_bytes: int = 8000

    @property
    def model(self) -> str:
        return self.inner.model

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        began = time.monotonic()

        def unavailable(error: str, *, calls: int = 0) -> ReasoningResult:
            return ReasoningResult(
                {},
                self.model,
                None,
                None,
                int((time.monotonic() - began) * 1000),
                self.provider,
                error,
                model_calls=calls,
            )

        # UTF-8 bytes bound ordinary text tokenization; schema/envelope gets 4096 tokens.
        size = len(
            (request.system + request.user + json.dumps(dict(request.schema))).encode("utf-8")
        )
        ceiling = turn_cost(self.max_input_tokens, request.max_output_tokens, self.rates)
        if (
            not request.tenant_ref
            or not request.focus_ref
            or size > self.max_prompt_bytes
            or size + 4096 > self.max_input_tokens
            or not 0 < request.max_output_tokens <= self.max_output_tokens
            or not self.maximum_cost.is_finite()
            or ceiling > self.maximum_cost
        ):
            return unavailable("BUDGET_BLOCKED")
        ref = self.audit.reserve(
            request, now=self.clock(), provider=self.provider, model=self.model, ceiling=ceiling
        )
        if ref is None:
            return unavailable("RATE_LIMITED")
        try:
            result = self.inner.reason(request)
        except Exception as error:
            result = unavailable(type(error).__name__, calls=1)
        cost = None
        input_tokens, output_tokens = result.input_tokens, result.output_tokens
        if input_tokens is None or output_tokens is None:
            result = replace(result, payload={}, error_class=result.error_class or "USAGE_UNKNOWN")
        elif (
            not 0 <= input_tokens <= self.max_input_tokens
            or not 0 <= output_tokens <= request.max_output_tokens
        ):
            result = replace(result, payload={}, error_class="USAGE_LIMIT_VIOLATION")
        else:
            cost = turn_cost(input_tokens, output_tokens, self.rates)
        result = replace(result, audit_ref=ref, provider=self.provider)
        self.audit.result(ref, result, cost=cost)
        return result
