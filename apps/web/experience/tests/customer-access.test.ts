import test from "node:test";
import assert from "node:assert/strict";
import { customerCommands, customerAccess, issuedInvite, pilotLink, activationCause, type CustomerAccess } from "../lib/customer-access";

test("Admin mutations reject billing, tenant selection, invalid TTL and control characters", () => {
  const valid = { reason: "Private partner", inviteHours: 168, idempotencyKey: "command:1" };
  assert.equal(customerCommands.issue.safeParse(valid).success, true);
  for (const bad of [{ capacity: 20 }, { tenantId: "foreign" }, { priceRef: "price_1" }, { inviteHours: 0 }, { inviteHours: 721 }, { inviteHours: true }, { reason: "Private\npartner" }])
    assert.equal(customerCommands.issue.safeParse({ ...valid, ...bad }).success, false);
});

test("copied invitation is fragment-only, compatible with onboarding; response strips extras", () => {
  const token = "a".repeat(43), link = new URL(pilotLink("https://axignal.com", token));
  assert.equal(link.pathname, "/signup"); assert.equal(link.search, ""); assert.equal(link.hash, "#pilot=" + token);
  assert.throws(() => pilotLink("javascript:alert(1)", token));
  assert.throws(() => pilotLink("https://axignal.com", "bad"));
  assert.equal("token_digest" in issuedInvite.parse({ inviteRef: "invite_a", inviteToken: token, expiresAt: "later", capacity: 1, token_digest: "private" }), false);
});

const customer: CustomerAccess["customers"][number] = {
  tenantId: "tenant_a", principalId: "principal_a", membership: "ACTIVE", capacity: null,
  capacityCurrentness: "UNKNOWN", entitlementSource: "UNKNOWN", organizations: [], billing: null,
  billingReadable: true, firstObservationEnabled: true,
};
test("diagnosis preserves unknown and separates billing, capacity, identity and runtime", () => {
  assert.equal(activationCause(customer), "ACCESS");
  const billing = { subscriptionRef: "sub_a", status: "UNKNOWN", paymentState: "UNKNOWN", contractedCapacity: null, verifiedAt: null, paidThrough: null };
  assert.equal(activationCause({ ...customer, billing }), "PAYMENT");
  const confirmed = { ...customer, capacity: 1, capacityCurrentness: "CURRENT" };
  const org = { focusId: "focus_a", organizationId: null, label: "Example", state: "CAPACITY_PENDING" };
  assert.equal(activationCause({ ...confirmed, organizations: [org] }), "CAPACITY");
  assert.equal(activationCause({ ...confirmed, organizations: [{ ...org, state: "IDENTITY_PENDING" }] }), "IDENTITY");
  assert.equal(activationCause({ ...confirmed, firstObservationEnabled: false }), "RUNTIME");
  assert.equal(activationCause(confirmed), "OBSERVATION");
  assert.equal(activationCause({ ...confirmed, organizations: [{ ...org, state: "IDENTITY_PENDING", observation: { state: "FIRST_PROOF_READY", firstProofReady: true, headline: "Public observation", headlineCode: null, observedAt: null } }] }), "READY");
});

test("read projection never retains unexpected token material", () => {
  const input = { asOf: "now", limit: 500, pilotEnabled: true, customers: [customer], accountOperations: { customers: [] }, pilot: { asOf: "now", limit: 500, invites: [], grants: [], audit: [], token_digest: "private", inviteToken: "secret" } };
  const view = customerAccess.parse(input);
  assert.equal(JSON.stringify(view).includes("secret"), false);
  assert.equal(JSON.stringify(view).includes("private"), false);
});
