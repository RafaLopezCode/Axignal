"""The subscriber wire for one turn: the existing RuntimeAnswer shape plus grounding."""

from __future__ import annotations

from application.axent.grounded.answer import AnswerRoute
from application.axent.grounded.copy import text
from application.axent.grounded.intent import QuestionKind
from application.axent.grounded.service import AxentTurn

_INTENT = {
    QuestionKind.OVERVIEW: "known",
    QuestionKind.COUNT: "known",
    QuestionKind.CHANGE: "changed",
    QuestionKind.WHY: "why",
    QuestionKind.UNKNOWNS: "unknown",
    QuestionKind.HOW_KNOWN: "evidence",
}


def runtime_answer_wire(turn: AxentTurn, *, locale: str) -> dict[str, object]:
    answer, metrics, kind = turn.answer, turn.metrics, turn.kind

    def labelled(claim_text: str, epistemic: str, currentness: str) -> str:
        prefix = [text(epistemic, locale)] if epistemic in {"POTENTIAL", "DECLARED"} else []
        if currentness in {"STALE", "HISTORICAL"}:
            prefix.append(text("STALE", locale))
        return " · ".join([*prefix, claim_text])

    evidence = list(answer.evidence)
    research = answer.research
    return {
        "organizationId": turn.organization_id,
        "contextId": answer.xeed_id,
        "signalIds": [e.item_id for e in evidence if e.kind == "SIGNAL"],
        "intent": "research"
        if research is not None and answer.route is AnswerRoute.ABSTAINED
        else _INTENT[kind],
        "summary": answer.answer,
        "known": [labelled(c.text, c.epistemic, c.currentness) for c in answer.claims],
        "openQuestions": list(answer.unknowns),
        "evidenceBasis": [e.label for e in evidence if e.kind != "GAP"],
        "researchPlan": [] if research is None else [answer.answer.split(". ")[-1]],
        "passages": [c.text for c in answer.claims],
        "action": "unknown"
        if answer.route is AnswerRoute.ABSTAINED
        else "evidence"
        if kind is QuestionKind.HOW_KNOWN
        else "focus",
        "sourceRefs": sorted({e.source_ref for e in evidence if e.source_ref}),
        "observedAt": sorted({e.observed_at for e in evidence if e.observed_at}),
        "currentness": sorted({e.currentness for e in evidence}),
        "grounding": {
            "route": answer.route.value,
            "asOf": answer.as_of.isoformat(),
            "families": list(answer.families),
            "claims": [
                {
                    "text": c.text,
                    "epistemic": c.epistemic,
                    "currentness": c.currentness,
                    "evidence": list(c.refs),
                }
                for c in answer.claims
            ],
            "evidence": [
                {
                    "ref": e.ref,
                    "label": e.label,
                    "kind": e.kind,
                    "epistemic": e.epistemic,
                    "currentness": e.currentness,
                    "observedAt": e.observed_at,
                    "source": e.source_ref,
                    "sourceLabel": e.source_label,
                }
                for e in evidence
            ],
            "research": None if research is None else research.to_wire(),
            "droppedClaims": answer.dropped_claims,
            "modelCalls": metrics.model_calls,
        },
        "memory": turn.memory.to_wire(),
    }
