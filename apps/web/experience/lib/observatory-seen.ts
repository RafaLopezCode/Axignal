/**
 * "Lit until seen": what this person has already noticed, kept on this device only.
 *
 * It is a viewing convenience, not cognitive memory or canonical state (HFX "Three
 * context authorities"). Losing it only re-lights findings; it never hides one.
 */
const STORAGE_NAME = "axignal.observatory.seen.v1";
const MAX_ORGANIZATIONS = 60;
const MAX_KEYS = 240;

export type SeenRecord = { visitedAt: string; keys: string[] };
export type SeenStore = Record<string, SeenRecord>;
type Storage = Pick<globalThis.Storage, "getItem" | "setItem">;

export function readSeen(storage: () => Storage): SeenStore {
  try {
    const raw = storage().getItem(STORAGE_NAME);
    const value: unknown = raw ? JSON.parse(raw) : {};
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    const out: SeenStore = {};
    for (const [focus, record] of Object.entries(value as Record<string, unknown>)) {
      const r = record as Partial<SeenRecord>;
      if (typeof r?.visitedAt === "string" && Array.isArray(r.keys)) out[focus] = { visitedAt: r.visitedAt, keys: r.keys.filter((k): k is string => typeof k === "string") };
    }
    return out;
  } catch { return {}; }
}

export function writeSeen(storage: () => Storage, store: SeenStore): void {
  try {
    const entries = Object.entries(store).sort((a, b) => b[1].visitedAt.localeCompare(a[1].visitedAt)).slice(0, MAX_ORGANIZATIONS);
    storage().setItem(STORAGE_NAME, JSON.stringify(Object.fromEntries(entries.map(([k, v]) => [k, { visitedAt: v.visitedAt, keys: v.keys.slice(-MAX_KEYS) }]))));
  } catch { /* Private mode or full storage: lamps simply stay lit. */ }
}

/** Keys that are new since the last recorded look at this organization. A first look lights nothing. */
export function litKeys(store: SeenStore, focusId: string, keys: string[]): Set<string> {
  const record = store[focusId];
  if (!record) return new Set();
  const seen = new Set(record.keys);
  return new Set(keys.filter(key => !seen.has(key)));
}

/** First look at an organization: everything currently shown becomes the baseline. */
export function baseline(store: SeenStore, focusId: string, keys: string[], now: string): SeenStore {
  if (store[focusId]) return store;
  return { ...store, [focusId]: { visitedAt: now, keys } };
}

/** Opening an organization notices its new observation; its findings stay lit until opened. */
export function touch(store: SeenStore, focusId: string, now: string): SeenStore {
  const record = store[focusId];
  return record ? { ...store, [focusId]: { ...record, visitedAt: now } } : store;
}

export function markSeen(store: SeenStore, focusId: string, keys: string[], now: string): SeenStore {
  const record = store[focusId] ?? { visitedAt: now, keys: [] };
  return { ...store, [focusId]: { visitedAt: now, keys: [...new Set([...record.keys, ...keys])] } };
}

/** An organization observed again after the last look carries a lamp in the portfolio. */
export function observedSinceVisit(store: SeenStore, focusId: string, observedAt: string | null | undefined): boolean {
  const record = store[focusId];
  if (!record || !observedAt) return false;
  return Date.parse(observedAt) > Date.parse(record.visitedAt);
}
