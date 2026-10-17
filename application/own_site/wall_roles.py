"""What the organizations on a logo wall are to the site's organization (spec 083).

A wall of logos was read as clients or partners from its heading alone, by a governed
vocabulary: "Partners" over press logos became partners, "Featured in" or "Ils utilisent
nos produits" were missed. This is a classification, so Jev answers it with the typed
state it needs (the heading and the names shown under it), one Choice per wall.

Python keeps the last word: a usable answer decides the role (CLIENTS, PARTNERS) or that
the wall is neither (technology, press, credentials, memberships, funders), and an
uncertain or missing answer leaves the governed vocabulary's reading untouched. A role
only the evaluator read stays POTENTIAL; the counterparty never confirmed any of them.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.first_observation.site import PageReading
from application.semantic_layer.cascade import CascadeOutcome
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion

VERSION = "1"
MIN_NAMES = 3
MAX_NAMES_ASKED = 12
MAX_WALLS = 8
#: Reading a wall as clients or partners needs a confident answer (measured 2026-10-17:
#: "Solution 01, …, Disney." read as clients at 0.63); reading it as neither does not.
MIN_ROLE_CONFIDENCE = 0.7

ROLES: tuple[tuple[str, str], ...] = (
    ("CLIENTS", "Organizations that buy from it: customers, case-study clients."),
    ("PARTNERS", "Organizations it works alongside: alliances, resellers, channel or "
                 "implementation partners."),
    ("SUPPLIERS_OR_TECHNOLOGY", "Technologies, platforms or suppliers it uses or integrates."),
    ("PRESS", "Media that wrote about it (\"featured in\", \"as seen in\")."),
    ("CREDENTIALS", "Certifications, awards, badges, ratings or review sites."),
    ("MEMBERSHIPS", "Associations, chambers, clusters or networks it belongs to."),
    ("FUNDERS", "Investors, grants or public funding programmes."),
    ("NOT_ORGANIZATIONS", "The names are products, projects, features, people, places or "
                          "decorations, not organizations."),
    ("UNCLEAR", "The heading and names do not establish it."),
)  # fmt: skip
#: What a usable answer means for the relationship read: a role, or "neither" (None).
_AS_ROLE: dict[str, str | None] = {
    "CLIENTS": "CLIENT", "PARTNERS": "PARTNER", "SUPPLIERS_OR_TECHNOLOGY": None,
    "PRESS": None, "CREDENTIALS": None, "MEMBERSHIPS": None, "FUNDERS": None,
    "NOT_ORGANIZATIONS": None,
}  # fmt: skip


@dataclass(frozen=True, slots=True)
class Wall:
    page_url: str
    heading: str
    names: tuple[str, ...]

    @property
    def key(self) -> tuple[str, str]:
        return self.page_url, self.heading

    def question(self) -> SemanticQuestion:
        shown = ", ".join(self.names[:MAX_NAMES_ASKED])
        digest = hashlib.sha256(f"{self.heading}|{shown}".encode()).hexdigest()[:16]
        return SemanticQuestion(
            question_id=f"wall_role_{digest}",
            version=VERSION,
            primitive=SemanticPrimitive.CHOICE,
            instructions=(
                f'Under the heading "{self.heading}" this website shows logos named: {shown}. '
                "Judging only from the heading and these names, what are these organizations "
                "to the website's own organization?"
            ),
            criteria=ROLES,
        )


def walls(pages: Sequence[PageReading], own_names: Iterable[str] = ()) -> tuple[Wall, ...]:
    """Every heading with at least three logo names (as the vocabulary reads them)."""
    from application.own_site import wall_groups

    found = [
        Wall(page.url, heading, tuple(names))
        for page in pages
        for heading, names in wall_groups(page, own_names)
        if len(names) >= MIN_NAMES
    ]
    return tuple(found[:MAX_WALLS])


def wall_batch(candidates: Sequence[Wall]) -> SemanticBatch | None:
    if not candidates:
        return None
    unique = tuple({w.question().question_id: w.question() for w in candidates}.values())
    return SemanticBatch(
        "own-site:walls",
        {"representation": "logo walls on a public website: heading and the names shown"},
        unique,
    )


def interpret_walls(
    candidates: Sequence[Wall], outcome: CascadeOutcome
) -> dict[tuple[str, str], str | None]:
    """Usable answers only: wall key -> CLIENT, PARTNER or None (neither). Absent: unjudged."""
    judged: dict[tuple[str, str], str | None] = {}
    for wall in candidates:
        judgment = outcome.judgments.get(wall.question().question_id)
        answer = None if judgment is None or not judgment.usable else judgment.answer
        if answer is None or answer.top not in _AS_ROLE:
            continue
        role = _AS_ROLE[answer.top]
        if role is not None and (answer.confidence or 0) < MIN_ROLE_CONFIDENCE:
            continue  # unsure it is a counterparty: the vocabulary's reading stands
        judged[wall.key] = role
    return judged
