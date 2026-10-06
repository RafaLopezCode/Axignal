# Implementation Plan: Subscriber Checkout and Billing Bridge

**Branch**: `codex/production-closure` | **Date**: 2026-10-06 | **Feature**: [spec.md](spec.md)
**Architecture disposition**: Root approved Phase B design and initial expansion proration policy before implementation.

## Summary

Complete the subscriber billing path behind explicit root-owned authentication and membership authority. Initial signup creates one server-owned Checkout for an approved total capacity. Later increases target the same subscription with absolute add-on quantity `desired_totalâˆ’1`; they use `always_invoice` and `pending_if_incomplete`, stay `pending_purchase`, and affect effective capacity only after the invoice is paid and a complete current binding snapshot matches. Durable SQLite subscriber state, signed webhook inbox and reconciliation are isolated from Admin AO-10. LIVE development is explicitly selected, but provider writes and any payment completion are root-controlled; the implementation and deterministic tests are offline by default.

The already implemented Phase-A validator remains pure, provider-neutral and grant-free. `checkout_mapping_from_verified_event()` remains unsafe for subscriber authority and is not called by the new path.

## Technical Context

**Language**: Python 3.11+, standard-library domain/application; Stripe SDK/transport only in the Stripe pipeline adapter.
**Runtime**: Root-owned Python HTTP routes call `tools/runtime/subscriber_checkout.py`; this feature adds no route or auth module.
**Storage**: Separate SQLite subscriber billing tables/connection, injected into pipeline store; no AO-10/Admin table or event log reuse.
**Provider**: Configurable Stripe adapter with pinned API version and explicit environment. Current prices are resolved through root-approved versioned catalogue; never hard-coded into domain.
**Testing**: Deterministic fake ports and mocked transport, no network or sockets. Required fixtures cover initial and expansion capacities 1/2/100.
**LIVE**: Human selected LIVE-only development. Root owns real Stripe writes and catalogue approval. CI must not default to live; this agent will not complete a payment.
**Scale**: Bounded full pagination with cursor-progress/duplicate detection; uncertainty or page failure is UNKNOWN.

## Constitution Check

| Gate | Plan |
|---|---|
| MASTER / money | Pass: persistent Organization observation is the unit, signals are non-billable; â‚¬9.95/â‚¬4.95 remain a price hypothesis under MASTER Â§27. |
| Truth separation | Pass: billing and subscriber state is private Admin/service state; Stripe never writes AXIGLAND or changes Organization facts. |
| UNKNOWN | Pass: missing auth, membership, catalogue, provider pages, currentness or payment remains non-positive. |
| Provider boundaries | Pass: provider-neutral domain/application, Stripe reads/writes only in pipeline adapter. |
| Auth boundary | Pass only with explicit root-constructed purchase-authority object; this feature does not implement or infer authentication. |
| Billing/access boundary | Pass: binding, payment, lifecycle, Tenant capacity and entitlement are separate; no signup grant. |
| LIVE exception | Human selects LIVE-only; root will amend the accepted ADR to record the exception. No fictitious sandbox evidence; no production activation from non-completed Checkout. |
| Deterministic CI | Pass by design: fakes only, live config absent in CI, tests require no provider/network. |

## Architecture and Data Flow

See [Phase B architecture](phase-b-architecture.md) for exact ownership, lifecycle, flows and gates.

```text
Root HTTP/Auth boundary
  â†’ SubscriberPurchaseAuthority (Principal + Tenant + live membership evidence)
  â†’ approved offer catalogue â†’ immutable intent and durable attempt
  â†’ Stripe Checkout create OR same-subscription absolute quantity update
  â†’ signed webhook inbox metadata â†’ full current Session/Subscription/Invoice reads
  â†’ Phase-A binding validator â†’ billing/payment projection
  â†’ explicit entitlement-policy evaluation (no default grant)
  â†’ independently authorized Tenant/Xeed read path
```

Any route request without an authenticated actor, successful membership read,
one authorized Tenant scope, approved current catalogue, and current eligible
subscription for expansion returns an unavailable/UNKNOWN outcome before a
Stripe mutation. Provider metadata is correlation only. Routes never interpret
success redirect as a billing fact.

## Storage and Processing Design

