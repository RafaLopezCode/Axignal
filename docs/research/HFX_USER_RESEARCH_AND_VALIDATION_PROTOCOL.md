# HFX User Research & Validation Protocol

**Status:** research protocol; pre-implementation  
**Authority:** subordinate to MASTER §55, Constitution and ADR-0016/0017  
**Purpose:** validate comprehension, epistemic understanding, navigation, evidence access, resumption, multi-client safety and accessibility.  
**No participants have been recruited and no UX result is claimed.**

## Research question

Can AXIGNAL present the same specialist-grade economic intelligence so people
with different domain fluency can identify what matters, understand its limits,
navigate by meaning, inspect evidence, resume investigations and reach expert
methodology without changing canonical truth?

## Participant groups

Recruit by task and expertise, not organization size alone: non-specialist SME
owner/operator; sales/business development; marketing generalist; SEO/GEO
specialist; agency/consultant; analyst/strategy professional. Include varied
ages, data/numeracy fluency, device use and accessibility needs. Include people
with cognitive and learning disabilities in appropriate research, with
informed consent, accessible materials, compensation and reasonable
accommodation. No participant represents an entire category.

## Study sequence

### 0 — Concept and vocabulary interviews

Without teaching AXIGNAL terms, ask how participants describe opportunity,
evidence, uncertainty, representation, comparison and trust. Capture natural
language, mental models and terminology burden.

### 1 — Information architecture

Use open/hybrid card sorting, tree testing and semantic-grouping interviews to
test human question families. Do not expose backend packages as the assumed
answer. Preserve Today / Explore / Evolution / Evidence / Ask AXENT as a
comparison baseline.

### 2 — Low-fidelity meaning and navigation

Compare meaning before metrics, semantic depth and direct jumps, horizontal
relationship navigation, focus/context, joined meaning with dependency trace
and “Why am I seeing this?”. Hold underlying facts and epistemic state constant
across variants.

### 3 — Epistemic and visual grammar

Test candidate labels/cues for OBSERVED, DECLARED, INFERRED, CORROBORATED,
POTENTIAL, UNKNOWN, STALE, CONTRADICTED, historical state and statistical
uncertainty. Include grayscale, color-vision variation, keyboard, screen reader,
zoom/text scaling and reduced motion. Measure interpretation accuracy, not
preference alone. Do not freeze a color/icon from a small preference poll.

### 4 — Interactive prototype (later authorized slice)

Use synthetic or rights-cleared realistic data across Opportunity,
Representation Gap, Public Experience change, PATHX, evidence trace, comparison
and resumption. This protocol does not authorize a prototype in P0-HFX-00.

### 5 — Interruption and return

Test short and delayed return. Ask what the user investigated, why (only when
recorded), what remained open, what changed and how to resume. Include missing
origin and verify no participant attributes an invented reason to AXIGNAL.

### 6 — Expert depth and trust calibration

Test exact methodology, instrument/version, sample/denominator, conditions,
comparison and source access without losing parent context. Include supported,
unknown, potential, stale and contradicted cases. The goal is appropriate
reliance, not maximized trust.

### 7 — Multi-client scope and cognitive accessibility

Test client switching, deep-link reauthorization, scoped fuzzy reference,
explicit portfolio mode, ambiguous references, interruption races and
understandable scope indicators. Include affected users; automated checks do
not replace them.

## Repeatable benchmark tasks

Build a fixed dataset and script for future design comparisons:

