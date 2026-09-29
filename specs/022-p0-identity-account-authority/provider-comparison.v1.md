# Authentication Provider Candidate Notes — P0

**Evidence checked:** 2026-09-28, official vendor documentation and pricing pages in the preserved Identity proposal.
**Status:** Dated candidate research only; not legal review, provider selection, or authority to install/configure an SDK. Recheck features, hosting, plan constraints, and price before procurement or runtime work.

## Product requirements used

Google is the primary sign-in path. Email/password is secondary and requires verified email, mandatory TOTP enrollment, and recovery codes. Google relies on external provider assurance for P0 without AXIGNAL-managed TOTP. The auth provider owns credential mechanisms, TOTP secrets, recovery codes, OAuth exchange, and sessions. AXIGNAL owns PrincipalId mapping, authorization, membership, private scope, and entitlement interpretation.

## Candidate status

| Candidate | Dated evidence from official documentation | Current disposition |
|---|---|---|
| Clerk | Google and password methods, verified email, TOTP/backup-code recovery, linking flows, React/Next.js and Python SDKs. The reviewed global MFA control may impose TOTP on Google users. U.S.-only hosting was reported in the reviewed source set. | Conditional candidate only. Recheck whether the selected configuration can require TOTP for the password path while preserving the Google path and whether hosting meets requirements. |
| WorkOS AuthKit | Google/password methods, email verification, TOTP, hosted UI, Python and Next.js guidance. Reviewed docs did not establish user recovery codes. | Candidate only; do not select until provider-owned recovery-code behavior and path-specific TOTP are verified. |
| Supabase Auth | Google/password, email verification, TOTP, and linking mechanisms. Reviewed MFA docs reported recovery codes unsupported. | Not a current fit unless current provider-owned recovery-code support is demonstrated. Do not substitute AXIGNAL-built recovery machinery. |
| Auth0 | Google/password, email verification, TOTP/recovery flows, explicit account linking and regional deployment options. Recovery behavior depends on factor/plan. | Candidate only; verify the exact plan, factor, recovery, linking, and regional terms before selection. |

These notes do not rank or select a provider. Product policy is provider-independent. Clerk remains a conditional evaluation candidate from the earlier review, not an accepted decision.

## Official source references from the dated review

- [Clerk authentication strategies and account linking](https://clerk.com/docs/guides/configure/auth-strategies/social-connections/account-linking)
- [Clerk MFA recovery](https://clerk.com/docs/guides/secure/mfa-recovery)
- [Clerk security and hosting](https://clerk.com/security)
- [Clerk pricing](https://clerk.com/pricing)
- [WorkOS identity linking](https://workos.com/docs/authkit/identity-linking)
- [WorkOS MFA](https://workos.com/docs/authkit/mfa)
- [WorkOS pricing](https://workos.com/pricing)
- [Supabase MFA reference](https://supabase.com/docs/reference/javascript/auth-mfa)
- [Supabase identity linking](https://supabase.com/docs/guides/auth/auth-identity-linking)
- [Auth0 account linking](https://auth0.com/docs/manage-users/user-accounts/user-account-linking/link-user-accounts)
- [Auth0 recovery codes](https://auth0.com/docs/secure/multi-factor-authentication/authenticate-using-ropg-flow-with-mfa/challenge-with-recovery-codes)
- [Auth0 pricing](https://auth0.com/pricing)

## Selection remains blocked on

- Data-location, transfer, retention, support, and operational requirements.
- Proof that the selected provider supports password-path TOTP and recovery without imposing AXIGNAL-managed TOTP on Google sign-in.
- Verified account-linking behavior in both registration orders, recovery edge cases, and email changes.
- Session revocation/lifetime and provider outage behavior.
- Current plan pricing, export/deletion, licensing, and total operating cost.
- Product payer/entitlement relationship decisions where relevant; provider Organizations and billing IDs cannot define them.
