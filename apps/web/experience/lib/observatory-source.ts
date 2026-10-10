/**
 * The one place where the Observatory's two contexts differ.
 *
 * The Observatory is a single experience. It runs in the authenticated account, over the subscriber's own
 * data and authorized operations, or in the public demonstration, over a fixed synthetic snapshot with no
 * session and no operations. Everything that differs is declared here: where data comes from, and which
 * capabilities exist. The components never ask which context they are in.
 */
import { portfolioSchema, type SubscriberPortfolio } from "./subscriber-contracts";
import type { Locale } from "./languages";

export type PortfolioItem = SubscriberPortfolio["organizations"][number];

/** What the context offers around the reading. The demo declares them all (it shows them disabled); an Admin lacks the account ones. */
export type ObservatoryCapabilities = {
  /** Account settings, capacity purchase, connections and sign-out. */
  readonly account: boolean;
  /** Pause, replace and remove an organization, and re-check an unresolved identity. */
  readonly manage: boolean;
  /** Re-check an organization whose identity is still unresolved. */
  readonly recheck: boolean;
  /** Where AXENT is asked: the subscriber's authorized endpoint, or the Admin session's own. */
  readonly axent: "subscriber" | "admin";
};

export type ObservatorySource = {
  readonly mode: "account" | "demo" | "admin";
  /** Operations that need an account and an authorization: add, pause, remove, purchase, AXENT, sign-out. */
  readonly canAct: boolean;
  /** The reads depend on the reader's language, so they are repeated when it changes. */
  readonly localized: boolean;
  readonly capabilities: ObservatoryCapabilities;
  /** The organization the context opens on when it has several; without one, a portfolio of several opens on the desk. */
  readonly landing?: string;
  readPortfolio(signal: AbortSignal, locale: Locale): Promise<SubscriberPortfolio | "SESSION_REQUIRED">;
  readOutput(focusId: string, signal: AbortSignal, locale: Locale): Promise<unknown>;
  /** Organizations the context already authorizes, offered while adding one. */
  suggestions?(signal: AbortSignal): Promise<readonly string[]>;
  /** An operation on the portfolio. Absent where nothing can be done (the demo). */
  command?(input: Record<string, unknown>, requestRef: string, signal: AbortSignal): Promise<unknown>;
  /** The rail's name for an organization, where it differs from the reading's own name. */
  menuName?: (item: PortfolioItem) => string;
};

/** The authenticated subscriber: the authorized API of the account. */
export const accountSource: ObservatorySource = {
  mode: "account",
  canAct: true,
  localized: false,
  capabilities: { account: true, manage: true, recheck: true, axent: "subscriber" },
  async readPortfolio(signal) {
    const response = await fetch("/api/subscriber/portfolio", { cache: "no-store", signal });
    if (response.status === 401) return "SESSION_REQUIRED";
    if (!response.ok) throw new Error("READ_FAILED");
    return portfolioSchema.parse(await response.json());
  },
  async readOutput(focusId, signal) {
    const response = await fetch(`/api/subscriber/organizations/${encodeURIComponent(focusId)}/output`, { cache: "no-store", signal });
    if (!response.ok) throw new Error("READ_FAILED");
    return response.json();
  },
  async command(input, requestRef, signal) {
    const response = await fetch("/api/subscriber/portfolio", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...input, requestRef }), signal });
    if (response.status === 401) return "SESSION_REQUIRED";
    if (!response.ok) throw new Error("COMMAND_FAILED");
    return response.json();
  },
};
