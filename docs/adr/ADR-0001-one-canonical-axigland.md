# ADR-0001: One Canonical AXIGLAND

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §3 (AXIGLAND), §6.1, §7.3, §46.1, §46.13, §52

## Context

AXIGNAL observers may issue many Xignals over the same organization. A naive
design would give each user or agency a private copy of "their" companies,
producing divergent truths and poisoning the canonical world.

## Decision

There is exactly one canonical economic world, AXIGLAND. Users never own nodes
and never create private versions of reality. Organization identity is canonical
and shared. Private classification (`MY_CLIENT`, `COMPETITOR`, ...) affects only
a user's perspective and never AXIGLAND.

## Consequences

- No per-customer duplicate Organization truth.
- Organization models carry no subscriber/account/tenant/owner scope.
- Perspectives, filters and private labels are stored outside canonical state.
- Many Xignals may point at one canonical Organization.

## Enforcement

- `domain/organizations/model.py` has no subscriber-scope fields.
- `tests/contracts/test_organization_canonical.py` fails if such a field is added.
- Architecture Guard forbids `domain` from importing outward layers.
