"""Before/after benchmark for AXENT context, tokens, grounding and cost.

before: the naive Luna integration — the full authorized reading as JSON plus
        the full transcript in every turn, citing object ids.
after:  tenant-grounded AXENT — resolved intent, governed retrieval, bounded
        pack, verified claims, deterministic answers and abstention.

Both see only tenant A's authorized reading (authorization is identical); the
difference is how much of it is sent and how claims are grounded.

Offline (default): a scripted reasoner and estimated tokens (chars/4).
Live: --live --env-file PATH runs gpt-6-luna and records the provider's usage.
Prices are arguments, never constants: --input-per-million --output-per-million.

Run: uv run --group research-canary-live python -m tests.axent.benchmark [--live --env-file F] [--out F]
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from application.axent.grounded import (
    ANSWER_SCHEMA,
    AnswerRoute,
    AxentService,
    CostRates,
    GroundedReasoner,
    ReasoningRequest,
    estimate_tokens,
)
from application.axent.grounded.cost import avoided_cost, projections
from tests.axent.fixtures import (
    FOCUS_A,
    NOW,
    TENANT_A,
    AuthorizingReader,
    ScriptedLuna,
    opportunity,
    reading,
)

QUERIES: tuple[tuple[str, str], ...] = (
    ("A_seo", "¿Cómo está mi SEO?"),
    ("B_reputation", "¿Qué dicen de nosotros?"),
    ("C_opportunities", "¿Qué oportunidades hay?"),
    ("D_relationships", "¿Qué clientes aparecen?"),
    ("E_change", "¿Qué ha cambiado?"),
    ("F_unknown", "¿Qué no sabemos todavía?"),
    ("G_cross_tenant", "¿Qué oportunidades tiene FrioNord en Lyon?"),
    ("H_why", "¿Por qué dices que la oportunidad de Getafe encaja?"),
    ("I_follow_up", "¿Y en Francia?"),
    ("J_count", "¿Cuántas oportunidades potenciales hay?"),
)

NAIVE_SYSTEM = (
    "You are AXENT, the assistant of AXIGNAL, an economic intelligence product. AXIGNAL observes "
    "public evidence about organizations and keeps an epistemic state for each statement: OBSERVED "
    "requires admitted evidence, POTENTIAL is possible but unconfirmed, UNKNOWN is not false, "
    "CURRENT/STALE/HISTORICAL describe currentness. Never mix tenants. Answer the user's question "
    "using the organization reading below. Cite the ids of the objects you rely on in refs. "
    "Answer in the user's language."
)


def tenant_reading() -> dict[str, Any]:
    """A realistic subscriber reading: opportunities in two markets, pages, signals, history."""

    opportunities = [
        opportunity(f"opp-es-{i}", title, buyer=buyer, observed=NOW - timedelta(days=i % 5 + 1))
        for i, (title, buyer) in enumerate(
            [
                (
                    "Instalación fotovoltaica de autoconsumo en edificios municipales",
                    "Ayuntamiento de Getafe",
                ),
                (
                    "Suministro e instalación de módulos fotovoltaicos en depuradoras",
                    "EMACSA Córdoba",
                ),
                (
                    "Sustitución de cubierta con integración fotovoltaica en mercado municipal",
                    "Ayuntamiento de Alicante",
                ),
                ("Instalación fotovoltaica en mercados municipales", "Diputación de Valencia"),
                ("Mantenimiento de instalaciones eléctricas en colegios", "Comunidad de Madrid"),
                ("Autoconsumo fotovoltaico en polideportivos", "Ayuntamiento de Elche"),
                ("Baja tensión en edificios administrativos", "Junta de Andalucía"),
                ("Marquesinas solares en aparcamientos públicos", "Ayuntamiento de Murcia"),
            ]
        )
    ]
    sources = [
        {
            "id": f"obs:page:{name}",
            "title": f"https://solartec.example/{name}",
            "observedAt": (NOW - timedelta(days=3)).isoformat(),
            "currentness": "CURRENT",
            "limitation": "One authorized source observation; coverage beyond this document remains unknown.",
            "sourceRef": f"https://solartec.example/{name}",
        }
        for name in ("servicios", "proyectos", "empresa", "contacto")
    ]
    projection = reading(
        xeed=FOCUS_A,
        organization="Solartec Levante",
        opportunities=opportunities,
        extra_sources=sources,
    )
    projection["nodes"] = [
        {
            "id": f"xignal:{i}",
            "title": title,
            "interpretation": text,
            "whyAttention": "Public buyers in its region publish compatible demand repeatedly.",
            "uncertainty": "Eligibility, capacity and pricing are not observed.",
            "epistemicState": "POTENTIAL",
            "currentness": "CURRENT",
            "observedAt": (NOW - timedelta(days=2)).isoformat(),
            "sourceRefs": ["https://solartec.example/"],
            "unknowns": ["eligibility", "available capacity"],
            "evidenceNarrative": {
                "steps": [{"label": text, "sourceRef": "https://solartec.example/"}]
            },
        }
        for i, (title, text) in enumerate(
            [
                (
                    "Demanda pública compatible",
                    "Compradores públicos publican demanda compatible con su capacidad declarada.",
                ),
                (
                    "Concentración regional",
                    "Las adjudicaciones se concentran en la Comunitat Valenciana.",
                ),
                (
                    "Capacidad declarada",
                    "Declara instalaciones fotovoltaicas de autoconsumo y baja tensión.",
                ),
            ]
        )
    ]
    projection["today"] = {
        "items": [
            {
                "xignalId": "xignal:0",
                "whatChanged": "Nueva licitación compatible publicada por la Diputación de Valencia",
                "whyItMatters": "Comprador recurrente con adjudicaciones previas compatibles.",
                "observedAt": (NOW - timedelta(days=1)).isoformat(),
            }
        ]
    }
    projection["temporalHistory"] = {
        "items": [
            {
                "observationId": f"obs:hist:{i}",
                "sourceRef": "https://solartec.example/",
                "sourceType": "PUBLIC_WEBSITE",
                "observedAt": (NOW - timedelta(days=30 - i * 7)).isoformat(),
                "currentness": "CURRENT" if i > 2 else "STALE",
                "normalizedStateChanged": i == 3,
            }
            for i in range(5)
        ]
    }
    return projection


@dataclass
class NaiveLuna:
    """Before: full reading + full transcript each turn."""

    reasoner: GroundedReasoner
    transcript: list[str] = field(default_factory=list)

    def ask(self, question: str, projection: dict[str, Any]) -> dict[str, Any]:
        reading_json = json.dumps(projection, ensure_ascii=False, indent=1)
        history = "\n".join(self.transcript)
        user = (
            f"ORGANIZATION READING:\n{reading_json}\n\nCONVERSATION:\n{history}\n\nUSER: {question}"
        )
        started = time.monotonic()
        result = self.reasoner.reason(
            ReasoningRequest("naive", NAIVE_SYSTEM, user, ANSWER_SCHEMA, 500)
        )
        latency = int((time.monotonic() - started) * 1000)
        claims = result.payload.get("claims")
        claims = claims if isinstance(claims, list) else []
        known_ids = set(_ids(projection))
        grounded = sum(
            1
            for c in claims
            if isinstance(c, dict)
            and c.get("refs")
            and all(r in known_ids for r in c.get("refs", []))
        )
        answer = " ".join(str(c.get("text", "")) for c in claims if isinstance(c, dict))
        self.transcript += [f"USER: {question}", f"AXENT: {answer}"]
        return {
            "input_tokens": result.input_tokens or estimate_tokens(NAIVE_SYSTEM + user),
            "output_tokens": result.output_tokens or 0,
            "model_calls": 1,
            "claims": len(claims),
            "grounded_claims": grounded,
            "ungrounded_claims": len(claims) - grounded,
            "latency_ms": latency,
            "context_chars": len(user),
            "answer": answer,
        }


def _ids(value: object) -> list[str]:
    if isinstance(value, dict):
        own = [str(value["id"])] if isinstance(value.get("id"), str) else []
        return own + [i for v in value.values() for i in _ids(v)]
    if isinstance(value, list):
        return [i for v in value for i in _ids(v)]
    return []


class NaiveScripted:
    """Offline stand-in for the naive call: cites the first opportunity ids it sees."""

    model = "offline-scripted"

    def reason(self, request: ReasoningRequest) -> Any:
        from application.axent.grounded import ReasoningResult

        ids = [
            i
            for i in _ids(
                json.loads(
                    request.user.split("ORGANIZATION READING:\n")[1].split("\n\nCONVERSATION")[0]
                )
            )
            if i.startswith("opp-")
        ][:3]
        payload = {
            "claims": [{"text": f"Opportunity {i}", "refs": [i]} for i in ids],
            "unknowns": [],
            "insufficient_evidence": False,
        }
        return ReasoningResult(payload, self.model, None, 60, 1)


def run(reasoner: GroundedReasoner, naive_reasoner: GroundedReasoner | Any) -> dict[str, Any]:
    projection = tenant_reading()
    reader = AuthorizingReader()
    reader.grant(TENANT_A, FOCUS_A, projection)
    service = AxentService(reader=reader, clock=lambda: NOW, reasoner=reasoner)
    naive = NaiveLuna(naive_reasoner)
    rows = []
    memory: object = None
    for key, question in QUERIES:
        before = naive.ask(question, projection)
        turn = service.ask(TENANT_A, FOCUS_A, question, memory=memory)
        memory = turn.memory.to_wire()
        m = turn.metrics
        after_input = m.input_tokens
        rows.append(
            {
                "query": key,
                "question": question,
                "before": {k: v for k, v in before.items() if k != "answer"},
                "after": {
                    "route": m.route.value,
                    "input_tokens": after_input,
                    "output_tokens": m.output_tokens,
                    "model_calls": m.model_calls,
                    "measured_tokens": m.measured,
                    "corpus_items": m.corpus_items,
                    "in_scope_items": m.in_scope_items,
                    "sent_items": m.sent_items,
                    "evidence_tokens": m.evidence_tokens,
                    "claims": m.claims,
                    "grounded_claims": m.claims,
                    "dropped_ungrounded_claims": m.dropped_claims,
                    "abstained": m.route is AnswerRoute.ABSTAINED,
                    "research_requested": turn.answer.research is not None,
                    "latency_ms": m.latency_ms,
                    "answer": turn.answer.answer[:300],
                },
                "before_answer": before["answer"][:300],
            }
        )
    return {"rows": rows}


def summarize(result: dict[str, Any], rates: CostRates, turns_per_month: int) -> dict[str, Any]:
    rows = result["rows"]

    def total(side: str, key: str) -> int:
        return sum(int(r[side][key]) for r in rows)

    n = len(rows)
    before_in, after_in = total("before", "input_tokens"), total("after", "input_tokens")
    before_out, after_out = total("before", "output_tokens"), total("after", "output_tokens")
    return {
        "turns": n,
        "before": {
            "input_tokens": before_in,
            "output_tokens": before_out,
            "model_calls": total("before", "model_calls"),
            "grounded_claims": total("before", "grounded_claims"),
            "ungrounded_claims": total("before", "ungrounded_claims"),
            "latency_ms": total("before", "latency_ms"),
            "cost": projections(
                input_tokens=before_in / n,
                output_tokens=before_out / n,
                rates=rates,
                turns_per_subscriber_month=turns_per_month,
            ),
        },
        "after": {
            "input_tokens": after_in,
            "output_tokens": after_out,
            "model_calls": total("after", "model_calls"),
            "grounded_claims": total("after", "grounded_claims"),
            "ungrounded_claims_dropped": total("after", "dropped_ungrounded_claims"),
            "abstentions": sum(r["after"]["abstained"] for r in rows),
            "research_requests": sum(r["after"]["research_requested"] for r in rows),
            "latency_ms": total("after", "latency_ms"),
            "cost": projections(
                input_tokens=after_in / n,
                output_tokens=after_out / n,
                rates=rates,
                turns_per_subscriber_month=turns_per_month,
            ),
        },
        "input_tokens_avoided": before_in - after_in,
        "cost_per_1m_tokens_avoided": f"{avoided_cost(1_000_000, rates):.4f} {rates.currency}",
        "rates": {
            "input_per_million": str(rates.input_per_million),
            "output_per_million": str(rates.output_per_million),
            "currency": rates.currency,
        },
        "turns_per_subscriber_month": turns_per_month,
    }


def _load_env(path: str) -> None:
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            if name.strip() == "OPENAI_API_KEY":
                os.environ["OPENAI_API_KEY"] = value.strip()


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--input-per-million", default="0")
    parser.add_argument("--output-per-million", default="0")
    parser.add_argument("--currency", default="EUR")
    parser.add_argument("--turns-per-month", type=int, default=200)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    rates = CostRates(
        Decimal(args.input_per_million), Decimal(args.output_per_million), args.currency
    )
    if args.live:
        if args.env_file:
            _load_env(args.env_file)
        from cognition.axent_reasoner import CognitiveGroundedReasoner
        from cognition.providers.luna_responses import LunaResponsesProvider
        from cognition.router.router import ModelRouter

        router = ModelRouter([LunaResponsesProvider(authorized_model=args.model)])
        reasoner: Any = CognitiveGroundedReasoner(router, model=args.model)
        naive_reasoner: Any = CognitiveGroundedReasoner(router, model=args.model)
    else:
        reasoner, naive_reasoner = ScriptedLuna(), NaiveScripted()
    result = run(reasoner, naive_reasoner)
    output = {
        "mode": "live" if args.live else "offline",
        "model": args.model if args.live else "scripted",
        **result,
        "summary": summarize(result, rates, args.turns_per_month),
    }
    text = json.dumps(output, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
