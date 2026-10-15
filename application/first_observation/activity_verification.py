"""Activity verification: does the site offer what the lexicon found? (spec 075 US2).

A lexicon match says a website *names* an activity; it does not say the organization
*offers* it. "Secure software development lifecycle" on a security company's page is a
practice it uses, not a service it sells. One narrow, versioned CHOICE question per
lexicon-detected activity asks a replaceable typing provider (MASTER §56.14) which it
is; Python composes the answer deterministically:

* OFFERED establishes the activity (verified);
* no usable judgment (layer off, budget, failure, uncertain) or UNCLEAR keeps today's
  lexicon result, marked UNVERIFIED;
* MENTIONED and USED_INTERNALLY do not establish it. They are kept as inspectable
  negative classifications (MASTER §56.13), never silently deleted.

The state is ADR-0090 as amended 2026-10-13: AXIGNAL's controlled vocabulary only (the
routing terms, a fixed set of neutral economic words and the catalog's own terms), the
capability's catalog label and terms, the deterministic kind of each page where the
match occurs and anonymous page ids. Never page text, quotations, URLs, names or
identifiers. Judgments are non-authoritative and are never training or calibration
data for any other evaluator (ADR-0090; spec 075 FR-009).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from urllib.parse import urlsplit

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.first_observation.activity import (
    _ROUTING_TERMS,
    STATE_CHARS_PER_PAGE,
    ActivityFinding,
    ActivityMethod,
)
from application.first_observation.site import PageReading
from application.observation_intelligence.catalog import CAPABILITY_LEXICON
from application.observation_intelligence.understanding import detect_capabilities
from application.semantic_layer.cascade import CascadeOutcome
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion
from application.value_chain import LEGAL_PAGE

ACTIVITY_OFFERED = SemanticQuestion(
    question_id="activity_offered",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions=(
        "The state names one activity from AXIGNAL's catalog (its label and catalog "
        "terms), the kinds of website pages where the organization's site names it and "
        "AXIGNAL's controlled economic words around each mention (not the page text). "
        "Does the organization offer this activity to its customers?"
    ),
    criteria=(
        ("OFFERED", "The organization offers or sells this activity to its customers: it "
                    "presents it as what it does, typically on service, product or home pages."),
        ("MENTIONED", "The activity is only mentioned: news, a client's or partner's "
                      "business, a sector it serves or a menu label, not something it offers."),
        ("USED_INTERNALLY", "The organization practises or uses it for its own operations "
                            "(an internal process, policy, standard or job role), not as an "
                            "offer to customers."),
        ("UNCLEAR", "The state does not establish which."),
    ),
)  # fmt: skip


class Verdict(StrEnum):
    OFFERED = "OFFERED"
    MENTIONED = "MENTIONED"
    USED_INTERNALLY = "USED_INTERNALLY"
    UNCLEAR = "UNCLEAR"
    #: No usable judgment: the layer is off, over budget, failed or stayed uncertain.
    UNKNOWN = "UNKNOWN"


#: Verdicts that do not establish the activity (kept as negative classifications).
REJECTING = frozenset({Verdict.MENTIONED, Verdict.USED_INTERNALLY})

VERIFIED = "OFFERED"
UNVERIFIED = "UNVERIFIED"


class PageKind(StrEnum):
    HOME = "HOME"
    SERVICE = "SERVICE"
    ABOUT = "ABOUT"
    LEGAL = "LEGAL"
    CAREERS = "CAREERS"
    NEWS = "NEWS"
    OTHER = "OTHER"


_LANGUAGE_ROOT = re.compile(r"^[a-z]{2}(?:[-_][a-z]{2})?$", re.IGNORECASE)
_KIND_PATTERNS: tuple[tuple[PageKind, re.Pattern[str]], ...] = (
    (PageKind.CAREERS, re.compile(
        r"career|jobs?\b|vacanc|hiring|join-us|work-with-us|empleo|trabaja|vacantes|karriere|"
        r"stellen|carri[eè]re|emplois|lavora|carriera|carreira|vagas", re.IGNORECASE)),
    (PageKind.NEWS, re.compile(
        r"news|blog|press|media|insights|noticias|actualidad|prensa|aktuelles|presse|"
        r"actualit|notizie|not[ií]cias|imprensa", re.IGNORECASE)),
    (PageKind.ABOUT, re.compile(
        r"about|who-we-are|company|nosotros|quienes-somos|qui[eé]nes|empresa|ueber-uns|"
        r"uber-uns|unternehmen|qui-sommes|a-propos|chi-siamo|azienda|sobre|quem-somos",
        re.IGNORECASE)),
    (PageKind.SERVICE, re.compile(
        r"service|solution|product|what-we-do|offer|servicio|soluci|producto|leistung|"
        r"angebot|l[oö]sung|produkt|prestation|produit|servizi|soluzion|prodott|servi[cç]o|"
        r"solu[cç]|produto", re.IGNORECASE)),
)  # fmt: skip


def page_kind(page: PageReading) -> PageKind:
    """The kind of page, from its URL path, then its title. Deterministic; no model."""

    path = urlsplit(page.url).path
    if LEGAL_PAGE.search(path):
        return PageKind.LEGAL
    segments = [s for s in path.split("/") if s and not _LANGUAGE_ROOT.match(s)]
    if not segments:
        return PageKind.HOME
    for subject in ("/".join(segments), page.title):
        for kind, pattern in _KIND_PATTERNS:
            if pattern.search(subject):
                return kind
    return PageKind.OTHER


#: Neutral economic words AXIGNAL adds to its controlled vocabulary so a judgment can
#: tell an offer from a practice. A fixed developer-owned list, never site text.
_VERIFICATION_WORDS = frozenset(
    """
    we our us offer offers offering offerings provide provides providing sell sells
    deliver delivers use uses using used internal internally own lifecycle life cycle
    practice practices process processes policy policies standard standards secure
    security compliance quality employees staff team career careers job jobs vacancy
    vacancies hiring join apply news press blog article project projects partner
    partners client clients industry industries sector sectors expertise solution
    solutions development develop developing operations tools platform certified
    certification framework approach method methodology governance risk commitment
    ofrecemos ofrece ofrecer nuestro nuestra nuestros nuestras usamos utilizamos uso
    interno interna internos práctica prácticas proceso procesos política políticas
    norma normas seguridad calidad empleados equipo empleo vacantes noticias prensa
    proyecto proyectos socios cliente soluciones solución desarrollo desarrollamos
    ciclo vida
    wir unser unsere bieten bietet angebot nutzen verwenden intern interne prozess
    prozesse richtlinie richtlinien sicherheit qualität mitarbeiter karriere stellen
    aktuelles presse projekt projekte kunden branche branchen lösungen entwicklung
    lebenszyklus
    nous notre nos offrons proposons utilisons processus politique sécurité qualité
    collaborateurs équipe carrière emplois actualités projet partenaires secteur
    développement
    offriamo nostro nostra nostri utilizziamo processo processi politica sicurezza
    qualità dipendenti carriera notizie progetto progetti clienti settore soluzioni
    sviluppo
    oferecemos nosso nossos utilizamos segurança qualidade colaboradores carreira
    vagas notícias projeto projetos parceiros setor soluções desenvolvimento
    """.split()  # noqa: SIM905
)
_CATALOG_WORDS = frozenset(
    word
    for entry in CAPABILITY_LEXICON
    for text in (entry.label, *entry.terms)
    for word in re.findall(r"[^\W\d_]+", text.casefold())
)
#: Every word that may reach the provider in a verification state.
VERIFICATION_TERMS = _ROUTING_TERMS | _VERIFICATION_WORDS | _CATALOG_WORDS
_SAFE_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

MAX_PAGES = 6
MAX_MENTIONS_PER_PAGE = 3


def project(text: str) -> str:
    """Only AXIGNAL's controlled vocabulary leaves; every other token is dropped."""
    tokens = [
        token
        for match in _SAFE_WORD.finditer(text.casefold())
        if (token := match.group()) in VERIFICATION_TERMS
    ]
    return " ".join(tokens)[:STATE_CHARS_PER_PAGE]


