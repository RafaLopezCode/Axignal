import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { factsAt } from "../lib/cognition/facts";
import {
  composeFamily,
  epistemicContent,
  validateCognitivePlan,
  type Device,
} from "../lib/cognition/compose";
import { COGNITIVE_REGISTRY, type Intent } from "../lib/cognition/registry";
import { families, makeContext, type FamilyId } from "../lib/projection";
import { validatePlan } from "../lib/governance";
import { CognitiveComponent, FamilyLens } from "../components/cognition/lenses";
import { POST } from "../app/api/axent/route";

const NOW = factsAt("norte", "2026-10-03");
const firstLayer = (
  family: FamilyId,
  intent: Intent = "overview",
  device: Device = "desktop",
) =>
  composeFamily({ family, intent, facts: NOW, device })
    .items.filter((i) => i.layer === 1)
    .map((i) => i.component);

test("each family is explained in its own cognitive language", () => {
  assert.deepEqual(firstLayer("presence"), ["trend-chart", "answer-space-matrix"]);
  assert.deepEqual(firstLayer("demand"), ["opportunity-brief"]);
  assert.deepEqual(firstLayer("relationships"), ["relationship-network"]);
  assert.deepEqual(firstLayer("markets"), ["territory-matrix"]);
  assert.deepEqual(firstLayer("reputation"), ["discourse-map"]);
  assert.deepEqual(firstLayer("activity"), ["change-timeline"]);
  assert.deepEqual(firstLayer("organization"), ["provenance-trail"]);
  // Every family keeps "how does AXIGNAL know?" one disclosure away.
  for (const family of families)
    assert.ok(
      composeFamily({ family: family.id, intent: "overview", facts: NOW, device: "desktop" }).items.some(
        (i) => i.component === "provenance-trail",
      ),
      family.id,
    );
});

test("the question changes the composition, not the facts", () => {
  const why = composeFamily({ family: "demand", intent: "why", facts: NOW, device: "desktop" });
  assert.equal(why.items[0].component, "opportunity-brief");
  assert.ok(why.items.some((i) => i.component === "capability-demand-match" && i.layer <= 2));
  const change = composeFamily({ family: "presence", intent: "change", facts: NOW, device: "desktop" });
  assert.equal(change.items[0].component, "change-timeline");
  assert.ok(change.items.some((i) => i.component === "trend-chart"));
  const known = composeFamily({ family: "markets", intent: "how_known", facts: NOW, device: "desktop" });
  assert.deepEqual(
    known.items.filter((i) => i.layer === 1).map((i) => i.component),
    ["provenance-trail"],
  );
});

test("mobile keeps one primary component in the first ten seconds", () => {
  assert.deepEqual(firstLayer("presence", "overview", "mobile"), ["trend-chart"]);
  const plan = composeFamily({ family: "presence", intent: "overview", facts: NOW, device: "mobile" });
  assert.equal(plan.items.find((i) => i.component === "answer-space-matrix")?.layer, 2);
});

test("the validator only renders allowlisted, compatible, available and honest components", () => {
  const plan = (family: FamilyId, component: string, layer = 1) => ({
    version: 2,
    family,
    intent: "overview",
    items: [{ component, layer }],
  });
  assert.equal(validateCognitivePlan(plan("demand", "opportunity-brief"), NOW).success, true);
  const reject = (input: unknown, facts = NOW) => {
    const result = validateCognitivePlan(input, facts);
    return result.success ? "ACCEPTED" : result.error;
  };
  assert.equal(reject(plan("demand", "generated-html")), "COMPONENT_NOT_ALLOWLISTED");
  assert.equal(reject(plan("demand", "relationship-network")), "FAMILY_INCOMPATIBLE");
  assert.equal(reject(plan("demand", "opportunity-brief"), factsAt("norte", "2026-07-01")), "DATA_UNAVAILABLE");
  assert.equal(reject({ ...plan("demand", "opportunity-brief"), facts: { epistemic: "OBSERVED" } }), "INVALID_PLAN");
  assert.equal(
    reject({ version: 2, family: "demand", intent: "overview", items: [{ component: "opportunity-brief", layer: 1, state: "OBSERVED" }] }),
    "INVALID_ITEM",
  );
  const tampered = {
    ...NOW,
    network: { ...NOW.network!, edges: [...NOW.network!.edges, { ...NOW.network!.edges[0], state: "UNKNOWN" as never }] },
  };
  assert.equal(reject(plan("relationships", "relationship-network"), tampered), "EPISTEMIC_STATE_UNSUPPORTED");
  for (const declaration of Object.values(COGNITIVE_REGISTRY)) {
    assert.ok(declaration.accessibleFallback.length > 10, declaration.id);
    assert.ok(declaration.states.empty && declaration.states.error, declaration.id);
  }
});

