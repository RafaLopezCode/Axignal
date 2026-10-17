"""Which prefiltered headlines are about a sector: one Jev judgment per headline (spec 082).

Sector context and regulation used to send every candidate to the generative assistant
and ask for "the indexes" back: one opaque call, a list nobody could audit and nothing
reusable. This is a classification, so it is asked as one: each headline is a Noul
question over a typed state (the sector, what counts and what does not), Python keeps
only usable "true" answers, and a headline judged once is remembered for every sector
run that meets it again. Uncertain stays out of the briefing: shown is what is judged
relevant, never what is merely unrejected. Non-authoritative: it decides what is shown,
never what is true.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion

VERSION = "1"


@dataclass(frozen=True, slots=True)
class HeadlinePurpose:
    """What a briefing keeps, typed for the evaluator."""

    kind: str  # "SECTOR_NEWS" or "REGULATION"
    keeps: str
    excludes: str


SECTOR_NEWS = HeadlinePurpose(
    "SECTOR_NEWS",
    keeps="about the sector itself: its market, prices, demand, regulation, technology, "
    "companies or workforce",
    excludes='headlines that only share a word with it ("seguridad social" is not private '
    'security; "energía" in a sports headline is not the energy sector)',
)
REGULATION = HeadlinePurpose(
    "REGULATION",
    keeps="official entries that set or change rules, obligations, standards, wages "
    "(collective agreements), subsidies or taxes for companies of the sector",
    excludes="appointments, individual cases, and entries that only share a word with it",
)


@dataclass(frozen=True, slots=True)
class HeadlineVerdict:
    kept: tuple[int, ...]
    instrument: Mapping[str, object]


#: (sector label, candidate titles, purpose, now) -> verdict; None when it cannot be asked.
HeadlineJudge = Callable[[str, Sequence[str], HeadlinePurpose, datetime], HeadlineVerdict | None]


def _question(title: str, purpose: HeadlinePurpose) -> SemanticQuestion:
    digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    return SemanticQuestion(
        question_id=f"hl_{purpose.kind.lower()}_{digest}",
        version=VERSION,
        primitive=SemanticPrimitive.NOUL,
        instructions=f'Is this headline {purpose.keeps}? Headline: "{title}"',
        criteria=(("true", "It is."), ("false", f"It is not; this includes {purpose.excludes}.")),
    )


def jev_headline_judge(factory: Callable[[], SemanticCascade | None]) -> HeadlineJudge:
    """The judge for sector context and regulation, through the semantic cascade (Jev)."""

    def judge(
        sector: str, titles: Sequence[str], purpose: HeadlinePurpose, now: datetime
    ) -> HeadlineVerdict | None:
        cascade = factory()
        if cascade is None or not titles:
            return None
        questions = tuple(_question(t, purpose) for t in titles)
        unique = tuple({q.question_id: q for q in questions}.values())
        batch = SemanticBatch(
            f"headlines:{purpose.kind}:{sector}",
            {
                "sector": sector,
                "briefing": purpose.kind,
                "keeps": purpose.keeps,
                "excludes": purpose.excludes,
            },
            unique,
        )
        outcome = cascade.run([batch], now=now)[batch.batch_id]
        kept = []
        for index, question in enumerate(questions):
            judgment = outcome.judgments.get(question.question_id)
            answer = None if judgment is None or not judgment.usable else judgment.answer
            if answer is not None and answer.top == "true":
                kept.append(index)
        return HeadlineVerdict(
            kept=tuple(kept),
            instrument={
                "evaluator": cascade.judge.name,
                "model": cascade.judge.model,
                "method": "one non-authoritative Noul judgment per headline",
            },
        )

    return judge
