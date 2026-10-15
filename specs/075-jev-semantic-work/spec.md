# Feature Specification: Jev where it is most useful

**Feature Branch**: `spec/jev-semantic-work`

**Created**: 2026-10-15

**Status**: Draft

**Input**: CTO, 2026-10-15: "Sácale el mayor provecho a Jev y donde sea más útil ponlo a
trabajar." Context: the flywheel truth set (11 organizations) showed that the deterministic
layers decide alone where a narrow semantic judgment would decide better. Jev made 6 judgments
in production in two days, because it only runs when the lexicon finds nothing.

## Authority

- **MASTER §56.13 (Universal Semantic Typing Layer).** Many narrow typed questions over rich
  state. Python composes a Typed Judgment Vector. Each dimension preserves NONE/UNKNOWN.
  TYPED != TRUE.
- **MASTER §56.14.** Jev is a replaceable semantic typing provider. It receives rich state plus
  narrow governed questions and is never asked to recompute deterministic facts.
- **MASTER §56.17.** A Jev probability or confidence never becomes a Señal meter. UNKNOWN is
  never rendered as FALSE.
- **ADR-0090 and its 2026-10-13 amendment:**
  - The layer is provider-neutral, with a cascade, budgets and judgment memory.
  - Input rights are a separate gate. Public demand that may be displayed may be sent.
    Website text needs per-site rights; AXIGNAL's controlled vocabulary does not.
  - Jev outputs are never used to train, calibrate or distil another evaluator.
- **ADR-0048.** An evaluator's use is promoted only on measured, governed evidence.
- **Spec 062.** The demand screen already exists: `tender_capability_fit` (CORE / PARTIAL /
  ADJACENT / UNRELATED) and `tender_delivery_mode`.

No MASTER change is needed. Nothing here creates candidates, widens reach, strengthens an
epistemic state or writes canonical truth.

## Where Jev is most useful (inventory, ranked)

