# 062 — Semantic judgment layer: Python, Jev and Luna together

**Status:** IMPLEMENTED (first consumer), deployable, off by default · **Date:** 2026-10-08 ·
**Decision:** [ADR-0090](../../docs/adr/ADR-0090-semantic-judgment-layer.md) (Accepted) ·
**Authority:** MASTER §8, §13–14, §27–29, §53; ADR-0047, ADR-0089; spec 059.

## Goal

Get the most economic and functional value from TypeSafe's Jev by combining it with
Python and GPT-6 Luna, each doing only what it is best at, without letting any model
become authority.

## Contractual boundary (ADR-0090)

| Use | Status |
| --- | --- |
| Jev inside AXIGNAL, integrated as a Customer Application component (MCA §§2.1–2.2) | ALLOWED |
| Internal typed semantic judgments and the AXIGNAL outputs derived from them | ALLOWED |
| Distillation, imitation training, training or fine-tuning any model on Jev outputs | FORBIDDEN |
| Jev outputs as training or calibration data for an AXIGNAL replacement evaluator | FORBIDDEN |
| Exposing or reselling Jev as a standalone, TypeSafe-competing service | FORBIDDEN |
| Input rights, privacy, provenance, DPA (MCA §5) | STILL GOVERNED |
| Model authority over truth | NEVER |

This is an internal CTO interpretation of the current MCA, not a TypeSafe amendment; a
Separate Agreement or Order with other terms would control. Replacement evaluators use
only human, AXIGNAL-owned or independently generated labels. A guard test fails if Jev
judgment memory gains any consumer beyond the cascade's composition.

**Input rights.** Only candidates that already passed the display gate (registered,
adopted and routable source, documented reuse rights, matching market scope, safe public
URL) are sent; state is the public notice and the capability class, person-free and
never tenant-private. An E2E test proves a notice failing provenance is never judged.

## Who does what

| Work | Owner | Why |
| --- | --- | --- |
| Exact lookups, codes, places, dates, deadlines, arithmetic, counts, rights, policy, composition, the final decision | **Python** | Deterministic, auditable, free; Jev 1.13 is documented as weak at numbers, dates, counting and indirection |
| Many narrow typed judgments over the same public state (fit, mode, binding, polarity, support, materiality, relevance ranking) | **Jev** (System One) | One call answers all questions over a state read once; input-only price; ~150 ms; returns distributions and confidence that tell Python when to trust, escalate or abstain |
| Uncertain judgments that matter, multi-step reasoning, language generation (AXENT answers, explanations, briefs) | **Luna** | Reasons and writes; consulted only when the cascade says so, within a call budget |

The cascade (`application/semantic_layer/cascade.py`): Python filters → exact memory →
one Jev call per batch → escalate only declared, uncertain questions to Luna → Python
decides. Over budget abstains (UNKNOWN). A provider failure is UNKNOWN for that batch.

## Economics (no figure here is a measured production cost yet)

| Item | Figure | Kind | Basis |
| --- | --- | --- | --- |
| Jev 1.13 price | USD 0.042 per million input tokens, output free | vendor-published | docs.typesafe.ai/models, reviewed 2026-10-08 |
| Any other Jev model | UNKNOWN | — | no governed price record; the ledger reports tokens, not cost |
| Luna price | USD 0.125 input / 0.50 output per million | operator-configured | `AXIGNAL_AXENT_*_PER_MILLION` |
| Demand screen batch | ≤ 434 input tokens | measured locally (estimator) | Getafe PV notice + PV capability class + 2 questions, 3 characters per token; Jev reports the real count |
| Per Focus, 200 batches a day, no reuse | 2.6 M tokens/month ≈ USD 0.11 | estimated | `monthly_system_one_usd` |
| Same with 50 % reuse across Foci | ≈ USD 0.05 | estimated | shared world memory |
| Luna escalations, 1 in 10 batches (~900 in / 40 out) | ≈ USD 0.08 per month | estimated | operator prices |
| Default run budget | 2 M Jev tokens ≈ USD 0.084 per run | operator-configured | `AXIGNAL_SEMANTIC_RUN_TOKEN_BUDGET` |
| Latency 154 ms (Jev) vs 860 ms (GPT-5.6 Luna) | ~5× | third-party published | OpenRouter Ori Eval via madewithjev.com |

Against €4.95 per additional Focus this is a few percent of revenue. Versus Luna the input
saving is about 3×; the vendor's 40–400× compares Jev with frontier models and does not
apply here. The strategic advantage is: typed probability distributions and confidence
(a cheap first pass Python can trust, escalate or abstain on); one state, many questions
per call; lower latency; shared cross-Focus reuse, which compounds with subscribers (the
agency case, MASTER §27.2); and controlled Luna escalation within a call budget.

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

## Deployment

- **Dependency:** dependency group `semantic-layer-live` (`typesafe-sdk==0.7.1`), installed
  in `subscriber-runtime.Dockerfile`; `decision-lab-live` includes it (one pin). The SDK is
  imported lazily: disabled composition imports nothing and reads no credential.
- **Secret:** `compose.semantic.override.yml` mounts `typesafe_api_key` into the runtime
  only, at `/run/secrets/typesafe_api_key`, from
  `${AXIGNAL_TYPESAFE_API_KEY_HOST_FILE:-/etc/axignal/secrets/typesafe_api_key}` (root-owned,
  0440, group `AXIGNAL_TYPESAFE_SECRET_GID`). It is a separate overlay so deployments without
  the key keep working; experience and landing never receive it.

## Activation (separate CTO step after merge)

1. Place the key on the host; add `compose.semantic.override.yml` to the runtime compose.
2. In the subscriber configuration set `AXIGNAL_SEMANTIC_LAYER_ENABLED=true`, keep
   `AXIGNAL_SEMANTIC_REASONING_CALLS=0` first.
3. Watch `semanticLayer.usage` and `relevanceFiltered.SEMANTIC_UNRELATED` per run; enable
   escalation after AXIGNAL-owned labels confirm the thresholds.

## Not changed

Production configuration (`AXIGNAL_SEMANTIC_LAYER_ENABLED=false`), the deterministic
gate's authority, AXENT, the decision lab (its TypeSafe adapter still sends one question
per call; the production adapter batches), the MASTER, prices, and any canonical writer.
