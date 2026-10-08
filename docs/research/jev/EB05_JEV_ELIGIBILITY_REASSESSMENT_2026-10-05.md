# EB-05 Jev Eligibility Reassessment — 2026-10-05

**Disposition:** `BLOCKED` for any Jev/provider evaluation or transmission.
**Scope:** Authority reassessment only. No provider was contacted or called; no
corpus records were created; no runtime, eligibility switch, or ADR-0048 gate
was changed.
**Authority:** MASTER Product Model → Engineering Constitution → ADR-0011,
ADR-0047, ADR-0048 → this dated reassessment. Open PR #18 remains unmerged and
is preserved as the P0-JEV-04A corpus research record.

## Finding

The blocker is not resolved by evidence available on 2026-10-05. The official
TypeSafe Master Customer Agreement (MCA) still creates an unresolved permission
question for the proposed EB-05 use:

- MCA §2.3(b) restricts using the Services or Output to develop (or facilitate
  development of) a similar or competing product or service.
- MCA §4.1 permits TypeSafe to process Input to perform the Services, including
  generating Output. It does not expressly address AXIGNAL's comparative
  evaluation or use of results in AXIGNAL product development.
- MCA §4.2 assigns TypeSafe's rights, if any, in Output to the customer. Output
  ownership does not itself grant permission to use the Services or Output for
  a purpose restricted by §2.3.
- MCA §4.3 permits use of Telemetry for service/product improvement. That
  separate permission does not resolve the customer's use of Services or
  Output under §2.3.
- MCA §5 makes the customer responsible for rights and permissions covering
  submitted Input. TypeSafe's no-model-weight-training sentence in §4.1 is not
  a no-processing promise and does not authorize AXIGNAL's evaluation use.

AXIGNAL's intended benchmark is part of developing and selecting components
for an economic-intelligence product. Whether AXIGNAL is a “similar or
competing” service for §2.3(b), and whether comparative evaluation for product
development is barred, cannot be settled by inference from public materials.
Therefore `MODEL_PROVIDER_TRANSMISSION_ALLOWED=UNKNOWN`, and UNKNOWN fails
closed under PR #18's rights gate and ADR-0048. This is an engineering
eligibility decision, not a legal opinion.

