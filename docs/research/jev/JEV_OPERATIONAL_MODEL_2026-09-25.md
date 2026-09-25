# Jev operational model — 2026-09-25

**Phase:** A — independent Jev reconstruction, completed before AXIGNAL Jev architecture inspection.  
**Evidence rule:** source IDs resolve in [JEV_SOURCE_LEDGER_2026-09-25.md](JEV_SOURCE_LEDGER_2026-09-25.md). Official fact, independent observation, AXIGNAL derivation and unknown are never interchangeable.  
**Scope:** public official material available on 2026-09-25 plus explicitly labeled ecosystem observations. No live calls were made.

## 1. Executive operational model

Jev is a typed semantic judgment component. A caller supplies a state and typed questions; Jev returns answers constrained by the question's answer form. This is an interface and judgment boundary, not an evidence-acquisition system, proof engine, canonical authority, policy executor or general-purpose generator (O2–O6, O9).

Reliable use therefore depends on whether the state contains enough relevant, discriminating information for the requested judgment; whether the question and answer space express the intended semantics; whether the result is evaluated on representative labeled outcomes; and whether deterministic code applies explicit policy. “Question-state answerability,” “state sufficiency,” and “minimum sufficient state” are useful AXIGNAL-derived controls, not official named Jev API guarantees (D1).

```text
application constructs evidence-bearing state
        + typed question / answer space
        → Jev judgment (typed value and available probabilities)
        → deterministic composition and explicit workflow policy
        → action only within domain authority
```

Typed output prevents an out-of-schema free-form answer from being the result. It does not guarantee that the selected answer is true, supported by supplied evidence, calibrated for a target population, safe to act on, or authorized by domain policy. Keep these five things distinct:

| Layer | Meaning | What it does not prove |
|---|---|---|
| Interface guarantee | Response has the declared answer shape | Semantic correctness |
| Semantic judgment | Model's judgment of supplied content under question wording | Truth independent of that content |
| Probabilistic information | Distribution/value returned for that typed judgment | AXIGNAL-domain calibration or action utility |
| Truth / evidence | Claim's actual status with provenance and scope | Not established by a typed answer |
| Workflow/domain authority | Rules permitting a downstream action or canonical admission | Never conferred by Jev output |

## 2. Source authority methodology

The source ledger follows CTO tiers. Current official docs and first-party SDK/skill outrank third-party clients and reports. Cookbooks are official descriptions of patterns, but cookbook outcomes remain author-reported experiments. Mutable `main`, mutable aliases, and current hosted docs are time-sensitive. Full retry/usage schema and immutable current skill head were not retrievable and remain UNKNOWN (U2). See ledger for exact access date, version, commit/tag where visible, and limitations.

## 3. State theory

Official docs define state as the content being evaluated, and permit strings, JSON objects, or arrays of text. Named fields make multi-part content easier to refer to in questions (O2). State is not merely an ID for remote evidence. To decide whether a claim is supported, the relevant claim and source passage must be present or deterministically retrieved and inserted; official citation-checking example sends both claim and section (O12).

Operational consequences:

- **Relevance and sufficiency:** supply content a competent evaluator needs; neither “more” nor “less” is universally better. TypeSafe's weak-spot guidance calls out filtering large irrelevant state, and examples show exact tasks can need full relevant context (O11/O12).
- **Structured state:** use named fields for claim, candidate entity, comparison entity, source passage, provenance, timestamp, and known missing/contradictory facts where these are part of the judgment. This schema recommendation is an AXIGNAL derivation, not a mandatory wire schema (D1).
- **Identifiers and references:** an identifier can distinguish records but does not supply the referenced semantics. Resolve it to evidence deterministically when the judgment needs that evidence (O12; D3).
- **Metadata/time:** include scope, date, source identity and status when they change what a statement means; exact date ordering/currentness checks remain code where determinable (O11; D3).
- **Negative and missing evidence:** represent “not found,” “not supplied,” “contradicted,” and “false” separately. Omission does not imply false (D3).
- **Contradictions:** preserve both statements with source/time instead of flattening conflict into one value; ask a bounded question about conflict only if that is the target (D1).
- **Size/repetition/versioning:** docs publish context limits, but no official universal minimum sufficient state or dilution threshold was found. Hash/version the exact state in experiments (O10; D2).

