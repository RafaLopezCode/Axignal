import { z } from "zod";
const ref = z.string().min(3).max(160), nullable = z.string().nullable();
const reason = z.string().trim().min(8).max(500).refine(v => !/[\u0000-\u001f]/.test(v));
const key = z.string().min(8).max(160);
export const customerActions = ["issue", "revoke-invite", "revoke-grant"] as const;
export type CustomerAction = typeof customerActions[number];
export const customerCommands = {
  issue: z.object({ reason, inviteHours: z.number().int().min(1).max(720), idempotencyKey: key }).strict(),
  "revoke-invite": z.object({ reference: ref.max(80), reason, idempotencyKey: key }).strict(),
  "revoke-grant": z.object({ reference: ref.max(80), reason, idempotencyKey: key }).strict(),
};
export const issuedInvite = z.object({ inviteRef: ref, inviteToken: z.string().regex(/^[A-Za-z0-9_-]{43}$/), expiresAt: z.string(), capacity: z.literal(1) });
const invite = z.object({
  invite_ref: ref, issued_by: z.string(), reason: z.string(), created_at: z.string(), expires_at: z.string(),
  redeemed_at: nullable, redeemed_principal_id: nullable, redeemed_tenant_id: nullable, revoked_at: nullable,
  capacity: z.literal(1), state: z.enum(["PENDING", "REDEEMED", "EXPIRED", "REVOKED"]),
});
const grant = z.object({
  grant_ref: ref, invite_ref: ref, principal_id: ref, tenant_id: ref, capacity: z.literal(1),
  granted_at: z.string(), expires_at: z.string(), revoked_at: nullable, state: z.enum(["ACTIVE", "REVOKED", "EXPIRED"]),
});
const observation = z.object({ state: z.string(), firstProofReady: z.boolean(), headline: nullable, headlineCode: nullable, observedAt: nullable });
const organization = z.object({ focusId: ref, organizationId: nullable, label: z.string(), state: z.string(), reason: nullable.optional(), observation: observation.optional() });
const billing = z.object({ subscriptionRef: ref, status: z.string(), paymentState: z.string(), contractedCapacity: z.number().int().nullable(), verifiedAt: nullable, paidThrough: nullable });
export const customerAccess = z.object({
  asOf: z.string(), limit: z.number(), pilotEnabled: z.boolean(),
  customers: z.array(z.object({
    tenantId: ref, principalId: ref, membership: z.literal("ACTIVE"), capacity: z.number().int().nullable(),
    capacityCurrentness: z.string(), entitlementSource: z.string(), organizations: z.array(organization),
    billing: billing.nullable(), billingReadable: z.boolean(), firstObservationEnabled: z.boolean(),
  })),
  accountOperations: z.object({ customers: z.array(z.object({
    accountId: ref, tenantId: ref, displayName: z.string(), accountStatus: z.string(), subscriptionStatus: z.string(), paymentState: z.string(),
  })) }),
  pilot: z.object({
    asOf: z.string(), limit: z.number(), invites: z.array(invite), grants: z.array(grant),
    audit: z.array(z.object({ sequence: z.number(), action: z.string(), actor: z.string(), reference: ref, occurred_at: z.string(), reason: z.string(), tenant_id: nullable, principal_id: nullable })),
  }).nullable(),
});
export type CustomerAccess = z.infer<typeof customerAccess>;
export function pilotLink(origin: string, token: string): string {
  const url = new URL("/signup", origin);
  if (!["https:", "http:"].includes(url.protocol) || !/^[A-Za-z0-9_-]{43}$/.test(token)) throw new Error("INVALID_INVITE");
  url.hash = "pilot=" + token;
  return url.href;
}
export function activationCause(c: CustomerAccess["customers"][number]): "PAYMENT" | "ACCESS" | "CAPACITY" | "IDENTITY" | "RUNTIME" | "OBSERVATION" | "READY" {
  if (c.capacityCurrentness !== "CURRENT") return c.billing && c.billing.paymentState !== "VERIFIED" ? "PAYMENT" : "ACCESS";
  if (c.organizations.some(o => ["CAPACITY_UNKNOWN", "CAPACITY_PENDING", "PURCHASE_AUTHORITY_REQUIRED"].includes(o.state))) return "CAPACITY";
  if (c.organizations.some(o => o.observation?.firstProofReady)) return "READY";
  if (c.organizations.some(o => o.organizationId === null)) return "IDENTITY";
  if (!c.firstObservationEnabled) return "RUNTIME";
  return c.organizations.some(o => o.observation?.firstProofReady) ? "READY" : "OBSERVATION";
}
