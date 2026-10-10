/**
 * Activation: from a typed organization to a running observation, without granting anything.
 *
 * The backend keeps an organization asked for while capacity is unconfirmed as a waiting attention. Capacity is
 * only ever confirmed by the services that own it: a redeemed Design Partner invitation, a verified payment or a
 * staff grant. These helpers read that state; none of them decides it.
 */
import { EUR_REFERENCE } from "./commercial-prices";
import type { SubscriberPortfolio } from "./subscriber-contracts";

type Item = SubscriberPortfolio["organizations"][number];

/** Attention kept while capacity is not confirmed: it observes nothing until capacity is verified. */
export const WAITING_STATES: ReadonlySet<string> = new Set(["CAPACITY_UNKNOWN", "CAPACITY_PENDING", "PURCHASE_AUTHORITY_REQUIRED"]);

export function waitingItems(portfolio: SubscriberPortfolio | null): Item[] {
  return portfolio ? portfolio.organizations.filter(item => WAITING_STATES.has(item.state)) : [];
}

/** Free confirmed places, or null while capacity is not confirmed (never read as zero). */
export function capacityRoom(portfolio: SubscriberPortfolio | null): number | null {
  if (!portfolio || portfolio.capacity === null || portfolio.capacityCurrentness !== "CURRENT") return null;
  const used = portfolio.organizations.filter(item => item.state === "ACTIVE" || item.state === "PAUSED").length;
  return Math.max(0, portfolio.capacity - used);
}

/** The organizations a first subscription would cover: the active ones plus those waiting, at least one. */
export function firstPurchaseTotal(portfolio: SubscriberPortfolio | null): number {
  if (!portfolio) return 1;
  const used = portfolio.organizations.filter(item => item.state === "ACTIVE" || item.state === "PAUSED").length;
  return Math.max(1, used + waitingItems(portfolio).length);
}

const TOKEN = /^[A-Za-z0-9_-]{20,256}$/;

/** An invitation pasted as its link (…#pilot=TOKEN) or as the bare token; anything else is not an invitation. */
export function inviteTokenFrom(input: string): string | null {
  const text = input.trim();
  if (!text) return null;
  const fromLink = /#pilot=([A-Za-z0-9_-]{20,256})(?:$|[&\s])/.exec(text);
  if (fromLink) return fromLink[1];
  return TOKEN.test(text) ? text : null;
}

/** The payment provider's return to /account (?billing=complete|cancelled). */
export function billingReturn(params: URLSearchParams): "complete" | "cancelled" | null {
  const value = params.get("billing") ?? params.get("purchase");
  return value === "complete" || value === "cancelled" ? value : null;
}

/** The published monthly offer: the governed EUR reference of the price book (MASTER §27, ADR-0093). */
export const PUBLISHED_OFFER = EUR_REFERENCE;
export const FIRST_ORGANIZATION_CENTS = EUR_REFERENCE.baseMinor;
export const ADDITIONAL_ORGANIZATION_CENTS = EUR_REFERENCE.additionalMinor;

/** What the activation screen is doing right now; each phase is a real step, never a fake progress. */
export type ActivationPhase =
  | "idle"
  | "needs_access"
  | "redeeming"
  | "invite_rejected"
  | "invite_failed"
  | "checkout"
  | "checkout_failed"
  | "confirming_payment"
  | "payment_unconfirmed"
  | "payment_cancelled"
  | "starting";
