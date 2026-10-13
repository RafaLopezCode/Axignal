# Feature Specification: Marketing pool
**Branch**: feat/marketing-pool | **Created**: 2026-10-13
**Input**: CEO request — an autonomous runtime (operable by Codex or Claude) that knows
AXIGNAL's buyer personas, finds the most promising organizations worldwide without ever
repeating one, studies each with AXIGNAL and writes to its most suitable published
address a personalized email, in its language, showing the value AXIGNAL observed.

## Authority
MASTER §171 and Admin spec §5.7–5.8: Admin may hold AXIGNAL's own first-party CRM,
marketing and acquisition state. `AXIGNAL CRM LEAD != AXIGLAND ORGANIZATION STATE`:
a prospect or its study never creates or changes an Organization, FAXT, Relationship or
any canonical state. Account-Based Pull strategy (2026-10-08): outreach starts from an
existing, evidence-backed demonstration, never a cold pitch; it must not be sendable
unchanged to another organization.

## User Scenarios & Testing
### Story 1 (P1): Autonomous, non-repeating discovery
Per buyer persona (SEO/GEO, digital marketing, reputation/PR, B2B consultancy) and
country rotation, the runtime reads open registries (OpenStreetMap office tags, Wikidata
classes), keeps only an organization's own website domain, and adds each domain once,
ever. Suppressed domains are never added again. A failing source is retried next day.
### Story 2 (P1): Study, qualify, draft
Each prospect is studied once by the governed First Observation runtime under the
staff tenant. It qualifies when its own site evidences the persona and the study holds
≥4 sourced findings in ≥3 families. A draft is phrased through `cognition/router`
(`OUTREACH_DRAFT`) in the site's language, citing ≥2 numbered findings, POTENTIAL as
possibility, no links of its own; otherwise it is not qualified.
### Story 3 (P1): Human approval and lawful sending
Admin › Clients and access › Marketing pool lists drafts with the exact HTML a
recipient gets. Nothing is sent without an explicit staff APPROVE. Only markets whose
versioned channel policy is EMAIL are sendable; others are HELD with their reason. The
recipient is a role address the organization publishes on its own domain. Each email
identifies the sender and postal address, says why the address was used, carries a
one-click List-Unsubscribe and a visible opt-out; an opt-out suppresses domain and
address permanently. Sends are capped per day.
### Story 4 (P2): Recipient reading
The email links to a private, non-indexed reading of the cited findings with sources
and epistemic states, in the email's language, and to the opt-out confirmation.

## Requirements
FR-001: No scraping of search engines, maps or social networks; robots.txt respected by
the governed fetcher; platforms are never treated as an organization's website.
FR-002: Personal-looking addresses are never chosen; only listed role local parts.
FR-003: Personas and channel policy are versioned and recorded on each prospect.
FR-004: Provider-neutral SMTP (default Hostinger, implicit TLS); password from a secret
file; sending off unless every setting exists.
FR-005: Admin read/write use acquisition scopes; every decision audited with its actor.
FR-006: Agents get a read-only CLI and a skill protocol; they never approve or send.

## Success Criteria
Every domain studied at most once; no email without approval; no email to a HOLD market,
suppressed domain/address or personal address; drafts cite only given findings; gates
pass; a real discovery run shows persona and role-address yield.
