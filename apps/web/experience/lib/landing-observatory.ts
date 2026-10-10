/**
 * The landing shows the real subscriber interface working on the one public example
 * (the fictional organization of /panorama, lib/projection). It is the same example,
 * never a second fixture: this module only presents it through the observatory's
 * Insight shape, so the visitor sees the actual product grammar, not a picture of it.
 */
import { evidence, organizations, signals, type Signal } from "./projection";
import type { Insight, Lane, Nature } from "./observatory";
import type { Copy } from "./languages";

export const EXAMPLE_ORGANIZATION = "norte";
/** The example's observable moments, oldest first. */
export const EXAMPLE_MOMENTS = ["2026-07-01", "2026-09-01", "2026-10-03"] as const;
export type ExampleMoment = (typeof EXAMPLE_MOMENTS)[number];

type CopyOf = (value: Copy) => string;

function laneOf(signal: Signal): Lane {
  if (signal.epistemic === "POTENTIAL") return "matters";
  if (signal.epistemic === "UNKNOWN") return "unknown";
  return "understood";
}

function insightOf(signal: Signal, copy: CopyOf): Insight {
  const sources = signal.evidenceIds
    .map(id => evidence.find(item => item.id === id))
    .filter(item => item !== undefined)
    .map(item => ({ url: null, label: copy(item.source), observedAt: item.observedAt, quote: copy(item.title) }));
  return {
    id: signal.id,
    lane: laneOf(signal),
    nature: signal.epistemic as Nature,
    headline: copy(signal.title),
    why: copy(signal.why),
    observedAt: signal.detectedAt,
    meaning: [copy(signal.summary)],
    reasoning: [copy(signal.derivation), copy(signal.limitation)],
    proposal: null,
    sources,
    proof: signal.dimensions.map(d => ({ label: copy(d.label), value: copy(d.value) })),
    dimensions: [],
    previous: null,
    changeKey: `${signal.id}#${signal.detectedAt}`,
  };
}

/** What the example's subscriber sees at a moment: only what was available then. */
export function exampleInsights(asOf: ExampleMoment, copy: CopyOf): Insight[] {
  const order: Record<Lane, number> = { matters: 0, understood: 1, unknown: 2 };
  return signals
    .filter(s => s.organizationId === EXAMPLE_ORGANIZATION && s.availableFrom <= asOf)
    .map(s => insightOf(s, copy))
    .sort((a, b) => order[a.lane] - order[b.lane]);
}

/** Findings that appeared after the previous moment: the lamps a returning visitor sees. */
export function exampleNewSince(asOf: ExampleMoment): Set<string> {
  const index = EXAMPLE_MOMENTS.indexOf(asOf);
  if (index <= 0) return new Set();
  const previous = EXAMPLE_MOMENTS[index - 1];
  return new Set(signals.filter(s => s.organizationId === EXAMPLE_ORGANIZATION && s.availableFrom > previous && s.availableFrom <= asOf).map(s => s.id));
}

export function exampleOrganization() {
  return organizations.find(o => o.id === EXAMPLE_ORGANIZATION)!;
}
