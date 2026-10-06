# Verification Record â€” 047

## Scope and current status

Phase A's provider-neutral exact-binding validator and Phase B's subscriber
checkout path are implemented in separate domain/application/pipeline modules.
The slice includes a SQLite subscriber billing/owner store, a real but
credential-gated Stripe HTTP adapter, signed webhook verification, bounded
retry/DLQ worker, current provider reads, and a route-independent composition
factory. Root-owned identity, auth routes, runtime HTTP routes and frontend are
outside this feature's change set. The existing AO-10 metadata-derived
`checkout_mapping_from_verified_event()` remains untouched.

The new subscriber bridge blocks initial Checkout and capacity mutation unless
the approved catalogue contains current explicit active-registration evidence.
Root's LIVE readback confirms prices `price_1UNYXv8feyjV8PemcFisvBJ2` (base,
EUR 9.95 monthly) and `price_1UNYY88feyjV8PemyuI3unra` (additional Xeed,
EUR 4.95 monthly), both active/per-unit/exclusive; Tax Settings report active,
but the active registrations query returned an empty list. Thus this snapshot
has no `ApprovedTaxConfiguration`: attempts fail with
`TAX_CONFIGURATION_UNKNOWN` before Checkout or an update. The account catalogue
is documented in [APPROVED_LIVE_CATALOGUE.md](../../docs/audits/production-readiness-2026-10-06/APPROVED_LIVE_CATALOGUE.md).
Stripe's tax guidance says an active registration is required for automatic tax
to collect and that recording it in Stripe does not itself register the
merchant with a tax authority ([Stripe Tax reference](https://docs.stripe.com/references/tax.md)).
The code does not infer jurisdictional obligations or a universal VAT rate.

The new bridge is a separate subscriber path; it does not close the outstanding
COMM-09/legacy AO-10 metadata-mapping finding. Root route wiring, required tax
registration evidence, production secret configuration, a paid LIVE journey,
refund/dispute operations and production deployment are still separate work.
No Stripe API/provider calls or writes were made by this implementation agent;
the catalogue/tax facts above are root-provided read-only observations.

## Checks

| Check | Result | Notes |
|---|---|---|
| Focused pytest | PASS â€” 69 passed | `uv run --offline pytest -q --basetemp D:\AXIGNAL\Worktrees\test-artifacts\pytest-billing-phaseb-final-20261006 tests/admin_billing`; deterministic fixtures only. |
| Ruff | PASS | `ruff check` and `ruff format --check` on changed billing modules/tests; all passed after formatting. |
| Syntax parse | PASS â€” 7 files | Python AST parse for changed application/domain/adapter/store/test modules. |
| Spec Kit prerequisites | Earlier PASS for Phase A | Not rerun after Phase B update. |
| Stripe docs | Read-only review | Official API references support `pending_if_incomplete`, `always_invoice`, and item `quantity`; local setting pins `2025-06-30.basil`, and no live mutation/payment verified the version-specific runtime. [`Subscription update`](https://docs.stripe.com/api/subscriptions/update?api-version=2025-04-30.basil), [`Subscription Item update`](https://docs.stripe.com/api/subscription_items/update), [`Stripe Tax`](https://docs.stripe.com/references/tax.md). |
| Provider network/writes | NOT RUN by this agent | Fake HTTP transport only; runtime construction makes no calls; checkout remains blocked by absent registration evidence. |
| Repository-wide gates | Pending root | Root owns full pytest, mypy, architecture guard, governance and final integration cross-review. |

## Coverage and limits

The full `tests/admin_billing` run passed 69 cases. Coverage includes initial capacity 1/2/100, same-subscription
expansion 1â†’2/100, duplicate clicks, stable idempotency after a prepared
provider failure, unknown payment, paid-through cancellation/expiry, transient
UNKNOWN recovery, missing tax configuration, Price tax-behavior mismatch,
automatic-tax disabled, refund/dispute evidence, full line-item pagination,
signed webhook replay/signature checks, durable owner receipts, and 8 MiB
transport response bounds in source. These fixture tests do not establish a
real payment, actual tax collection, exact live pinned-version mutation,
identity/auth/HTTP end-to-end, production deployment, or the legacy AO-10 path.

The store still needs dedicated tests for duplicate request and conflicting
event fingerprints, monotonic projection conflicts and lifecycle races.
Retries are bounded with deterministic capped exponential delay; jitter and an
operator-facing inbox repair workflow are not included. Checkout/update can
still race an out-of-band Dashboard subscription edit between the final current
read and mutation; that limitation is documented and does not grant capacity
without subsequent exact reconciliation.