**Question-state answerability:** official materials recommend sufficient relevant state but do not establish a named answerability gate, formal information-requirement schema, or guaranteed preflight API. **AXIGNAL_DERIVATION:** before interpreting an evaluation score, check whether the target can be judged from the exact serialized state. A minimum sufficient state is a per-task empirical construct, not a universal model rule (D1/U3).

## 4. Question theory

Question instructions define the semantic judgment; Choice options/criteria, Score levels, or a Noul proposition define what answers mean. Put relevant input facts in state and refer to them explicitly. Use one coherent judgment per question, but do not reduce a naturally relational judgment to context-free atomization. Options should be clear and distinct; add `none`, `other`, unknown, or review where the set is not exhaustive or missing input is plausible (O3/O4/O6; installed official skill).

- Split a complex question when dimensions have separate evidence requirements, labels, error costs, or downstream uses. Keep them together when the relationship itself is the target.
- Several questions may share state when each is independently answerable from that same evidence. Fan-out answers cannot observe each other (O7).
- A second request should wait if the first answer determines a retrieval, newly constructed state, candidate set, or conditional next step. Use code for that dependency; do not pretend questions are sequential inside fan-out (O7/O9).
- Compose outputs in code when applying weights, thresholds, vetoes, missing-answer behavior, disagreement, escalation, or action (O8/O9).
- Version semantic wording, criteria, options, and examples. Test equivalent phrasings; no official guarantee of wording invariance was found (U1).

## 5. Primitive theory

| Primitive | Input semantics | Output / probability | Confidence | Appropriate use / limits |
|---|---|---|---|---|
| Choice | One answer from a fixed, unordered set with descriptions/criteria | Chosen option and distribution over options; docs say up to 255 options | Included as statistic of distribution shape | Exclusive bounded classification/selection. Cannot produce an omitted answer; do not use for independently coexisting labels. Include no-match/review as needed (O3). |
| Score | One dimension described by ordered levels (docs recommend 2–10) | Level distribution and expected position, potentially between levels | Included as statistic of distribution shape | Graded ordered judgment. Do not assume equal intervals or compare unrelated rubrics as calibrated quantities (O4). |
| Noul | A yes/no proposition | Probability assigned to “yes,” 0–1 | No separate confidence field | One binary proposition; use one per independently applicable label when multi-label. A value near 0.5 is probability parity, not intensity (O5/O6). |

Selection framework: choose Choice for exclusive enumerated outcomes; one Noul per independent binary proposition; Score for an ordered graded dimension. Use deterministic code for exact calculations, parsing, sorting, equality and policy. These types are not interchangeable wrappers (O3–O5/O9).

## 6. Probability and confidence semantics

Choice probabilities and Score level probabilities describe the model's distribution over the declared answers. Their confidence field summarizes distribution concentration/spread; it is not an independent correctness certificate. Noul's number is the probability of “yes” and has no distinct confidence field. Flat distributions indicate less concentration. Concentrated distributions can still be wrong. Confidence must not be interpreted as workflow correctness, factual truth, evidence sufficiency, or permission (O3–O6).

The official confidence material recommends handling uncertainty with `I don't know`/review/escalation patterns and says thresholds depend on stakes and domain; a universal threshold is unsupported. Evaluate probability quality and action outcomes on the target data. Separate repeatability, calibration, accuracy, selective risk and workflow utility. Agreement across related questions is not independent evidence (O6/O7; D2/U3).

## 7. Composition

Keep four owners distinct:

1. **Jev judgment:** answer to a supplied question over supplied state.
2. **Code composition:** deterministic combination, weights, comparisons, missingness and veto rules.
3. **Workflow policy:** thresholds, review, escalation and execution eligibility.
4. **Domain authority:** who/what may establish canonical facts or admit evidence.

Independent parallel judgments can fan out; dependent evidence gathering is sequential. Composite-score cookbook composes dimensions in application code; no universal weights are supplied (O7–O9). Keep raw answers so policy can be replayed. Handle missing, invalid, contradictory and abstained responses explicitly. Never convert UNKNOWN to FALSE or sum correlated probabilities as independent.

## 8. Routing and action selection