test("nothing observed later leaks into an earlier time cut", () => {
  const july = factsAt("norte", "2026-07-01");
  assert.equal(july.opportunities?.length, 0);
  assert.deepEqual(july.trend?.points.map((p) => p.date), ["2026-07-01"]);
  assert.equal(july.network?.edges.some((e) => e.sourceId === "src-programme"), false);
  assert.equal(july.territory?.markets.find((m) => m.code === "ES-PV")?.state, "UNKNOWN");
  assert.deepEqual(epistemicContent(july, "markets"), new Set(["OBSERVED", "UNKNOWN"]));
});

const html = (id: string, asOf = "2026-10-03") =>
  renderToStaticMarkup(createElement(CognitiveComponent, { id: id as never, facts: factsAt("norte", asOf), asOf }));

test("grammar: UNKNOWN is named and never drawn as zero", () => {
  const trend = html("trend-chart");
  assert.match(trend, /data-epistemic="UNKNOWN"/);
  assert.match(trend, /<td>Desconocido<\/td>/);
  assert.doesNotMatch(trend, /<td>0%<\/td>/);
  const topics = html("topic-deltas");
  assert.match(topics, /class="cg-unknown"[^>]*>Sin medición/);
  const territory = html("territory-matrix");
  assert.equal((territory.match(/data-epistemic="UNKNOWN"/g) ?? []).length >= 2, true);
});

test("grammar: POTENTIAL stays visually and structurally separate from OBSERVED", () => {
  const network = html("relationship-network");
  const observedList = network.split("cg-edges-potential")[0];
  assert.doesNotMatch(observedList.split("Potenciales")[1] ?? "", /data-epistemic="POTENTIAL"/);
  assert.match(network, /class="cg-edge-potential"/);
  assert.match(network, /class="cg-edges cg-edges-potential"/);
  assert.match(network, /Sin fuente: es una hipótesis/);
  const opportunities = html("opportunity-brief");
  assert.doesNotMatch(opportunities, /badge-observed/);
  assert.equal((opportunities.match(/badge-potential/g) ?? []).length, 2);
});

test("grammar: provenance and why are reachable from every family lens", () => {
  for (const family of ["presence", "demand", "relationships", "markets", "reputation", "activity"] as FamilyId[]) {
    const markup = renderToStaticMarkup(
      createElement(FamilyLens, { organizationId: "norte", family, asOf: "2026-10-03" }),
    );
    assert.match(markup, /data-layer="1"/, family);
    assert.match(markup, /¿Cómo lo sabe AXIGNAL\?|data-cognitive-component="provenance-trail"/, family);
    assert.match(markup, /data-provenance=/, family);
  }
});

async function ask(text: string, family: FamilyId) {
  const response = await POST(
    new Request("http://127.0.0.1:3810/api/axent", {
      method: "POST",
      headers: { origin: "http://127.0.0.1:3810", host: "127.0.0.1:3810", "content-type": "application/json" },
      body: JSON.stringify({
        locale: "en",
        context: makeContext("norte", family),
        messages: [{ role: "user", parts: [{ type: "text", text }] }],
      }),
    }),
  );
  const line = (await response.text()).split("\n").find((l) => l.includes("tool-output-available"));
  return JSON.parse(line!.replace(/^data: /, "")).output.items as { component: string; ref: string }[];
}

test("AXENT composes family lenses for the question and governance re-checks them", async () => {
  const why = await ask("Why does this matter?", "demand");
  assert.ok(why.some((i) => i.component === "lens" && i.ref === "opportunity-brief"));
  const network = await ask("Explain this context", "relationships");
  assert.ok(network.some((i) => i.component === "lens" && i.ref === "relationship-network"));
  assert.ok(why.length <= 3 && network.length <= 3);
  const context = makeContext("norte", "demand");
  const plan = (ref: string) => ({
    version: 1,
    revision: context.revision,
    items: [{ component: "lens", ref, priority: "primary" }],
  });
  assert.equal(validatePlan(plan("capability-demand-match"), context).success, true);
  assert.equal(validatePlan(plan("relationship-network"), context).success, false);
  assert.equal(validatePlan(plan("<script>"), context).success, false);
});
