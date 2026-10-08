# ADR-0090: Semantic judgment layer (Python, System One, reasoning)

- **Status:** Accepted (CTO decision)
- **Date:** 2026-10-08
- **Supersedes:** the EB-05 eligibility disposition (`docs/research/jev/EB05_JEV_ELIGIBILITY_REASSESSMENT_2026-10-05.md`) for the use of Jev as an internal semantic provider in AXIGNAL. EB-05 stays in the record as the 2026-10-05 decision.
- **Authority:** MASTER §8 (demand-materialized reuse), §13–14 (models are replaceable and not authority), §27–29 (price per Focus, computational budget), §53 (typed questions, no universal score); Constitution; ADR-0006, ADR-0011, ADR-0047, ADR-0048, ADR-0089; spec 062.

## Context

AXIGNAL had two cognitive extremes in production: deterministic cues (cheap, auditable, low recall, local vocabularies) and Luna (`gpt-6-luna`, grounded answers). TypeSafe's Jev answers narrow typed questions over supplied state, charges only input tokens (vendor-published: USD 0.042 per million for `jev-1.13.0`) and reads the state once for many questions. It was unused: the only live run (P0-JEV-03) sent state without the claim or evidence, and EB-05 then failed closed on MCA §2.3(b), requiring additional written authorization from TypeSafe before any product use.

## Contractual decision

The current TypeSafe Master Customer Agreement (updated 2026-09-23) already licenses the integration described here:

- **§2.1** grants a licence to access and use the Services and to integrate the API with Customer Applications.
- **§2.2** defines a Customer Application as software developed and operated by the Customer for the benefit of its End Users. AXIGNAL is such an application.
- **§2.3(b)** prohibits using the Services or Output to perform model distillation, to train a model to imitate the Services' output, or to develop or facilitate a similar or competing product or service.

Read together, integrating Jev as a replaceable component of AXIGNAL, a vertical economic-intelligence application, is the use §§2.1–2.2 license; it is not developing a competitor to TypeSafe. Reading §2.3(b) as a general bar on using Jev while developing a Customer Application would make §§2.1–2.2 incoherent.

This is an internal CTO contractual and engineering interpretation. It is not a representation that TypeSafe supplied an amendment or a bespoke written authorization; none exists in the record. If AXIGNAL is governed by a Separate Agreement or an Order with conflicting or additional terms, those terms control.

### Permanent invariants

Allowed:

```
Jev API → internal component of AXIGNAL → typed semantic judgments
        → product functionality → derived subscriber-facing AXIGNAL outputs
```

Forbidden:

```
Jev output → training of another model
Jev output → fine-tuning of another model
Jev output → distillation
Jev output → imitation
Jev output → training or calibration data for an AXIGNAL replacement evaluator
Jev        → standalone service exposed or resold as a TypeSafe replacement
```

Open-weight or other evaluators may be evaluated or trained only with human labels, AXIGNAL-owned labels or independently generated ground truth, never with Jev outputs.

**Input rights remain a separate gate (MCA §5).** The Customer stays responsible for the rights, disclosures, notices, consents and permissions over submitted Input. Provider eligibility never widens what may be sent: only demand whose source provenance, scope and reuse rights already qualify it for display is transmitted; state is world-level and person-free; tenant-private context is never sent; DPA obligations apply.

**Output remains non-authoritative.** Model output ≠ truth; a Jev judgment is not a FAXT, not evidence and not a canonical write; Jev confidence is not a canonical probability. Python owns deterministic mechanisms, policy, budgets, thresholds, final effects, EvidenceAdmission boundaries and canonical writes. Jev is a replaceable semantic judgment provider; Luna is a replaceable reasoning escalation provider.

No additional rights flag exists for Jev: the boundaries are `AXIGNAL_SEMANTIC_LAYER_ENABLED`, credential availability, budgets, provider configuration, typed semantic contracts and Python policy authority, plus the invariants and tests above.

## Architectural decision

1. **One provider-neutral layer** (`application/semantic_layer`): versioned questions (Choice, Score, Noul), world-level JSON state, typed non-authoritative answers, a cost ledger with versioned prices, per-run budgets, and an exact judgment memory keyed by state fingerprint, question version and evaluator model.
2. **A cascade with Python at both ends.** Python compiles state and filters first. System One answers every question of a batch in one call. Questions declared escalable that stay uncertain go to the reasoning model, one call per batch, within a call budget. Python decides what any answer may change. Over budget abstains (UNKNOWN); a provider failure is UNKNOWN for that batch only; state over the documented limits is refused, never truncated.
3. **Replaceable adapters.** `cognition/providers/typesafe_system_one.py` is the only module importing the TypeSafe SDK, lazily. Luna serves a `SEMANTIC_DECISION` job with a strict JSON schema whose values are the declared labels or `UNKNOWN`; quoted state is data, never instructions.
4. **Reuse is the economic engine.** World-level state lets one judgment serve every Focus that meets the same tender. Model or question changes are misses and are judged again.
5. **First consumer: the semantic demand screen** (spec 062). It may filter confidently unrelated demand (`SEMANTIC_UNRELATED`, counted, not deleted), supply the delivery mode the Economic Relevance Gate needs (a mode the channel does not evidence downgrades reach to `UNRESOLVED_REACH`), and order surfaced demand by judged fit. It never creates candidates, widens reach or strengthens an epistemic state.
6. **Deployable, off by default.** The subscriber runtime image installs the `semantic-layer-live` group (`typesafe-sdk==0.7.1`); `compose.semantic.override.yml` mounts the key into the runtime only at `/run/secrets/typesafe_api_key`. Activation (`AXIGNAL_SEMANTIC_LAYER_ENABLED=true`, budget, optional Luna call budget) is a separate CTO step.

## Consequences

- Semantic depth per Focus costs cents a month (estimated, spec 062), small against €4.95 per additional Focus.
- Thresholds are policy, not truth; they must be evaluated on AXIGNAL-owned labels before being trusted.
- Known Jev 1.13 weaknesses (vendor-published: counting, dates, arithmetic, indirection, large noisy state) stay in Python by construction.
- TypeSafe adjusts rate limits dynamically; the SDK's bounded backoff applies and failures degrade to UNKNOWN.
