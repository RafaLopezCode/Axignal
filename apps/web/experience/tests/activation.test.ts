import test from "node:test";
import assert from "node:assert/strict";
import { ADDITIONAL_ORGANIZATION_CENTS, billingReturn, capacityRoom, FIRST_ORGANIZATION_CENTS, firstPurchaseTotal, inviteTokenFrom, waitingItems } from "../lib/activation";
import { portfolioSchema } from "../lib/subscriber-contracts";

const portfolio = (capacity: number | null, currentness: "CURRENT" | "UNKNOWN", states: string[]) => portfolioSchema.parse({
  state: "success", capacity, capacityCurrentness: currentness, canPurchase: true, contractingEnabled: true,
  organizations: states.map((state, i) => ({ focusId: `f${i}`, organizationId: state === "ACTIVE" ? `org:${i}` : null, label: `Org ${i}`, state })),
});

test("a waiting organization is kept apart from the active ones, and unconfirmed capacity is never read as zero", () => {
  const p = portfolio(null, "UNKNOWN", ["CAPACITY_UNKNOWN"]);
  assert.deepEqual(waitingItems(p).map(i => i.focusId), ["f0"]);
  assert.equal(capacityRoom(p), null);
  assert.equal(capacityRoom(portfolio(1, "CURRENT", ["CAPACITY_UNKNOWN"])), 1);
  assert.equal(capacityRoom(portfolio(1, "CURRENT", ["ACTIVE", "CAPACITY_UNKNOWN"])), 0);
});

test("a first subscription covers the active and the waiting organizations, at least one", () => {
  assert.equal(firstPurchaseTotal(portfolio(null, "UNKNOWN", [])), 1);
  assert.equal(firstPurchaseTotal(portfolio(null, "UNKNOWN", ["CAPACITY_UNKNOWN", "CAPACITY_UNKNOWN"])), 2);
});

test("an invitation can be pasted as its link or as its token; nothing else is accepted", () => {
  const token = "abcdefghijklmnopqrstuvwxyz012345";
  assert.equal(inviteTokenFrom(`https://axignal.com/signup#pilot=${token}`), token);
  assert.equal(inviteTokenFrom(`  ${token}  `), token);
  for (const bad of ["", "short", "https://axignal.com/signup", "javascript:alert(1)", `#pilot=${token}<script>`]) assert.equal(inviteTokenFrom(bad), null, bad);
});

test("the payment provider's return is read, and only its two outcomes", () => {
  assert.equal(billingReturn(new URLSearchParams("billing=complete")), "complete");
  assert.equal(billingReturn(new URLSearchParams("billing=cancelled")), "cancelled");
  assert.equal(billingReturn(new URLSearchParams("billing=paid")), null);
  assert.equal(billingReturn(new URLSearchParams("")), null);
});

test("the published prices come from the pricing function: 9,95 € the first organization, 4,95 € each additional", () => {
  assert.equal(FIRST_ORGANIZATION_CENTS, 995);
  assert.equal(ADDITIONAL_ORGANIZATION_CENTS, 495);
});
