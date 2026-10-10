import snapshot from "./synthetic-observatory.json";
import { portfolioSchema, type SubscriberPortfolio } from "@/lib/subscriber-contracts";

/**
 * The public demo reads a fixed, fictional snapshot instead of the account's API.
 * Nothing here is private data: every organization is fictional and every host is an example domain (RFC 2606).
 * The demo renders the same Observatory as the subscriber; only this data source differs.
 */
export const SYNTHETIC_PROVENANCE: string = snapshot.provenance;

const outputs = snapshot.outputs as Record<string, unknown>;

export function syntheticPortfolio(): SubscriberPortfolio {
  return portfolioSchema.parse({
    state: "success",
    capacity: 10,
    capacityCurrentness: "CURRENT",
    entitlementSource: "UNKNOWN",
    canPurchase: false,
    contractingEnabled: false,
    organizations: snapshot.portfolio,
  });
}

export function syntheticOutput(focusId: string): unknown {
  if (!Object.prototype.hasOwnProperty.call(outputs, focusId)) throw new Error("READ_FAILED");
  return outputs[focusId];
}
