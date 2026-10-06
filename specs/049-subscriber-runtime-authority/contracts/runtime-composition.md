# Runtime Composition Contract

Root-owned `tools/runtime/config.py` and `tools/runtime/service.py` are the only composition owners. They load environment-specific values by configured file paths and pass immutable typed settings to these feature faÃ§ades. The feature never reads ambient secrets or scans arbitrary files.

## Identity settings

```python
@dataclass(frozen=True)
class OidcProviderConfig:
    provider_id: OidcProviderId
    issuer: str
    client_id: str
    redirect_uri: str
    enabled: bool
    registered: bool
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    client_secret_path: Path | None = None
    client_scope: str | None = None
```

The root loader verifies configuration completeness and the configured exact issuer/endpoints. It reads a client secret only through the declared server-only path where the provider requires one. An incomplete or unregistered provider is omitted/disabled with a safe public reason. No OAuth client IDs, secrets, or endpoints are accepted from requests. Production provider callback values must match the exact deployment environment. OpenAI SIWC remains disabled unless AXIGNAL has an approved, provisioned partner client.

```python
class SubscriberIdentityRuntime:
    def start(self, provider_id: OidcProviderId, intent: AuthIntent) -> SignInStart: ...
    def callback(
        self,
        provider_id: OidcProviderId,
        transaction_token: str,
        state: str,
        code: str,
    ) -> IssuedSubscriberSession: ...
    def authenticate(self, session_token: str) -> TrustedSubscriberContext: ...
    def logout(self, session_token: str) -> RevocationResult: ...


def build_subscriber_identity_runtime(
    data_dir: Path,
    providers: Mapping[OidcProviderId, OidcProviderConfig],
    clock: Clock,
    purchase_scope_provisioner: InitialPurchaseScopeProvisioner,
) -> SubscriberIdentityRuntime: ...
```

`SignInStart` returns `authorization_url`, a high-entropy opaque `transaction_token`, and expiry. Root HTTP sets transaction token as a short-lived `__Host-` cookie with `Secure`, `HttpOnly`, `SameSite=Lax`, and `Path=/`. Callback passes the cookie value and route-selected provider alongside state/code; it never accepts a client-selected issuer, client, callback URI, or tenant. After successful callback, HTTP replaces the transaction cookie with the issued high-entropy session token using the same cookie attributes. Raw tokens are returned once to HTTP and never persisted or logged; stores persist only hashes. The runtime accepts an injected clock for deterministic expiry tests. Defaults are 10 minutes for an OIDC transaction and 24 hours for a subscriber session; root sets matching cookie lifetimes and does not silently extend the server policy.

## Identity application and persistence types

```python
VerifiedExternalIdentity(issuer: str, subject: str, client_id: str | None)
RegisteredSubscriber(principal_id: PrincipalId, tenant_id: TenantId)
TrustedSubscriberContext(principal_id: PrincipalId, tenant_id: TenantId)

SubscriberAuthenticationService(
    provider_configs: Mapping[OidcProviderId, OidcProviderConfig],
    provider: OidcProviderPort,
    transactions: OidcTransactionStore,
    bootstrap: SubscriberBootstrapStore,
    sessions: SubscriberSessionStore,
    memberships: PrincipalTenantMembershipReader,
    purchase_scope_provisioner: InitialPurchaseScopeProvisioner,
    clock: Clock,
)
```

The first-subscriber bootstrap operation atomically records `(issuer, subject, configured client scope)`, Principal, initial Tenant and binary membership. LOGIN only resolves an existing exact binding. REGISTER is an explicit intent; only it may create the first binding. A known binding with REGISTER returns its existing subscriber. A uniqueness conflict resolves to the exact existing identity mapping and cannot create a second Tenant. Email is not a binding key. If a Principal later has multiple memberships, no arbitrary Tenant is selected; runtime returns a context-selection-required result until an explicit product contract supplies selection.

After bootstrap commits, only explicit REGISTER calls the injected billing-owned `InitialPurchaseScopeProvisioner.ensure_initial_purchase_scope(principal_id, initial_tenant_id, registration_key)`. This records initial purchase authority separately from membership and grants no capacity. The operation must be idempotent and re-run for an already-known identity on repeated REGISTER so a cross-store outage can recover. LOGIN never provisions. Billing's current purchase-authority answer is checked again on each checkout request.

`OidcProviderPort` implements Authorization Code + PKCE S256 and OIDC validation with a maintained library. `exchange_and_verify(config, transaction, code)` returns only `VerifiedExternalIdentity`; it validates exact issuer, signature/JWKS, audience/authorized party, expiry/issued-at, nonce and redirect/client binding. OAuth tokens do not escape the adapter and are not stored after validation. OIDC transaction stores atomically consume the provider + configured client + browser transaction token + state exactly once before code exchange. PKCE verifier and nonce are server-side transaction data with short expiry.

## Portfolio application and persistence types

