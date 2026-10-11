# Controlled rollout handoff

This is a candidate, not deployment evidence. Do not deploy from this feature branch.

## Integration order

1. Integrate onboarding PR #200 at its reviewed head.
2. Retarget this stacked PR to main, verify only customer-access changes remain,
   and require green deterministic CI on the exact resulting commit.
3. Obtain explicit human visual acceptance and production authorization.
4. Use an immutable release of that approved main SHA.

## Production preflight

Use the existing deploy/production/deploy-axignal.sh and subscriber overlay under ADR-0059.
Record the live current SHA, image digests and health of axignal-prod-runtime,
axignal-prod-experience and axignal-prod-landing before any write. Verify ownership and
backup/restore of /var/lib/axignal/runtime, especially subscriber-pilot.sqlite3 and
subscriber-runtime.sqlite3. Do not touch other projects or services.

The documented topology is private experience at loopback 18182, runtime on
axignal_prod_internal:18181 and public edge at loopback 18180. Its live inventory has
not been inspected in this task. Confirm operator-only Admin can reach the authorized
runtime with AXIGNAL_RUNTIME_ORIGIN and AXIGNAL_CONTAINERIZED=true. Preserve the
public boundary and the existing PRIMARY/independent Staff Step-Up mechanism.

Confirm existing AXIGNAL_SUBSCRIBER_PILOT_ENABLED authorization, Google registration
and exact callback origin, membership/tenant binding, and the separately authorized
first-observation runtime/rights/configuration. Do not enable Stripe/contracting or
new providers to compensate for missing access. Staff session bootstrap remains the
existing operational authority; routine invitation issuance/revocation is now in Admin.

## Migration and rollback

The existing pilot store adds nullable revoked_at on invitations, private commands and
audit tables; existing invites/grants are preserved. Initialization is additive and
repeatable. Legacy fixture migration is tested, including continued redemption.

On rollback to pre-feature binaries, first disable pilot access through its existing
governed flag: old code does not honor invitation revoked_at. Keep pilot access disabled
until a compatible revision is restored. Do not delete history, grants, memberships or
canonical evidence. Restore an SQLite-consistent preflight backup only if needed under
the existing operator procedure. Reactivation requires authority and verification.

## Cutover acceptance

After approved check/build/up with the mandatory subscriber overlay, run the existing
verify-product-surface.sh. Require exact artifact SHA, private Admin authorization,
unauthorized read/write denial and no public Admin exposure. On an authorized pilot
account, use browser-only Admin create/copy, real Google sign-in, redemption, pending
organization activation, real first observation and Observatory reading. Check Admin
reflects the same tenant/capacity/result automatically. Revoke a disposable unused
invitation and verify it cannot redeem; test grant revocation only on a designated
disposable pilot, preserving its history.

Record timestamps, status codes and references only. Never save invitation/session
secrets in tickets, screenshots or logs. Do not perform real payments. A provider or
runtime double is local validation, not real production E2E.
