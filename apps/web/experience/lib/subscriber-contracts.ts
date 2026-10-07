import { z } from "zod";
import { runtimeProjectionSchema } from "./runtime-projection";

const ref = z.string().min(1).max(160).regex(/^[A-Za-z0-9:_-]+$/);
export const subscriberCommandSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("add"), requestRef: ref, locator: z.string().trim().min(1).max(2048) }).strict(),
  z.object({ action: z.enum(["pause", "resume", "remove", "reobserve", "retry_pending", "cancel_pending"]), requestRef: ref, focusId: ref }).strict(),
  z.object({ action: z.literal("replace"), requestRef: ref, focusId: ref, locator: z.string().trim().min(1).max(2048) }).strict(),
  z.object({ action: z.enum(["purchase", "expand"]), requestRef: ref, desiredOrganizationTotal: z.number().int().min(1).max(100000) }).strict(),
  z.object({ action: z.literal("refresh_purchase"), requestRef: ref }).strict(),
]);
export const portfolioSchema = z.object({
  state: z.literal("success"),
  capacity: z.number().int().nonnegative().nullable(),
  capacityCurrentness: z.enum(["CURRENT", "STALE", "HISTORICAL", "UNKNOWN"]),
  entitlementSource: z.enum(["BILLING", "DESIGN_PARTNER_PILOT", "UNKNOWN"]).default("UNKNOWN"),
  canPurchase: z.boolean().nullable(),
  contractingEnabled: z.boolean(),
  organizations: z.array(z.object({
    focusId: ref, organizationId: ref.nullable(), label: z.string().max(2048),
    state: z.enum(["ACTIVE", "PAUSED", "REMOVED", "IDENTITY_PENDING", "IDENTITY_REJECTED", "CAPACITY_UNKNOWN", "CAPACITY_PENDING", "PURCHASE_AUTHORITY_REQUIRED", "RESOLVED", "CANCELLED"]),
    // Why identity is unresolved (spec 052); a stable code, never the typed text.
    reason: z.string().max(160).nullable().optional(),
  })),
});
export type SubscriberPortfolio = z.infer<typeof portfolioSchema>;
export const pilotRedemptionSchema = z.discriminatedUnion("state", [
  z.object({ state: z.literal("PILOT_ACTIVE"), accepted: z.literal(true),
    capacity: z.literal(1), expiresAt: z.string().datetime({ offset: true }) }),
  z.object({ state: z.literal("PILOT_INVITE_INVALID"), accepted: z.literal(false) }),
]);
export const subscriberOutputSchema = z.object({
  state: z.enum(["success", "INSUFFICIENT_EVIDENCE"]),
  projection: runtimeProjectionSchema,
  revision: z.string().regex(/^[a-f0-9]{64}$/).optional(),
  reason: z.string().max(160).optional(),
});
export const subscriberResultSchema = z.object({
  state: z.string().max(80), code: z.string().max(160).optional(),
  requestRef: ref.optional(), focusId: ref.optional(),
  effectiveCapacity: z.number().int().nonnegative().nullable().optional(),
  desiredCapacity: z.number().int().positive().optional(),
  checkoutUrl: z.url().nullable().optional(), paymentUrl: z.url().nullable().optional(),
  reason: z.string().max(160).nullable().optional(),
  observationState: z.enum(["NOT_READY", "BLOCKED_COST_UNKNOWN", "BLOCKED_BUDGET", "PARTIAL", "COMPLETED", "BLOCKED", "ACCEPTED", "INSUFFICIENT_EVIDENCE"]).optional(),
  runId: ref.optional(),
});
export function approvedPaymentUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password &&
      (!url.port || url.port === "443") &&
      ["checkout.stripe.com", "invoice.stripe.com", "pay.stripe.com"].includes(url.hostname)
      ? value : null;
  } catch { return null; }
}
export function monthlyCapacityCents(total: number): number {
  if (!Number.isSafeInteger(total) || total < 1 || total > 100000) throw new Error("INVALID_CAPACITY");
  return 995 + (total - 1) * 495;
}
