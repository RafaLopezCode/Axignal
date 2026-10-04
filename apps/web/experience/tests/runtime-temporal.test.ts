import { test } from "node:test";
import assert from "node:assert/strict";
import { runtimeProjectionSchema } from "../lib/runtime-projection";
import { orderedTemporalHistory, temporalHistoryForSource } from "../lib/runtime-temporal";

const projection = runtimeProjectionSchema.parse({
  realityLevel:"LIVE", runtimeCodeSha:"sha", lifecycleStatus:"LIVE",
  context:{id:"ctx",label:"Subject"}, organization:{id:"org",name:"Subject"},
  nodes:[{
    id:"signal",nodeKind:"XIGNAL",title:"Observed",whyAttention:"Why",interpretation:"Known",
    uncertainty:"Open",epistemicState:"OBSERVED",currentness:"CURRENT",
    observedAt:"2026-10-04T11:00:00Z",evidenceAccess:"AVAILABLE",
    sourceRefs:["https://example.org/"],observationSupportRefs:["obs:2"],unknowns:["Open"],
    evidenceNarrative:{xignalId:"signal",focusStepId:"obs:2",steps:[]}
  }],
  temporalHistory:{disposition:"MULTIPLE_OBSERVATIONS",items:[
    {observationId:"obs:1",sourceRef:"https://example.org/",sourceType:"OFFICIAL_WEB",observedAt:"2026-10-03T10:00:00Z",currentness:"CURRENT",normalizedStateChanged:null},
    {observationId:"obs:2",sourceRef:"https://example.org/",sourceType:"OFFICIAL_WEB",observedAt:"2026-10-04T11:00:00Z",currentness:"CURRENT",normalizedStateChanged:false},
    {observationId:"obs:other",sourceRef:"https://other.example/",sourceType:"PUBLIC_RECORD",observedAt:"2026-10-04T09:00:00Z",currentness:"CURRENT",normalizedStateChanged:true},
  ]},
  today:{disposition:"READY",items:[]},
  reloadContinuity:"PERSISTED_RUNTIME_READ_MODEL",
});

test("temporal history is ordered newest first without mutating canonical projection",()=>{
  const before=JSON.stringify(projection);
  assert.deepEqual(orderedTemporalHistory(projection).map(v=>v.observationId),["obs:2","obs:other","obs:1"]);
  assert.equal(JSON.stringify(projection),before);
});

test("focused signal temporal history filters to its governed public source",()=>{
  assert.deepEqual(
    temporalHistoryForSource(projection,projection.nodes[0].sourceRefs).map(v=>v.observationId),
    ["obs:2","obs:1"],
  );
});