Official material supports typed judgments used by application code and describes decision use cases; a Jev answer alone is not an execution authorization (O1/O9). A bounded action Choice can select among code-provided legal candidates, but code must revalidate candidate identity, current constraints, authorization and side effects (D3). Classification/ranking/routing are candidates for evaluation, not blanket recommendations. Exact eligibility, safety invariants, permissions, and final authority stay deterministic/domain-owned.

Community E1/E2 show routing with explicit confidence review paths and bounded choices; these demonstrate independent implementation patterns only. Their sample data and thresholds do not generalize.

## 9. Speculative fan-out

Fan-out asks independent questions against shared state in one request; questions do not see each other's answers (O7). It is useful for speculative branches if state supports each branch and code discards irrelevant outputs. It can reduce orchestration latency but still adds input/question tokens; actual costs and latency must be measured (O7/O10). Do not fan out a question that presumes another answer or that requires evidence not in shared state.

## 10. Research / autoresearch patterns

The official autoresearch cookbook proposes features/questions, then evaluates downstream predictive utility with a separate labeled dataset, held-out split, and external ML metric (O14). This illustrates separation between semantic feature generation and the objective/evaluation owner. Its reported wine-review dataset/results are cookbook claims, not independently reproduced performance, and do not validate AXIGNAL research planning or canonical admission.

## 11. Entity alignment

Official cookbook demonstrates pairwise record comparison with an ordered same/related/different judgment and separate field-level judgments (O13). Candidate records and their relevant fields are state. Identity errors are asymmetric by consequence: false merge may be worse than false split; policy should route uncertain cases to review and be measured against labeled pairs. Cookbook-reported Magellan results are not AXIGNAL performance evidence.

## 12. Citation / evidence checking

Official recipe first finds exact text in code and then asks Jev to judge a claim with the claim and retrieved section together (O12). Exact quote retrieval is not itself semantic support. Preserve source boundaries and provenance; a quote may contradict, support, or be unrelated. Do not ask Jev to judge evidence from an ID alone. Report exact evidence and semantic judgment separately; evidence admission remains policy-controlled.

## 13. Context compaction / relevance

Current official weak-spot guidance recommends reducing irrelevant state; community recipes explore transcript pruning (O11/E3). Selective pruning can remove needed context, so compare against gold answers, include hard cases, and preserve verbatim retained content/provenance. Compaction, summarization, and relevance filtering are different operations; no official guarantee that one Jev judgment can safely compact arbitrary context was found (U1/U3).

## 14. Failure taxonomy

See [JEV_FAILURE_TAXONOMY_2026-09-25.md](JEV_FAILURE_TAXONOMY_2026-09-25.md). It distinguishes state omission, identifiers without semantic content, ambiguity/noise/contradiction/missingness, question/answer-space/primitive problems, model error, composition/policy error, provider/transport failure, adversarial inputs, and evaluation defects. This is AXIGNAL-derived operational discipline, not official API vocabulary.

## 15. Evaluation methodology

See [JEV_EVALUATION_METHODOLOGY_2026-09-25.md](JEV_EVALUATION_METHODOLOGY_2026-09-25.md). Validate answerability and labels before quality scoring; freeze the estimand, split data without leakage, control state/question/primitive/provider, report class and selective metrics, calibration, repeatability, cost and latency, retain immutable manifests, and attribute errors before calling them model failures. Official docs say evaluate on the target domain; precise acceptance limits must be domain-derived (O6/O9/U3).

## 16. Cost model

Official model docs as accessed 2026-09-25 report Jev `jev-1.13.0`, a mutable `jev-latest` alias, 64k request context with a lower state-plus-longest-question constraint of 32k, and input pricing of $0.042 per million tokens with output free (O10). Treat as dated official page facts, not quote/availability guarantees. Questions sharing one state, retries, gateway markup, tokens, and provider behavior affect total economics; exact request usage and retry billing semantics are UNKNOWN (U2). Do not optimize cost ahead of semantic answerability.

## 17. Versioning / reproducibility

The Python SDK release page reports v0.7.1 on 2026-09-21 at commit prefix `0ffd094`; v0.7.0 changed serialization from msgspec to Pydantic and added a response-model option; v0.6.0 changed Score criteria shape (O15). Pin SDK and record schema. Record resolved model ID, provider, API version/endpoint, request data hash, question revision, code/evaluator version and response metadata. `jev-latest` is mutable; gateway aliases may differ (O10/O15; E1/E4). A release tag and short SHA are the only source pin visible in reviewed release page; full immutable tree SHA remains UNKNOWN.

