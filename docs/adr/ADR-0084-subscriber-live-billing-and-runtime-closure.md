# ADR-0084: Subscriber runtime and explicitly authorized live billing closure

- **Status:** Accepted for the implementation campaign; external enablement and verification remain separate.
- **Date:** 2026-10-06
- **Authority:** MASTER Â§Â§5â€“7, 15, 27, 54â€“56; Constitution; direct human instruction.
- **Scope:** subscriber authentication, private observation portfolio, billing and evidence-backed outputs.

## Context and human authority

The human requested completion of the commercial E2E with Luna agents, specified
Google and ChatGPT sign-in, and answered the sandbox question: **â€œNO, todo se
debe hacer en live.â€** The human also specified purchasing additional observed
Organizations from the subscriber dashboard. This supersedes ADR-0061's sandbox
prerequisite for this campaign only; it does not supersede payment verification,
item binding, deployment controls or the economic truth firewall. Required CI
remains deterministic and cannot contact live providers.

## Decisions

1. Google and officially registered Sign in with ChatGPT are configurable OIDC
   adapters. Exact registered issuer/client/callback, signature, audience,
   expiry, nonce, browser-bound state and PKCE are checked before a first-party
   session. An unconfigured or unauthorized provider remains unavailable.
   ChatGPT identity does not authorize AI-plan usage. Emails do not link actors.
2. Verified first registration atomically creates an internal Principal,
   initial private Tenant, binary membership and external-identity binding.
   Tenant remains consumption/isolation scope, not payer or Organization.
   The registering Principal receives a separately recorded initial purchase
   authority for that scope. No shared-team roles/invitations are inferred.
3. SQLite is the first single-host durable adapter, consistent with the runtime's
   existing persistence. It requires transactions, uniqueness, restart and
   isolation checks. Multi-host availability and operational recovery are not
   inferred from local storage tests.
4. New private observation requires current server-resolved paid capacity and
   independently resolved global Organization identity. Unresolved identity is
   pending attention. User labels/URLs never author canonical economic facts.
   Pause retains a slot; removal releases private attention without deleting
   public truth. Replacement and retries are transactional and preserve history.
5. Billing uses the MASTER's current self-service offer: EUR 9.95 monthly for
   one observed Organization and EUR 4.95 monthly per additional Organization.
   These amounts are a price hypothesis, not proven value or margin. Signals
   remain non-billable. Catalogue references are deployment configuration.
6. Initial purchase creates one subscription. Expansion changes absolute addon
   quantity to desired total minus one on that same subscription, using reviewed
   Stripe `always_invoice` proration and `pending_if_incomplete`. The subscriber
   sees the provider-hosted invoice when payment action is required. Duplicate
   requests cannot create another subscription, increment twice or charge twice.
7. Browser returns, metadata, Checkout completion and requested quantities are
   not entitlement authority. Full provider item evidence, independent verified
   invoice payment, lifecycle and scope binding must agree before expansion.
   Missing/partial/stale/conflicting evidence cannot grant capacity.
8. Live catalogue and uncompleted Checkout verification are permissible under
   the direct human instruction. No real payment is completed by the agent.
   Actual payment/renewal/refund evidence remains outstanding until observed.
   Live-only development is not a reason to use fixtures as external evidence.
9. Subscriber HTTP, sessions and UI are separate from internal Customer Zero
   and Admin grants. All private reads and evidence links reauthorize scope.
   UI plans can reference only server-authorized output IDs and revisions.
10. Public contracting requires configured, published responsible-party and
    consent/terms authority. Missing legal identity is not invented. Production
    deployment requires the repository's explicit deployment authorization.

## Consequences and verification

Features 049, 050 and 051 and Phase B of 047 implement these seams. Local tests
cover the real application services, durable adapters, HTTP/proxy and rendered
journey, with external fixtures explicitly identified. Provider registration,
live payment lifecycle, exact deployed candidate, operational drills and human
visual/comprehension acceptance retain their own evidence states. No gate is
weakened and no claim of production readiness follows from this ADR alone.

## Sources

- [OpenAI website sign-in](https://developers.openai.com/siwc/website): registered
  commercial client availability and identity-only OIDC flow.
- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect):
  client registration and token validation.
- ADR-0018/0021, ADR-0016/0017, ADR-0061 and feature 022 preserve independent
  identity, private scope, billing and canonical truth authorities.
