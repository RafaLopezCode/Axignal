# P0 — Persistent Observation Memory Runtime

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER §56.1, §56.15, §56.18; Engineering Constitution §§VI, XVII; existing Brain contracts.

## Objective

Turn governed Observation Memory from an in-memory contract into durable, replay-safe runtime infrastructure that can reconstruct current subject state without granting canonical truth authority.

## Required behavior

- Persist governed observations independently of EvidenceAdmission.
- Preserve provenance, source type, UTC-normalized observation time, mode and content fingerprint.
- Preserve reconstructible raw observation material either inline or through an immutable artifact reference.
- Preserve normalized state contributions and complete observation history.
- Exact replay of the same observation id is idempotent.
- Reusing an observation id for different governed content fails closed, including concurrent writer races.
- Reconstruct current state deterministically from temporal history across timezone offsets.
- A later observation may supersede a current field without deleting prior observations.
- State fingerprints change when selected provenance/time changes, even if the visible value does not.
- Expose changed state fields so existing dependency-aware planning can reevaluate only impacted dimensions.
- Public subject observation memory is keyed by canonical subject, not duplicated per Xeed.

## Non-goals

No sensor implementation, crawler, JEV invocation, canonical FAXT write, canonical Relationship write, queue, worker, production database selection or AXIGLAND UI projection is authorized by this slice.

SQLite is only the first replaceable durable adapter for local/runtime proof. It is not product doctrine.

## Invariants

INFORMATION SURVIVAL != TRUTH ADMISSION.
OBSERVATION MEMORY != CANONICAL AXIGLAND.
OBSERVATION != EVIDENCE ADMISSION.
UNKNOWN != FALSE.
XEED ATTENTION != SUBJECT OWNERSHIP.
