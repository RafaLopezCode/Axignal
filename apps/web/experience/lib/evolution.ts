/**
 * Comparable evolution (spec 076): any recorded day X against any day Y.
 *
 * Mirrors `application/timeline` exactly: the same thresholds, polarity and instrument rule
 * (a before/after is comparable only under the same instrument and version, MASTER §22).
 * A metric absent on a day is not measured that day, never zero or empty. A change is what
 * differs between two readings, never why.
 */
import type { Channel, Facet } from "./observation-families";
import type { FamilyId } from "./projection";

export type CatalogEntry = { family: string; polarity: number; state?: string; minAbs: number; minRel: number };
export type EvolutionVersion = { from: string; to: string; metrics: Record<string, unknown> };
export type Evolution = { timelineVersion?: string; days: string[]; versions: EvolutionVersion[]; catalog: Record<string, CatalogEntry> };

export type Direction = "EVOLUTION" | "REGRESSION" | "UP" | "DOWN" | "ADDED" | "REMOVED" | "CHANGED" | "SAME" | "NOT_COMPARABLE" | "NOT_MEASURED";
export type Row = {
  key: string; family: FamilyId; channel: Channel | null;
  before: unknown; after: unknown; direction: Direction;
  delta?: number; added?: string[]; removed?: string[];
};

const INSTRUMENTS = "_instruments";
/** Metrics measured by an instrument of their own (audit, generative probe); the rest are the timeline's definition. */
const MEASURED = new Set(["presence.ai_named_share", "presence.ai_knows_brand", "presence.search_ranked_share", "presence.audit_attention", "presence.audit_passed", "presence.lcp_ms", "presence.inp_ms"]);

export function channelOf(key: string): Channel | null {
  if (key.startsWith("presence.ai_")) return "GEO";
  return key.startsWith("presence.") ? "WEB" : null;
}

/** The recorded version that covers a day, if any. */
export function versionOn(evolution: Evolution, day: string): EvolutionVersion | null {
  return evolution.versions.find(v => v.from <= day && day <= v.to) ?? null;
}

function instrumentOf(metrics: Record<string, unknown>, key: string, version: string | undefined): string | null {
  const held = metrics[INSTRUMENTS];
  if (held && typeof held === "object" && key in (held as Record<string, unknown>)) return String((held as Record<string, unknown>)[key]);
  return MEASURED.has(key) ? null : (version ?? "timeline-v1");
}

const isNumber = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

/** One metric between two days, exactly as the engine's `changes` would state it. */
export function compareMetric(key: string, entry: CatalogEntry, before: Record<string, unknown> | null, after: Record<string, unknown> | null, version?: string): Row {
  const row: Row = { key, family: entry.family as FamilyId, channel: channelOf(key), before: before?.[key], after: after?.[key], direction: "SAME" };
  if (!before || !after || before[key] === undefined || before[key] === null || after[key] === undefined || after[key] === null) return { ...row, direction: "NOT_MEASURED" };
  if (instrumentOf(before, key, version) !== instrumentOf(after, key, version)) return { ...row, direction: "NOT_COMPARABLE" };
  const [b, a] = [before[key], after[key]];
  if (Array.isArray(b) && Array.isArray(a)) {
    const was = new Set(b.map(String)), now = new Set(a.map(String));
    const added = [...now].filter(x => !was.has(x)).sort(), removed = [...was].filter(x => !now.has(x)).sort();
    if (!added.length && !removed.length) return row;
    let direction: Direction = added.length && !removed.length ? "ADDED" : removed.length && !added.length ? "REMOVED" : "CHANGED";
    if (entry.polarity) {
      const better = entry.polarity < 0 ? a.length < b.length : a.length > b.length;
      const worse = entry.polarity < 0 ? a.length > b.length : a.length < b.length;
      direction = better ? "EVOLUTION" : worse ? "REGRESSION" : direction;
    }
    return { ...row, direction, added, removed };
  }
  if (isNumber(b) && isNumber(a)) {
    const delta = a - b;
    const rel = b ? Math.abs(delta) / Math.abs(b) : 1;
    if (Math.abs(delta) < entry.minAbs || rel < entry.minRel) return { ...row, delta: Math.round(delta * 10000) / 10000 };
    const direction: Direction = entry.polarity ? (delta * entry.polarity > 0 ? "EVOLUTION" : "REGRESSION") : delta > 0 ? "UP" : "DOWN";
    return { ...row, direction, delta: Math.round(delta * 10000) / 10000 };
  }
  return row;
}

/** Every catalogued metric between day X and day Y, filtered by the selected family/channel. */
export function compareDays(evolution: Evolution, x: string, y: string, facet: Facet): Row[] {
  const before = versionOn(evolution, x)?.metrics ?? null, after = versionOn(evolution, y)?.metrics ?? null;
  return Object.entries(evolution.catalog)
    .map(([key, entry]) => compareMetric(key, entry, before, after, evolution.timelineVersion))
    .filter(r => !facet.family || (r.family === facet.family && (!facet.channel || r.channel === facet.channel)))
    .filter(r => !(r.direction === "NOT_MEASURED" && r.before === undefined && r.after === undefined));
}

/** A numeric metric across every recorded day (for a small trend line); unmeasured days are gaps. */
export function seriesOf(evolution: Evolution, key: string): Array<[string, number | null]> {
  return evolution.days.map(day => {
    const value = versionOn(evolution, day)?.metrics[key];
    return [day, isNumber(value) ? value : null];
  });
}
