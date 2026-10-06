# Clarifications â€” Subscriber Billing Bridge

**Status:** Resolved by root review and explicit human direction for this slice.
**Date:** 2026-10-06

| Topic | Resolution | Boundary |
|---|---|---|
| Development environment | LIVE-only is the explicit human direction. No sandbox is assumed, required, or fabricated as evidence. | Root controls every live write. This feature does not complete a payment or enable production collection. The existing ADR-0061 sandbox requirement is reconciled in a root-owned ADR amendment before production activation. |
| Offer | MASTER Â§27 hypothesis: â‚¬9.95/month base includes one Organization/Observation Focus; â‚¬4.95/month for each additional. | Root verifies and approves actual active recurring EUR price references outside domain code; economics remain hypothesis, not willingness-to-pay validation. Missing/mismatched catalog blocks provider calls. |
| Initial capacity | Subscriber chooses the desired total. Initial Checkout contains one base item and `max(0, totalâˆ’1)` additional item quantity. | One Stripe subscription per authorized Tenant consumption scope; never bill per Signal. |
| Expansion | The subscriber requests a larger total on the existing subscription. Set additional quantity to absolute `desired_totalâˆ’1`; never create another base/subscription. | One open capacity-change intent per scope/subscription, durable compare-and-set and idempotency key prevent duplicate charges. Membership revocation or unknown/overdue payment blocks update before provider contact. |
| Upgrade proration | `always_invoice` + `pending_if_incomplete`; invoice now for Stripe-calculated proration and only apply provider update after payment succeeds. | Pin API version; exact attribute support is documented by Stripe for `items.quantity`. On action-required/failure, capacity stays `pending_purchase`; only a validated hosted invoice URL can be returned. |
| Capacity scope / identity | Consumed capacity belongs to an authorized Tenant. Bootstrap links the purchasing Principal to that Tenant under an explicit purchase-authority port. | No general payer-to-Tenant cardinality, subscriber roles, or auth provider is inferred; no provider IDs/metadata authorize a scope. |
| Authentication | HTTP routes and production auth runtime are root-owned/out of scope. The use case accepts an unforgeable typed authority value constructed by root's verified auth + membership boundary. | Missing/invalid authority is non-authorizing and fails before Stripe. A plain PrincipalId/TenantId string is not proof. |
| Payment and access | Checkout completion/binding never proves payment. `invoice.paid` plus matching current complete items is necessary but not sufficient. | Access also needs valid current identity/membership, billing lifecycle and a separately authorized entitlement policy/port. Signup creates no default entitlement. |
| Overdue/cancel/refund/dispute | Overdue or unknown blocks increases and grants no new paid capacity; no affirmative grace. Period-end cancellation retains only previously paid-through verified capacity until its provider-confirmed boundary. | Full refund/dispute does not expand capacity and remains held until explicit policy. No new refund access rule is inferred. |
| Retry/reconciliation | Durable signed-event inbox, exact replay no-op, same event ID with changed fingerprint conflict, bounded retries/DLQ, current-state re-fetch before repair. | Events are notifications, not ordered complete truth; ambiguity remains UNKNOWN. |
| Persistence | Root approves separate durable SQLite subscriber store for purchase attempts, billing projection, signed inbox metadata and retry/DLQ state. | Keep subscriber tables isolated from Admin AO-10 data; no secrets/raw payload/card data. |
| Customer Portal | Portal must not expose uncontrolled plan/quantity changes. | Unless it can enforce the same one-scope/one-subscription/add-on-only/idempotent policy, use the AXIGNAL server-mediated update intent and Stripe-hosted invoice payment URL only. |

## Exact provider evidence checked

- Stripe's current [pending update guide](https://docs.stripe.com/billing/subscriptions/pending-updates) lists `items.quantity` as a supported pending-update parameter and documents that `always_invoice` creates and attempts the invoice; successful payment applies the pending update.
- Stripe's [Invoice object](https://docs.stripe.com/api/invoices/object) defines `hosted_invoice_url` as nullable and as the hosted payment page. AXIGNAL treats the returned string as untrusted until HTTPS host allowlist validation.
- Stripe's [Checkout Session line-items endpoint](https://docs.stripe.com/api/checkout/sessions/line_items) and [Subscription item listing](https://docs.stripe.com/api/subscription_items/list) are cursor-paginated. Embedded first-page items are not completeness evidence.

These documentation checks are not provider calls and do not claim live payment or sandbox behavior.