- `subscriber_purchase_intents`: immutable initial desired total or capacity-change target; scoped to opaque authorized Tenant reference; catalogue version; actor/request-authority evidence reference; provider environment and version.
- `subscriber_checkout_attempts`: stable attempt/idempotency identity and Checkout/customer/subscription references; no secret/payment credentials.
- `subscriber_billing_state`: current fully reconciled provider refs, effective paid capacity, current payment/lifecycle/currentness, last evidence and paid-through facts; requested capacity stays separate.
- `subscriber_webhook_inbox`: event ID/type/time/account/environment, payload fingerprint, processing disposition and safe references; raw body/signature/header/secret never persisted.
- `subscriber_retry_dlq`: bounded attempt count, next retry, safe failure category, DLQ reason and audited recovery marker.
- All mutating operations use DB transactions and unique constraints for idempotency. A transaction commits intent before the network call; successful or ambiguous provider responses are reconciled using references/idempotency key, never guessed.
- No grant is executed in the billing adapter. A separately injected entitlement port is evaluated only after exact identity, membership, binding, paid invoice, current lifecycle and policy evidence.

## Provider Adapter Rules

- Explicit `environment=live|test`; no test fallback or live default. Live-write methods require root-owned composition/configuration and remain disabled in tests by missing transport.
- Before initial Checkout, verify configured approved Price references and provider facts: expected active state, livemode, product/price identity, EUR, monthly recurrence/count and integer amount. Unknown or mismatch blocks Checkout.
- Initial capacity uses one approved base item, quantity one, plus optional approved add-on `totalâˆ’1`.
- Expansion identifies the existing add-on subscription-item ID and updates its **absolute** quantity to `desired_totalâˆ’1`, with the stored subscription reference, pinned API version, `proration_behavior=always_invoice`, `payment_behavior=pending_if_incomplete`, and durable per-intent idempotency key. Never create another Subscription/base item.
- Stripe pending updates support `items.quantity`; if current pinned version/collection method/payment method does not support this behavior, return safe unsupported/UNKNOWN. Never silently fall back to update-before-payment behavior.
- Fully paginate Checkout Session lines and Subscription items. Ignore embedded first-page lines for completeness. Detect cursor loops, duplicate IDs, missing `has_more`, wrong account/livemode/object ownership and partial errors.
- Safe pay URL: retrieve latest invoice by verified subscription/invoice reference; return `hosted_invoice_url` only when its parsed origin is HTTPS and host is in explicit runtime allowlist. Treat null/non-final invoice, unparsable URL, credentials, non-default port or unapproved host as no-link/pending. Do not return client secret or raw provider URL.

## Reconciliation and Lifecycle

- Stripe events authenticate by signed raw request body and configured endpoint secret before event replay checks; durable inbox acceptance precedes acknowledgment.
- Exact event replay: no-op; same ID/new fingerprint: quarantined conflict; event arrival/time alone cannot order current state.
- Process events by retrieving current Session, Subscription and associated Invoice plus all subscription item pages, then invoke binding validator; stale, equal-time ambiguous, unavailable, or partial reads remain UNKNOWN.
- Transient provider/SQLite errors receive bounded retry/backoff; permanent signature/reference/payload violations reject; exhausted retries become DLQ. Recovery reads current provider state before mutation.
- Invoice `paid` is necessary payment-success evidence, associated to the correct customer/subscription/attempt. Checkout completion is never payment proof.
- `pending_purchase` has no capacity increase. Failed or abandoned action-required payment retains last verified effective capacity only. Expired/void invoice discards the desired change after reconciliation.
- Overdue/unknown blocks capacity increases. Cancellation-at-period-end retains currently paid-through verified capacity only until provider-confirmed boundary. No grace-period access is inferred. Full refund/dispute leaves expansion pending until a separately approved policy; it never increases capacity.

## Runtime Integration Contract

`tools/runtime/subscriber_checkout.py` exposes a route-independent boundary for root's web runtime. Exact type/method/payload JSON examples are in [subscriber checkout contract v1](contracts/subscriber-checkout.v1.md). Root owns route paths/status codes and auth/session construction. The feature accepts only a typed purchase authority supplied by that boundary; it does not accept raw principal/tenant strings as proof.

## Validation

Focused checks: `pytest tests/admin_billing`, Ruff on touched files, focused mypy, Architecture Guard and governance. Test store uses isolated temporary SQLite and mocked Stripe transport; no provider calls or sockets. Root will run repository-wide gates and review before any LIVE operation. This agent will report exact pass/fail and coverage denominators, never claim sandbox/live paid E2E from fixtures.