```python
class SubscriberPortfolioRuntime:
    def list(self, context: TrustedSubscriberContext) -> tuple[PortfolioEntry, ...]: ...
    def list_pending(
        self, context: TrustedSubscriberContext
    ) -> tuple[PendingAttentionEntry, ...]: ...
    def retry_pending(self, context: TrustedSubscriberContext, pending_id: str) -> AddResult: ...
    def cancel_pending(
        self, context: TrustedSubscriberContext, pending_id: str, idempotency_key: str
    ) -> PendingAttentionEntry: ...
    def add(
        self, context: TrustedSubscriberContext, request: AddOrganizationRequest
    ) -> AddResult: ...
    def pause(
        self, context: TrustedSubscriberContext, focus_id: FocusId, idempotency_key: str
    ) -> PortfolioCommandResult: ...
    def resume(
        self, context: TrustedSubscriberContext, focus_id: FocusId, idempotency_key: str
    ) -> PortfolioCommandResult: ...
    def remove(
        self, context: TrustedSubscriberContext, focus_id: FocusId, idempotency_key: str
    ) -> PortfolioCommandResult: ...
    def replace(
        self,
        context: TrustedSubscriberContext,
        focus_id: FocusId,
        target: AddOrganizationRequest,
        idempotency_key: str,
    ) -> ReplaceResult: ...
    def reobserve(
        self, context: TrustedSubscriberContext, focus_id: FocusId, idempotency_key: str
    ) -> ObservationRunResult: ...


class ObservationTriggerPort:
    def trigger(
        self, context: TrustedSubscriberContext, focus_id: FocusId, idempotency_key: str
    ) -> str: ...
```

```python
SubscriberPortfolioService(
    portfolio: SubscriberPortfolioStore,
    memberships: PrincipalTenantMembershipReader,
    entitlement: EntitlementPort,
    organization_resolution: OrganizationResolutionPort,
    observation_trigger: ObservationTriggerPort,
    purchase_authority: PurchaseAuthorityPort,
    checkout: CapacityCheckoutPort,
    clock: Clock,
)
EntitlementSnapshot(capacity: int | None, currentness: Currentness, confirmed_at: datetime | None)
PurchaseAuthorityPort.resolve(context, now) -> PurchaseScopeAuthorization | None
CapacityCheckoutRequest(context, authorization, current_capacity, additional_count, idempotency_key)
CapacityCheckoutRequest.desired_capacity == current_capacity + additional_count
CapacityCheckoutPort.request_checkout(request) -> CheckoutRequestResult

PurchaseScopeAuthorization(principal_id, tenant_id, authority_ref, membership_ref, checked_at)

SubscriberPortfolioStore.get_authorized(context, focus_id) -> PortfolioEntry | None
SubscriberPortfolioStore.list_authorized(context) -> tuple[PortfolioEntry, ...]
```

The runtime accepts `TrustedSubscriberContext` only from the authenticated root request dependency. Application services still verify current membership before reading any private Focus, pending request, output, reservation or projection. Mutation transactions recheck membership and capacity while serializing additions. For capacity above the confirmed limit, service asks the root-provided `PurchaseAuthorityPort.resolve(context, now)` for a typed receipt containing exact Principal/Tenant, authority reference, membership reference and checked time. It passes the validated context and receipt into `CapacityCheckoutRequest`, together with known current capacity and exact positive delta. Root adapts billing's `AuthorizedPurchaseScope` to this local receipt without making 049 depend on billing. No actor is inferred from Tenant. No Focus is created, and browser checkout return cannot change entitlement. Active and paused Focuses consume a slot. Unknown/stale entitlement returns a blocked/unknown result and does not add a Focus.

`OrganizationResolutionPort.resolve(locator)` returns only a canonical Organization from the AXIGLAND authority after governed identity resolution, or a typed pending/rejected result. It never promotes the input locator, registry candidate or display label. Pending identity may create a private pending request without canonical Organization/Focus/output. Pending rows survive restart and are listed only after current membership authorization; subscribers may retry or cancel them. A retry may transition the same pending request to ADD only when its idempotency key, locator and label are unchanged, the resolver now returns a canonical Organization, and serialized confirmed capacity permits the Focus. RESOLVED/CANCELLED rows remain as audit tombstones. Observation triggers receive the trusted Principal+Tenant context so durable work can record its requester and recheck membership before work; they never infer a Principal from Tenant. Canonical writes remain behind existing EvidenceAdmission paths.

## HTTP result mapping

Root's HTTP adapter maps typed outcomes to transport status and safe public code, retaining epistemic states:

| Typed outcome | Suggested API code | Meaning |
|---|---|---|
| Provider unavailable/unregistered | `AUTH_PROVIDER_UNAVAILABLE` | No login attempt started |
| Invalid, expired or replayed transaction | `AUTH_TRANSACTION_INVALID` | No session issued |
| Unknown identity on LOGIN | `AUTHENTICATION_REQUIRED` | No account provisioned |
| Membership unavailable/revoked | `ACCESS_DENIED` | Private storage was not read |
| Entitlement unknown/stale | `CAPACITY_UNKNOWN` | No new active Focus |
| Capacity exceeded | `CHECKOUT_REQUIRED` | Exact checkout request returned, no Focus |
| Organization unresolved | `IDENTITY_PENDING` | No canonical or output claim |
| Accepted add/reobserve | `ACCEPTED` | Durable command/run ID returned; output state remains explicit |

The adapter must not serialize provider tokens, OAuth codes, transaction/session token values, internal exception reprs, SQLite paths, or subscriber data for errors.
