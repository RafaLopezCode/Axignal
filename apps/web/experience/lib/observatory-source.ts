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

export type ObservatorySource = {
  readonly mode: "account" | "demo";
  /** Operations that need an account and an authorization: add, pause, remove, purchase, AXENT, sign-out. */
  readonly canAct: boolean;
  /** The reads depend on the reader's language, so they are repeated when it changes. */
  readonly localized: boolean;
  readPortfolio(signal: AbortSignal, locale: Locale): Promise<SubscriberPortfolio | "SESSION_REQUIRED">;
  readOutput(focusId: string, signal: AbortSignal, locale: Locale): Promise<unknown>;
  /** The rail's name for an organization, where it differs from the reading's own name. */
  menuName?: (item: PortfolioItem) => string;
};

/** The authenticated subscriber: the authorized API of the account. */
export const accountSource: ObservatorySource = {
  mode: "account",
  canAct: true,
  localized: false,
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
};
