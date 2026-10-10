import test from "node:test";
import assert from "node:assert/strict";
import snapshot from "../lib/demo/synthetic-observatory.json";

test("the demo snapshot is labelled synthetic and points only at reserved example hosts", () => {
  assert.match(String(snapshot.provenance), /^SYNTHETIC:/);
  const text = JSON.stringify(snapshot);
  const hosts = new Set([...text.matchAll(/https?:\/\/([^/"\\ ]+)/g)].map(m => m[1].replace(/^www\./, "")));
  assert.ok(hosts.size > 0);
  for (const host of hosts) assert.match(host, /\.(example|test|invalid)$|^example\.(com|org|net)$|\.example\.com$/, host);
  // Names and hosts that could match a real company, public body or procurement platform.
  assert.doesNotMatch(text, /Solartec|Solaria Norte|Ledgerly|Boulangerie de la Lune|Little Rock Language|Getafe|ted\.europa|\bTED\b/);
});

test("every snapshot read parses with the same contracts as the live subscriber read", async () => {
  const { syntheticOutput, syntheticPortfolio } = await import("../lib/demo/synthetic-source");
  const { pendingOutputSchema, subscriberOutputSchema } = await import("../lib/subscriber-contracts");
  assert.ok(syntheticPortfolio().organizations.length > 0);
  for (const focusId of Object.keys(snapshot.outputs)) {
    const payload = syntheticOutput(focusId) as { kind?: string };
    if (payload.kind === "PENDING_ATTENTION") pendingOutputSchema.parse(payload);
    else subscriberOutputSchema.parse(payload);
  }
});
