"""Human First brief: where plausible demand exists, why AXIGNAL looked, what is unknown.

The brief answers the Brain's root question through one typed card per
opportunity family. Procurement has its own card, but it is one way of
discovering demand among several; families not yet observable say so honestly.
No router scores reach the reader. Every finding names its source, its last
observation time and the observed capability that made it relevant.
"""

from __future__ import annotations

from dataclasses import dataclass

from application.observation_intelligence.catalog import QUESTIONS, ROOT_QUESTION
from application.observation_intelligence.contracts import (
    OpportunityFamily,
    XeedObservationContext,
)
from application.observation_intelligence.coverage import CoverageState, EvidenceCoverageMap
from application.observation_intelligence.loop import LoopResult, OpportunityCandidate, StopReason
from application.observation_intelligence.registry import SourceRegistry
from application.observation_intelligence.strategy import ObservationStrategy

_COVERAGE_ES = {
    CoverageState.OBSERVED_CURRENT: "observado, actual",
    CoverageState.SEARCHED_NO_EVIDENCE: (
        "buscado sin resultados en las fuentes adoptadas (no implica ausencia)"
    ),
    CoverageState.STALE: "evidencia envejecida",
    CoverageState.UNKNOWN: "desconocido",
}
_STOP_ES = {
    StopReason.SUFFICIENT_EVIDENCE: (
        "Paramos porque la demanda encontrada ya está caracterizada para cada capacidad."
    ),
    StopReason.NO_MARGINAL_GAIN: "Paramos porque las últimas búsquedas no aportaban nada nuevo.",
    StopReason.BUDGET_EXHAUSTED: "Paramos al agotar el presupuesto de observación.",
    StopReason.SOURCES_EXHAUSTED: "Paramos porque no quedan fuentes que puedan aportar más.",
    StopReason.IRREDUCIBLE_WITH_ADOPTED_SOURCES: (
        "Paramos: el resto de preguntas necesita fuentes que aún no hemos adoptado."
    ),
}
_FAMILY_ES = {
    OpportunityFamily.PUBLIC_PROCUREMENT: ("Contratación pública", "licitaciones abiertas"),
    OpportunityFamily.PUBLIC_INVESTMENT: ("Inversión pública", "inversiones planificadas"),
    OpportunityFamily.GRANTS_AND_SUBSIDIES: ("Ayudas y subvenciones", "convocatorias"),
    OpportunityFamily.PLANNING_AND_PERMITS: ("Planeamiento y licencias", "proyectos"),
    OpportunityFamily.PRIVATE_PROJECT_SIGNALS: ("Proyectos privados", "proyectos anunciados"),
    OpportunityFamily.REGULATION_DRIVEN_DEMAND: ("Demanda regulatoria", "obligaciones"),
    OpportunityFamily.BUYER_EXPANSION_SIGNALS: ("Compradores en expansión", "señales"),
}


def _place(path: str) -> str:
    return path.rsplit("/", 1)[-1]


class CardStatus:
    FINDINGS = "FINDINGS"
    SEARCHED_NO_EVIDENCE = "SEARCHED_NO_EVIDENCE"
    NOT_YET_OBSERVABLE = "NOT_YET_OBSERVABLE"
    NOT_SEARCHED = "NOT_SEARCHED"


@dataclass(frozen=True, slots=True)
class FindingLine:
    title: str
    buyer: str | None
    place: str
    deadline: str | None
    why: str
    unknown: str
    source: str
    source_url: str
    last_observed: str
    match_basis: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OpportunityCard:
    """One opportunity family, as a typed unit Generative UI may compose; never a score."""

    family: OpportunityFamily
    title: str
    status: str
    summary: str
    findings: tuple[FindingLine, ...]
    coverage: tuple[str, ...]
    pending_sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HumanObservationBrief:
    question: str
    headline: str
    cards: tuple[OpportunityCard, ...]
    why_we_looked: tuple[str, ...]
    stop: str

    @property
    def findings(self) -> tuple[FindingLine, ...]:
        return tuple(f for card in self.cards for f in card.findings)

    def render_es(self) -> str:
        lines = [self.headline, ""]
        for card in self.cards:
            lines.append(f"[{card.title}] {card.summary}")
            for item in card.findings:
                lines += [
                    f"  • {item.title}",
                    f"    Comprador: {item.buyer or 'no publicado'} · Lugar: {item.place}"
                    + (f" · Plazo: {item.deadline}" if item.deadline else ""),
                    f"    Por qué aparece: {item.why}",
                    f"    Todavía no sabemos: {item.unknown}",
                    f"    Fuente: {item.source} ({item.source_url})"
                    f" · Última observación: {item.last_observed}",
                ]
            lines += [f"    {line}" for line in card.coverage]
        lines += ["", "¿Por qué AXIGNAL miró ahí?", *[f"- {x}" for x in self.why_we_looked]]
        return "\n".join([*lines, "", self.stop])


