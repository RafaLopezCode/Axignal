# ADR-0004: XIGNAL Is Observation, Not Ownership

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §4.4, §7, §26, §32, §33, §46.5, §46.14

## Context

Calling the commercial unit a claim or a profile would turn AXIGNAL into a
business social network with cold-start, abandoned profiles, verification, spam
and data-poisoning problems.

## Decision

`XIGNAL` allocates persistent computational observation to an organization. It
is not a claim, not a profile, and not ownership. It grants no ability to
configure canonical truth. An agency may Xignal many companies without owning or
speaking for them. The technical shape is `ObservationSeed`.

## Consequences

- No claiming flow is required for an organization to be represented.
- One canonical Organization regardless of how many users Xignal it.
- Observation lifecycle is EXPANDING → LIVE. There is no DONE.

## Enforcement

- `domain/xignal/**` must not import `domain/organizations/**`.
- `ObservationStatus` has no `DONE` member.
- Architecture Guard rule `XIGNAL_ISOLATION`.
- `tests/contracts/test_xignal_observation_not_ownership.py`.