| # | Decision point | Decides today | Measured failure | Jev's value |
|---|---|---|---|---|
| 1 | Is this open call about the activity? (live demand list, what subscribers see) | CPV codes plus the buyer's main object (#269) | Truth set: Zitron matched to building ventilation works; AXIGNAL to foster-family and welfare calls | The question already exists (spec 062) but is wired only to the legacy projection |
| 2 | Does the organization offer this activity, or only mention or use it? (activity reading) | Lexicon hit = activity | Securitas read as "software development" from "secure software development lifecycle" (#274) | A CHOICE (OFFERED / MENTIONED / USED_INTERNALLY / UNCLEAR) over controlled vocabulary plus page kind |
| 3 | Which activity, when the lexicon finds none | Jev, but only sector and CPV division | Ferrovial: no activity found | Already in place; it gains from #2's richer state |
| 4 | Later, specified separately: relationship role and direction (buyers, customers), event and change type, regulation applicability | Rules | Not yet measured by the truth set | Typed Judgment Vector dimensions (§56.13) |

This feature covers #1 and #2. #4 is recorded so that it is specified only once the truth set
measures it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The demand a subscriber sees is judged for fit (Priority: P1)

A subscriber's open calls are matched by codes. Jev's fit judgment (spec 062) now also types
each one, and that list is what the subscriber reads.

**Why this priority**: Demand is the most acted-upon list. The judgment and its contract
already exist; only the wiring and the precomputation are missing. The 2 remaining truth-set
failures are demand.

**Independent Test**: Run the self-check on the truth set with and without fit judgments, and
compare demand precision per organization.

**Acceptance Scenarios**:

1. **Given** an open call matched by code, **When** Jev judged its fit for that capability as
   UNRELATED, **Then** it is not listed as an opportunity. It is counted and reachable as
   "set aside by fit", and is never deleted.
2. **Given** a call judged ADJACENT or PARTIAL, **When** the list is shown, **Then** it carries
   that label and is ordered after CORE calls, alongside the buyer's main or additional
   classification (#269).
3. **Given** no judgment yet (new call, layer off, budget exhausted or provider failure),
   **When** the list is shown, **Then** the call appears exactly as today. UNKNOWN is never
   UNRELATED.
4. **Given** the same call and capability for many subscribers, **When** they read their
   demand, **Then** one world-level judgment serves all of them (judgment memory) and no read
   waits for a provider.

### User Story 2 - An activity is established only when the site offers it (Priority: P2)

Each activity the lexicon detects is verified by one narrow question: does the site offer it,
merely mention it, or use it internally?

**Why this priority**: Activity routes demand, industry, buyers, regulation and sector context.
A wrong activity propagates to every family.

**Independent Test**: Truth-set and golden-set activity precision, with and without
verification.

**Acceptance Scenarios**:

1. **Given** "secure software development lifecycle" on a policy page of a security company,
   **When** verified, **Then** software development is MENTIONED or USED_INTERNALLY and is not
   established.
2. **Given** a site without content rights, **When** verified, **Then** only AXIGNAL's
   controlled vocabulary around the match, the page kind (service, about, legal, careers, news)
   and anonymous page ids reach the provider. The rights test still proves this.
3. **Given** verification is unavailable, **When** the site is read, **Then** the lexicon
   result stands as today, marked unverified.

### Edge Cases

- A call judged UNRELATED for one capability may be CORE for another of the same organization.
  It is listed by its best fit.
- A judgment from an older question version or model is a memory miss. It is judged again,
  never reused.
- An inconsistent judgment, such as a CORE fit on a call whose main object is
  ADDITIONAL-classified, keeps both labels. Python never merges them into one score.
- A provider outage or budget exhaustion means no judgment: lists behave as today, and the
  ledger says why.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Fit judgments for (open call, capability) pairs that the code match produces MUST
  be computed off the read path, during or after daily ingestion. They are world-level and
  stored in judgment memory keyed by call, capability, question version and model.
- **FR-002**: Live demand MUST read fit judgments from memory only. A missing judgment leaves
  the call as today.
- **FR-003**: UNRELATED calls MUST be set aside, counted and inspectable, never deleted.
  ADJACENT and PARTIAL are labelled and ordered after CORE. No combined score is shown.
- **FR-004**: Activity verification MUST ask one CHOICE question per detected activity
  (OFFERED / MENTIONED / USED_INTERNALLY / UNCLEAR). Only OFFERED, or the lexicon result when no
  judgment exists, establishes the activity. MENTIONED and USED_INTERNALLY are recorded as
  negative classifications (MASTER §56.13), not discarded.
- **FR-005**: The activity state MUST stay within ADR-0090 and its amendment: controlled
  vocabulary, page kind and anonymous page ids, with no site text unless rights exist.
- **FR-006**: Budgets MUST be per run and per day, in the cost ledger with versioned prices.
  Over budget means abstention.
- **FR-007**: Every judgment shown MUST say it is an evaluator's judgment (instrument, model,
  question version), never a fact, with its source.
- **FR-008**: Promotion MUST be measured. The self-check reports demand and activity precision
  with and without judgments. A use is enabled by default only if it does not lower any
  organization's accuracy and raises the set's. Labels are AXIGNAL-owned, never Jev output.
- **FR-009**: No Jev output may be stored or exported as training or calibration data for any
  other evaluator (ADR-0090).

### Key Entities

- **FitJudgment**: call, capability, label (CORE / PARTIAL / ADJACENT / UNRELATED / UNKNOWN),
  model, question version, judged-at time. World-level.
- **ActivityVerification**: organization reading, capability, label (OFFERED / MENTIONED /
  USED_INTERNALLY / UNCLEAR / UNKNOWN), page kind, model, question version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Truth-set demand precision rises. The two open demand failures (Zitron, AXIGNAL)
  are resolved, either set aside or labelled, without new demand false negatives.
- **SC-002**: No organization's self-check accuracy drops, and the set's accuracy rises.
- **SC-003**: Golden-set (30 organizations) activity precision does not drop, and lexicon false
  positives of the Securitas kind are rejected.
- **SC-004**: No subscriber read waits on a provider. The p95 read latency of live demand is
  unchanged.
- **SC-005**: Daily Jev spend is reported in the ledger and stays within budget. Judgments per
  day rise from single digits to the number of new (call, capability) pairs.

## Assumptions

- The semantic layer stays enabled in production with its current key, model `jev-1.13.0` and
  budgets. Raising budgets is a CTO step.
- Open calls from TED and PLACSP are public demand that may be displayed. Their title, buyer
  and classification may be sent (ADR-0090).
- The truth set and the golden set are the measurement.
