"""One AXENT turn: authorize → corpus → resolve → retrieve → route → verify → answer.

The authorization boundary is the subscriber read: it re-checks principal,
membership, tenant and Xeed before any evidence exists for this turn, so
retrieval can only ever see that tenant's authorized reading. Python answers
whatever it can answer exactly; the model only synthesizes verified claims
over a bounded pack; abstention and research requests are first-class.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from application.axent.grounded.answer import (
    ANSWER_SCHEMA,
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    AnswerRoute,
    Claim,
    GroundedAnswer,
    GroundedReasoner,
    ReasoningRequest,
    ResearchRequest,
    ResearchRequestSink,
    build_user_message,
    evidence_refs,
    is_deterministic,
    pack_refs,
    request_id,
    verify,
)
from application.axent.grounded.copy import family_name, gap_text, text
from application.axent.grounded.corpus import (
    AuthorizedCorpus,
    EvidenceItem,
    EvidenceKind,
    corpus_from_reading,
    fold,
)
from application.axent.grounded.intent import (
    ConversationMemory,
    QuestionKind,
    ResolvedQuestion,
    resolve,
)
from application.axent.grounded.model_budget import ModelAudit
from application.axent.grounded.retrieval import (
    ContextBudget,
    Retrieval,
    estimate_tokens,
    in_scope,
    render_item,
    retrieve,
)
from application.observation_runtime.families import ObservationFamily
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId


class AuthorizedReading(Protocol):
    @property
    def projection(self) -> dict[str, object]: ...


class AuthorizedReadingPort(Protocol):
    """The subscriber read: membership, tenant and Xeed are checked inside it."""

    def read(
        self, authorized_context: TrustedRequestContext, xeed_id: XeedId, as_of: datetime
    ) -> AuthorizedReading: ...


class FamilyCoveragePort(Protocol):
    """Why a family is UNKNOWN for this (already authorized) Xeed, if known."""

    def coverage(
        self, xeed_id: str, as_of: datetime
    ) -> tuple[tuple[ObservationFamily, str, str], ...]: ...


@dataclass(frozen=True, slots=True)
class TurnMetrics:
    route: AnswerRoute
    model_calls: int
    input_tokens: int
    output_tokens: int
    #: True when the token counts were reported by the provider, not estimated.
    measured: bool
    corpus_items: int
    in_scope_items: int
    sent_items: int
    excluded: tuple[tuple[str, int], ...]
    evidence_tokens: int
    latency_ms: int
    cache_hit: bool
    claims: int
    dropped_claims: int


@dataclass(frozen=True, slots=True)
class AxentTurn:
    answer: GroundedAnswer
    memory: ConversationMemory
    metrics: TurnMetrics
    organization_id: str
    kind: QuestionKind


class AnswerCache:
    """Process-local LRU. Keys carry tenant, Xeed and the evidence fingerprint."""

    def __init__(self, capacity: int = 512) -> None:
        self._items: OrderedDict[str, GroundedAnswer] = OrderedDict()
        self._capacity = capacity

    def get(self, key: str) -> GroundedAnswer | None:
        item = self._items.get(key)
        if item is not None:
            self._items.move_to_end(key)
        return item

    def put(self, key: str, value: GroundedAnswer) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        while len(self._items) > self._capacity:
            self._items.popitem(last=False)

    def __len__(self) -> int:
        return len(self._items)


def cache_key(
    corpus: AuthorizedCorpus, question: ResolvedQuestion, *, locale: str, model: str
) -> str:
    """Same tenant, Xeed, evidence (incl. currentness and cut), question and model."""
    return request_id(
        corpus.tenant_id,
        corpus.xeed_id,
        corpus.fingerprint,
        question.kind.value,
        ",".join(f.value for f in question.families),
        ",".join(question.geographies),
        " ".join(fold(question.text).split()),
        locale,
        model,
        PROMPT_VERSION,
    )


@dataclass
class AxentService:
    reader: AuthorizedReadingPort
    clock: Callable[[], datetime]
    reasoner: GroundedReasoner | None = None
    coverage: FamilyCoveragePort | None = None
    research: ResearchRequestSink | None = None
    budget: ContextBudget = field(default_factory=ContextBudget)
    cache: AnswerCache = field(default_factory=AnswerCache)
    max_output_tokens: int = 500
    model_audit: ModelAudit | None = None

    def ask(
        self,
        context: TrustedRequestContext,
        focus_id: XeedId,
        question: str,
        *,
        memory: object = None,
        locale: str = "es",
    ) -> AxentTurn:
        started = time.monotonic()
        if not question.strip() or len(question) > 1000:
            raise ValueError("an AXENT question must be 1..1000 characters")
        now = self.clock()
        # Authorization first: nothing exists for this turn until the read succeeds.
        reading = self.reader.read(context, focus_id, now)
        corpus = corpus_from_reading(
            tenant_id=str(context.tenant_id),
            projection=reading.projection,
            as_of=now,
            coverage=() if self.coverage is None else self.coverage.coverage(str(focus_id), now),
        )
        if corpus.xeed_id != str(focus_id):
            raise PermissionError("the authorized reading does not belong to the requested focus")
        # Memory may hint intent; it never carries scope or evidence.
        prior = ConversationMemory.from_wire(memory, focus_id=str(focus_id))
        resolved = resolve(question, prior)
        retrieval = retrieve(corpus, resolved, self.budget)
        refs = pack_refs(retrieval.selected)
        evidence = [i for i in retrieval.selected if i.kind is not EvidenceKind.GAP]

        input_tokens = output_tokens = model_calls = dropped = 0
        measured = cache_hit = False
        model_name: str | None = None
        research: ResearchRequest | None = None
        claims: tuple[Claim, ...] = ()
        unknowns = tuple(
            dict.fromkeys(
                gap_text(i.item_id, i.limits[0] if i.limits else "", locale) or i.text
                for i in retrieval.selected
                if i.kind is EvidenceKind.GAP
            )
        )

        foreign = tuple(
            name for name in resolved.named
            if fold(name) not in fold(corpus.organization_name) and not any(
                fold(name) in fold(" ".join((i.text, *i.limits))) for i in corpus.items
            )
        )  # fmt: skip
        if foreign:
            # The question is about something this tenant's evidence never mentions (maybe
            # another organization): no evidence, no inference, and no research on a third party.
            route = AnswerRoute.ABSTAINED
            evidence, refs = [], {}
            unknowns = ()
            summary = text(
                "abstain_subject", locale, org=corpus.organization_name, subject=", ".join(foreign)
            )
        elif not evidence and resolved.kind is QuestionKind.UNKNOWNS and unknowns:
            route = AnswerRoute.DETERMINISTIC
            summary = text("unknowns", locale)
        elif not evidence:
            route = AnswerRoute.ABSTAINED
            research = self._research(corpus, resolved, retrieval, now, "NO_AUTHORIZED_EVIDENCE")
            summary = text("abstain", locale, org=corpus.organization_name)
        elif is_deterministic(resolved):
            route = AnswerRoute.DETERMINISTIC
            summary, claims, unknowns = self._deterministic(
                corpus, resolved, refs, unknowns, locale
            )
        else:
            key = cache_key(
                corpus, resolved, locale=locale, model=self.reasoner.model if self.reasoner else "-"
            )
            cached = self.cache.get(key) if self.reasoner is not None else None
            if cached is not None:
                route, summary, claims, unknowns = (
                    cached.route,
                    cached.answer,
                    cached.claims,
                    cached.unknowns,
                )
                model_name, cache_hit = cached.model, True
            elif self.reasoner is None:
                route, summary = AnswerRoute.EXTRACTIVE, text("extractive", locale)
            else:
                lines = [render_item(ref, item) for ref, item in refs.items()]
                user = build_user_message(
                    organization_name=corpus.organization_name,
                    as_of=now,
                    question=resolved,
                    lines=lines,
                    locale=locale,
                    in_scope=retrieval.in_scope,
                )
                result = self.reasoner.reason(
                    ReasoningRequest(
                        request_id=key,
                        system=SYSTEM_PROMPT,
                        user=user,
                        schema=ANSWER_SCHEMA,
                        max_output_tokens=self.max_output_tokens,
                        tenant_ref=request_id("tenant", corpus.tenant_id),
                        focus_ref=request_id("focus", corpus.tenant_id, corpus.xeed_id),
                    )
                )
                model_calls, model_name = result.model_calls, result.model
                measured = result.input_tokens is not None
                input_tokens = result.input_tokens or estimate_tokens(SYSTEM_PROMPT + user)
                output_tokens = result.output_tokens or 0
                claims, model_unknowns, insufficient, dropped = verify(
                    {} if result.error_class else result.payload, refs
                )
                unknowns = tuple(dict.fromkeys((*model_unknowns, *unknowns)))
                if claims:
                    route = AnswerRoute.MODEL
                    summary = " ".join(c.text for c in claims)
                    if insufficient:
                        research = self._research(
                            corpus, resolved, retrieval, now, "MODEL_FOUND_EVIDENCE_INSUFFICIENT"
                        )
                elif insufficient:
                    route = AnswerRoute.ABSTAINED
                    summary = text("abstain", locale, org=corpus.organization_name)
                    research = self._research(
                        corpus, resolved, retrieval, now, "MODEL_FOUND_EVIDENCE_INSUFFICIENT"
                    )
                else:
                    route, summary = AnswerRoute.EXTRACTIVE, text("extractive", locale)
                if self.model_audit is not None and result.audit_ref is not None:
                    self.model_audit.verified(result.audit_ref, route=route.value, dropped=dropped)
            if route is AnswerRoute.MODEL and not cache_hit:
                self.cache.put(
                    key,
                    GroundedAnswer(
                        summary,
                        route,
                        corpus.tenant_id,
                        corpus.xeed_id,
                        now,
                        claims,
                        unknowns,
                        (),
                        model=model_name,
                    ),
                )
        if evidence and all(i.currentness != "CURRENT" for i in evidence) and research is None:
            research = self._research(corpus, resolved, retrieval, now, "EVIDENCE_NOT_CURRENT")
            unknowns = (*unknowns, text("stale", locale))
        if research is not None:
            scope = self._scope_label(resolved, locale)
            summary = f"{summary} {text('research', locale, scope=scope)}"

        cited = {r for c in claims for r in c.refs}
        shown = {
            ref: item
            for ref, item in refs.items()
            if ref in cited or route is not AnswerRoute.MODEL
        }
        answer = GroundedAnswer(
            answer=summary,
            route=route,
            tenant_id=corpus.tenant_id,
            xeed_id=corpus.xeed_id,
            as_of=now,
            claims=claims,
            unknowns=unknowns,
            evidence=evidence_refs(shown),
            research=research,
            dropped_claims=dropped,
            model=model_name,
            families=tuple(f.value for f in resolved.families),
        )
        next_memory = ConversationMemory(
            focus_id=str(focus_id),
            family=resolved.families[0]
            if len(resolved.families) == 1
            else (prior.family if prior else None),
            geographies=resolved.geographies,
            previous_refs=tuple(refs[r].item_id for r in sorted(cited))[
                : self.budget.max_memory_refs
            ],
            turn=(prior.turn if prior else 0) + 1,
        )
        metrics = TurnMetrics(
            route=route,
            model_calls=model_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            measured=measured,
            corpus_items=retrieval.considered,
            in_scope_items=retrieval.in_scope,
            sent_items=len(refs) if model_calls else 0,
            excluded=retrieval.excluded,
            evidence_tokens=retrieval.evidence_tokens,
            latency_ms=int((time.monotonic() - started) * 1000),
            cache_hit=cache_hit,
            claims=len(claims),
            dropped_claims=dropped,
        )
        return AxentTurn(answer, next_memory, metrics, corpus.organization_id, resolved.kind)

    def _deterministic(
        self,
        corpus: AuthorizedCorpus,
        question: ResolvedQuestion,
        refs: Mapping[str, EvidenceItem],
        unknowns: tuple[str, ...],
        locale: str,
    ) -> tuple[str, tuple[Claim, ...], tuple[str, ...]]:
        packed = {item.item_id: ref for ref, item in refs.items()}
        if question.kind is QuestionKind.COUNT:
            # Exact over the whole authorized scope, not just what fits in a pack.
            scoped = [
                i for i in corpus.items if in_scope(i, question) and i.kind is not EvidenceKind.GAP
            ]
            opportunities = [i for i in scoped if i.kind is EvidenceKind.OPPORTUNITY]
            where = (
                text("where", locale, geo=", ".join(question.geographies))
                if question.geographies
                else ""
            )
            if not question.families or ObservationFamily.DEMAND in question.families:
                summary = text("count", locale, n=len(opportunities), where=where)
                items = opportunities
            else:
                summary = text(
                    "count_items", locale, n=len(scoped), scope=self._scope_label(question, locale)
                )
                items = scoped
            cited = tuple(packed[i.item_id] for i in items if i.item_id in packed)
            claims: tuple[Claim, ...] = (
                (
                    Claim(
                        summary,
                        cited,
                        "POTENTIAL" if items is opportunities else "OBSERVED",
                        "CURRENT",
                    ),
                )
                if cited
                else ()
            )
            return summary, claims, unknowns
        if question.kind is QuestionKind.UNKNOWNS:
            limits = tuple(dict.fromkeys(limit for i in refs.values() for limit in i.limits))
            all_unknowns = tuple(dict.fromkeys((*unknowns, *limits)))
            return text("unknowns", locale), (), all_unknowns
        observed = tuple(
            Claim(
                text(
                    "observed",
                    locale,
                    label=item.text.split(";")[0],
                    when=item.observed_at.date().isoformat()
                    if item.observed_at
                    else text("unknown_date", locale),
                ),
                (ref,),
                item.epistemic,
                item.currentness,
            )
            for ref, item in refs.items()
            if item.kind is not EvidenceKind.GAP
        )
        return text("sources", locale), observed, unknowns

    def _scope_label(self, question: ResolvedQuestion, locale: str) -> str:
        families = ", ".join(family_name(f, locale) for f in question.families) or family_name(
            ObservationFamily.ORGANIZATION, locale
        )
        return (
            f"{families} ({', '.join(question.geographies)})" if question.geographies else families
        )

    def _research(
        self,
        corpus: AuthorizedCorpus,
        question: ResolvedQuestion,
        retrieval: Retrieval,
        now: datetime,
        reason: str,
    ) -> ResearchRequest:
        family = question.families[0] if question.families else None
        item = ResearchRequest(
            request_id=request_id(
                corpus.tenant_id,
                corpus.xeed_id,
                corpus.organization_id,
                family.value if family else "-",
                ",".join(question.geographies),
                question.kind.value,
                corpus.dependency_fingerprint,
            ),
            tenant_id=corpus.tenant_id,
            xeed_id=corpus.xeed_id,
            family=family,
            geographies=question.geographies,
            reason=reason,
            question_kind=question.kind.value,
            created_at=now,
            organization_id=corpus.organization_id,
            dependency_fingerprint=corpus.dependency_fingerprint,
        )
        if self.research is not None:
            self.research.request(item)
        return item