def _finding(
    candidate: OpportunityCandidate,
    context: XeedObservationContext,
    source_name: str,
) -> FindingLine:
    capabilities = {c.capability_id: c for c in context.capabilities}
    searched_for = next(
        (r.split(":", 1)[1] for r in candidate.why_looked if r.startswith("XEED_CAPABILITY:")),
        None,
    )
    capability = capabilities[
        searched_for if searched_for in candidate.capability_ids else candidate.capability_ids[0]
    ]
    record = candidate.record
    adjacency = (
        " Es una categoría vecina que compradores de la zona ya adjudicaron junto a ella."
        if "ADJACENT_CODE_REVEALED_BY_AWARDS" in candidate.match_basis
        else ""
    )
    return FindingLine(
        title=record.title,
        buyer=record.buyer_name,
        place=", ".join(sorted({_place(p.code) for p in record.places})),
        deadline=record.deadline,
        why=(
            f"AXIGNAL observó que la empresa declara «{capability.basis[0].excerpt}» y este "
            f"comprador pide {', '.join(c.code for c in candidate.matched_codes)} "
            f"({capability.label}).{adjacency}"
        ),
        unknown=", ".join(candidate.missing_context) + ".",
        source=source_name,
        source_url=record.source_url,
        last_observed=candidate.observed_at.date().isoformat(),
        match_basis=candidate.match_basis,
    )


def build_brief(
    *,
    context: XeedObservationContext,
    strategy: ObservationStrategy,
    result: LoopResult,
    coverage: EvidenceCoverageMap,
    registry: SourceRegistry | None = None,
) -> HumanObservationBrief:
    registry = registry or SourceRegistry()
    sources = {source.source_id: source for source in registry.sources}
    questions = {question.question_id: question for question in QUESTIONS}
    asked = {question_id for question_id, _ in strategy.questions}
    cards: list[OpportunityCard] = []
    for family in OpportunityFamily:
        family_questions = [
            q for q in QUESTIONS if q.opportunity_family is family and q.question_id in asked
        ]
        if not family_questions:
            continue
        title, noun = _FAMILY_ES[family]
        findings = tuple(
            _finding(c, context, sources[c.record.source_id].name)
            for c in result.candidates
            if c.opportunity_family is family
        )
        coverage_lines: list[str] = []
        states: set[CoverageState] = set()
        for question in family_questions:
            for market in context.markets:
                if not market.roles & question.market_roles:
                    continue
                state = coverage.state(question.question_id, market.geography, as_of=context.as_of)
                states.add(state)
                coverage_lines.append(
                    f"{_place(market.geography.code)} · {question.text} → {_COVERAGE_ES[state]}"
                )
        family_gaps = [
            g for g in strategy.gaps if g.question_id in {q.question_id for q in family_questions}
        ]
        pending = tuple(sorted({s for g in family_gaps for s in g.candidate_sources}))
        if findings:
            status = CardStatus.FINDINGS
            summary = f"{len(findings)} {noun} compatibles con las capacidades observadas."
        elif states & {CoverageState.SEARCHED_NO_EVIDENCE, CoverageState.OBSERVED_CURRENT}:
            status = CardStatus.SEARCHED_NO_EVIDENCE
            summary = (
                "Buscado en las fuentes adoptadas sin resultados; no implica que no exista demanda."
            )
        elif family_gaps and len({(g.question_id, g.market) for g in family_gaps}) == len(
            coverage_lines
        ):
            status = CardStatus.NOT_YET_OBSERVABLE
            summary = "Todavía no observable: ninguna fuente adoptada cubre esta vía" + (
                f" (en evaluación: {', '.join(pending)})." if pending else "."
            )
        else:
            status = CardStatus.NOT_SEARCHED
            summary = "Aún no observado en esta ejecución."
        cards.append(
            OpportunityCard(
                family, title, status, summary, findings, tuple(coverage_lines), pending
            )
        )

    why = []
    for step in result.steps:
        action = step.action
        source = sources[action.source_id]
        question = questions[action.question_id]
        if action.parent_action_id is None:
            why.append(
                f"«{question.text}» necesita "
                f"{', '.join(sorted(k.value for k in action.query.capabilities))}; "
                f"{source.name} lo publica para {_place(action.market.code)} y permite buscar por "
                f"{', '.join(sorted(source.classification_systems)) or 'texto'}."
            )
        else:
            region = _place(
                next(r for r in action.reasons if r.startswith("REGION:")).split(":")[1]
            )
            buyers = next(r for r in action.reasons if r.startswith("BUYERS:")).removeprefix(
                "BUYERS:"
            )
            why.append(
                f"Profundizamos en {region} porque varias adjudicaciones recientes se "
                f"concentraban allí (compradores: {buyers.replace('|', ', ')})."
            )
    with_findings = [c for c in cards if c.findings]
    headline = (
        f"Encontramos {sum(len(c.findings) for c in with_findings)} señales de demanda plausible "
        "para las capacidades observadas: "
        + "; ".join(f"{len(c.findings)} en {c.title.lower()}" for c in with_findings)
        + f". {len(cards) - len(with_findings)} vías más siguen abiertas."
        if with_findings
        else "Todavía no hemos encontrado demanda plausible en las fuentes adoptadas."
    )
    return HumanObservationBrief(
        question=ROOT_QUESTION,
        headline=headline,
        cards=tuple(cards),
        why_we_looked=tuple(why),
        stop=_STOP_ES[result.stop_reason],
    )
