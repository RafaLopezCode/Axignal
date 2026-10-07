import test from "node:test";
import assert from "node:assert/strict";
import { capturePilotInvite, pendingPilotInvite, clearPilotInvite } from "../lib/pilot-invite";
import { pilotRedemptionSchema } from "../lib/subscriber-contracts";
function storage() {
  const values = new Map<string, string>();
  return { getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => { values.set(key, value); },
    removeItem: (key: string) => { values.delete(key); } };
}
test("invite survives OIDC only for bounded time; URL and terminal storage are cleared", () => {
  const store = storage(), token = "a".repeat(43), replaced: unknown[][] = [];
  const location = { hash: "#pilot=" + token, pathname: "/signup", search: "" };
  assert.equal(capturePilotInvite(location, { replaceState: (...args) => replaced.push(args) }, store, 100), true);
  assert.deepEqual(replaced, [[null, "", "/signup"]]);
  assert.equal(pendingPilotInvite(store, 101), token);
  assert.equal(pendingPilotInvite(store, 100 + 30 * 60 * 1000), null);
  assert.equal(pendingPilotInvite(store, 102), null);
  capturePilotInvite(location, { replaceState: () => {} }, store, 200);
  clearPilotInvite(store);
  assert.equal(pendingPilotInvite(store, 201), null);
});
test("malformed invite and denied storage never grant authority; valid secret fragment is removed", () => {
  const store = storage();
  store.setItem("axignal_pilot_invite", '{"token":"short","expiresAt":999}');
  assert.equal(pendingPilotInvite(store, 100), null);
  let stripped = false;
  assert.equal(capturePilotInvite({ hash: "#pilot=" + "a".repeat(43), pathname: "/signup", search: "" },
    { replaceState: () => { stripped = true; } }, { ...store, setItem: () => { throw new Error("denied"); } }, 100), false);
  assert.equal(stripped, true);
});
test("pilot result rejects unconfirmed capacity or contradictory acceptance", () => {
  assert.equal(pilotRedemptionSchema.safeParse({ state: "PILOT_ACTIVE", accepted: true }).success, false);
  assert.equal(pilotRedemptionSchema.safeParse({ state: "PILOT_INVITE_INVALID", accepted: true }).success, false);
  assert.equal(pilotRedemptionSchema.safeParse({ state: "PILOT_ACTIVE", accepted: true, capacity: 2,
    expiresAt: "2026-12-06T12:00:00+00:00" }).success, false);
});

test("browser storage getter denial strips the fragment and fails closed", () => {
  const unavailable = () => { throw new Error("SECURITY_ERROR"); };
  let clean = "";
  assert.equal(capturePilotInvite({ hash: "#pilot=" + "b".repeat(32), pathname: "/signup", search: "" }, { replaceState: (_state, _title, url) => { clean = String(url); } }, unavailable), false);
  assert.equal(clean, "/signup");
  assert.equal(pendingPilotInvite(unavailable), null);
});