The current official [MCA](https://typesafe.ai/legal/mca) was reviewed on
2026-10-05 (the page states last updated 2026-09-23). The official
[DPA](https://typesafe.ai/legal/data-processing) governs Customer Personal Data
processing; it does not grant source-content rights or settle use of Output for
product development. The [API documentation](https://api.typesafe.ai/redoc)
describes the service interface, not a license exception to MCA §2.3. No
official documentation reviewed grants a benchmark or competitive-development
exception.

## Corpus rights are a separate gate

AXIGNAL-authored synthetic inputs can avoid third-party corpus licensing when
their authorship and provenance are recorded. The existing vNext synthetic
corpus can support local compiler, contract, answerability, deterministic
baseline, artifact, and offline replay checks under ADR-0011/0048. It is
structural test material; it does not establish natural-corpus provenance,
representative business reasoning, or statistical/real-world performance.

That route does **not** grant permission to send the inputs to Jev or use Jev
Output for AXIGNAL development. Source/input rights, provider transmission
permission, personal-data handling, and output-use permission are independent
gates. A fully AXIGNAL-owned synthetic corpus clears only its own content-rights
question. It cannot make the provider contract ambiguity disappear.

PR #18's proposed natural and procedural source routes also remain unaccepted.
The SEC route still lacks audited eligible yield and record-level
privacy/third-party filtering. The GLEIF route still lacks verified person-free
held-out yield and is necessarily procedural/self-confirming when the same
record supplies claim, evidence, and expected class. Public source availability
or CC0 source rights do not satisfy provider transmission permission.

## What may execute now

Without contacting a provider or transmitting data, EB-05 may continue only
local deterministic preparation already supported by the accepted decisions:

- compile the existing versioned AXIGNAL-owned synthetic fixtures;
- exercise DecisionContract/StateContract validation and pre-provider
  AnswerabilityGate behavior;
- run deterministic baselines, offline fixture replay, manifest/digest checks,
  and artifact validation;
- report that material as structural/implementation evidence only, with no
  Jev result, quality claim, corpus eligibility claim, or model comparison.

No natural/procedural golden corpus admission, held-out Jev benchmark, Jev API
or Playground use, paid/live provider call, input transmission, provider-output
capture, or product-selection conclusion based on Jev is authorized by this
reassessment. A lower-level task cannot bypass the gate.

## Exact evidence/action required to unblock

Before any Jev input transmission or output-based EB-05 evaluation, the
repository must contain all of the following:

1. **Provider permission:** an executed TypeSafe amendment/order or other
   contractually effective written authorization from an authorized TypeSafe
   representative that explicitly permits AXIGNAL to submit evaluation inputs
   and use Jev Outputs and derived comparative metrics for controlled evaluator
   benchmarking and AXIGNAL product/component development, notwithstanding
   MCA §2.3(b). A generic statement about no model-weight training, output
   ownership, service operation, or “evaluation” without the development use
   does not satisfy this item. AXIGNAL legal review must confirm that the
   writing is effective under the applicable agreement.
2. **Input and data handling:** confirm the applicable order/API terms, current
   DPA and subprocessors, permitted retention/replay, deletion, and reporting
   boundaries for the exact submitted content and output artifacts. Keep
   personal and sensitive data out unless separately cleared and necessary;
   the current corpus design requires person-free records.
3. **Corpus eligibility:** choose an explicitly bounded natural or procedural
   stratum; record record-level source rights and provenance; demonstrate the
   route's stated person-free eligible yield, answer-space coverage and
   leakage-safe held-out split; freeze labels before any provider call. For a
   natural route, preserve independent blinded human adjudication. For a
   synthetic/procedural route, disclose construction and circularity and limit
   claims to that controlled task.
4. **New authority decision:** update the rights manifest with primary evidence
   and issue a reviewed decision superseding the blocked disposition. Until
   that decision exists, `P0_JEV_04_LIVE_ELIGIBLE=NO`.

No vendor contact was made in this reassessment. The exact external action is
to obtain and review the contractual permission above; the repository must not
represent that action as complete before documentary evidence is admitted.

## Primary evidence consulted

- [TypeSafe Master Customer Agreement](https://typesafe.ai/legal/mca), §§2.3,
  4.1–4.4, 5; current page as observed 2026-10-05.
- [TypeSafe Data Processing Addendum](https://typesafe.ai/legal/data-processing),
  scope limited to personal data; current page as observed 2026-10-05.
- [TypeSafe API reference](https://api.typesafe.ai/redoc), interface reference;
  no additional use permission established.
- [PR #18 — P0-JEV-04A golden corpus authority](https://github.com/RafaLopezCode/Axignal/pull/18),
  open, unmerged at head `e877547f27a17f945df40ae546533fa68cf3ee79` when
  reviewed; `BLOCKED_NO_VALID_CORPUS`, no provider activity authorized.
- [ADR-0011](../../adr/ADR-0011-jev-structured-decision-reconciliation.md),
  [ADR-0047](../../adr/ADR-0047-provider-neutral-structured-evaluator-contract.md),
  [ADR-0048](../../adr/ADR-0048-evaluator-decision-lab-bakeoff-governance.md).

## Reconciliation — 2026-10-08: SUPERSEDED BY ADR-0090

**Scope of the supersession:** production eligibility of Jev as an internal semantic
provider in AXIGNAL. Everything above remains the record of the decision taken on
2026-10-05 and is not rewritten.

**What was stricter than necessary.** EB-05 treated the purpose of the work, developing
and selecting components for AXIGNAL, as possibly falling within MCA §2.3(b) and required
an additional written authorization from TypeSafe before any input transmission or
product use. EB-05 adopted a stricter internal fail-closed interpretation than the CTO now
considers necessary under the current MCA.

**The joint reading that replaces it.** §2.1 licenses using the Services and integrating
the API with Customer Applications; §2.2 defines a Customer Application as software the
Customer develops and operates for its End Users, which AXIGNAL is; §2.3(b) prohibits
distillation, training a model to imitate the output, and developing a similar or
competing product or service. Integrating Jev as a replaceable component of AXIGNAL is the
licensed use, not a competitor to TypeSafe. This is an internal CTO interpretation, not a
claim that TypeSafe granted any amendment or bespoke authorization; a Separate Agreement
or Order with other terms would control.

**Still forbidden:** using Jev outputs to train, fine-tune, distil or imitate any model;
using them as training or calibration data for an AXIGNAL replacement evaluator; exposing
or reselling Jev as a standalone service. Replacement evaluators may use only human,
AXIGNAL-owned or independently generated labels.

**Still required:** Input rights under MCA §5 (source provenance, reuse rights, privacy,
person-free state where applicable, DPA), non-authoritative outputs, Python policy
authority, budgets and the separate CTO activation step. The benchmark corpus questions
recorded above (rights, yield, human adjudication) still govern any evaluation corpus.
