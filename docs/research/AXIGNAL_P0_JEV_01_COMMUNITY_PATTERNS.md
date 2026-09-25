# P0-JEV-01 Community Jev Research

**Reviewed:** 2026-09-25
**Authority:** Non-authoritative inspiration only. Official TypeSafe docs,
official skill, SDK code, AXIGNAL doctrine and empirical AXIGNAL data take
precedence. Neither repository below was installed or added as a dependency.

## Selected repositories

### `wuyoscar/jev-skill`

**Source:** [GitHub repository](https://github.com/wuyoscar/jev-skill), including
its skill documentation and calibration reference. Reviewed as a community
skill/reference set; its own page distinguishes real TypeSafe calls from
simulation and disclaims adapter guarantees.

- **PATTERN:** preserve request/state/question/response details; label real Jev
  separately from model or agent simulation; test offline before live calls;
  capture observed pairs and compare on bounded representative samples.
- **MEASURED_OR_CLAIMED:** repository includes task-specific pilot examples and
  reports; these are author-reported/community data, not independently
  reproduced AXIGNAL or TypeSafe guarantees. The repository itself warns that
  a compatibility adapter does not establish production server behavior.
- **TRANSFERABLE_TO_AXIGNAL:** experimental mode labels, bounded sample-first
  procedure, complete reproducibility ledger, no fabricated confidence, and
  explicit separation between recorded outputs and live outputs.
- **RISKS:** the community skill can install scripts and may suggest a provider
  selection/live use that P0-JEV-01 does not authorize. Community formulas and
  thresholds must not be imported as TypeSafe semantics or AXIGNAL policy.
- **OFFICIAL_DOC_COMPATIBILITY:** compatible where it recommends reading live
  docs, keeps code in control, and labels uncertainty; non-authoritative for
  API guarantees and threshold/calibration claims.

### `lazniak/jevskill`

**Source:** [GitHub repository](https://github.com/lazniak/jevskill). Reviewed
as a community harness for coding-agent context selection and decision
measurement, not as AXIGNAL product architecture.

- **PATTERN:** reversible context reduction, explicit decision candidate set,
  decision/event ledger, and per-stage A/B evaluation can help ensure an
  uncertain filter does not irreversibly discard context.
- **MEASURED_OR_CLAIMED:** repository title and documentation advertise
  specific speed/token/accuracy improvements. They are project-specific
  claims and were not independently reproduced or transferred to AXIGNAL.
- **TRANSFERABLE_TO_AXIGNAL:** use reversibility and record changed state when
  studying context reduction; compare against a deterministic or current
  baseline and track false omissions as well as savings.
- **RISKS:** agent coding context and AXIGNAL economic evidence are different
  populations and loss functions. Reversible filtering is not permission to
  discard source evidence or alter canonical state. Community test labels may
  be self-derived.
- **OFFICIAL_DOC_COMPATIBILITY:** directionally compatible with official
  minimal-state and target-data evaluation guidance; numerical claims are not
  official facts.

## Disposition

No community Skill, CLI, SDK, threshold, confidence formula, provider wrapper,
dataset, or claimed performance result is adopted. The only carried patterns
are governance and experiment-design ideas already expressed in the AXIGNAL
architecture: label live versus mock data, preserve replayable evidence,
compare same cases under controlled variables, keep reductions auditable, and
publish negative as well as positive outcomes. The official TypeSafe research
record is [here](AXIGNAL_P0_JEV_01_TYPESAFE_RESEARCH.md).
