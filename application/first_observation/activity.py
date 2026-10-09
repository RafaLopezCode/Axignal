"""Open activity discovery: Python reads, Jev classifies, Python validates (spec 063 §5).

Every finding is POTENTIAL, cites an exact line of the page's citable content and says
how it was found. Classification codes are routing indexes for sources, never the
organization's economic reality and never evidence of fit.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.first_observation.geography import jurisdiction, mentioned_places, place_words
from application.first_observation.site import PageReading
from application.first_observation.vocabularies import (
    CPV_DIVISIONS,
    ISIC_SECTIONS,
    NAICS_SECTORS,
    SCHEMA_TYPE_SECTIONS,
    SECTION_ROUTING,
    naics_prefixes,
)
from application.observation_intelligence.catalog import CAPABILITY_LEXICON
from application.observation_intelligence.contracts import (
    CapabilityHypothesis,
    EvidenceRef,
    MarketRole,
    TaxonomyCode,
)
from application.observation_intelligence.understanding import detect_capabilities
from application.semantic_layer.cascade import CascadeOutcome
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion
from domain.xignal import XignalEpistemicState

STATE_CHARS_PER_PAGE = 1_800


class ActivityMethod(StrEnum):
    LEXICON = "LEXICON"
    SCHEMA_ORG_TYPE = "SCHEMA_ORG_TYPE"
    SEMANTIC_JUDGMENT = "SEMANTIC_JUDGMENT"


@dataclass(frozen=True, slots=True)
class ActivityFinding:
    """One POTENTIAL activity hypothesis with its exact citation."""

    activity_id: str
    label: str
    method: ActivityMethod
    page_url: str
    excerpt: str
    observed_at: datetime
    demand_codes: tuple[TaxonomyCode, ...]
    confidence: float | None = None
    model: str | None = None

    def to_wire(self) -> dict[str, object]:
        return {
            "activityId": self.activity_id,
            "label": self.label,
            "method": self.method.value,
            "pageUrl": self.page_url,
            "excerpt": self.excerpt,
            "observedAt": self.observed_at.isoformat(),
            "demandCodes": [[c.scheme, c.code] for c in self.demand_codes],
            "confidence": self.confidence,
            "model": self.model,
            "state": XignalEpistemicState.POTENTIAL.value,
        }

    @staticmethod
    def from_wire(raw: Mapping[str, object]) -> ActivityFinding:
        codes = raw["demandCodes"]
        assert isinstance(codes, list)
        confidence = raw.get("confidence")
        return ActivityFinding(
            activity_id=str(raw["activityId"]),
            label=str(raw["label"]),
            method=ActivityMethod(str(raw["method"])),
            page_url=str(raw["pageUrl"]),
            excerpt=str(raw["excerpt"]),
            observed_at=datetime.fromisoformat(str(raw["observedAt"])),
            demand_codes=tuple(TaxonomyCode(str(s), str(c)) for s, c in codes),
            confidence=float(confidence) if isinstance(confidence, int | float) else None,
            model=None if raw.get("model") is None else str(raw.get("model")),
        )


def _section_codes(section: str) -> tuple[TaxonomyCode, ...]:
    cpv, naics = SECTION_ROUTING.get(section, ((), ()))
    return (
        *(TaxonomyCode("CPV", f"{division}000000") for division in cpv),
        *(TaxonomyCode("NAICS", p) for sector in naics for p in naics_prefixes(sector)),
    )


def _schema_line(page: PageReading) -> str | None:
    return next((line for line in page.lines() if line.startswith("schema.org @type:")), None)


def deterministic_activity(pages: Sequence[PageReading]) -> tuple[ActivityFinding, ...]:
    """Lexicon matches and schema.org self-declared types. No network, no model."""

    findings: dict[str, ActivityFinding] = {}
    for page in pages:
        for hypothesis in detect_capabilities(
            text=page.readable(),
            observation_id="page",
            source_ref=page.url,
            observed_at=page.observed_at,
        ):
            findings.setdefault(
                hypothesis.capability_id,
                ActivityFinding(
                    activity_id=hypothesis.capability_id,
                    label=hypothesis.label,
                    method=ActivityMethod.LEXICON,
                    page_url=page.url,
                    excerpt=hypothesis.basis[0].excerpt,
                    observed_at=page.observed_at,
                    demand_codes=hypothesis.demand_codes,
                ),
            )
        line = _schema_line(page)
        for schema_type in page.schema_types:
            section = SCHEMA_TYPE_SECTIONS.get(schema_type)
            if section is None or line is None or f"isic-{section}" in findings:
                continue
            findings[f"isic-{section}"] = ActivityFinding(
                activity_id=f"isic-{section}",
                label=ISIC_SECTIONS[section],
                method=ActivityMethod.SCHEMA_ORG_TYPE,
                page_url=page.url,
                excerpt=line,
                observed_at=page.observed_at,
                demand_codes=_section_codes(section),
            )
    return tuple(findings.values())


# --- Semantic questions (one state, many questions; selected by routing need) -------

SECTOR = SemanticQuestion(
    question_id="fo_isic_section",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "Using only this public website reading, which ISIC Rev.4 section best describes "
        "the main economic activity the organization offers to its customers? Choose "
        "UNCLEAR when the reading does not say what it offers."
    ),
    criteria=(*ISIC_SECTIONS.items(), ("UNCLEAR", "The reading does not establish it.")),
)
CPV_DIVISION = SemanticQuestion(
    question_id="fo_cpv_division",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "If a public buyer procured what this organization offers, which CPV division "
        "would classify it? Choose NONE when public buyers would not procure it and "
        "UNCLEAR when the reading does not say what it offers."
    ),
    criteria=(
        *CPV_DIVISIONS.items(),
        ("NONE", "Not something public buyers procure."),
        ("UNCLEAR", "The reading does not establish it."),
    ),
)
NAICS_SECTOR = SemanticQuestion(
    question_id="fo_naics_sector",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "Which NAICS 2022 sector best classifies what this organization offers? Choose "
        "UNCLEAR when the reading does not say what it offers."
    ),
    criteria=(*NAICS_SECTORS.items(), ("UNCLEAR", "The reading does not establish it.")),
)
CUSTOMERS = SemanticQuestion(
    question_id="fo_customer_type",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions="Who does the reading say the organization sells to?",
    criteria=(
        ("CONSUMERS", "Individuals and households."),
        ("BUSINESSES", "Companies and professionals."),
        ("PUBLIC_SECTOR", "Public administrations and public bodies."),
        ("MIXED", "More than one of the above, explicitly."),
        ("UNCLEAR", "The reading does not say."),
    ),
)
DELIVERY = SemanticQuestion(
    question_id="fo_delivery_mode",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions="How does the reading say the main offer is delivered?",
    criteria=(
        ("CUSTOMER_SITE", "Performed at the customer's location (works, installation, on-site service)."),
        ("PREMISES", "Customers come to the organization's own premises."),
        ("SHIPPED", "Goods shipped or delivered to customers."),
        ("REMOTE_OR_DIGITAL", "Delivered remotely or digitally (software, online service)."),
        ("UNCLEAR", "The reading does not say."),
    ),
)  # fmt: skip
OPERATING = SemanticQuestion(
    question_id="fo_operating_business",
    version="1",
    primitive=SemanticPrimitive.NOUL,
    instructions=(
        "Is this the website of an operating organization that offers goods or services "
        "(not a parked domain, placeholder or page under construction)?"
    ),
    criteria=(("true", "An operating organization's site."), ("false", "Not one.")),
)


def _location_question(candidates: Sequence[tuple[TaxonomyCode, str]]) -> SemanticQuestion:
    return SemanticQuestion(
        question_id="fo_operating_location",
        version="1",
        primitive=SemanticPrimitive.CHOICE,
        instructions=(
            "Which of these places does the reading state as where the organization is "
            "located or operates? Choose NONE_STATED if it only mentions them otherwise."
        ),
        criteria=(
            *((place.code, f"Located or operating in {name.title()}.") for place, name in candidates),
            ("NONE_STATED", "No listed place is stated as its location."),
        ),
    )  # fmt: skip


@dataclass(frozen=True, slots=True)
class ActivityBatchPlan:
    batch: SemanticBatch
    place_candidates: tuple[tuple[TaxonomyCode, str, str, str], ...]  # place, name, url, line


# Evaluator input is a bounded **routing signal projection**, not an excerpt.
# A free-text regex cannot guarantee that single-token or lowercase personal names
# are absent. Every emitted term comes from this developer-controlled vocabulary.
# The actual source text remains only in the tenant's governed observation context.
_ROUTING_TERMS = (
    frozenset(
        """
    language languages school schools classes courses course education educational
    teaching teachers training lessons learn studio students adults kids children
    software cloud invoicing bookkeeping accounting banking payments finance
    solar photovoltaic panels electricity electrical renewable energy construction
    maintenance heating ventilation cooling hvac industrial manufacturing
    retail wholesale repair repairs products services service installation
    installations installing logistics transport agriculture farming food
    marketing advertising communication consulting consultancy agency design
    digital online remote premises location located operates operating located
    consumer consumers clients customer customers business businesses public
    government government procurement supplies supplies sale selling delivery
    shipped offers provides provision for at in from to and or with
    small medium large local national international website
    coming soon under construction placeholder
    little rock
    """.split()  # noqa: SIM905
    )
    | place_words()
    | frozenset(
        token
        for labels in (ISIC_SECTIONS, CPV_DIVISIONS, NAICS_SECTORS)
        for label in labels.values()
        for token in re.findall(r"[a-z]{3,}", label.casefold())
    )
)
_SAFE_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def minimize(text: str, allowed: frozenset[str] = frozenset()) -> str:
    """Emit only fixed non-identifying economic vocabulary; never forward source text.

    A person's name, e-mail, phone, URL, username or unexpected token is incapable
    of leaving this boundary. The output is not a complete rendering of the page.
    """
    del allowed
    tokens = [
        token
        for match in _SAFE_WORD.finditer(text.casefold())
        if (token := match.group()) in _ROUTING_TERMS
    ]
    return " ".join(tokens)[:STATE_CHARS_PER_PAGE]


def person_free(text: str) -> str:
    return minimize(text)


def _state(origin: str, pages: Sequence[PageReading]) -> dict[str, object]:
    del origin
    return {
        "representation": "controlled economic terms, not complete page text",
        "site": "[site]",
        "pages": [
            {
                "url": f"[page-{index}]",
                "title": minimize(page.title),
                "description": minimize(page.description),
                "headings": [minimize(h) for h in page.headings[:8]],
                "services": [minimize(x) for x in page.services[:12]],
                "text": minimize(page.text[:STATE_CHARS_PER_PAGE]),
            }
            for index, page in enumerate(pages, 1)
        ],
    }


def plan_activity_batch(
    origin: str,
    pages: Sequence[PageReading],
    *,
    known_scopes: Sequence[TaxonomyCode],
    deterministic: Sequence[ActivityFinding],
) -> ActivityBatchPlan | None:
    """The questions worth asking, or None when the deterministic answer suffices.

    Sector is asked when no deterministic activity exists; CPV / NAICS only when an EU /
    US scope (declared or mentioned) could route them; location only when none is
    declared and the text mentions listed places.
    """

    if not pages:
        return None
    candidates: list[tuple[TaxonomyCode, str, str, str]] = []
    if not known_scopes:
        for page in pages:
            english = (page.language or "").lower().startswith("en")
            for line in page.lines():
                mentions = mentioned_places(line)
                us_named = any(place.code == "US" for place, _ in mentions)
                for place, name in mentions:
                    if place.code.startswith("US/") and not (english or us_named):
                        continue  # "Colorado", "Nevada" are also Spanish words
                    if all(place.code != c[0].code for c in candidates):
                        candidates.append((place, name, page.url, line))
        candidates = candidates[:10]
    scopes = [*known_scopes, *(c[0] for c in candidates)]
    eu = any(s.code.startswith("EU/") or s.code == "EU" for s in scopes)
    us = any(s.code == "US" or s.code.startswith("US/") for s in scopes)
    questions: list[SemanticQuestion] = []
    routed = any(f.demand_codes for f in deterministic)
    if not deterministic:
        questions += [OPERATING, SECTOR]
    if eu and not routed:
        questions.append(CPV_DIVISION)
    if us and not routed:
        questions.append(NAICS_SECTOR)
    if candidates:
        questions.append(_location_question([(p, n) for p, n, _u, _l in candidates]))
    if not questions:
        return None
    batch = SemanticBatch(f"first-observation:{origin}", _state(origin, pages), tuple(questions))
    return ActivityBatchPlan(batch, tuple(candidates))


@dataclass(frozen=True, slots=True)
class SemanticReading:
    findings: tuple[ActivityFinding, ...]
    codes: tuple[TaxonomyCode, ...]
    roles: frozenset[MarketRole] | None
    delivery: str | None
    operating: bool | None
    located: tuple[tuple[TaxonomyCode, str, str], ...]  # place, url, cited line
    judged: dict[str, str]


def _usable(outcome: CascadeOutcome, question_id: str) -> tuple[str, float | None] | None:
    judgment = outcome.judgments.get(question_id)
    if judgment is None or not judgment.usable or judgment.answer is None:
        return None
    return judgment.answer.top, judgment.answer.confidence


def _cite(pages: Sequence[PageReading]) -> tuple[PageReading, str]:
    page = pages[0]
    line = page.description or page.title or next(iter(page.lines()), "")
    return page, line


def interpret_activity(
    plan: ActivityBatchPlan,
    outcome: CascadeOutcome,
    pages: Sequence[PageReading],
    *,
    model: str | None,
) -> SemanticReading:
    """Python validates judgments: UNCLEAR, NONE and unusable answers stay UNKNOWN."""

    judged: dict[str, str] = {}
    findings: list[ActivityFinding] = []
    page, line = _cite(pages)
    codes: list[TaxonomyCode] = []
    sector = _usable(outcome, SECTOR.question_id)
    cpv = _usable(outcome, CPV_DIVISION.question_id)
    naics = _usable(outcome, NAICS_SECTOR.question_id)
    if cpv and cpv[0] in CPV_DIVISIONS:
        codes.append(TaxonomyCode("CPV", f"{cpv[0]}000000"))
        judged["cpvDivision"] = cpv[0]
    if naics and naics[0] in NAICS_SECTORS:
        codes += [TaxonomyCode("NAICS", p) for p in naics_prefixes(naics[0])]
        judged["naicsSector"] = naics[0]
    if sector and sector[0] in ISIC_SECTIONS and line:
        judged["isicSection"] = sector[0]
        findings.append(
            ActivityFinding(
                activity_id=f"isic-{sector[0]}",
                label=ISIC_SECTIONS[sector[0]],
                method=ActivityMethod.SEMANTIC_JUDGMENT,
                page_url=page.url,
                excerpt=line,
                observed_at=page.observed_at,
                demand_codes=tuple(codes),
                confidence=sector[1],
                model=model,
            )
        )
    customers = _usable(outcome, CUSTOMERS.question_id)
    roles = {
        "CONSUMERS": frozenset({MarketRole.CONSUMERS}),
        "BUSINESSES": frozenset({MarketRole.PRIVATE_BUSINESSES}),
        "PUBLIC_SECTOR": frozenset({MarketRole.PUBLIC_BUYERS}),
        "MIXED": frozenset(MarketRole),
    }.get(customers[0] if customers else "")
    delivery = _usable(outcome, DELIVERY.question_id)
    operating = _usable(outcome, OPERATING.question_id)
    located: list[tuple[TaxonomyCode, str, str]] = []
    location = _usable(outcome, "fo_operating_location")
    if location is not None:
        for place, _name, url, cited in plan.place_candidates:
            if place.code == location[0]:
                located.append((place, url, cited))
    for key, value in (
        ("customers", customers),
        ("delivery", delivery),
        ("operating", operating),
        ("location", location),
    ):
        if value is not None:
            judged[key] = value[0]
    return SemanticReading(
        findings=tuple(findings),
        codes=tuple(codes),
        roles=roles,
        delivery=None if delivery is None or delivery[0] == "UNCLEAR" else delivery[0],
        operating=None if operating is None else operating[0] == "true",
        located=tuple(located),
        judged=judged,
    )


def to_capabilities(
    findings: Sequence[ActivityFinding],
    observation_for: Mapping[str, str],
    pages: Sequence[PageReading],
) -> tuple[CapabilityHypothesis, ...]:
    """POTENTIAL hypotheses whose basis cites the observation that holds each page."""

    by_url = {page.url: page for page in pages}
    out: list[CapabilityHypothesis] = []
    for finding in findings:
        page = by_url.get(finding.page_url)
        observation_id = observation_for.get(finding.page_url)
        if page is None or observation_id is None or finding.excerpt not in page.readable():
            continue
        lexicon = next(
            (e for e in CAPABILITY_LEXICON if e.capability_id == finding.activity_id), None
        )
        out.append(
            CapabilityHypothesis(
                capability_id=finding.activity_id,
                label=finding.label,
                state=XignalEpistemicState.POTENTIAL,
                basis=(EvidenceRef(observation_id, page.url, finding.excerpt, page.observed_at),),
                demand_codes=finding.demand_codes,
                buyer_jobs=() if lexicon is None else lexicon.buyer_jobs,
            )
        )
    return tuple(out)


def declared_scopes(pages: Sequence[PageReading]) -> tuple[TaxonomyCode, ...]:
    """Jurisdictions of declared postal addresses (premises), deduplicated."""
    scopes: dict[str, TaxonomyCode] = {}
    for page in pages:
        for address in page.addresses:
            code = jurisdiction(address.country, address.region)
            if code is not None:
                scopes.setdefault(code.code, code)
    return tuple(scopes.values())
