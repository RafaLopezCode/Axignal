# Checkout Binding Contract v1

**Status**: Implemented as an offline provider-neutral contract; not connected to Checkout or webhooks.

## API

`application.admin_billing.checkout_binding.validate_checkout_binding(...)`
accepts an optional `PurchaseIntent`, `ApprovedOfferCatalogue`,
`CheckoutAttemptBinding`, `SubscriptionItemSnapshot`, and an optional previous
`BindingValidationResult`. It returns an immutable result and performs no I/O
or state mutation.

Domain types are declared in `domain.admin_billing.checkout_binding`. They are
imported explicitly from that module; package `__init__.py` files are unchanged.

## Input contract

- An intent is AXIGNAL-owned and authorized before a future Checkout attempt;
  it fixes the catalogue version, capacity and environment. Payer/scope identity
  is deliberately absent.
- The attempt binding is a server-owned association between the intent/attempt
  and opaque Checkout session, customer and subscription references. It is an
  input trust boundary, not cryptographic proof: producers must not construct
  it from subscriber-supplied or provider metadata alone.
- A future provider reader must obtain binding references through the
  authorized server-owned attempt record and verify the Checkout-to-customer-
  to-subscription relationship from provider facts. It must attest that its
  snapshot is provider-current, carry a stable state/evidence reference and
  establish complete pagination. A signed event by itself does not establish
  that line items are complete or current.
- A snapshot carries the same object/environment references, state identity and
  time, currentness, complete-enumeration/pagination facts (`has_more` must be
  explicitly false), optional metadata
  correlation, and all normalized recurring items. `None` means the fact is
  unknown, never false or zero.
- Chronology must satisfy `intent.authorized_at <= binding.established_at <=
  snapshot.retrieved_at` and `intent.authorized_at <= provider_state_at <=
  snapshot.retrieved_at`. There is no required ordering between provider state
  time and local binding establishment time.
- Each normalized item has an opaque offer reference, positive known quantity,
  recurring flag and terms. The recurring offer catalogue is versioned and
  supplied as input. No live/test provider names, SDK classes or concrete price
  IDs are encoded in the domain.

## Output contract

| Status | Meaning | Capacity fields |
|---|---|---|
| `VERIFIED` | Complete, current, exact item-to-intent binding under the supplied catalogue and attempt binding. | Present; derived from base plus additional-Xeed quantities. |
| `MISMATCH` | Known contradiction or conflicting replay. | Always null. |
| `UNKNOWN` | Missing, incomplete, stale, unapproved-by-catalogue-reference, or ambiguous evidence. | Always null. |

Every result carries a stable reason enum. When a snapshot is present, its
canonical `sha256:` fingerprint excludes retrieval time but includes intent,
catalogue, attempt binding, state reference/time, object references,
currentness, completeness, metadata correlation and the sorted full item set.
Exact evidence replay reruns deterministic validation from the current inputs;
the prior result is comparison data only and never supplies capacity authority.
The complete recomputed result must equal a prior VERIFIED result or the replay
is `MISMATCH/CONFLICTING_REPLAY`. Reuse of an evidence reference with changed
normalized content is also `MISMATCH/CONFLICTING_REPLAY`.

## Required consumer behavior

- Do not interpret `VERIFIED` as paid, authenticated, entitled, or authorized to
  access a Tenant/Xeed.
- Keep the separate AO-10 `invoice.paid` payment verification unchanged.
- Do not pass metadata-derived capacity to entitlement logic as a substitute
  for this validator. Existing AO-10 runtime is not modified in this phase.
- Treat `MISMATCH` and `UNKNOWN` as non-positive; send reconciliation work only
  through a separately authorized operational path.

## Compatibility / versioning

Version 1 is a new offline contract with no persisted data migration and no
package-level re-export. Any later addition of provider retrieval, storage,
Checkout creation or grant behavior requires a new reviewed slice and does not
follow from this contract's status.
