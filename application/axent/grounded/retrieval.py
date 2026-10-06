"""Governed retrieval over one authorized corpus, then budgeted packing.

Order of work: structural narrowing (family) → geography → temporal cut →
lexical relevance → dedup → packing by explicit priority until the token
budget is spent. Gaps (explicit UNKNOWNs) for the requested scope are always
packed when room remains, so the answer cannot over-assert by omission.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from application.axent.grounded.corpus import AuthorizedCorpus, EvidenceItem, EvidenceKind, terms
from application.axent.grounded.intent import QuestionKind, ResolvedQuestion

_CURRENT_RANK = {"CURRENT": 0, "STALE": 1, "HISTORICAL": 2, "UNKNOWN": 3}


@dataclass(frozen=True, slots=True)
class ContextBudget:
    """Explicit ceilings; nothing grows the prompt by accident."""

    max_items: int = 8
    max_items_per_family: int = 5
    max_changes: int = 3
    max_gaps: int = 3
    max_evidence_tokens: int = 700
    max_memory_refs: int = 6

    def __post_init__(self) -> None:
        if min(self.max_items, self.max_items_per_family, self.max_evidence_tokens) < 1:
            raise ValueError("context budget limits must be positive")


def estimate_tokens(text: str) -> int:
    """Conservative estimate (~4 characters per token); live calls report the real count."""
    return max(1, math.ceil(len(text) / 4))


def render_item(ref: str, item: EvidenceItem) -> str:
    """One compact evidence line; the text is quoted data, never instructions."""
    when = "" if item.observed_at is None else item.observed_at.date().isoformat()
    source = item.source_label or (item.source_ref or "")
    limits = "" if not item.limits else " limits=" + " | ".join(item.limits)
    flag = " untrusted_text=true" if item.untrusted_instructions else ""
    return (
        f"{ref} {item.kind.value} {item.epistemic} {item.currentness} {when} "
        f'"{item.text}" src="{source[:90]}"{limits}{flag}'
    )


@dataclass(frozen=True, slots=True)
class Retrieval:
    selected: tuple[EvidenceItem, ...]
    considered: int
    in_scope: int
    excluded: tuple[tuple[str, int], ...] = field(default=())
    evidence_tokens: int = 0


def in_scope(item: EvidenceItem, question: ResolvedQuestion) -> bool:
    if question.families and not (item.families & set(question.families)):
        return False
    if question.geographies and item.kind is not EvidenceKind.GAP:
        if not item.geographies:
            # Unlocated evidence cannot answer a located question (it would over-assert).
            return (
                item.kind in {EvidenceKind.CAPABILITY, EvidenceKind.OBSERVATION}
                and question.kind is QuestionKind.HOW_KNOWN
            )
        return any(
            geo == wanted or geo.startswith(wanted + "/")
            for geo in item.geographies
            for wanted in question.geographies
        )
    return True


def _priority(
    item: EvidenceItem, question: ResolvedQuestion, query: frozenset[str]
) -> tuple[object, ...]:
    overlap = len(query & item.terms)
    direct = item.kind is not EvidenceKind.GAP and (
        bool(question.families and item.families & set(question.families)) or overlap > 0
    )
    change_first = question.kind is QuestionKind.CHANGE and item.kind is EvidenceKind.CHANGE
    return (
        not (direct or change_first),  # 1. directly answering evidence
        _CURRENT_RANK.get(item.currentness, 3),  # 2. freshest / current
        item.source_ref is None,  # 3. stronger provenance
        item.kind is not EvidenceKind.CHANGE,  # 4. material change
        -overlap,  # 5. relevance
        item.observed_at is None,
        -(item.observed_at.timestamp() if item.observed_at else 0.0),
        item.item_id,
    )


def retrieve(
    corpus: AuthorizedCorpus, question: ResolvedQuestion, budget: ContextBudget
) -> Retrieval:
    query = terms(question.text)
    excluded: dict[str, int] = {}
    scoped: list[EvidenceItem] = []
    for item in corpus.items:
        if not in_scope(item, question):
            excluded["OUT_OF_SCOPE"] = excluded.get("OUT_OF_SCOPE", 0) + 1
            continue
        scoped.append(item)
    if not question.families and question.kind is not QuestionKind.UNKNOWNS:
        # An unscoped overview starts from interpreted signals and opportunities, not raw pages.
        wanted = (
            {EvidenceKind.CHANGE, EvidenceKind.SIGNAL}
            if question.kind is QuestionKind.CHANGE
            else {EvidenceKind.SIGNAL, EvidenceKind.OPPORTUNITY}
        )
        preferred = [i for i in scoped if i.kind in wanted]
        scoped = preferred or scoped

    seen_text: set[tuple[str, str | None]] = set()
    evidence: list[EvidenceItem] = []
    gaps: list[EvidenceItem] = []
    for item in sorted(scoped, key=lambda i: _priority(i, question, query)):
        key = (item.text, item.source_ref)
        if key in seen_text:
            excluded["DUPLICATE"] = excluded.get("DUPLICATE", 0) + 1
            continue
        seen_text.add(key)
        (gaps if item.kind is EvidenceKind.GAP else evidence).append(item)

    selected: list[EvidenceItem] = []
    per_family: dict[str, int] = {}
    changes = 0
    tokens = 0
    want_gaps = question.kind is QuestionKind.UNKNOWNS or bool(
        question.families or question.geographies
    )
    # Required UNKNOWNs reserve room first when the question is about what is not known.
    ordered = (
        (gaps[: budget.max_gaps] + evidence) if question.kind is QuestionKind.UNKNOWNS else evidence
    )
    reserve = (
        gaps[: budget.max_gaps] if want_gaps and question.kind is not QuestionKind.UNKNOWNS else []
    )
    reserved_tokens = sum(estimate_tokens(render_item("E0", g)) for g in reserve)
    for item in ordered:
        cost = estimate_tokens(render_item(f"E{len(selected) + 1}", item))
        family = min((f.value for f in item.families), default="none")
        if len(selected) >= budget.max_items - len(reserve):
            excluded["ITEM_BUDGET"] = excluded.get("ITEM_BUDGET", 0) + 1
            continue
        if per_family.get(family, 0) >= budget.max_items_per_family:
            excluded["FAMILY_BUDGET"] = excluded.get("FAMILY_BUDGET", 0) + 1
            continue
        if item.kind is EvidenceKind.CHANGE and changes >= budget.max_changes:
            excluded["CHANGE_BUDGET"] = excluded.get("CHANGE_BUDGET", 0) + 1
            continue
        if tokens + cost + reserved_tokens > budget.max_evidence_tokens:
            excluded["TOKEN_BUDGET"] = excluded.get("TOKEN_BUDGET", 0) + 1
            continue
        selected.append(item)
        tokens += cost
        per_family[family] = per_family.get(family, 0) + 1
        changes += item.kind is EvidenceKind.CHANGE
    for gap in reserve:
        cost = estimate_tokens(render_item(f"E{len(selected) + 1}", gap))
        if tokens + cost <= budget.max_evidence_tokens and len(selected) < budget.max_items:
            selected.append(gap)
            tokens += cost
    return Retrieval(
        selected=tuple(selected),
        considered=len(corpus.items),
        in_scope=len(scoped),
        excluded=tuple(sorted(excluded.items())),
        evidence_tokens=tokens,
    )
