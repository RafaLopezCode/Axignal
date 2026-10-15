# Real Admin data verification — 2026-10-15

## Result and boundary

All twelve operational sections completed real authorized reads through the
existing operator-only Admin experience on loopback 18182. The polished local
UI on 3835 uses a read-only review relay to that existing BFF; it does not use
the controlled runtime on 18235. That runtime was stopped and its browser tab
closed. No example values, seeded database, generated Admin session, copied
production data store or fallback response is used by this review surface.

The operator renewed the existing session through the normal access mechanism.
The browser supplies its HttpOnly cookie normally; no credential was extracted
or copied by the agent. The temporary relay forwards only allowlisted Admin
GETs to the existing experience. Writes, arbitrary APIs and upstream redirects
are rejected; cookies are not forwarded to the local UI server or logged.
This is a local review arrangement, not a deployment architecture change.

An attempted direct runtime tunnel was rejected by automatic approval review;
it was not opened. The existing operator-only experience path was retained.
Production runtime and experience reported healthy image revision `d16a0c1`.
No deployment, integration activation, financial action, invitation issue,
revocation, account edit or canonical mutation was performed during real QA.

## Source map and observed coverage

| Admin section | Existing source boundary | Real review result |
| --- | --- | --- |
| Centro de atención | `admin-observability` source snapshots → command-center projector | 16 metrics; all unknown because source projections are unavailable |
| Focos de observación | persisted LearningMemory and Admin metadata → Xeed observatory | 19 contexts, eight on first page; production first-proof learning references inspectable |
| Calidad de AXIGLAND | same authorized observatory, AXIGLAND branch | source states returned; unknown quality dimensions preserved |
| Axent y Brain | LearningMemory and Admin metadata → Brain observatory | research/provider coverage returned; missing observations preserved |
| Clientes y accesos | customer-access, pilot-test-accounts, staff-capacity and marketing-pool BFFs | base read, account/invitation tabs and persisted pilot configuration available; pool explicitly disabled |
| Adquisición | Admin acquisition store and private GSC store | both sections returned; no fabricated requests or analytics |
| Ingresos | revenue subset of command-center source snapshots | three metrics unknown; no monetary substitute |
| Finanzas y fiscalidad | financial document, accounting, fiscal compliance, tax stores | four sections returned; no invented invoices, transactions or compliance |
| Gobernanza | policy store, governance audit, LearningMemory and Admin metadata | policies/audit and eight alert families rendered; two alert counts unknown |
| Integraciones | integration registry and API operations store | registry empty; six API endpoint records, including real health telemetry |
| Frontier Advisor | measurement registry | definitions/readouts returned; definition is not asserted to be an observed value |
| Sistema | system subset of command-center source snapshots | three metrics unknown; no inferred health verdict |

These are successful real reads, not a claim of complete upstream observation
coverage. In particular, `_command_center_projection` reads persisted governed
snapshots; this runtime does not automatically create executive summary
snapshots from the owning stores. `SOURCE_PROJECTION_UNAVAILABLE` remains the
source's reason. Existing billing events do not establish MRR without the
required subscription period, currency, methodology and completeness. Learning
events do not establish an active-Xeed lifecycle count. No substitute calculation
or retrospective synthetic snapshot was introduced to fill those gaps.

## Verification evidence

- `evidence/real-domain-checks.json`: all twelve completed reads, correct section
  headings, no operational read errors, no horizontal page overflow at desktop.
- `evidence/real-customer-checks.json`: customer read tabs; no real mutations.
- `evidence/admin-real-integrations.png`: actual telemetry in the new UI.
- `evidence/admin-real-source.png`: actual missing-source reason, without a
  substitute revenue amount.
- `evidence/real-mobile-checks.json` and `admin-real-mobile.png`: all twelve
  sections at measured DOM viewport 390×844, no horizontal page overflow,
  read errors or drawer left open. Chrome's 90% zoom required a 351×760
  viewport override to produce that measured CSS viewport; it was reset after QA.
- `evidence/real-no-session.json`: all twelve unauthenticated reads return the
  same HTTP 401 and reason as the existing real BFF; no substitute response.
- Real source disclosure inspected: persisted production-first-proof learning
  references, separate from the old `controlled-ux-072` fixture records.

Earlier screenshots and interaction checks in this directory describe controlled
regression tests only. They are retained as test evidence and are superseded by
this report for real-data acceptance. No private account email or credential is
included in these new artifacts. Human visual acceptance is still pending.

Final frontend checks after the source-copy refinements: 312 tests, TypeScript,
production build and six-language inventory pass. Architecture Guard,
axignal-governance and diff whitespace checks pass. AST-only Graphify refresh:
21906 nodes, 60783 edges; no model or external API calls. The earlier complete
Python run remains valid: no Python/domain/runtime implementation changed.

Review processes are temporary: Next on 127.0.0.1:3836, read-only relay on
127.0.0.1:3835, existing real Admin BFF on 127.0.0.1:18182. Relay source is
`D:/AXIGNAL/_tmp/admin-real-preview.mjs`; it is development infrastructure and
is not included in the application change or a production deployment.
