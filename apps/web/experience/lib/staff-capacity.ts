import { z } from "zod";

/** Staff-provisioned capacity (issue #177): governed Admin grants, never billing. */
export const staffActions = ["preview", "grant", "revoke", "organizations"] as const;
export type StaffAction = (typeof staffActions)[number];

export const tenantId = z.string().regex(/^[A-Za-z0-9:_.-]{3,160}$/);
const reason = z.string().trim().min(8).max(500);
const idempotencyKey = z.string().min(8).max(160);
const destination = z.enum(["AXIGNAL_INTERNAL", "CUSTOMER_ACCOUNT"]);

const capacityTerms = {
  tenantId,
  destination,
  capacity: z.number().int().min(1).max(500),
  expiresAt: z.iso.datetime({ offset: true }),
};

/** Strict: any extra field (billing, price, subscription…) is refused before the runtime. */
export const staffCommands = {
  preview: z.object(capacityTerms).strict(),
  grant: z.object({ ...capacityTerms, reason, idempotencyKey }).strict(),
  revoke: z.object({ grantRef: z.string().regex(/^staff_capacity_[a-f0-9]{8,64}$/), reason }).strict(),
  organizations: z.object({ tenantId, locator: z.string().trim().min(2).max(2048), reason, idempotencyKey }).strict(),
} satisfies Record<StaffAction, z.ZodType>;

const notBilling = z.literal("STAFF_GRANT_NOT_BILLING");
export const staffGrant = z.object({
  grantRef: z.string(),
  tenantId: z.string(),
  destination,
  capacity: z.number().int(),
  reason: z.string(),
  grantedBy: z.string(),
  grantedAt: z.string(),
  expiresAt: z.string(),
  revokedAt: z.string().nullable(),
  revokedBy: z.string().nullable(),
  revocationReason: z.string().nullable(),
  state: z.enum(["ACTIVE", "EXPIRED", "REVOKED"]),
  provenance: notBilling,
});
export type StaffGrant = z.infer<typeof staffGrant>;

export const entitlementSource = z.enum(["BILLING", "BILLING+STAFF_GRANT", "STAFF_GRANT", "DESIGN_PARTNER_PILOT", "UNKNOWN"]);
export const staffAuditRow = z.object({
  occurredAt: z.string(),
  actor: z.string(),
  action: z.string(),
  tenantId: z.string(),
  grantRef: z.string().nullable(),
  detail: z.record(z.string(), z.unknown()),
});
export const staffState = z.object({
  tenantId: z.string(),
  entitlementSource,
  activeStaffCapacity: z.number().int().nonnegative(),
  grants: z.array(staffGrant),
  audit: z.array(staffAuditRow),
});
export type StaffState = z.infer<typeof staffState>;

export const staffResults = {
  preview: z.object({
    tenantId: z.string(),
    destination,
    currentStaffCapacity: z.number().int(),
    staffCapacityAfter: z.number().int(),
    expiresAt: z.string(),
    billingChanged: z.literal(false),
    checkoutCreated: z.literal(false),
    provenance: notBilling,
  }),
  grant: z.object({ grant: staffGrant, entitlementSource }),
  revoke: z.object({ grant: staffGrant, entitlementSource }),
  organizations: z.object({
    status: z.string().nullable(),
    focusId: z.string().nullable(),
    identityReason: z.string().nullable(),
    checkoutCreated: z.literal(false),
  }),
} satisfies Record<StaffAction, z.ZodType>;
export type StaffPreview = z.infer<typeof staffResults.preview>;
export type StaffAddResult = z.infer<typeof staffResults.organizations>;

/** Runtime refusals the panel explains; anything else is a generic failure. */
export const staffReasons = [
  "ADMIN_SESSION_REQUIRED", "STEP_UP_REQUIRED", "ADMIN_SCOPE_REQUIRED", "SCOPE_REQUIRED",
  "TENANT_UNKNOWN", "GRANT_NOT_FOUND", "IDEMPOTENCY_CONFLICT", "INVALID_REQUEST",
  "STAFF_CAPACITY_DISABLED", "ORIGIN_REQUIRED",
] as const;
export type StaffReason = (typeof staffReasons)[number] | "FAILED";
export function staffReason(value: unknown): StaffReason {
  return (staffReasons as readonly unknown[]).includes(value) ? (value as StaffReason) : "FAILED";
}
