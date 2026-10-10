/**
 * The Admin's Observatory source: Customer Zero, read through the same components as a subscriber.
 *
 * Only where data comes from and which operations exist differ. The Admin session reads its organizations
 * from the internal attention inventory and opens a reading from the governed runtime projection. Adding an
 * organization is an attention command, never a purchase: no capacity, checkout or billing is involved.
 * Nothing here grants authority; every call is authorized by the Admin session the service already holds.
 */
import { organizationInventorySchema, type OrganizationInventory } from "./organization-attention";
import { readCustomerZeroResponse } from "./runtime-projection";
import { portfolioSchema, type SubscriberPortfolio } from "./subscriber-contracts";
import type { ObservatorySource } from "./observatory-source";

type Entry = OrganizationInventory["organizations"][number];

/** A name or a public website, as the add form collects it, becomes the label and address an attention needs. */
export function attentionFromLocator(locator: string): { name: string; targetUri: string } | null {
  const text = locator.trim();
  if (!text || /\s/.test(text)) return null;
  const candidate = /^https?:\/\//i.test(text) ? text : `https://${text}`;
  try {
    const url = new URL(candidate);
    if (!/^https?:$/.test(url.protocol) || url.username || url.password || !url.hostname.includes(".")) return null;
    return { name: url.hostname.replace(/^www\./, ""), targetUri: url.toString() };
  } catch { return null; }
}

/** The inventory's own states, shown as the portfolio's: an identified organization is readable, the rest is pending. */
function portfolioState(entry: Entry): SubscriberPortfolio["organizations"][number]["state"] {
  return entry.organizationId ? "ACTIVE" : "IDENTITY_PENDING";
}

export function adminPortfolio(inventory: OrganizationInventory): SubscriberPortfolio {
  return portfolioSchema.parse({
    state: "success",
    // An Admin attends organizations by authority, not by purchased capacity.
    capacity: null,
    capacityCurrentness: "UNKNOWN",
    entitlementSource: "UNKNOWN",
    canPurchase: false,
    contractingEnabled: false,
    organizations: inventory.organizations.map(entry => ({
      focusId: entry.id,
      organizationId: entry.organizationId,
      label: entry.name ?? entry.requestedLabel,
      state: portfolioState(entry),
      reason: entry.organizationId ? null : entry.state,
    })),
  });
}

/** A reading is selected and then read: the selection is the existing attention command, serialized so readings never interleave. */
let queue: Promise<unknown> = Promise.resolve();
function serialized<T>(task: () => Promise<T>): Promise<T> {
  const next = queue.then(task, task);
  queue = next.catch(() => undefined);
  return next;
}

async function sha256Hex(text: string): Promise<string | undefined> {
  if (typeof crypto === "undefined" || !crypto.subtle) return undefined;
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
}

async function post(body: Record<string, unknown>, signal: AbortSignal) {
  return fetch("/api/xeeds", { method: "POST", cache: "no-store", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal });
}

export const adminSource: ObservatorySource = {
  mode: "admin",
  canAct: true,
  localized: false,
  // The Admin has no account to purchase, sign out of or connect; organizations are managed as attention.
  capabilities: { account: false, manage: false, axent: "admin" },
  async readPortfolio(signal) {
    const response = await fetch("/api/organizations", { cache: "no-store", signal });
    if (response.status === 401) return "SESSION_REQUIRED";
    if (!response.ok) throw new Error("READ_FAILED");
    return adminPortfolio(organizationInventorySchema.parse(await response.json()));
  },
  readOutput(focusId, signal) {
    return serialized(async () => {
      const selected = await post({ action: "select", id: focusId }, signal);
      if (!selected.ok) throw new Error("READ_FAILED");
      const response = await fetch("/api/subscriber-context", { cache: "no-store", signal });
      const state = readCustomerZeroResponse(await response.json(), response.status);
      if (state.state === "unauthorized") throw new Error("SESSION_REQUIRED");
      if (state.state === "INSUFFICIENT_EVIDENCE") throw new Error("INSUFFICIENT_EVIDENCE");
      if (state.state !== "success") throw new Error("READ_FAILED");
      const projection = state.projection;
      const revision = await sha256Hex([projection.context.id, projection.runtimeCodeSha, JSON.stringify(projection.organization)].join("|"));
      return { state: "success", projection, ...(revision ? { revision } : {}), firstObservation: null };
    });
  },
  async command(input, _requestRef, signal) {
    if (input.action === "add") {
      const attention = attentionFromLocator(String(input.locator ?? ""));
      if (!attention) return { state: "WEBSITE_REQUIRED" };
      const response = await post({ action: "add", ...attention }, signal);
      if (response.status === 401) return "SESSION_REQUIRED";
      if (!response.ok) throw new Error("COMMAND_FAILED");
      return { state: "ACCEPTED", observationState: "COMPLETED" };
    }
    if (input.action === "reobserve") {
      const response = await post({ action: "reobserve", id: String(input.focusId ?? "") }, signal);
      if (response.status === 401) return "SESSION_REQUIRED";
      if (!response.ok) throw new Error("COMMAND_FAILED");
      return { state: "ACCEPTED", observationState: "COMPLETED" };
    }
    throw new Error("COMMAND_NOT_AVAILABLE");
  },
};
