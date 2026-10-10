/**
 * Thematic navigation of the Observatory: which family, and for Presence which channel, a finding belongs to.
 *
 * Classification is deterministic and reads typed contract values only: the Discovery `kind` and `code`, the
 * Opportunity `familyId`, and the observation `sourceType`. It never reads headlines, quotes or any free text, and
 * a finding the contract cannot place has no family; it then appears under "All" and is never attributed to one.
 *
 * The Presence channels mirror the source capabilities the domain already governs (observation_intelligence
 * SourceCapability): DIGITAL_REPRESENTATION (the organization's own web), PUBLIC_SEARCH_VISIBILITY (search
 * engines) and GENERATIVE_ANSWER_SURFACES (generative answers).
 */
import type { FamilyId } from "./projection";
import type { Discovery } from "./subscriber-contracts";

/** The ten families, in the order a subscriber reads them. */
export const FAMILY_ORDER = [
  "presence", "reputation", "value", "markets", "relationships",
  "demand", "activity", "economics", "organization", "context",
] as const satisfies readonly FamilyId[];

export type Channel = "SEO" | "GEO" | "WEB";
/** Presence channels in reading order: SEO · GEO / AI · Web. */
export const CHANNEL_ORDER = ["SEO", "GEO", "WEB"] as const satisfies readonly Channel[];

export type Facet = { family: FamilyId | null; channel: Channel | null };
export const NO_FACET: Facet = { family: null, channel: null };

const WEB: Facet = { family: "presence", channel: "WEB" };

/** Discovery kinds that name their family by themselves. */
const BY_KIND: Partial<Record<Discovery["kind"], Facet>> = {
  PUBLIC_PRESENCE: WEB,
  WEB_REPRESENTATION: WEB,
  REPRESENTATION_GAP: WEB,
  LANGUAGES: WEB,
  SEARCH_VISIBILITY: { family: "presence", channel: "SEO" },
  GENERATIVE_VISIBILITY: { family: "presence", channel: "GEO" },
  ACTIVITY: { family: "value", channel: null },
  DECLARED_LOCATION: { family: "markets", channel: null },
  DECLARED_SERVICE_AREA: { family: "markets", channel: null },
  IDENTITY_HINT: { family: "organization", channel: null },
  DEMAND: { family: "demand", channel: null },
};

/** A grounded unknown names what is unknown through its code; codes carry an optional ":<jurisdiction>" suffix. */
const BY_UNKNOWN_CODE: Record<string, Facet> = {
  ROBOTS_DISALLOWED: WEB,
  NOT_AN_OPERATING_BUSINESS_SITE: WEB,
  IDENTITY_NOT_VERIFIED: { family: "organization", channel: null },
  ACTIVITY_NOT_ESTABLISHED: { family: "value", channel: null },
  NO_GOVERNED_DEMAND_SOURCE: { family: "demand", channel: null },
  NO_RELEVANT_DEMAND_FOUND: { family: "demand", channel: null },
};

export function facetOfDiscovery(d: Pick<Discovery, "kind" | "code">): Facet {
  if (d.kind === "SIGNIFICANT_UNKNOWN") return BY_UNKNOWN_CODE[d.code.split(":")[0]] ?? NO_FACET;
  return BY_KIND[d.kind] ?? NO_FACET;
}

/** Opportunities carry their family in the contract. */
export function facetOfOpportunity(o: { familyId: FamilyId }): Facet {
  return { family: o.familyId, channel: null };
}

/** The observation source types of the temporal history, named after the governed source capabilities. */
const BY_SOURCE_TYPE: Record<string, Facet> = {
  PUBLIC_WEBSITE: WEB,
  DIGITAL_REPRESENTATION: WEB,
  PUBLIC_SEARCH_VISIBILITY: { family: "presence", channel: "SEO" },
  GENERATIVE_ANSWER_SURFACES: { family: "presence", channel: "GEO" },
};

export function facetOfSourceType(sourceType: string): Facet {
  return BY_SOURCE_TYPE[sourceType] ?? NO_FACET;
}

/** A finding matches a selection when it lies in its family and, if a channel is selected, in that channel. */
export function matchesFacet(item: Facet, selected: Facet): boolean {
  if (!selected.family) return true;
  if (item.family !== selected.family) return false;
  return !selected.channel || item.channel === selected.channel;
}

export function countByFacet(items: Facet[]): { families: Record<FamilyId, number>; channels: Record<Channel, number> } {
  const families = Object.fromEntries(FAMILY_ORDER.map(id => [id, 0])) as Record<FamilyId, number>;
  const channels: Record<Channel, number> = { SEO: 0, GEO: 0, WEB: 0 };
  for (const item of items) {
    if (item.family) families[item.family] += 1;
    if (item.family === "presence" && item.channel) channels[item.channel] += 1;
  }
  return { families, channels };
}

export function litByFamily(items: Array<Facet & { changeKey: string }>, lit: ReadonlySet<string>): Record<FamilyId, number> {
  const out = Object.fromEntries(FAMILY_ORDER.map(id => [id, 0])) as Record<FamilyId, number>;
  for (const item of items) if (item.family && lit.has(item.changeKey)) out[item.family] += 1;
  return out;
}

/** Unread findings per Presence channel, from the same lit keys as the families. */
export function litByChannel(items: Array<Facet & { changeKey: string }>, lit: ReadonlySet<string>): Record<Channel, number> {
  const out: Record<Channel, number> = { SEO: 0, GEO: 0, WEB: 0 };
  for (const item of items) if (item.family === "presence" && item.channel && lit.has(item.changeKey)) out[item.channel] += 1;
  return out;
}

const FAMILY_SET = new Set<string>(FAMILY_ORDER);
const CHANNEL_SET = new Set<string>(CHANNEL_ORDER);

/** URL form: `family=presence&channel=seo`. Anything unrecognised is ignored, never guessed. */
export function parseFacet(family: string | null, channel: string | null): Facet {
  const f = family && FAMILY_SET.has(family) ? (family as FamilyId) : null;
  const c = channel && CHANNEL_SET.has(channel.toUpperCase()) ? (channel.toUpperCase() as Channel) : null;
  return f === "presence" ? { family: f, channel: c } : { family: f, channel: null };
}

export function facetParams(facet: Facet): { family: string | null; channel: string | null } {
  return { family: facet.family, channel: facet.family === "presence" && facet.channel ? facet.channel.toLowerCase() : null };
}