## 18. Security and trust boundaries

Treat state as potentially untrusted content: it may contain adversarial instructions, private data or injected text. Keep credentials server-side, use least privilege, minimize sent data, and separate source content from application instructions. The official API key issue fix notes early validation and excluding the key from logged exceptions (O15); this reinforces secret hygiene but does not replace local controls. Validate response and candidate IDs before effects. No Jev response creates authority to perform an action (O9/O11/D3).

## 19. Anti-pattern catalog

- Sending IDs where the semantic evidence is needed.
- Treating valid typed output as truthful or calibrated for an untested domain.
- Treating Choice confidence as correctness, Noul as intensity, Score as exact measurement, or one threshold as universal.
- Asking Jev to calculate exact values, dates, or equality better handled in code.
- Hiding domain policy inside question wording or weights with no explicit owner.
- Using mutually exclusive Choice for multi-label outcomes, omitting no-match, or presenting incomplete candidates.
- Counting correlated judgments as multiple independent confirmations.
- Evaluating on ambiguous/unanswerable examples as if they tested model capability.
- Using synthetic cookbook scores as deployment evidence.
- Treating mutable aliases, gateway IDs, or unpinned dependencies as reproducible.
- Letting a semantic judgment mutate canonical state or authorize irreversible action.

## 20. Ecosystem / Jevable patterns

No Jevable-first-party project was independently identified from reviewed sources; reviewed third-party repositories are inventoried in the source ledger. E1 is an OpenRouter-backed cookbook with small labeled samples and openly stated limits. E2 is an independent recipe library with offline fixtures and application-owned result handling. E3 reports benchmark/linter work; E4 explicitly distinguishes run provider. E5 is an independent Haskell client. Use them to discover testable patterns, not vendor semantics or performance guarantees.

## 21. Unknowns

- Exact API retry defaults, retry-after behavior, idempotency, billing on retries, and usage schema: UNKNOWN (U2).
- Exact calibration guarantee and the populations/metrics behind broad product claims: UNKNOWN (U1).
- Current official Agent Skill immutable head SHA and complete content hash: UNKNOWN (O16).
- Universal state sufficiency / answerability interface or minimum-state criterion: not established by reviewed official sources (O2/O9; D1).
- Gateway equivalence, current service availability/quotas, and model alias pinning beyond displayed docs: UNKNOWN (O10/E4).
- Target AXIGNAL task performance, threshold utility, and acceptable error rates: REQUIRES_EXPERIMENT (U3).

## 22. Unproven hypotheses

- An AXIGNAL information-requirements contract plus answerability preflight may prevent structurally unanswerable judgments (UNPROVEN_HYPOTHESIS; to be tested).
- Minimal sufficient state may improve some tasks by removing distractions, while harming tasks needing relational context (UNPROVEN_HYPOTHESIS; per-task ablation required).
- Review bands may improve net utility for selected high-cost decisions (UNPROVEN_HYPOTHESIS; costs and reviewer capacity required).
- Separate targeted questions may improve detection where a single broad score obscures a critical condition (community E1 reports such a case; AXIGNAL transfer is unproven).

## 23. Source ledger and freeze

Source details, tiers, access date, freshness, and limitations are in [JEV_SOURCE_LEDGER_2026-09-25.md](JEV_SOURCE_LEDGER_2026-09-25.md). Pattern, failure, and evaluation companions are linked above. Red-team review corrected the following risks before freeze: confidence is not correctness; official cookbook reports are not benchmarks; lower context is not always better; IDs do not stand in for evidence; and typed actions do not confer authority. No Phase B AXIGNAL architecture was used to construct this independent model.

The freeze hash is SHA-256 over this file's exact UTF-8 bytes **excluding only the final `PHASE_A_FROZEN_SHA256=` line**, avoiding an impossible self-referential digest. No other normalization is applied. Phase A companions are frozen with this model; later Phase B findings must not backfit them. Any necessary reopening must add a separate, explicit reason and source trace.

PHASE_A_FROZEN_SHA256=0e5607b0a2829fec5b03a3242e4e633c58bedf5befaea1d49ed8b98420854945
