import test from "node:test";
import assert from "node:assert/strict";
import { adminOriginAllowed } from "../lib/admin-origin";
import { pilotAccountsCommand, pilotAccountsSnapshot } from "../lib/pilot-test-accounts";

test("pilot preparation validates blank/replacement/clear and duplicate or forged authority", () => {
  assert.equal(pilotAccountsCommand.safeParse({ a: "", b: "", expectedRevision: 0 }).success, true);
  assert.equal(pilotAccountsCommand.safeParse({ a: "a@example.com", b: "b@example.com", expectedRevision: 1 }).success, true);
  for (const body of [
    { a: "bad", b: "", expectedRevision: 0 },
    { a: "A@example.com", b: "a@example.com", expectedRevision: 0 },
    { a: "", b: "", expectedRevision: -1 },
    { a: "", b: "", expectedRevision: 0, tenantId: "forged" },
  ]) assert.equal(pilotAccountsCommand.safeParse(body).success, false);
  assert.equal(pilotAccountsSnapshot.safeParse({ a: "", b: "", revision: 0, savedBy: null, savedAt: null, authorizedForTest: true }).success, false);
});
test("private SSH Admin origin remains usable with subscriber HTTPS, without accepting external origins", () => {
  const request = (origin: string, host = "127.0.0.1:18182") => new Request("http://127.0.0.1:18182/api/admin/pilot-test-accounts", { headers: { origin, host } });
  assert.equal(adminOriginAllowed(request("http://127.0.0.1:18182"), "https://axignal.com"), true);
  assert.equal(adminOriginAllowed(request("https://axignal.com", "axignal.com"), "https://axignal.com"), true);
  for (const origin of ["https://evil.example", "http://127.0.0.1:18183", "null", "not-a-url"])
    assert.equal(adminOriginAllowed(request(origin), "https://axignal.com"), false);
  assert.equal(adminOriginAllowed(request("https://axignal.com"), "https://axignal.com"), false);
});
