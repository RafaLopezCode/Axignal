"""Is a headline that names the organization about *this* organization? (spec 085).

A headline matching the organization's name was shown as a mention with "not verified"
attribution: homonyms (another company, a person, a place, a product sharing the name)
reached its reputation. Jev answers one Choice per headline over a typed state: the
organization's name, website and activity, and the headline.

The read path never calls a provider: it recalls remembered judgments and queues the
missing ones for the background runner. Python keeps the last word: ANOTHER_ENTITY
withholds the headline (the safe direction), ABOUT_IT names who judged it, and an
uncertain or missing judgment leaves the headline exactly as before (POTENTIAL,
attribution not verified). A mention is never an endorsement (MASTER §54).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.cascade import CascadePolicy, SemanticCascade
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion
from application.semantic_layer.memory import memory_key

ABOUT_IT = "ABOUT_IT"
ANOTHER_ENTITY = "ANOTHER_ENTITY"
ATTRIBUTION = SemanticQuestion(
    question_id="press_attribution",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "The headline contains the organization's name. Using the organization's website "
        "and activity, is the headline about this organization, or about another company, "
        "person, place, product or event that shares the name?"
    ),
    criteria=(
        (ABOUT_IT, "About this organization (it acts, is reported on, or is the source)."),
        (ANOTHER_ENTITY, "About someone or something else that shares the name."),
        ("UNCLEAR", "The headline does not establish it."),
    ),
)
MAX_PENDING = 500


def attribution_batch(
    name: str, website: str | None, activity: str | None, headline: str
) -> SemanticBatch:
    return SemanticBatch(
        f"press-attribution:{name}:{headline}"[:300],
        {"organization": name, "website": website, "activity": activity, "headline": headline},
        (ATTRIBUTION,),
    )


@dataclass
class PressAttribution:
    """Recall on read, judge in the background, through the semantic cascade (Jev)."""

    factory: Callable[[], SemanticCascade | None]
    policy: CascadePolicy = field(default_factory=CascadePolicy)
    _pending: dict[str, SemanticBatch] = field(default_factory=dict)

    def recall(
        self, name: str, website: str | None, activity: str | None
    ) -> Callable[[str], tuple[str, str] | None]:
        """A per-headline lookup: (label, model) when remembered and usable, else None."""
        cascade = self.factory()

        def check(headline: str) -> tuple[str, str] | None:
            if cascade is None or cascade.memory is None:
                return None
            batch = attribution_batch(name, website, activity, headline)
            answer = cascade.memory.get(memory_key(
                batch.state_fingerprint, ATTRIBUTION, cascade.judge.name, cascade.judge.model
            ))  # fmt: skip
            if answer is None:
                if len(self._pending) < MAX_PENDING:
                    self._pending.setdefault(batch.batch_id, batch)
                return None
            if self.policy.uncertain(answer) or answer.top not in {ABOUT_IT, ANOTHER_ENTITY}:
                return None
            return answer.top, cascade.judge.model

        return check

    def run(self, now: datetime, *, max_batches: int = 60) -> int:
        """Judge queued headlines; the judgments land in the shared memory."""
        if not self._pending:
            return 0
        cascade = self.factory()
        if cascade is None:
            return 0
        batches = list(self._pending.values())[:max_batches]
        cascade.run(batches, now=now)
        for batch in batches:
            self._pending.pop(batch.batch_id, None)
        return len(batches)
