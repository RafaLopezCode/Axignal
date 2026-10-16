# Feature Specification: Observe without a verified identity (web-anchored Focus)

**Feature Branch**: `spec/web-anchored-focus`

**Created**: 2026-10-16

**Status**: Proposed (CTO review of the ADR-0087 amendment)

**Input**: CTO, 2026-10-16:
> "Biocultor no está dado de alta en GLEIF por lo que no puedo verificar identidad y no sé hasta qué punto es necesario o determinante si se quiere observar a la competencia… Yo propondría 'verificar la identidad' si una empresa quiere aumentar las posibilidades de observación, pero hay casos de uso en los que me parece una condición restrictiva."

## Measured problem

The audit's P0 (the autonomous loop is not proven) was traced in production on 2026-10-16:

1. The daily observation timer runs, but the flag is off (`exec-condition`).
2. The enrollment check reports `NO_ELIGIBLE_FOCUS`, with 0 Foci.
3. The first real pilot is a Spanish online shop, added by its URL. It stayed `IDENTITY_PENDING / IDENTITY_SOURCE_UNAVAILABLE`, because the only registry is GLEIF (LEI holders).

Under ADR-0087 as written, **no small business without an LEI, and no competitor, can ever become a Focus**. A Focus is what the autonomous loop observes.

## Authority

- **MASTER §22 (line 1377).** A Focus writes nothing about the organizations it observes; it only directs observation. Agencies observe clients and competitors without proving they represent them.
- **MASTER §15.3.** The official website is the source for declared products and capabilities; the registry is the source for legal identity.
- **MASTER §15.4.** UNKNOWN ≠ FALSE.
- **ADR-0087 amendment 2026-10-16** (in this PR).

## User stories

1. **(P1)** A subscriber adds a company by its website. No registry attests it, so a Focus is created on a web-anchored subject and observed like any other: presence, reputation, value, markets, relationships, demand, activity, context and evolution in time. Legal-identity predicates are UNKNOWN, with "identity not verified (optional)".
2. **(P1)** A request already pending for that reason becomes a Focus on retry. The pilot's pending shop is retried as is.
3. **(P2)** Verifying identity stays available as an upgrade: a registry-attested identity (an LEI today) admits the canonical Organization. Re-pointing the Focus keeps its history.

## Requirements

- **FR-001**: Only `IDENTITY_SOURCE_UNAVAILABLE` and `NOT_FOUND_IN_IDENTITY_SOURCE` are anchored, and only for a locator with a public website. AMBIGUOUS, CONFLICT, INVALID_INPUT and bare names keep today's outcomes.
- **FR-002**: The subject id is `org:web:<sha256(domain)>`. It lives in its own operational store (`web-subjects.sqlite3`), never in the canonical Organization store or AXIGLAND. One domain gives one subject, shared across Tenants. A registry-attested website always wins over a web anchor for the same domain.
- **FR-003**: A web-anchored subject can never hold canonical state. `FAXT.create` refuses an `org:web:` subject.
- **FR-004**: Display uses the domain, never an invented legal name. The identity finding states that verification is optional and what it adds.
- **FR-005**: `AXIGNAL_WEB_ANCHORED_FOCUS_ENABLED` defaults to `true`. Turning it off restores registry-only Foci; existing web-anchored Foci keep reading.

## Success criteria

- **SC-001**: In production, the pending shop becomes a Focus on retry, and the enrollment check moves from `NO_ELIGIBLE_FOCUS` to eligible.
- **SC-002**: A test proves that no FAXT can be written for a web-anchored subject. A canonical Organization store count of 0 after a web-anchored add is asserted end to end.
- **SC-003**: Every existing registry-path test passes unchanged, with the flag off where it exercises pending attention.
