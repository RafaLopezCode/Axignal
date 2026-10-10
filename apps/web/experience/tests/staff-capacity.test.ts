import { readFileSync } from "node:fs";
import test from "node:test";
import assert from "node:assert/strict";
import { staffCommands, staffReason, staffResults, staffState } from "../lib/staff-capacity";

const later = new Date(Date.now() + 30 * 86_400_000).toISOString();
const grant = {
  grantRef: "staff_capacity_0123456789abcdef01234567", tenantId: "tenant_a", destination: "CUSTOMER_ACCOUNT",
  capacity: 2, reason: "Client onboarding", grantedBy: "admin:founder", grantedAt: later, expiresAt: later,
  revokedAt: null, revokedBy: null, revocationReason: null, state: "ACTIVE", provenance: "STAFF_GRANT_NOT_BILLING",
};

test("staff commands are strict: no billing, price or subscription can ride along", () => {
  const base = { tenantId: "tenant_a", destination: "CUSTOMER_ACCOUNT", capacity: 2, expiresAt: later, reason: "Client onboarding", idempotencyKey: "grant:abcdef" };
  assert.equal(staffCommands.grant.safeParse(base).success, true);
  for (const extra of [{ priceRef: "price_live" }, { subscriptionRef: "sub_1" }, { checkout: true }, { paymentState: "VERIFIED" }])
    assert.equal(staffCommands.grant.safeParse({ ...base, ...extra }).success, false);
  for (const bad of [{ capacity: 0 }, { capacity: 501 }, { capacity: 1.5 }, { reason: "short" }, { tenantId: "../other" }, { destination: "PAID" }, { expiresAt: "tomorrow" }])
    assert.equal(staffCommands.grant.safeParse({ ...base, ...bad }).success, false);
  assert.equal(staffCommands.revoke.safeParse({ grantRef: "sub_123", reason: "Engagement finished" }).success, false);
  assert.equal(staffCommands.organizations.safeParse({ tenantId: "tenant_a", locator: "https://example.com", reason: "Own research", idempotencyKey: "staff-add:1" }).success, true);
});

test("runtime results must declare they are not billing and created no checkout", () => {
  assert.equal(staffResults.grant.safeParse({ grant, entitlementSource: "STAFF_GRANT" }).success, true);
  assert.equal(staffResults.grant.safeParse({ grant: { ...grant, provenance: "BILLING" }, entitlementSource: "STAFF_GRANT" }).success, false);
  assert.equal(staffResults.organizations.safeParse({ status: "CREATED", focusId: "focus_1", identityReason: null, checkoutCreated: true }).success, false);
  assert.equal(staffResults.preview.safeParse({ tenantId: "tenant_a", destination: "CUSTOMER_ACCOUNT", currentStaffCapacity: 0, staffCapacityAfter: 2, expiresAt: later, billingChanged: true, checkoutCreated: false, provenance: "STAFF_GRANT_NOT_BILLING" }).success, false);
  assert.equal(staffState.safeParse({ tenantId: "tenant_a", entitlementSource: "STAFF_GRANT", activeStaffCapacity: 2, grants: [grant], audit: [] }).success, true);
});

test("unknown runtime reasons collapse to a generic failure", () => {
  assert.equal(staffReason("STEP_UP_REQUIRED"), "STEP_UP_REQUIRED");
  assert.equal(staffReason("<script>"), "FAILED");
  assert.equal(staffReason(undefined), "FAILED");
});


test("operator step-up keeps an isolated short-lived cookie, primary pairing and bounded input", () => {
  const route = readFileSync(new URL("../app/api/admin/step-up/route.ts", import.meta.url), "utf8");
  const proxy = readFileSync(new URL("../lib/staff-capacity-server.ts", import.meta.url), "utf8");
  assert.match(route, /sameOrigin\(request\)/);
  assert.match(route, /maxAge: 600/);
  assert.match(route, /path: "\/api\/admin\/staff-capacity"/);
  assert.match(route, /httpOnly: true/);
  assert.match(route, /size > 1024/);
  assert.match(proxy, /validateStaffStepUp\(primary, elevated\)/);
  assert.match(proxy, /token = elevated \?\? primary/);
  assert.match(proxy, /return reply\(\{ reason: "STEP_UP_REQUIRED" \}, 403\)/);
});
