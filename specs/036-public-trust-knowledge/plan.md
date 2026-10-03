# Implementation Plan: Public Trust, Knowledge and Access
## Summary
Extend apps/web/experience in the existing isolated worktree, inheriting 035's visual grammar. Add public navigation, editorial index and six article permalinks, policy hub and three documents, contact draft studio, identity-only access pages, GDPR rights and local request draft.
## Technical Context
Existing Next 16.3.8 / React 19.3.0 / TypeScript / Lucide / Zod. No new packages or Python/runtime dependencies. Local fonts and official assets unchanged. Typed auth presentation boundary only; no production auth, email or privacy service.
## Constitution Check
PASS before and after design: one AXIGLAND, human attention not truth, explicit temporal/provenance semantics, unknown remains unknown, provider-neutral identity mapping and separate Admin plane. No graph runtime, canonical edits, provider selection, authenticated scraping, sponsored UI or subscriber CRM. Source UI stays separate from accepted legacy surfaces.
## Shape before build
Typography and tokens inherit 035. Public navigation is a stable bridge. Knowledge feels like an open notebook: one asymmetrical featured spread, then calm editorial rows, indexed by topic. A conceptual lens shows observation/possibility/unknown without invented graph edges. Contact feels like a letter on a desk; preview is the same content that downloads. Access frames the Observador in a quiet threshold and shows narrow permission facts. Trust uses a readable document rail and clear draft provenance, not a compliance-badge grid.
Desktop: two-column reading/contact/access spreads, sticky reading index, restrained line length. Mobile: linear content, accessible menu dialog, full-width inputs/buttons, no hidden legal qualifiers. The explicitly requested use-case ribbon moves through a fixed focal aperture; it has a pause control and respects system and in-app reduced motion.
## Architecture review
Graphify query surfaced specs/022, ADR-0056, AdminCustomerAccountService and PublicBriefRequestService. Those services are separate authorities; no presentation form may pretend to execute their commands. Existing AuthenticationPort has no runtime, therefore prepared Google/OpenAI starts fail closed. No backend contract implementation or domain change needed. Identity providers remain adapter references, never Principal or Tenant IDs. Rights request draft is not a rights command; canonical persistence creates no exemption from data-protection obligations.
## Project Structure
components/public-shell.tsx, knowledge.tsx, trust.tsx, drafts.tsx, access.tsx; lib/editorial.ts, public-contracts.ts; app/public.css and route wrappers; app/api/auth/start and status; tests/public-contracts.test.ts. Spec artifacts here include contract, quickstart and QA evidence.
## Phases
Foundations -> Knowledge -> Policies/Contact/GDPR -> Access -> browser QA/repair -> deterministic gates -> convergence -> local commit.
## Complexity Tracking
No exception or gate suppression. Public service integrations deliberately pending as requested by human.

## Browser review architecture extension
All additions stay in the frontend presentation boundary. The timeline's existing snapshots collection owns dates; flex layout does not synthesize history. A deterministic integer-cents calculator presents MASTER §27 reference economics and never bills. Newsletter uses local DraftForm preview/download until an explicit PublicBriefRequestService adapter and controller channel are authorized/configured; application acquisition semantics are preserved. Locale registry separates supported identity from completed copy and supports explicit source-language fallbacks. Only locale and notice-dismissal preferences may persist locally; personal drafts remain ephemeral. The first-visit notice is not a legal-consent gate: no optional trackers load before or after dismissal. Provider logos are copied unchanged from official sign-in branding resources. Observer gesture PNG is copied byte-identically from the human-supplied action sheet; SVG viewports reuse approved poses.

## Final presentation refinements
The six supported languages are fully represented in the bounded catalog; the AST inventory checks actual authored copy including route explanations and fails on incomplete entries. The demo Axent route accepts the same six-language enum and translates existing authorized fixture copy; its context/plan validation and economic authority are unchanged. Nested native dialogs have unique accessible heading IDs and stop cancel propagation so Escape preserves the parent draft. Shared public footer links the human-specified LinkedIn company profile in a new tab with noopener noreferrer.
