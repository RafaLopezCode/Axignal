# Subscriber Identity and Session Contract

## Provider configuration

Each OIDC provider is configured by the root-owned runtime configuration loader and injected as a typed immutable configuration. It includes provider ID, exact issuer, client ID, server-only client-secret reference where required, exact callback URI, configured client subject scope, enabled/registration status, and validated discovery/token/JWKS endpoints anchored to that issuer. Missing or incomplete configuration disables the provider with a safe reason; it does not fall back to another provider.

Google is the first supported provider. OpenAI Sign in with ChatGPT uses the official SIWC issuer and endpoints only when AXIGNAL has a registered client and access. ChatGPT's selected-partner availability is not assumed. No API token, Codex session, password submitted to AXIGNAL, or arbitrary issuer URL is accepted.

## API-facing application interfaces

```text
VerifiedExternalIdentity(issuer, subject, client_id=None)
SignInStart(authorization_url, transaction_token, expires_at)
IssuedSubscriberSession(principal_id, tenant_id, session_token, expires_at)
TrustedSubscriberContext(principal_id, tenant_id)

SubscriberAuthenticationService.begin_sign_in(provider_id, intent, now)
  -> SignInStart
SubscriberAuthenticationService.complete_sign_in(
    provider_id, transaction_token, state, code, now
) -> IssuedSubscriberSession
SubscriberAuthenticationService.resolve_session(session_token, now)
  -> TrustedSubscriberContext
SubscriberAuthenticationService.revoke_session(session_token, now)
  -> RevocationResult
```

`intent` is explicit `REGISTER` or `LOGIN`. An unknown binding during `LOGIN` never creates an account; an unknown binding during explicit `REGISTER` may use the atomic first-subscriber bootstrap. A known identity under `REGISTER` resolves to the existing subscriber.

## Provider adapter

```text
OidcProviderPort.begin(config, transaction) -> authorization_url
OidcProviderPort.exchange_and_verify(config, transaction, code)
  -> VerifiedExternalIdentity
```

The adapter uses Authorization Code + PKCE S256, configured issuer/client/callback, nonce, state and a maintained OIDC/JWT library. It validates signature/JWKS, exact issuer, client audience/authorized party, time claims, nonce and exact redirect. It returns no token, email or authority role to application policy. OAuth errors are sanitized and no token/code/secret appears in `repr` or logs.

## Durable ports

```text
OidcTransactionStore.create(transaction, now) -> StoredTransactionRef
OidcTransactionStore.consume_once(provider_id, transaction_token, state, now)
  -> OidcTransaction

SubscriberBootstrapStore.register(identity_key, principal_id, tenant_id, now)
  -> RegisteredSubscriber

InitialPurchaseScopeProvisioner.ensure_initial_purchase_scope(
    principal_id, initial_tenant_id, registration_key
) -> PurchaseScopeProvisioningReceipt

SubscriberSessionStore.issue(principal_id, tenant_id, token_hash, now, expires_at)
SubscriberSessionStore.resolve(token_hash, now) -> ActiveSubscriberSession | None
SubscriberSessionStore.revoke(token_hash, now) -> RevocationResult
```

`consume_once` atomically compares provider, client, state and expiry and marks consumed before code exchange; duplicate callback cannot redeem twice. Invalid/missing/expired/replayed transaction is non-authorizing. `register` atomically inserts binding, Principal, initial Tenant and membership under uniqueness constraints; on an identity uniqueness race it returns only the exact already-created Principal/Tenant, never duplicate provisioning.

After successful explicit REGISTER (including repeat REGISTER of the same exact identity), the authentication service calls the billing-owned `InitialPurchaseScopeProvisioner` with the registered Principal/Tenant and stable opaque registration key. The operation is idempotent and records purchase authority for the initial scope only; it grants no capacity. The service does not call it during LOGIN. Billing confirms the owner separately on every checkout request. Because the identity and billing authorities are separate stores, a provisioning outage leaves identity bootstrap durable but registration returns a retryable provisioning-pending outcome and no checkout authority; repeated REGISTER retries the same idempotent provisioning operation. Root runtime composition supplies this port.

`PrincipalTenantMembershipReader` is rechecked for each portfolio request. A session is not permanent membership authority.

## HTTP cookie boundary owned by runtime composition

- Start returns an authorization URL plus opaque transaction token; runtime puts the token in a short-lived `__Host-` HttpOnly, Secure, SameSite=Lax, Path=/ cookie.
- Callback reads that cookie and exact provider route plus OIDC `state`/`code`; query parameters cannot choose client, issuer or redirect.
- Successful callback rotates to a high-entropy server-side session cookie with the same `__Host-` security attributes. Raw token is stored only as a hash.
- Logout/revocation clears cookie and records revocation; session lookup after restart still rejects it.
- Production and local callback URIs are exact per environment; no wildcard/local HTTP URI is enabled in production.
