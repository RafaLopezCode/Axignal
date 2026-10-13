# Subscriber account self service

Authority: MASTER §§5, 23, 27, 55; Constitution; ADR-0061/0084/0094; explicit user request to implement the missing subscriber settings. Spec 021's deferred profile scope is implemented only in this bounded slice; no canonical Organization profile editing.

## Requirements and clarification
Principal owns private avatar and UI locale across devices and Tenant contexts. Authenticated membership/session is rechecked before every read/write; clients cannot name owner, Tenant or billing Customer. Locale nullable with six supported languages; revision controls lost updates. Browser accepts a local PNG/JPEG/WebP up to 5 MB and crops it before upload. Server avatar payload accepts PNG/JPEG/WebP, max 128 KiB, <=2048px each edge and <=4M pixels, safe decode and re-encode to a 128px PNG with metadata removed; SVG, animation and arbitrary remote URLs rejected. Remove avatar and clear locale are distinct commands.

Existing billing purchase owner authority plus current membership authorizes management of the mapped tenant subscription. Provider-neutral portal port returns ephemeral validated redirects for payment method, invoices and period-end cancellation. No payment credentials or financial statements mirrored in private profiles. Portal cannot update quantities/plans; existing capacity purchase flow remains authoritative. Provider confirmation remains the actual cancellation action. Returning from Stripe is not payment/cancellation evidence; existing signed webhook/current reconciliation owns entitlement.

A pilot/unconfigured/unauthorized payer gets a clear state, never fake subscription controls. Account actions stay disabled in public demo. Account panel inherits existing visual grammar, responsive controls, accessible feedback and recovery. No production deployment or live provider mutation performed by coding tests.

## Acceptance
Two Principals cannot read/change each other's profile or payer; revoked membership/session and stale versions fail closed; profile survives process restart. No canonical/evidence writes from settings. Portal uses only server mapping, merchant/environment, expected subscription and allowlisted return/redirect. Features verified before session creation. Model/network-independent required tests. Browser desktop/mobile QA. Commit, merge and push authorized by user.


## Follow-up clarification

Account settings must remain reachable before the first organization exists, including on mobile. Portal return is an attention to reconcile with the provider, never a payment/cancellation receipt, and selects the account settings view. All subscriber and AXENT messages use six supported languages; inventory must have no missing entries. E2E closure includes actual HTTP session, authorization, Next proxy, persistence, recovery and revocation, with controlled external IO. Never describe controlled tests as live merchant validation or claim blocked native browser steps were exercised.
