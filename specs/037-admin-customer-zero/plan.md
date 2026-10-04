# AO-24A organization attention extension plan

CURRENT_TASK = AO-24A

Authority: spec.md and organizations-contract.md; MASTER, constitution and
ADR-0017/0076/0081/0082 remain controlling. Architecture review: Graphify query
examined FirstProofService, Admin authorization, identity resolver and Xeed flow.

Extend the existing FR-30 read-model database with append-only request attempts
and per-principal reading selection. Resolve submitted name/domain against
already-canonical server source bindings; unresolved and ambiguous identity
cannot enter germination. Generalize the existing pipeline by resolved subject,
keeping legacy AXIGNAL compatibility. Reserve execution sequence before each run.

AO-01 authenticates XEEDS_READ and RESEARCH_OPERATE at runtime. Browser proxies
never accept roles, canonical IDs, payment status or economic conclusions.
No new datastore/backend/Brain or commercial checkout is introduced.

Reuse the shared organization dialog and product renderer. Read persisted state
after writes, reset transient product/Axent scope on context change and reject
questions from an obsolete Xeed. A failed request retains the current reading.

Verify controlled multi-focus acquisition, duplicates, unresolved/ambiguous,
unsafe targets, insufficient evidence, failure, revocation, per-principal
selection, history and restart. Exercise actual browser desktop and mobile;
normal localhost retains only existing AXIGNAL observation. Full deterministic
gates and frontend typecheck/test/locales/build are required before integration.
