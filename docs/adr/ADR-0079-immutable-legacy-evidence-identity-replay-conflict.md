# ADR-0079 — Immutable Legacy Evidence Identity and Replay Conflict

**Status:** ACCEPTED  
**Date:** 2026-10-04  
**Scope:** AUD-08; legacy EvidenceLedger; XeedSemanticGermination  
**Derives from:** MASTER §§15.2, 20, 53.4; Engineering Constitution VI; ADR-0032 replay doctrine; ADR-0072

## Context

The legacy in-memory EvidenceLedger appended every Evidence instance to a list. It did not distinguish an exact replay from reuse of the same evidence id with changed source, claim, time, authority or reference.

That made an evidence reference ambiguous: multiple incompatible observations could exist under the same id, and an exact replay could be counted twice.

Observation Memory and webhook inboxes already implement the required replay pattern: exact replay is idempotent and an identity collision with different immutable content fails closed.

## Decision

Evidence identity is immutable.

The canonical material fingerprint for an Evidence instance is the same deterministic digest used by EvidenceAdmission. It covers:

- evidence id;
- source;
- source type;
- reference;
- extracted claim;
- observed_at;
- source authority.

The public primitive `evidence_fingerprint()` is the single definition used by both EvidenceAdmission and EvidenceLedger.

### Ledger append contract

`EvidenceLedger.append(evidence)` returns:

- `True` when the evidence id is new and the observation is appended;
- `False` when the same evidence id is replayed with the exact same fingerprint;
- `EvidenceLedgerConflict` when the same id is presented with a different fingerprint.

Conflict never replaces or appends the original evidence.

### Resolution

`EvidenceLedger.get(evidence_id)` resolves at most one Evidence instance.

Therefore an `evidence_ref` can no longer point to multiple incompatible payloads inside this legacy ledger.

### New observations and versions

A materially different observation is historical information, not a replay.

It must use a new evidence id. Both old and new ids remain in append order and preserve history.

### Legacy semantic flow

The legacy EvidenceWriter contract now reports whether an append inserted new evidence.

XeedSemanticGermination writes a canonical FAXT only when the evidence append was new:

```
admit proposition
→ build FAXT
→ append evidence
   → conflict: abort
   → exact replay: no-op
   → new: write FAXT
```

Thus exact replay is end-to-end idempotent in the legacy experiment, and altered replay fails before a second FAXT write.

This does not add a storage layer and does not alter Prime production composition.

## Invariants

```
SAME_EVIDENCE_ID + SAME_FINGERPRINT = REPLAY
SAME_EVIDENCE_ID + DIFFERENT_FINGERPRINT = CONFLICT
NEW_OBSERVATION = NEW_EVIDENCE_ID
EVIDENCE_REF -> ONE_EXACT_CONTENT
REPLAY != DUPLICATE_CANONICAL_WRITE
```

## Consequences

- Legacy evidence references are unambiguous.
- Exact retries do not duplicate evidence or downstream FAXT writes.
- Changed claim/time/authority/source under the same identity fails closed.
- Historical evolution is preserved by assigning a new evidence id.
- EvidenceAdmission and persistence cannot drift into separate fingerprint definitions.