def verification_state(
    finding: ActivityFinding, pages: Sequence[PageReading]
) -> dict[str, object] | None:
    """World-level state for one lexicon activity, or None if it has no catalog entry."""

    entry = next((e for e in CAPABILITY_LEXICON if e.capability_id == finding.activity_id), None)
    if entry is None:
        return None
    read: list[dict[str, object]] = []
    mentions: list[dict[str, object]] = []
    for index, page in enumerate(pages, 1):
        kind = page_kind(page)
        read.append({"page": f"[page-{index}]", "kind": kind.value})
        if len(mentions) >= MAX_PAGES:
            continue
        found = detect_capabilities(
            text=page.readable(),
            observation_id="page",
            source_ref="[page]",
            observed_at=page.observed_at,
            lexicon=(entry,),
        )
        if not found:
            continue
        mentions.append(
            {
                "page": f"[page-{index}]",
                "kind": kind.value,
                "around": [project(e.excerpt) for e in found[0].basis[:MAX_MENTIONS_PER_PAGE]],
            }
        )
    return {
        "representation": "controlled economic terms and page kinds, not page text",
        "site": "[site]",
        "activity": {"label": entry.label, "catalogTerms": list(entry.terms)},
        "pagesRead": read,
        "mentions": mentions,
    }


@dataclass(frozen=True, slots=True)
class VerificationRequest:
    finding: ActivityFinding
    batch: SemanticBatch
    page_kinds: tuple[str, ...]


