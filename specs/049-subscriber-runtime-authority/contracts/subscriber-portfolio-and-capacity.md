# Subscriber Portfolio and Capacity Contract

## Service surface

```text
AddOrganizationRequest(idempotency_key, locator, display_label=None)
EntitlementSnapshot(capacity: int | None, currentness, confirmed_at)
CapacityCheckoutRequest(tenant_id, additional_count, idempotency_key)

SubscriberPortfolioService.list(context) -> tuple[PortfolioEntry, ...]
SubscriberPortfolioService.add(context, request) -> AddResult
SubscriberPortfolioService.pause(context, focus_id, idempotency_key) -> PortfolioCommandResult
SubscriberPortfolioService.resume(context, focus_id, idempotency_key) -> PortfolioCommandResult
SubscriberPortfolioService.remove(context, focus_id, idempotency_key) -> PortfolioCommandResult
SubscriberPortfolioService.replace(context, focus_id, target, idempotency_key) -> ReplaceResult
SubscriberPortfolioService.reobserve(context, focus_id, idempotency_key) -> ObservationRunResult

EntitlementPort.snapshot(tenant_id) -> EntitlementSnapshot
CapacityCheckoutRequest(context, authorization, current_capacity, additional_count, idempotency_key)
CapacityCheckoutRequest.desired_capacity == current_capacity + additional_count
CapacityCheckoutPort.request_checkout(request)
  -> CheckoutRequestResult
OrganizationResolutionPort.resolve(locator)
  -> CanonicalOrganization | OrganizationIdentityPending | OrganizationIdentityRejected
```

Root owns HTTP routing and the billing contract implementation. Tenant is the consumption scope passed to EntitlementPort; the port never treats it as payer identity.

## Authorization and capacity order

1. Resolve the opaque subscriber session to server-issued Principal/Tenant context.
2. Load the Principal and current binary membership. If denied or unavailable, stop before private Focus/portfolio/projection read.
3. For every mutation transaction, recheck membership under the same durable store transaction.
4. Resolve current entitlement from the server-side port. A missing or stale capacity is unknown and cannot authorize a positive capacity delta.
5. Count active, paused and live-reserved Focus slots under a serialized transaction. Never accept a client-provided count or maximum.
6. If an addition exceeds capacity, request checkout for the exact positive delta and return `CHECKOUT_REQUIRED` without an active Focus. Browser success/return changes no entitlement.
7. Only a separate verified billing authority update changes the snapshot. Then a retry can create Focuses within the new confirmed capacity.

## Organization resolution and Focus creation

- `locator` and `display_label` direct attention only. Provider-supplied candidate names, domains and registry identifiers remain untrusted input.
- A canonical Organization object/ID may be returned only by the global Organization authority or its separately governed bootstrap after identity evidence is resolved/admitted. Public registers are candidate sources, not canonical stores.
- If identity is pending, return `IDENTITY_PENDING`; persist only a private pending request if the authority allows it. Do not create a Focus, Organization, FAXT, or output.
- Pending requests are durable, membership-scoped private attention entries. The same request can be retried or cancelled. Retry may create a Focus only for the original locator and label after canonical resolution and an atomic capacity check; resolved/cancelled rows remain as tombstones.
- Observation trigger commands receive the authenticated `TrustedSubscriberContext` so the durable job can record the requesting Principal and Tenant and recheck membership before processing.
- Once canonical Organization is resolved, a durable unique `(tenant_id, organization_id)` constraint prevents duplicate Focuses in one Tenant. Distinct Tenants may hold separate Focuses pointing to the same Organization.
- Focus create stores private ownership/reference and triggers an idempotent observation run. Canonical writes still require the independent EvidenceAdmission path.

## Lifecycle semantics

| Command | Result | Capacity | Prior successful output |
|---|---|---:|---|
| Add | One resolved Focus or pending identity/checkout result | Active Focus consumes one; pending capacity hold is bounded and idempotent | Not applicable |
| Pause | Future scheduled observation stops; entry remains visible | Consumes one | Retained and readable |
| Resume | Revalidate capacity/currentness, then observation resumes | Consumes one | Retained until newer success |
| Remove | Private Focus leaves active portfolio; no future work | Frees one | No longer active; global canonical truth remains untouched |
| Replace | Stage target, resolve identity, then atomically swap Focus references | One slot for one-for-one replacement; no transient extra active slot | Old remains until swap succeeds |
| Reobserve | Create one new run for existing Focus | No additional Focus slot | Retained until the new run passes output/evidence readiness |

Replacement or reobservation failure leaves the old Focus/output usable and reports the failed attempt truthfully. Removal/erasure retention policy remains separate; this contract does not delete AXIGLAND truth.

## Durable repository obligations

File-backed adapters enforce unique IDs, FK constraints, idempotency uniqueness and transactional capacity serialization. Reads after restart return only current authenticated membership scope. An unavailable/corrupt database never returns cached private data or a positive authorization. Production backup/restore, multi-host consistency and high availability remain outside this contract.
