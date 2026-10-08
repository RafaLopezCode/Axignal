import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  customerZeroCommand,
  readCustomerZeroResponse,
  safeSourceLink,
} from "../lib/runtime-projection";
import { POST as connectSession } from "../app/api/admin/session/route";
import { explainRuntime } from "../lib/runtime-axent";
import { focusHistory, productHome } from "../lib/product-navigation";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { RuntimeProductProjection } from "../components/runtime-product";
import { Admin } from "../components/admin";
import { RuntimeOrganizations } from "../components/runtime-organizations";
import { POST as askAxent } from "../app/api/axent/route";

const projection = {
  realityLevel: "CONTROLLED_TEST",
  runtimeCodeSha: "test-sha",
  lifecycleStatus: "LIVE",
  organization: {
    id: "org:test",
    name: "Contract subject",
    privateRevenue: 999,
  },
  context: { id: "focus:test", label: "Contract focus" },
  nodes: [
    {
      id: "signal:test",
      nodeKind: "XIGNAL",
      title: "Observed surface",
      whyAttention: "Source changed",
      interpretation: "A bounded reading",
      uncertainty: "Other surfaces remain unknown",
      epistemicState: "OBSERVED",
      currentness: "CURRENT",
      observedAt: "2026-10-04T00:00:00Z",
      evidenceAccess: "AVAILABLE",
      sourceRefs: ["https://example.org/"],
      observationSupportRefs: ["observation:test"],
      unknowns: ["Reach unknown"],
      evidenceNarrative: {
        xignalId: "signal:test",
        focusStepId: "step:source",
        steps: [
          {
            id: "step:source",
            kind: "SOURCE",
            label: "Observed source",
            sourceRef: "https://example.org/",
            observedAt: "2026-10-04T00:00:00Z",
            currentness: "CURRENT",
            artifactVerified: true,
          },
        ],
      },
    },
  ],
  temporalHistory: {
    disposition: "SINGLE_OBSERVATION",
    items: [{
      observationId: "observation:test",
      sourceRef: "https://example.org/",
      sourceType: "OFFICIAL_WEB",
      observedAt: "2026-10-04T00:00:00Z",
      currentness: "CURRENT",
      normalizedStateChanged: null,
    }],
  },
  today: {
    disposition: "READY",
    items: [
      {
        xignalId: "signal:test",
        whatChanged: "Surface observed",
        whyItMatters: "A bounded observation",
        observedAt: "2026-10-04T00:00:00Z",
        showHowRef: "step:source",
      },
    ],
  },
  reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
  privateAccounts: ["secret"],
};
test("distinct runtime states never create a fallback signal", () => {
  for (const [payload, status, state] of [
    [{ state: "NO_XEED" }, 200, "NO_XEED"],
    [
      { state: "INSUFFICIENT_EVIDENCE", reason: "NO_BODY" },
      422,
      "INSUFFICIENT_EVIDENCE",
    ],
    [{ status: "failed", reason: "HTTP_FAILURE" }, 502, "failure"],
    [{ status: "rejected", reason: "POLICY" }, 400, "rejected"],
    [{ state: "rejected", reason: "POLICY" }, 400, "rejected"],
    [{}, 401, "unauthorized"],
    [{}, 200, "failure"],
  ] as const)
    assert.equal(readCustomerZeroResponse(payload, status).state, state);
});
test("projection identity, narrative, currentness and sources survive persisted reload; private fields do not", () => {
  const first = readCustomerZeroResponse(projection, 201);
  const reload = readCustomerZeroResponse(
    JSON.parse(JSON.stringify(projection)),
    200,
  );
  assert.deepEqual(first, reload);
  assert.equal(first.state, "success");
  if (first.state !== "success") throw new Error("projection not accepted");
  assert.equal(first.projection.organization.name, "Contract subject");
  assert.equal(first.projection.nodes[0].currentness, "CURRENT");
  assert.equal(
    first.projection.nodes[0].evidenceNarrative.steps[0].artifactVerified,
    true,
  );
  assert.deepEqual(first.projection.nodes[0].sourceRefs, [
    "https://example.org/",
  ]);
  assert.ok(!JSON.stringify(first).includes("privateRevenue"));
  assert.ok(!JSON.stringify(first).includes("privateAccounts"));
});
test("source navigation rejects credentials and potentially private URL material", () => {
  assert.equal(safeSourceLink("https://example.org/"), "https://example.org/");
  for (const ref of [
    "javascript:alert(1)",
    "https://user:password@example.org/",
    "https://example.org/?token=secret",
    "https://example.org/#secret",
    "artifact:sha256:test",
  ])
    assert.equal(safeSourceLink(ref), null);
});
test("Customer Zero only sends canonical attention, and consumes the real read endpoint", () => {
  assert.deepEqual(customerZeroCommand, {
    label: "AXIGNAL self-observation",
    targetUri: "https://axignal.com/",
  });
  const client = readFileSync("components/customer-zero.tsx", "utf8");
  const renderer = readFileSync("components/runtime-product.tsx", "utf8");
  const adapter = readFileSync("lib/customer-zero-server.ts", "utf8");
  const subscriber = readFileSync("components/runtime-panorama.tsx", "utf8");
  assert.ok(client.includes('"/api/subscriber-context"'));
  assert.ok(client.includes('"/api/xeeds"'));
  assert.ok(adapter.includes('"/internal/admin/customer-zero/access"'));
  for (const content of [client, renderer, adapter, subscriber]) {
    assert.doesNotMatch(
      content,
      /Norte|Atlas|adminRecords|subscriberFixture|from ["'].*\/projection["']/,
    );
    assert.doesNotMatch(
      content,
      /nodeKind:\s*["']XIGNAL|epistemicState:\s*["']OBSERVED/,
    );
  }
  assert.ok(renderer.includes("signal.evidenceNarrative.steps"));
  assert.ok(renderer.includes("signal.uncertainty"));
  assert.ok(renderer.includes("signal.currentness"));
  assert.ok(subscriber.includes("<RuntimeExperience"));
  assert.ok(client.includes("<RuntimeProductProjection"));
  assert.ok(renderer.includes('t("señal observada", "observed signal")'));
  assert.ok(renderer.includes('t("fuente pública", "public source")'));
  assert.ok(renderer.includes('t("observación gobernada", "governed observation")'));
  assert.ok(renderer.includes('t("vigente ahora", "current now")'));
  assert.ok(
    client.includes(
      't("Cliente cero · Controles internos", "Customer Zero · Staff controls")',
    ),
  );
  assert.ok(
    readFileSync("components/admin.tsx", "utf8").includes(
      't("AXIGNAL / Cliente cero", "AXIGNAL / Customer Zero")',
    ),
  );
  assert.doesNotMatch(
    readFileSync("app/globals.css", "utf8"),
    /content:\s*["']AXIGNAL \/ Customer Zero["']/,
  );
  assert.doesNotMatch(client, />\s*Customer Zero · \{t\(/);
  assert.ok(client.includes('t("Volver a Admin", "Return to Admin")'));
});

test("product focus back/forward/home is reversible and never changes runtime truth", () => {
  const original = JSON.stringify(projection);
  let history = {trail:[productHome],cursor:0};
  history=focusHistory(history,{type:"go",focus:{...productHome,view:"today"}});
  history=focusHistory(history,{type:"go",focus:{...productHome,signalId:"signal:test"}});
  history=focusHistory(history,{type:"back"});
  assert.equal(history.trail[history.cursor].view,"today");
  history=focusHistory(history,{type:"forward"});
  assert.equal(history.trail[history.cursor].signalId,"signal:test");
  history=focusHistory(history,{type:"home"});
  assert.deepEqual(history.trail[history.cursor],productHome);
  history=focusHistory(history,{type:"back"});
  history=focusHistory(history,{type:"go",focus:{...productHome,view:"timeline"}});
  assert.equal(focusHistory(history,{type:"forward"}).cursor,history.cursor);
  assert.equal(JSON.stringify(projection),original);
});

test("runtime AXENT selects exact authorized evidence and preserves uncertainty without writes",()=>{
  const result=readCustomerZeroResponse(projection,200);
  assert.equal(result.state,"success"); if(result.state!=="success")throw new Error("Invalid test projection");
  const p=result.projection, original=JSON.stringify(p);
  const changed=explainRuntime(p,"qué cambió");
  assert.equal(changed.intent,"changed");
  assert.deepEqual(changed.passages,["Surface observed"]);
  const why=explainRuntime(p,"por qué importa");
  assert.equal(why.intent,"why");
  assert.deepEqual(why.passages,["Source changed"]);
  assert.deepEqual(explainRuntime(p,"muéstrame la evidencia").passages,["Observed source"]);
  const unknown=explainRuntime(p,"what remains UNKNOWN");
  assert.deepEqual(unknown.passages,["Other surfaces remain unknown","Reach unknown"]);
  const research=explainRuntime(p,"qué investigarías después",undefined,"es");
  assert.equal(research.action,"research-unavailable");
  assert.match(research.summary,/plan propuesto de investigación/i);
  assert.equal(research.researchPlan.length,3);
  assert.deepEqual(research.openQuestions,["Other surfaces remain unknown","Reach unknown"]);
  assert.deepEqual(research.sourceRefs,["https://example.org/"]);
  const english=explainRuntime(p,"what would you investigate next",undefined,"en");
  assert.match(english.summary,/proposed research plan/i);
  assert.notEqual(english.summary,research.summary);
  assert.throws(()=>explainRuntime(p,"evidence","foreign:signal"),/FOCUS_OUTSIDE_PROJECTION/);
  assert.equal(JSON.stringify(p),original);
  assert.deepEqual(unknown.sourceRefs,["https://example.org/"]);
  assert.ok(!JSON.stringify(unknown).includes("privateRevenue"));
});

test("subscriber and Customer Zero render the same economic shell; Staff adds only utility",()=>{
  const result=readCustomerZeroResponse(projection,200);
  if(result.state!=="success")throw new Error("Invalid contract");
  const plain=renderToStaticMarkup(createElement(RuntimeProductProjection,{projection:result.projection}));
  const staff=renderToStaticMarkup(createElement(RuntimeProductProjection,{projection:result.projection,staffControls:createElement("details",{"data-staff-test":true},"Staff only")}));
  assert.equal(staff.replace('<details data-staff-test="true">Staff only</details>',""),plain);
  assert.ok(plain.includes("product-shell canonical-product"));
  assert.ok(plain.includes("Contract subject"));
  assert.ok(plain.includes("Observed surface"));
  assert.ok(plain.includes("Product navigation"));
  assert.doesNotMatch(plain,/Norte|Atlas|Demo|privateRevenue|privateAccounts/);
  const embedded=renderToStaticMarkup(createElement(RuntimeProductProjection,{projection:result.projection,mainId:"customer-zero-main"}));
  assert.equal(embedded.replace('id="customer-zero-main"','id="main"'),plain);
});

test("Admin hosts the real product with retained administrative navigation and one skip target",()=>{
  const html=renderToStaticMarkup(createElement(Admin,{initialDomain:"customer-zero"}));
  assert.ok(html.includes('aria-label="Admin navigation"'));
  assert.ok(html.includes('class="admin-product-host"'));
  assert.ok(html.includes('data-runtime-state="loading"'));
  assert.ok(html.includes('id="customer-zero-main"'));
  assert.equal((html.match(/id="main"/g)||[]).length,1);
  assert.ok(!html.includes('class="panorama-main admin-main"'));
  const admin=readFileSync("components/admin.tsx","utf8");
  assert.doesNotMatch(admin,/window\.location\.(assign|replace)/);
  assert.ok(admin.includes('<CustomerZero embedded navigationHost={productNavigationHost}'));
  assert.ok(admin.includes('hidden={domainId !== "customer-zero"}'));
});

test("host navigation removes the duplicate product frame while preserving the actual reading",()=>{
  const result=readCustomerZeroResponse(projection,200);
  assert.equal(result.state,"success");
  if(result.state!=="success") return;
  const plain=renderToStaticMarkup(createElement(RuntimeProductProjection,{projection:result.projection}));
  const embedded=renderToStaticMarkup(createElement(RuntimeProductProjection,{projection:result.projection,embedded:true}));
  assert.equal(embedded.match(/<main[\s\S]*?<\/main>/)?.[0],plain.match(/<main[\s\S]*?<\/main>/)?.[0]);
  assert.doesNotMatch(embedded,/<aside[^>]*class="product-sidebar/);
  assert.doesNotMatch(embedded,/sidebar-brand|Abrir navegación/);
  assert.doesNotMatch(embedded,/<header class="product-topbar">/);
  assert.ok(plain.includes('<header class="product-topbar">'));
  assert.ok(embedded.includes('aria-label="AXENT"'));
});

test("runtime AXENT refuses economic input and foreign origin before authorized reading",async()=>{
  for(const [body,origin,expected] of [
    [{mode:"runtime",prompt:"evidence",projection},"http://127.0.0.1:3810",400],
    [{mode:"runtime",prompt:"evidence",organizationId:"org:foreign"},"http://127.0.0.1:3810",400],
    [{mode:"runtime",prompt:"evidence"},"https://foreign.example",403],
  ] as const){
    const response=await askAxent(new Request("http://127.0.0.1:3810/api/axent",{method:"POST",headers:{origin,host:"127.0.0.1:3810","content-type":"application/json"},body:JSON.stringify(body)}));
    assert.equal(response.status,expected);
  }
});
test("session transport rejects foreign origin, malformed, oversized and non-JSON bodies", async () => {
  const url = "http://127.0.0.1:3810/api/admin/session";
  const headers = {
    origin: "http://127.0.0.1:3810",
    host: "127.0.0.1:3810",
    "content-type": "application/json",
  };
  for (const [body, overrides, expected] of [
    ["{}", { origin: "https://foreign.example" }, 403],
    ["{}", { host: "foreign.example" }, 403],
    ["{", {}, 400],
    ["{}", {}, 400],
    ["a".repeat(1025), {}, 413],
    ["{}", { "content-type": "text/plain" }, 415],
  ] as const) {
    const response = await connectSession(
      new Request(url, {
        method: "POST",
        headers: { ...headers, ...overrides },
        body,
      }),
    );
    assert.equal(response.status, expected);
    assert.equal(response.headers.get("set-cookie"), null);
  }
});

test("organization availability separates internal no-payment use from unknown subscriber capacity", () => {
  const props = {name:"Authorized subject",onReturn:()=>{}};
  const internal = renderToStaticMarkup(createElement(RuntimeOrganizations,{...props,internal:true}));
  const subscriber = renderToStaticMarkup(createElement(RuntimeOrganizations,{...props,internal:false}));
  assert.match(internal,/without checkout or payment/);
  assert.match(internal,/internal service authorization/);
  assert.doesNotMatch(subscriber,/without checkout or payment/);
  assert.match(subscriber,/does not report your plan/);
  for (const html of [internal, subscriber]) {
    assert.match(html,/Authorized subject/);
    assert.match(html,/disabled="" aria-describedby="organization-availability"/);
    assert.match(html,/<form/);
    assert.match(html,/Public website/);
    assert.match(html,/verify identity/);
    assert.doesNotMatch(html,/\/checkout|Norte|Atlas/);
  }
  const admin = renderToStaticMarkup(createElement(Admin,{initialDomain:"command"}));
  assert.match(admin,/href="\/admin\/customer-zero"/);
  assert.doesNotMatch(admin,/href="\/panorama"/);
});
import { attentionCommandSchema, organizationInventorySchema } from "../lib/organization-attention";
test("attention contracts reject economic authority and strip private inventory metadata", () => {
  assert.equal(attentionCommandSchema.safeParse({action:"add",name:"Requested",targetUri:"https://public.example/"}).success,true);
  for (const extra of [{organizationId:"org:spoof"},{role:"ADMIN"},{epistemicState:"OBSERVED"},{billing:false}])
    assert.equal(attentionCommandSchema.safeParse({action:"add",name:"Requested",targetUri:"https://public.example/",...extra}).success,false);
  const inventory=organizationInventorySchema.parse({accessMode:"INTERNAL_ADMIN",canObserve:false,selectedId:null,organizations:[],available:[],session:"secret",privateRevenue:999});
  assert.equal("session" in inventory,false);
  assert.equal("privateRevenue" in inventory,false);
  assert.equal(inventory.canObserve,false);
});