def plan_verification(
    origin: str, pages: Sequence[PageReading], findings: Sequence[ActivityFinding]
) -> tuple[VerificationRequest, ...]:
    """One single-question batch per lexicon activity (schema.org types are declared)."""

    requests: list[VerificationRequest] = []
    for finding in findings:
        if finding.method is not ActivityMethod.LEXICON:
            continue
        state = verification_state(finding, pages)
        if state is None:
            continue
        mentions = state["mentions"]
        assert isinstance(mentions, list)
        kinds = tuple(sorted({str(m["kind"]) for m in mentions}))
        batch = SemanticBatch(
            f"activity-verification:{origin}:{finding.activity_id}", state, (ACTIVITY_OFFERED,)
        )
        requests.append(VerificationRequest(finding, batch, kinds))
    return tuple(requests)


@dataclass(frozen=True, slots=True)
class ActivityVerification:
    """One typed, non-authoritative judgment about one lexicon activity."""

    activity_id: str
    label: str
    verdict: Verdict
    page_kinds: tuple[str, ...]
    model: str | None
    reason: str | None = None
    question_id: str = ACTIVITY_OFFERED.question_id
    question_version: str = ACTIVITY_OFFERED.version

    @property
    def established(self) -> bool:
        return self.verdict not in REJECTING

    @property
    def decision(self) -> str:
        if self.verdict is Verdict.OFFERED:
            return f"ACTIVITY_VERIFIED:{self.activity_id}:OFFERED"
        if self.verdict in REJECTING:
            return f"ACTIVITY_REJECTED:{self.activity_id}:{self.verdict.value}"
        # UNCLEAR carries no reason; UNKNOWN names why no judgment is usable.
        return f"ACTIVITY_UNVERIFIED:{self.activity_id}:{self.reason or self.verdict.value}"

    def to_wire(self) -> dict[str, object]:
        return {
            "activityId": self.activity_id,
            "label": self.label,
            "verdict": self.verdict.value,
            "established": self.established,
            "pageKinds": list(self.page_kinds),
            "model": self.model,
            "reason": self.reason,
            "questionId": self.question_id,
            "questionVersion": self.question_version,
            "nonAuthoritative": True,
        }


def interpret_verification(
    requests: Sequence[VerificationRequest],
    outcomes: Mapping[str, CascadeOutcome] | None,
    *,
    unavailable: str = "NO_JUDGMENT",
) -> tuple[ActivityVerification, ...]:
    """Python reads each judgment; anything unusable is UNKNOWN, never a rejection."""

    out: list[ActivityVerification] = []
    for request in requests:
        verdict, reason, model = Verdict.UNKNOWN, unavailable, None
        outcome = None if outcomes is None else outcomes.get(request.batch.batch_id)
        judgment = None if outcome is None else outcome.judgments.get(ACTIVITY_OFFERED.question_id)
        if judgment is not None:
            answer = judgment.answer
            if judgment.usable and answer is not None and answer.top in ACTIVITY_OFFERED.labels:
                verdict, reason, model = Verdict(answer.top), "", answer.model
            else:
                reason = judgment.reason or judgment.resolution.value
        out.append(
            ActivityVerification(
                activity_id=request.finding.activity_id,
                label=request.finding.label,
                verdict=verdict,
                page_kinds=request.page_kinds,
                model=model,
                reason=reason or None,
            )
        )
    return tuple(out)


def compose(
    findings: Sequence[ActivityFinding], verifications: Sequence[ActivityVerification]
) -> tuple[ActivityFinding, ...]:
    """Deterministic composition: rejected lexicon activities are not established.

    Lexicon findings without a verification keep today's result, marked UNVERIFIED.
    Other methods (schema.org self-declaration, semantic judgment) are not verified here.
    """

    by_id = {v.activity_id: v for v in verifications}
    out: list[ActivityFinding] = []
    for finding in findings:
        if finding.method is not ActivityMethod.LEXICON:
            out.append(finding)
            continue
        verification = by_id.get(finding.activity_id)
        if verification is None:
            out.append(replace(finding, verification=UNVERIFIED))
        elif verification.established:
            status = VERIFIED if verification.verdict is Verdict.OFFERED else UNVERIFIED
            out.append(replace(finding, verification=status))
    return tuple(out)
