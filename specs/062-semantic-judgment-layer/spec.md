# 062 — Semantic judgment layer: Python, Jev and Luna together

**Status:** IMPLEMENTED (first consumer), off by default · **Date:** 2026-10-08 ·
**Decision:** [ADR-0090](../../docs/adr/ADR-0090-semantic-judgment-layer.md) ·
**Authority:** MASTER §8, §13–14, §27–29, §53; ADR-0047, ADR-0089; spec 059.

## Goal

Get the most economic and functional value from TypeSafe's Jev by combining it with
Python and GPT-6 Luna, each doing only what it is best at, without letting any model
become authority.

## Who does what

| Work | Owner | Why |
| --- | --- | --- |
| Exact lookups, codes, places, dates, deadlines, arithmetic, counts, rights, policy, composition, the final decision | **Python** | Deterministic, auditable, free; Jev 1.13 is documented as weak at numbers, dates, counting and indirection |
| Many narrow typed judgments over the same public state (fit, mode, binding, polarity, support, materiality, relevance ranking) | **Jev** (System One) | One call answers all questions over a state read once; input-only price; ~150 ms; returns distributions and confidence that tell Python when to trust, escalate or abstain |
| Uncertain judgments that matter, multi-step reasoning, language generation (AXENT answers, explanations, briefs) | **Luna** | Reasons and writes; consulted only when the cascade says so, within a call budget |

The cascade (`application/semantic_layer/cascade.py`): Python filters → exact memory →
one Jev call per batch → escalate only declared, uncertain questions to Luna → Python
decides. Over budget abstains (UNKNOWN). A provider failure is UNKNOWN for that batch.

## Economics (planning figures, to be replaced by measured usage)

| Item | Figure | Basis |
| --- | --- | --- |
| Jev price | USD 0.042 per million input tokens, output free | docs.typesafe.ai/models, 2026-10-08 |
| Luna price | USD 0.125 input / 0.50 output per million | operator configuration (`AXIGNAL_AXENT_*_PER_MILLION`) |
| Demand screen batch | ≤ 434 input tokens (Getafe PV notice + PV capability class + 2 questions) | conservative estimate (3 characters per token); Jev reports the real count |
| Per Focus, 200 candidate batches a day, no reuse | 2.6 M tokens/month ≈ **USD 0.11** | `monthly_system_one_usd` |
| Same with 50 % reuse across Foci | ≈ **USD 0.05** | shared world memory |
| Luna escalations, 1 in 10 batches (~900 in / 40 out) | ≈ **USD 0.08**/month | operator prices |
| Default run budget | 2 M Jev tokens ≈ USD 0.084 per run | `AXIGNAL_SEMANTIC_RUN_TOKEN_BUDGET` |

Against €4.95 per additional Focus this is a few percent of revenue. Versus Luna alone the
input saving is about 3×, not the vendor's 40–400× (that compares Jev with frontier
models). The larger gains are elsewhere: calibrated distributions make a cheap first pass
safe to trust or escalate; one call answers every question about a state; latency is
about 5× lower (OpenRouter's published median: 154 ms against 860 ms); and reuse of
world-level judgments across Foci compounds with the number of subscribers, which is the
agency case (MASTER §27.2).

## First consumer: semantic demand screen

`application/observation_intelligence/semantic_screen.py`, wired into the subscriber
opportunity projection (`semantic_screen` on `SubscriberEconomicRuntime`):

- **State:** the public notice (title, buyer, classification codes) and the capability
  class (lexicon label, terms, buyer jobs). Nothing tenant-private.
- **Questions:** `tender_capability_fit` (Score: UNRELATED, ADJACENT, PARTIAL, CORE) and
  `tender_delivery_mode` (Choice: CUSTOMER_SITE, SHIPPED, REMOTE_OR_DIGITAL, UNCLEAR).
- **Effects:** confidently UNRELATED demand is counted as `SEMANTIC_UNRELATED`; the judged
  delivery mode feeds the gate (a mode the channel does not evidence downgrades reach to
  UNRESOLVED, never to "cannot"); surfaced demand is ordered CORE, PARTIAL, ADJACENT. Each
  opportunity carries `semanticScreen` with every resolution and the evaluator; the
  snapshot carries `semanticLayer` with judgment counts and the cost ledger.
- **Never:** create a candidate, widen reach, mark anything OBSERVED, or act on doubt.

## Next consumers (designed, not built here)

1. **Global reach interpretation** (spec 059 `derive.py`): Python finds sentences with
   place candidates; Jev decides binding (this activity, whole organization, not a service
   area), polarity (included, excluded, only) and basis (service area, premises, expansion,
   origin only). Replaces Spanish-only cue lists; multilingual accuracy must be measured.
2. **AXENT grounding:** Jev Noul "is this sentence supported by the cited excerpt" on each
   Luna answer before display; Jev ranks corpus items so Luna reads less.
3. **Organization admission** (spec 052): Choice among registry candidates, abstain on
   low confidence.
4. **Change materiality** (continuity/T12): Noul "does this change alter capability or
   reach?" before recomputing.
5. **Digital representation:** mention, citation or recommendation in AI answers.
6. **Tender requirements:** certification and lot requirements from tender documents
   after Python chunking (regulatory family, spec 059 T9).

## Measurement before trust

A human-labelled set of public TED notices × capability classes (fit and delivery mode),
person-free, never derived from Jev outputs. Report precision of `SEMANTIC_UNRELATED`
(a CORE tender wrongly filtered is the critical error), calibration of fit confidence,
escalation rate, Luna agreement, cost and latency per run; tune `CascadePolicy` only from
that set. Open-weight evaluators may be compared on the same port and trained only on
these human labels, never on Jev outputs (MCA §2.3(b)).

## Activation (CTO)

1. Accept ADR-0090 (supersedes the EB-05 production eligibility disposition).
2. Mount the key as `/run/secrets/typesafe_api_key`; set
   `AXIGNAL_SEMANTIC_LAYER_ENABLED=true`, keep `AXIGNAL_SEMANTIC_REASONING_CALLS=0` first.
3. Watch `semanticLayer.usage` and `relevanceFiltered.SEMANTIC_UNRELATED` per run; enable
   escalation after the labelled set confirms the thresholds.

## Not changed

Production configuration (`AXIGNAL_SEMANTIC_LAYER_ENABLED=false`), the deterministic
gate's authority, AXENT, the decision lab (its TypeSafe adapter still sends one question
per call; the production adapter batches), the MASTER, prices, and any canonical writer.
