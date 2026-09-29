# ADR-0004: XIGNAL Is Observation, Not Ownership

- **Status:** Superseded by ADR-0023
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §4.4, §7, §26, §32, §33, §46.5, §46.14

## Context

Calling the commercial unit a claim or a profile would turn AXIGNAL into a
business social network with cold-start, abandoned profiles, verification, spam
and data-poisoning problems.

## Decision

This ADR used `XIGNAL` for the customer's persistent observation unit. That terminology was superseded after product reconciliation established the seed/germination model: the customer plants a `XEED`; the Brain germinates that Xeed and produces many `XIGNAL`s. The original ownership prohibition remains valid, but the unit name and technical mapping do not.

## Consequences

- No claiming flow is required for an organization to be represented.
- One canonical Organization regardless of how many Xeeds observe it.
- See ADR-0023 for current XEED/XIGNAL semantics and migration obligations.

## Enforcement

- Historical enforcement references remain evidence of the superseded model. Current enforcement is defined by ADR-0023 and its follow-up implementation slice.

[executed on device: DESKTOP-7L6CMEJ (d615520f-0404-49b0-83c7-620cc18c31f4)]