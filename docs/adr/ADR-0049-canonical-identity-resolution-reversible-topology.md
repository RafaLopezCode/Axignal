# ADR-0049 — Canonical Identity Resolution and Reversible Topology Governance

**Status:** Accepted  
**Date:** 2026-10-01  
**Authority:** MASTER §§14, 35, 36, 46.1, 46.6, 46.10–13; ADR-0001, ADR-0021, ADR-0030.

## Context

AXIGLAND has one canonical Organization identity shared across all Xeeds. The existing baseline resolver indexed normalized names with first-write-wins behavior. Two organizations with the same normalized name or alias could therefore collapse silently to whichever candidate entered the index first.

That failure mode is systemic: a wrong identity binding can contaminate observations, relationships, FAXTs and Xignals reused by many Xeeds.

FR-23 separates two responsibilities:

1. deterministic identity resolution;
2. governed canonical identity-topology changes.

## Decision

### Resolution outcomes

Identity resolution returns one of:

- RESOLVED;
- AMBIGUOUS;
- UNRESOLVED.

Ambiguity is a valid terminal result. No candidate wins because it was indexed first.

AMBIGUOUS_IDENTITY != SAME_ENTITY

UNKNOWN_IDENTITY != FALSE

### Governed resolution signals

The deterministic resolver may use:

1. verified external identifiers;
2. unique exact normalized canonical names;
3. unique exact normalized aliases.

A verified identifier takes precedence over a name. If a supplied verified identifier is unknown to AXIGLAND, the resolver does not fall back to a coincident name.

No fuzzy similarity, model output, subscriber preference or opaque confidence score establishes canonical identity in FR-23.

### Identifier collision

If the same verified identifier is attached to more than one candidate, resolution is AMBIGUOUS and fails closed.

If a canonical name or alias resolves to multiple candidates, resolution is AMBIGUOUS and fails closed.

FIRST_MATCH_WINS = FORBIDDEN

### Subscriber authority

Identity-governance decisions admit only the closed authority classes:

- GOVERNED_HUMAN;
- DETERMINISTIC_POLICY.

No subscriber, tenant, Xeed, account or profile-owner field exists in the canonical identity-governance contract.

SUBSCRIBER_INPUT = ATTENTION_OR_CONTEXT

SUBSCRIBER_INPUT != IDENTITY_DECISION_AUTHORITY

### Merge

A MERGE redirects one or more currently ACTIVE OrganizationIds to one retained ACTIVE canonical OrganizationId.

A merge requires explicit evidence references, reason code, governed authority, actor and timezone-aware decision time.

Historical observations are not rewritten to the retained subject.

MERGE != HISTORY_REWRITE

### Split

A SPLIT converts one ACTIVE source identity into AMBIGUOUS state and references at least two ACTIVE target identities.

The old source does not automatically redirect to either child.

SPLIT => NO_AUTOMATIC_CHILD_SELECTION

The source and children are marked for revalidation.

### Reversal / correction

A REVERSAL appends a new immutable decision referencing the exact prior MERGE or SPLIT.

The prior decision remains in history.

A reversal is permitted only while the decision being reversed is still the latest decision affecting every involved subject. If later topology changes touched any affected identity, the reversal fails closed as stale.

Correction marks affected identities for revalidation.

CORRECTION != HISTORY_DELETION

### Durable topology store

The SQLite identity-governance adapter stores:

- current subject pointers;
- immutable identity-decision history;
- redirect state;
- ambiguity state;
- revalidation requirement;
- previous-decision lineage;
- reversal lineage.

Identity topology changes execute under one SQLite BEGIN IMMEDIATE transaction.

Decision rows are append-only. They are never updated or deleted.

### Shared observation boundary

Resolving an old OrganizationId through an explicit merge may identify the current canonical subject, but it does not rebind historical observations.

For current use, an observation matches only when:

observation_subject_id == exact current canonical subject

An observation still bound to an absorbed or different subject fails the FR-23 boundary.

FR-24 may later authorize explicit reuse based on rights, provenance, currentness, scope and applicability. FR-23 does not infer that permission.

SHARED_OBSERVATION != SILENT_SUBJECT_MIGRATION

## Invariants

ONE_CANONICAL_ORGANIZATION_PER_RESOLVED_IDENTITY

AMBIGUOUS_IDENTITY != SAME_ENTITY

FIRST_MATCH_WINS = FORBIDDEN

VERIFIED_IDENTIFIER > NAME_MATCH

UNKNOWN_VERIFIED_IDENTIFIER != NAME_FALLBACK

SUBSCRIBER_INPUT != IDENTITY_DECISION_AUTHORITY

MERGE => EXPLICIT_EVIDENCE

SPLIT => AMBIGUOUS_OLD_IDENTITY

SPLIT => NO_AUTOMATIC_CHILD_SELECTION

CORRECTION != HISTORY_DELETION

IDENTITY_DECISION_HISTORY = APPEND_ONLY

STALE_REVERSAL => FAIL_CLOSED

SHARED_OBSERVATION != SILENT_SUBJECT_MIGRATION

## Consequences

AXIGNAL now preserves uncertainty instead of forcing entity merges, can explicitly merge/split canonical identity with durable lineage, and can reverse erroneous decisions without erasing history.

The shared-world contamination frontier is bounded: old observations cannot silently cross into another canonical subject merely because an identity redirect exists.

## Non-goals

FR-23 does not implement probabilistic/fuzzy entity resolution, automatic corporate-family inference, rights/reuse policy, temporal currentness, canonical observation migration or subscriber-editable company profiles.
