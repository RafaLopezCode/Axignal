# Runtime E2E closure — 2026-10-10

Candidate branch: `codex/runtime-e2e-closure`, independently based on canonical
`cbd04b75526c6db1d43e88e42fd9871798e70a9e` (merged PR #180). No production write,
merge, canonical checkout change, Claude worktree inspection, or UI change.
The earlier owned WIP is preserved as `f6d521a`; this candidate reuses its small
budget repair on the verified canonical base. Existing specs 063/064/065 govern
this repair; it adds no feature family, new spec, queue or provider authority.

## Three demonstrated discontinuities repaired

1. **Hard kill after dispatch, before receipt reset apparent spend.** The RED
   child-process regression made one acquisition and exited with code 17; the
   old persisted budget still reported zero requests. The existing fenced atomic
   runtime commit now persists conservative request/cost bounds before dispatch.
   Returned bounded consumption settles that reservation with its receipt.
   A lost receipt retains UNKNOWN consumption and prevents same-day redispatch.
   Status inspection exposes aggregate unsettled reservations. A bound is not
   evidence of actual billed cost; no observation is invented. Legacy budget
   JSON remains readable without migration.
2. **Pending identity admission lost the original host/path.** Pending attention
   was preserved, but retry created First Observation with the canonical normalized
   domain. The real HTTP journey reached OBSERVATION_MISS instead of measuring the
   authorized `www` services URL. Retry now passes the tenant-authorized stored
   locator through the existing First Observation context and clears it in
   `finally`. Registry admission, website ownership, rights and entitlement
   remain independent authorities.
3. **Two empty normalized bases falsely established no economic change.**
   Raw-only observations now yield a null/UNKNOWN normalized comparison.
   Comparable public-offer interpretations still report their conditioned changes;
   these are not canonical business improvements. The existing MCP E2E now also
   verifies that two actual normalized predecessors still produce a material
   change. No gate is weakened to accept UNKNOWN as FALSE.

## Executed evidence and its limits

- [TCP journey](evidence/journey.json): actual production HTTP handler, subscriber
  composition, admission, SQLite memory/output stores, OAuth PKCE and MCP. Starts
  without an organization, observes private pending attention, independently admits
  identity, seeds authorized memory, projects a POTENTIAL opportunity, validates
  AXENT citations, denies another tenant, restarts, reobserves unchanged and changed
  pages, and preserves knowledge-cut history through another restart.
  OIDC, registry, RFC 2606 pages, demand and model judgments are synthetic ports;
  accidental non-loopback egress fails. This is not Google or JEV quality evidence.
- [Live public source proof](evidence/live-public-sources.json): bounded real GLEIF
  CC0 registry admission for Bloomberg Finance L.P. and three real TED notices.
  The successful run uses one registry GET and one TED POST, zero model calls and
  zero paid cost. Subscriber HTTP returns 200, MCP reads and persisted identity
  survive a rebuilt composition. AXENT abstains with no fabricated economic fit.
  Authentication/invitation are controlled synthetic authorities; the live probe
  does not certify a real Google login. GLEIF does not attest an official website,
  capability or market reach. TED notices are independent demand, not relationships
  or a fit assertion for this organization. The original successful artifact labels
  the canonical base SHA; a final committed-code probe replaces it before handoff.
- [Production inspection](evidence/production-read-only.json): real Hostinger SSH,
  container metadata, whitelisted flags, read-only SQLite aggregate counts,
  scheduler status and external HTTP. Deployed SHA is
  `f0c54a6240f7dcd3f10d49acfc28b9608a9b0188`, an ancestor of the canonical base,
  predating integrated specs 063/064/065. Healthy services are not evidence of an
  active observing product. Observation is disabled and no active focus/grant is
  present. No source/private customer rows, secrets, or credentials were read.

An initial opt-in probe failed because its case-sensitive environment whitelist
removed Windows OS/TLS settings. The harness now preserves required OS/TLS paths
while clearing optional provider flags/secrets. TLS, source policy and production
configuration were not relaxed. Failed acquisition was not promoted to observation.

Source authority verified against official documentation:
[GLEIF CC0](https://www.gleif.org/en/meta/lei-data-terms-of-use),
[TED anonymous search](https://docs.ted.europa.eu/api/latest/search.html),
[TED legal notice](https://ted.europa.eu/en/legal-notice),
[TED bounded pagination](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html).

## Executive answers A–F

| Question | Demonstrated answer | Boundary |
| --- | --- | --- |
| A. Real organization and governed memory | Real registry identity was admitted and persisted; autonomous governed acquisition/recovery passes with controlled ports. | A fully real website/capability research cycle is not certified: current GLEIF authority supplies neither website binding nor capabilities. |
| B. Useful finding or justified uncertainty | Synthetic composed opportunity remains POTENTIAL with sources; live identity yields explicit insufficient evidence/AXENT abstention. | No commercial-fit inference is made from LEI registration or independent TED demand. |
| C. AXENT continuity | Grounded synthetic AXENT answer, scheduler/research continuation gates and historical reading survive restart/reobservation. | No external JEV/Luna output-quality claim. |
| D. Subscriber/MCP | Real HTTP/OAuth/MCP; five composed DTO states and one live-source DTO parse through the unchanged frontend Zod schemas. | Browser/visual UX was not audited by this runtime change. |
| E. Adversarial recovery | Hard kill, settlement, restart, retry, rights withdrawal, expiry, tenant, entitlement and provider-failure regressions run through existing runtime gates. | Optional SDK and POSIX deployment cases require their respective environments; inspect exact validation results below. |
| F. Productive activation | Exact deployment/config/source boundaries identified below. | This PR makes no production change. |

## Remaining activation boundaries

1. CTO-approved deployment of integrated security/observation code and this repair:
   current production still runs the older SHA above.
2. Verified subscriber access/grant and active attention, then separately authorized
   source rights/website binding and operator activation of bounded observation.
   Timer availability alone does not authorize an enabled acquisition cycle.
3. Source availability/coverage: GLEIF legal identity is available; official website,
   capabilities and economic fit require appropriate admitted evidence. Missing
   context remains UNKNOWN and routes research/abstention, not a fabricated lead.
4. If live JEV/Luna interpretation is required, separately approve provider use,
   privacy purposes and cost, and evaluate output quality. Deterministic observation
   and honest abstention require no paid model activation.
5. Subscriber experience: runtime DTOs are verified; real authenticated/browser UX
   and human acceptance belong to the independent subscriber/landing work. This PR
   neither modifies nor certifies those visual decisions.

## Validation

Python 3.12, locked `uv sync --frozen`. Ruff formatting/check, strict mypy
(475 source files), Architecture Guard and all governance checks pass. AST-only
Graphify is refreshed, without LLM/API cost. No suppressions or CI changes.

- New budget regressions: 7 passed; runtime units/crash suite: 12 passed.
- Existing autonomous/scheduler/research/continuity selection: 42 passed,
  4 POSIX-only skips on Windows.
- Timeline/projection/MCP plus composed journey selection: 40 passed.
- Final journey with contract snapshots: 1 passed.
- Initial full suite: 2050 passed, 6 skipped, one obsolete temporal expectation
  failed. Its scenario is strengthened as described above; the final full run
  result is recorded before handoff.
- Frontend: 162 tests passed; typecheck passed; i18n inventory 1539, missing 0;
  production build passed. No frontend source changes.
- Actual frontend schema parse: pending, initial, restarted, changed, final and
  live-source subscriber outputs passed.

Reproduce deterministic composition: `uv run pytest -q
 tests/integration/test_runtime_frontier_journey.py
 tests/integration/test_product_mcp_e2e.py
 tests/observation_runtime/test_acquisition_crash_budget.py
 tests/observation_runtime/test_acquisition_budget_settlement.py`.

The opt-in live proof is outside required CI. Use a fresh isolated data directory:
`uv run python -m docs.audits.runtime-e2e-2026-10-10.live_identity_proof
 --data-dir <new-empty-directory> --sha <tested-code-sha> --public-source-probe`.
Its JSON keeps fixtures and live facts separate; do not run against production data.

## Delivery state

IMPLEMENTED: three existing runtime seams repaired. PROBADO: deterministic gates,
TCP composition, real licensed source acquisition and production read-only checks.
INTEGRADO: candidate branch only; canonical base contains PR #180, this repair is
not merged. DESPLEGADO: no. VERIFICADO E2E: complete local chain with synthetic
external ports, partial live-source identity/uncertainty chain; no active production
product or external-model quality certification. Final SHA/CI belong to the PR.
