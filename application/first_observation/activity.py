"""Open activity discovery: Python reads, Jev classifies, Python validates (spec 063 §5).

Every finding is POTENTIAL, cites an exact line of the page's citable content and says
how it was found. Classification codes are routing indexes for sources, never the
organization's economic reality and never evidence of fit.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.first_observation.geography import jurisdiction, mentioned_places, place_words
from application.first_observation.public_text import public_text
from application.first_observation.routing_terms import MULTILINGUAL_ROUTING_TERMS
from application.first_observation.site import PageReading
from application.first_observation.vocabularies import (
    CPV_DIVISIONS,
    ISIC_SECTIONS,
    NAICS_SECTORS,
    SCHEMA_TYPE_SECTIONS,
    SECTION_ROUTING,
    naics_prefixes,
)
from application.observation_intelligence.catalog import CAPABILITY_LEXICON, offer_natures
from application.observation_intelligence.contracts import (
    CapabilityHypothesis,
    EvidenceRef,
    MarketRole,
    TaxonomyCode,
)
from application.observation_intelligence.findings import cpv_nature
from application.observation_intelligence.understanding import detect_capabilities
from application.semantic_layer.cascade import CascadeOutcome
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion
from application.value_chain import LEGAL_PAGE
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
    #: Lexicon activities only (spec 075 US2): OFFERED when a judgment verified that the
    #: site offers it, UNVERIFIED when no usable judgment exists; None for other methods.
    verification: str | None = None

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
            "verification": self.verification,
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
            verification=(
                None if raw.get("verification") is None else str(raw.get("verification"))
            ),
        )


def _section_codes(section: str) -> tuple[TaxonomyCode, ...]:
    cpv, naics = SECTION_ROUTING.get(section, ((), ()))
    return (
        *(TaxonomyCode("CPV", f"{division}000000") for division in cpv),
        *(TaxonomyCode("NAICS", p) for sector in naics for p in naics_prefixes(sector)),
    )


def prefer_specific_routing(findings: Sequence[ActivityFinding]) -> tuple[ActivityFinding, ...]:
    """A section reading (``isic-*``) routes demand only while no specific activity does.

    A section routes whole CPV divisions: "Manufacturing" read on novonordisk.com routed all
    of CPV 33, and a pharmaceutical maker was offered cardiac-ablation devices (self-check,
    2026-10-17). The section stays as a reading; only its broad routing yields.
    """
    if not any(f.demand_codes and not f.activity_id.startswith("isic-") for f in findings):
        return tuple(findings)
    return tuple(
        replace(f, demand_codes=()) if f.activity_id.startswith("isic-") else f for f in findings
    )


def _schema_line(page: PageReading) -> str | None:
    return next((line for line in page.lines() if line.startswith("schema.org @type:")), None)


#: Lexicon hypotheses kept per observation: the ones its pages lead with. A broad
#: lexicon would otherwise turn every passing mention into a demand search.
MAX_LEXICON_FINDINGS = 3


def deterministic_activity(pages: Sequence[PageReading]) -> tuple[ActivityFinding, ...]:
    """Lexicon matches and schema.org self-declared types. No network, no model."""

    findings: dict[str, ActivityFinding] = {}
    for page in pages:
        lexical = sum(f.method is ActivityMethod.LEXICON for f in findings.values())
        if LEGAL_PAGE.search(urlsplit(page.url).path):
            continue  # contracts and policies name services it uses, not what it does
        for hypothesis in detect_capabilities(
            text=page.readable(),
            observation_id="page",
            source_ref=page.url,
            observed_at=page.observed_at,
        )[: max(0, MAX_LEXICON_FINDINGS - lexical)]:
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
    version="2",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "If a public buyer procured what this organization itself supplies or performs, "
        "which CPV division would classify it? For goods, the division of the goods, never "
        "of the services or works its customers perform with them. Choose NONE when public "
        "buyers would not procure it and UNCLEAR when the reading does not say what it offers."
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
_NATURE_WORDS = {"SUPPLIES": "supplies goods", "SERVICES": "performs services",
                  "WORKS": "carries out construction works"}  # fmt: skip


def _with_nature(entry_label: str, natures: frozenset[str]) -> str:
    said = " or ".join(_NATURE_WORDS[n] for n in sorted(natures))
    return f"{entry_label} (the organization {said})" if said else entry_label


#: AXIGNAL's own activity catalog, asked over the public text when the lexicon finds nothing
#: (found on biocultor.com: "Comprar té de humus y servicios para jardines" read as nothing;
#: then read as landscaping, the use of what it sells, because no entry fitted: spec 080).
CATALOG_ACTIVITY = SemanticQuestion(
    question_id="fo_catalog_activity",
    version="2",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "Using only this public website reading, which of these activities is the main thing "
        "the organization itself sells or performs for its customers? What its customers do "
        "with its products, who buys them, and what it only mentions, uses itself or sells "
        "through are not its activity: a shop selling fertiliser for gardens supplies "
        "fertiliser, it does not maintain gardens. Choose NONE when no activity in the list is "
        "what it sells or performs (never the closest one), and UNCLEAR when the reading does "
        "not say."
    ),
    criteria=(
        *((e.capability_id, _with_nature(e.label, offer_natures(e))) for e in CAPABILITY_LEXICON),
        ("NONE", "What it sells or performs is not in this list."),
        ("UNCLEAR", "The reading does not establish what it offers."),
    ),
)
#: What kind of offer it is: the structural check every judged activity must agree with.
OFFER_NATURE = SemanticQuestion(
    question_id="fo_offer_nature",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "Using only this public website reading, what does the organization mainly sell to "
        "its customers? What customers then do with it is not what it sells."
    ),
    criteria=(
        ("SUPPLIES", "Goods or products it makes, distributes or sells."),
        ("SERVICES", "Services it performs for its customers."),
        ("WORKS", "Construction works it carries out."),
        ("MIXED", "More than one of the above, explicitly and substantially."),
        ("UNCLEAR", "The reading does not establish it."),
    ),
)
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
    #: The lexicon's own readings, kept so the offer's nature can arbitrate between them.
    deterministic: tuple[ActivityFinding, ...] = ()


_ENTRIES = {e.capability_id: e for e in CAPABILITY_LEXICON}


def _natures(finding: ActivityFinding) -> frozenset[str]:
    entry = _ENTRIES.get(finding.activity_id)
    return frozenset() if entry is None else offer_natures(entry)


def natures_disagree(findings: Sequence[ActivityFinding]) -> bool:
    """The site's own readings name offers of natures no single answer reconciles (spec 080):
    a fertiliser shop that also reads as landscaping from an article headline."""
    natured = [n for n in map(_natures, findings) if n]
    return len(natured) > 1 and not frozenset.intersection(*natured)


# AXIGNAL's routing vocabulary. Since the ADR-0090 amendment of 2026-10-16 the evaluator
# receives public text (``public_text``) rather than this projection; ``minimize`` remains
# for routing heuristics and for any consumer that must stay vocabulary-only.
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
    | MULTILINGUAL_ROUTING_TERMS
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
    """Typed public text per page (ADR-0090 amendment 2026-10-16): what the site says, with
    contact data and sentences about people removed. Legal pages are not sent; an about page
    contributes its title, description and headings, not its body (often about people)."""
    from application.first_observation.activity_verification import PageKind, page_kind

    del origin
    out: list[dict[str, object]] = []
    for index, page in enumerate(pages, 1):
        kind = page_kind(page)
        if kind is PageKind.LEGAL:
            continue
        body = "" if kind in {PageKind.ABOUT, PageKind.CAREERS} else page.text
        out.append({
            "url": f"[page-{index}]",
            "kind": kind.value,
            "title": public_text(page.title, 300),
            "description": public_text(page.description, 600),
            "headings": [public_text(h, 200) for h in page.headings[:8]],
            "services": [public_text(x, 200) for x in page.services[:12]],
            "text": public_text(body[: STATE_CHARS_PER_PAGE * 2], STATE_CHARS_PER_PAGE),
        })  # fmt: skip
    return {
        "representation": "public website text; contact data and sentences about people removed",
        "site": "[site]",
        "pages": out,
    }


def plan_activity_batch(
    origin: str,
    pages: Sequence[PageReading],
    *,
    known_scopes: Sequence[TaxonomyCode],
    deterministic: Sequence[ActivityFinding],
    premises_known: bool | None = None,
) -> ActivityBatchPlan | None:
    """The questions worth asking, or None when the deterministic answer suffices.

    Sector is asked when no deterministic activity exists; CPV / NAICS only when an EU /
    US scope (declared or mentioned) could route them; location only when no premises are
    declared and the text mentions listed places. A declared service area ("Worldwide")
    says where it sells, not where it is (found on axignal.com, 2026-10-17), so it does
    not stop the question; ``premises_known`` defaults to "any scope known".
    """

    if not pages:
        return None
    candidates: list[tuple[TaxonomyCode, str, str, str]] = []
    if not (bool(known_scopes) if premises_known is None else premises_known):
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
        questions += [OPERATING, SECTOR, CATALOG_ACTIVITY, OFFER_NATURE]
    elif natures_disagree(deterministic):
        questions.append(OFFER_NATURE)
    if eu and not routed:
        questions.append(CPV_DIVISION)
    if us and not routed:
        questions.append(NAICS_SECTOR)
    if candidates:
        questions.append(_location_question([(p, n) for p, n, _u, _l in candidates]))
    if not questions:
        return None
    batch = SemanticBatch(f"first-observation:{origin}", _state(origin, pages), tuple(questions))
    return ActivityBatchPlan(batch, tuple(candidates), tuple(deterministic))


@dataclass(frozen=True, slots=True)
class SemanticReading:
    findings: tuple[ActivityFinding, ...]
    codes: tuple[TaxonomyCode, ...]
    roles: frozenset[MarketRole] | None
    delivery: str | None
    operating: bool | None
    located: tuple[tuple[TaxonomyCode, str, str], ...]  # place, url, cited line
    judged: dict[str, str]
    #: Lexicon activities whose nature contradicts what the organization sells (spec 080).
    withheld: tuple[str, ...] = ()


def _usable(outcome: CascadeOutcome, question_id: str) -> tuple[str, float | None] | None:
    judgment = outcome.judgments.get(question_id)
    if judgment is None or not judgment.usable or judgment.answer is None:
        return None
    return judgment.answer.top, judgment.answer.confidence


def _cite(pages: Sequence[PageReading]) -> tuple[PageReading, str]:
    page = pages[0]
    line = page.description or page.title or next(iter(page.lines()), "")
    return page, line


#: Distinct controlled words the judgment must have seen before "not an operating
#: business" is believed (real companies with sparse homepages read 1-9 words).
MIN_WORDS_TO_DENY = 15


#: Words a placeholder page says of itself; with them a short page may be judged one.
PLACEHOLDER_WORDS = frozenset(
    ["coming", "soon", "construction", "placeholder", "próximamente", "construcción",
     "demnächst", "bientôt", "prossimamente", "brevemente", "binnenkort", "snart"]
)  # fmt: skip


def _vocabulary(plan: ActivityBatchPlan, only: frozenset[str] | None = None) -> int:
    """Distinct controlled words the batch carried (or, with ``only``, those of them)."""
    pages = plan.batch.state.get("pages") if isinstance(plan.batch.state, dict) else None
    words: set[str] = set()
    for page in pages if isinstance(pages, list) else []:
        if isinstance(page, dict):
            fields = [str(page.get(k) or "") for k in ("title", "description", "text")]
            fields += [str(i) for k in ("headings", "services") for i in page.get(k) or []]
            for field in fields:
                words.update(_SAFE_WORD.findall(field.casefold()))
    return len(words if only is None else words & only)


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
    answered_nature = _usable(outcome, OFFER_NATURE.question_id)
    nature = answered_nature[0] if answered_nature and answered_nature[0] in _NATURE_WORDS else None
    if nature is not None:
        judged["offerNature"] = nature
    if cpv and cpv[0] in CPV_DIVISIONS and nature not in (None, cpv_nature(cpv[0])):
        # Spec 080: a goods seller's division is never that of what its buyers do with them.
        judged["cpvDivisionWithheld"] = "NATURE_CONFLICT"
        cpv = None
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
    catalog = _usable(outcome, CATALOG_ACTIVITY.question_id)
    entry = next((e for e in CAPABILITY_LEXICON if catalog and e.capability_id == catalog[0]), None)
    if (
        entry is not None
        and nature is not None
        and offer_natures(entry)
        and (nature not in offer_natures(entry))
    ):
        # Spec 080: the judged activity disagrees with what the organization sells (a shop
        # read as the service its buyers perform). Unknown, never the nearest activity.
        judged["catalogActivityWithheld"] = "NATURE_CONFLICT"
        entry = None
    elif catalog is not None and catalog[0] == "NONE":
        judged["catalogGap"] = "NONE"  # operator trace: the catalog may lack this activity
    if entry is not None and catalog is not None and line:
        judged["catalogActivity"] = entry.capability_id
        findings.insert(
            0,
            ActivityFinding(
                activity_id=entry.capability_id,
                label=entry.label,
                method=ActivityMethod.SEMANTIC_JUDGMENT,
                page_url=page.url,
                excerpt=line,
                observed_at=page.observed_at,
                demand_codes=entry.demand_codes,
                confidence=catalog[1],
                model=model,
            ),
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
    if (
        operating is not None
        and operating[0] == "false"
        and _vocabulary(plan) < MIN_WORDS_TO_DENY
        and not _vocabulary(plan, PLACEHOLDER_WORDS)
    ):
        # Too little of the page reached the judgment to say it is not a business: a
        # script-built or image-only page reads empty. Unknown, never a false negative.
        operating = None
        judged["operatingDenialWithheld"] = "THIN_STATE"
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
    withheld: tuple[str, ...] = ()
    agreeing = [f for f in plan.deterministic if nature in _natures(f)]
    if nature is not None and agreeing:
        # The evaluator only arbitrates between the site's own readings: it withholds those
        # of another nature when one of the nature it sells remains, never all of them.
        withheld = tuple(
            f.activity_id for f in plan.deterministic if _natures(f) and nature not in _natures(f)
        )
    return SemanticReading(
        withheld=withheld,
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
