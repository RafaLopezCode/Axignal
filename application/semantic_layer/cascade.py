"""The cascade: Python → System One → (only if it matters) reasoning → Python.

1. Exact memory first: a judgment already made on the same world state is reused.
2. One System One call per batch answers every remaining question (fan-out), inside
   the token budget. Over budget, the questions abstain: UNKNOWN, never a guess.
3. Answers that stay uncertain and are declared escalable go to the reasoning model,
   one call per batch, while its call budget lasts.
4. Python receives typed, traced resolutions and decides what they may change.

A provider failure becomes FAILED for that batch only; the rest of the run continues.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.contracts import (
    JudgmentSource,
    ReasoningEscalationPort,
    SemanticAnswer,
    SemanticBatch,
    SemanticJudgeError,
    SemanticJudgePort,
)
from application.semantic_layer.ledger import CostLedger, SemanticBudget
from application.semantic_layer.memory import JudgmentMemoryPort, memory_key

#: Jev 1.13 limits (official models page): state + all questions ≤ 64k tokens;
#: state + the longest question ≤ 32k. Accuracy degrades with large, noisy state, so
#: callers must filter state first; the cascade refuses rather than truncating.
MAX_BATCH_TOKENS = 60_000
MAX_STATE_TOKENS = 30_000


class Resolution(StrEnum):
    DECIDED = "DECIDED"
    UNCERTAIN = "UNCERTAIN"
    ESCALATED = "ESCALATED"
    ABSTAINED_BUDGET = "ABSTAINED_BUDGET"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class CascadePolicy:
    """When a System One answer counts as decided, and which questions may escalate.

    Thresholds are policy to be evaluated on AXIGNAL's own labelled data; they are not
    canonical (MASTER: no probability threshold is canonical)."""

    min_confidence: float = 0.6
    noul_uncertain_band: tuple[float, float] = (0.3, 0.7)
    escalable: frozenset[str] = frozenset()

    def uncertain(self, answer: SemanticAnswer) -> bool:
        if answer.primitive is SemanticPrimitive.NOUL:
            p = answer.probability("true")
            low, high = self.noul_uncertain_band
            return p is None or low < p < high
        return answer.confidence is None or answer.confidence < self.min_confidence


@dataclass(frozen=True, slots=True)
class ResolvedJudgment:
    question_id: str
    resolution: Resolution
    answer: SemanticAnswer | None = None
    from_memory: bool = False
    reason: str | None = None

    @property
    def usable(self) -> bool:
        return self.resolution in {Resolution.DECIDED, Resolution.ESCALATED}

    def to_wire(self) -> dict[str, object]:
        return {
            "questionId": self.question_id,
            "resolution": self.resolution.value,
            "fromMemory": self.from_memory,
            "reason": self.reason,
            "answer": None if self.answer is None else self.answer.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CascadeOutcome:
    batch_id: str
    state_fingerprint: str
    judgments: dict[str, ResolvedJudgment] = field(default_factory=dict)

    def judgment(self, question_id: str) -> ResolvedJudgment:
        return self.judgments[question_id]


@dataclass(slots=True)
class SemanticCascade:
    judge: SemanticJudgePort
    ledger: CostLedger
    budget: SemanticBudget
    policy: CascadePolicy = CascadePolicy()
    memory: JudgmentMemoryPort | None = None
    escalation: ReasoningEscalationPort | None = None

    def run(self, batches: Sequence[SemanticBatch], *, now: datetime) -> dict[str, CascadeOutcome]:
        """Resolve ``batches`` in the given order (callers put the most valuable first)."""
        outcomes: dict[str, CascadeOutcome] = {}
        for batch in batches:
            outcomes[batch.batch_id] = self._one(batch, now)
        return outcomes

    def _remember(self, batch: SemanticBatch, answer: SemanticAnswer, now: datetime) -> None:
        if self.memory is not None:
            key = memory_key(
                batch.state_fingerprint,
                batch.question(answer.question_id),
                answer.evaluator,
                answer.model,
            )
            self.memory.put(key, answer, recorded_at=now)

    def _recall(self, batch: SemanticBatch, question_id: str) -> SemanticAnswer | None:
        if self.memory is None:
            return None
        question = batch.question(question_id)
        for evaluator, model in (
            (self.judge.name, self.judge.model),
            *(
                ((self.escalation.name, self.escalation.model),)
                if self.escalation is not None
                else ()
            ),
        ):
            hit = self.memory.get(memory_key(batch.state_fingerprint, question, evaluator, model))
            if hit is not None:
                return hit
        return None

    def _one(self, batch: SemanticBatch, now: datetime) -> CascadeOutcome:
        judged: dict[str, ResolvedJudgment] = {}
        missing: list[str] = []
        for question in batch.questions:
            hit = self._recall(batch, question.question_id)
            if hit is None:
                missing.append(question.question_id)
                continue
            self.ledger.memory_hits += 1
            if hit.source is JudgmentSource.REASONING:
                resolution = Resolution.ESCALATED
            elif self.policy.uncertain(hit):
                resolution = Resolution.UNCERTAIN
            else:
                resolution = Resolution.DECIDED
            judged[question.question_id] = ResolvedJudgment(
                question.question_id, resolution, hit, from_memory=True
            )
        if missing:
            judged.update(self._system_one(batch.only(tuple(missing)), now))
        uncertain = tuple(
            qid
            for qid, item in judged.items()
            if item.resolution is Resolution.UNCERTAIN and qid in self.policy.escalable
        )
        if uncertain:
            judged.update(self._escalate(batch.only(uncertain), now))
        ordered = {q.question_id: judged[q.question_id] for q in batch.questions}
        return CascadeOutcome(batch.batch_id, batch.state_fingerprint, ordered)

    def _system_one(self, batch: SemanticBatch, now: datetime) -> dict[str, ResolvedJudgment]:
        estimate = batch.estimated_input_tokens()
        state_only = SemanticBatch(batch.batch_id, batch.state, batch.questions[:1])
        if estimate > MAX_BATCH_TOKENS or state_only.estimated_input_tokens() > MAX_STATE_TOKENS:
            return {
                q.question_id: ResolvedJudgment(
                    q.question_id, Resolution.FAILED, reason="STATE_TOO_LARGE_FILTER_FIRST"
                )
                for q in batch.questions
            }
        spent = self.ledger.system_one_tokens(self.judge.name)
        if spent + estimate > self.budget.max_system_one_input_tokens:
            return {
                q.question_id: ResolvedJudgment(
                    q.question_id, Resolution.ABSTAINED_BUDGET, reason="SYSTEM_ONE_BUDGET"
                )
                for q in batch.questions
            }
        try:
            result = self.judge.judge(batch)
        except SemanticJudgeError as error:
            return {
                q.question_id: ResolvedJudgment(
                    q.question_id, Resolution.FAILED, reason=error.category
                )
                for q in batch.questions
            }
        self.ledger.record(result)
        answers = {answer.question_id: answer for answer in result.answers}
        resolved: dict[str, ResolvedJudgment] = {}
        for question in batch.questions:
            answer = answers.get(question.question_id)
            if answer is None or set(label for label, _ in answer.distribution) - set(
                question.labels
            ):
                resolved[question.question_id] = ResolvedJudgment(
                    question.question_id, Resolution.FAILED, reason="ANSWER_OUTSIDE_CONTRACT"
                )
                continue
            self._remember(batch, answer, now)
            resolved[question.question_id] = ResolvedJudgment(
                question.question_id,
                Resolution.UNCERTAIN if self.policy.uncertain(answer) else Resolution.DECIDED,
                answer,
            )
        return resolved

    def _escalate(self, batch: SemanticBatch, now: datetime) -> dict[str, ResolvedJudgment]:
        if self.escalation is None:
            return {}
        if self.ledger.reasoning_calls(self.escalation.name) >= self.budget.max_reasoning_calls:
            return {}
        try:
            result = self.escalation.decide(batch)
        except SemanticJudgeError:
            return {}
        self.ledger.record(result)
        resolved: dict[str, ResolvedJudgment] = {}
        for answer in result.answers:
            question = batch.question(answer.question_id)
            if answer.top not in question.labels:
                continue
            self._remember(batch, answer, now)
            resolved[answer.question_id] = ResolvedJudgment(
                answer.question_id, Resolution.ESCALATED, answer
            )
        return resolved
