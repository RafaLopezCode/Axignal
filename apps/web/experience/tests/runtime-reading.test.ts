import { test } from "node:test";
import assert from "node:assert/strict";
import { latestObservedSignal, orderedSignals, signalGroups } from "../lib/runtime-reading";
import type { RuntimeSignal } from "../lib/runtime-projection";

function signal(
  id: string,
  epistemicState: RuntimeSignal["epistemicState"],
  currentness: RuntimeSignal["currentness"],
  observedAt: string,
): RuntimeSignal {
  return {
    id,
    nodeKind: "XIGNAL",
    title: id,
    whyAttention: id + " attention",
    interpretation: id + " interpretation",
    uncertainty: id + " uncertainty",
    epistemicState,
    currentness,
    observedAt,
    evidenceAccess: "AVAILABLE",
    sourceRefs: [],
    observationSupportRefs: [],
    unknowns: [],
    evidenceNarrative: { xignalId: id, focusStepId: id, steps: [] },
  };
}

test("Signals prioritizes epistemic state, currentness and recency without mutation", () => {
  const nodes = [
    signal("unknown-new", "UNKNOWN", "CURRENT", "2026-10-04T12:00:00Z"),
    signal("observed-old", "OBSERVED", "CURRENT", "2026-10-03T12:00:00Z"),
    signal("observed-new", "OBSERVED", "CURRENT", "2026-10-04T12:00:00Z"),
    signal("observed-stale", "OBSERVED", "STALE", "2026-10-05T12:00:00Z"),
    signal("potential", "POTENTIAL", "CURRENT", "2026-10-04T12:00:00Z"),
  ];
  const before = nodes.map((item) => item.id);
  assert.deepEqual(
    orderedSignals(nodes).map((item) => item.id),
    ["observed-new", "observed-old", "observed-stale", "potential", "unknown-new"],
  );
  assert.deepEqual(nodes.map((item) => item.id), before);
  assert.deepEqual(
    signalGroups(nodes).map((group) => [group.state, group.signals.length]),
    [["OBSERVED", 3], ["POTENTIAL", 1], ["UNKNOWN", 1]],
  );
});

test("Today fallback selects latest known observation but does not fabricate a Today item", () => {
  const nodes = [
    signal("older", "OBSERVED", "CURRENT", "2026-10-01T12:00:00Z"),
    signal("latest", "UNKNOWN", "CURRENT", "2026-10-03T12:00:00Z"),
  ];
  const projection = { nodes, today: { disposition: "READY", items: [] } };
  assert.equal(latestObservedSignal(projection)?.id, "latest");
  assert.equal(projection.today.items.length, 0);
});

test("Today fallback is null when no observation exists", () => {
  assert.equal(latestObservedSignal({ nodes: [] }), null);
});