| ID | Prompt | Primary correctness check |
|---|---|---|
| T1 | “You opened AXIGNAL after several days. What deserves attention, and why?” | Correct material item and reason. |
| T2 | “Is this observed, potential, unknown or contradicted?” | Correct epistemic interpretation; unknown is not false. |
| T3 | “Why does this opportunity exist?” | Joined meaning and preserved dependencies without a mental join across modules. |
| T4 | “Show what supports this conclusion.” | Reaches actual evidence and describes trace correctly. |
| T5 | “What does this measure mean, and what does it not prove?” | Correct scope, denominator, period and interpretation boundary. |
| T6 | “Compare these organizations/periods.” | Correct conditions, scope, coverage and denominator. |
| T7 | “Find the France opportunity related to the capability we discussed.” | Meaning-based navigation retains context. |
| T8 | “Ask AXENT to show why this matters.” | Navigates relevant view with inspectable reference; not prose only. |
| T9 | “Resume the investigation you left open.” | Restores question/then-state/change; missing origin stays unknown. |
| T10 | “Show exact method, sample, denominator and source.” | Expert reaches proof without losing parent context. |
| T11 | “Find that France thing.” | Resolve inside active client or disambiguate; no cross-client jump. |
| T12 | “Which of my clients has deteriorating Public Experience?” | Explicit authorized portfolio scope and client attribution. |
| T13 | “Switch Client A to Client B while a response is loading.” | No stale A response renders in B context. |

## Acceptance scenarios A–J

- **A — Nontechnical owner:** a PVC-window seller understands a representation
  change without first knowing CTR, SERP, share of voice or instrument version;
  technical detail remains available.
- **B — Specialist:** an SEO expert reaches instrument, sample, denominator,
  comparison, method and evidence on the same object and truth.
- **C — Resume after 30 days:** report investigation, recorded reason, open
  question and changes, subject to retained data.
- **D — Why was I following this?:** trace actual attention origin; otherwise
  say unknown.
- **E — Then vs now:** historical UNKNOWN remains historical UNKNOWN if current
  evidence later supports the claim.
- **F — Consultancy:** Client A private state never appears in Client B context.
- **G — Fuzzy recall:** “Aquello de Francia” resolves inside current client or
  requests concise disambiguation.
- **H — Portfolio:** explicit authorized cross-client request uses visible
  portfolio scope and attributes results.
- **I — Evidence:** every material output reaches actual evidence without
  repository/data-architecture knowledge.
- **J — No mental join:** explain cross-domain meaning while preserving
  dependencies and their epistemic states.

These are future acceptance questions, not results or demonstrated runtime.

## Measures and analysis

Pair behavioral and comprehension data:

```text
TIME_TO_UNDERSTANDING          MEANING_ACCURACY
EPISTEMIC_ACCURACY             CHANGE / SCOPE / METRIC ACCURACY
TIME_TO_EVIDENCE               NAVIGATION_ERROR_RATE / BACKTRACKING
RESUMPTION_LAG                 UNKNOWN_TO_FALSE_CONFUSION
POTENTIAL_TO_OBSERVED_CONFUSION AXENT_NAVIGATION_SUCCESS
CROSS_CLIENT_CONTEXT_ERROR_RATE
```

Candidate instruments: SEQ after benchmark tasks; UMUX-LITE or SUS at a defined
milestone; NASA-TLX or Paas mental-effort only when workload is the question.
Predefine what each instrument measures. Do not mix them casually, set
thresholds before baseline, or use stated trust alone. Report sample,
exclusions, task/version, uncertainty, limitations and distinguish observation
from interpretation.

For Expertise Tax research, record familiarity with terms before tasks and
measure task correctness without requiring professional vocabulary. Success
means non-specialists understand business meaning while experts retain method
and evidence access, not that technical terms disappear. Adaptive-density
variants must preserve identical canonical facts and epistemic states, then
measure speed, accuracy, trust calibration and expert friction together.

## Ethics and evidence handling

- Use synthetic/rights-cleared examples unless separate authority approves
  other data; do not expose subscriber private information.
- Obtain informed consent, minimize collection, define retention/access and
  provide accommodations.
- Do not infer psychological, protected or sensitive traits from behavior.
- Think-aloud can alter cognition; use sparingly and pair with retrospective
  probing.
- Keep participant observations distinct from interpretation and product
  decision.

When studies are separately authorized, store governed artifacts under
`docs/research/hfx/` with participant segment, task, prototype/version,
observed evidence, confidence, limitations and decision impact. No finding
silently becomes doctrine.

## Production evidence gate

Polished prototypes alone do not authorize production. Review evidence in
comprehension, navigation, epistemic accuracy, accessibility, expert depth,
resumption and trust calibration. P0-HFX-01/02 may set thresholds only after
baseline. User preference cannot override epistemic truth; if truth is hard to
understand, change representation, not truth.
