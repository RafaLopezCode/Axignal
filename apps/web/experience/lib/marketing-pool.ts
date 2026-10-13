import { z } from "zod";

/** AXIGNAL's own marketing pool (Admin, first-party acquisition). Not AXIGLAND state. */
export const poolStates = ["DRAFTED", "APPROVED", "SENT", "HELD", "SEND_FAILED", "NOT_QUALIFIED",
  "STUDYING", "STUDY_FAILED", "SUPPRESSED", "DISCARDED", "DISCOVERED"] as const;

const finding = z.object({
  family: z.string(), kind: z.string(), code: z.string(), statement: z.string(),
  state: z.string(), source: z.string().nullable(), value: z.unknown().optional(),
});
export const poolProspect = z.object({
  domain: z.string(), name: z.string(), website: z.string(), country: z.string(),
  persona: z.string().nullable(), source: z.string(), sourceRef: z.string().nullable(),
  state: z.enum(poolStates), reason: z.string().nullable(), updatedAt: z.string(),
  recipient: z.string().nullable().optional(), language: z.string().nullable().optional(),
  channel: z.string().nullable().optional(), channelBasis: z.string().nullable().optional(),
  families: z.array(z.string()), findings: z.array(finding),
  draft: z.object({ subject: z.unknown(), body: z.unknown(), footer: z.unknown() }).nullable(),
  sentAt: z.string().nullable().optional(), html: z.string().nullable().optional(),
  campaign: z.string().nullable().optional(),
});
export const poolCampaign = z.object({
  id: z.string(), name: z.string(), state: z.enum(["ACTIVE", "COMPLETED", "ENDED", "EXHAUSTED", "CANCELLED"]),
  reason: z.string().nullable(), personas: z.array(z.string()), countries: z.array(z.string()),
  target: z.number(), endsAt: z.string().nullable(), createdBy: z.string(), createdAt: z.string(),
  progress: z.object({ discovered: z.number(), studied: z.number(), qualified: z.number(),
    drafted: z.number(), approved: z.number(), sent: z.number(), held: z.number(), optedOut: z.number() }),
});
export const poolSnapshot = z.union([
  z.object({ enabled: z.literal(false) }),
  z.object({
    enabled: z.literal(true),
    sending: z.string().nullable(),
    drafting: z.boolean(),
    limits: z.object({ studiesPerDay: z.number(), sendsPerDay: z.number() }),
    versions: z.object({ personas: z.string(), channelPolicy: z.string() }),
    personas: z.array(z.object({ id: z.string(), label: z.string() })),
    markets: z.array(z.object({ iso: z.string(), channel: z.string(), basis: z.string() })),
    counts: z.record(z.string(), z.number()),
    campaigns: z.array(poolCampaign),
    prospects: z.array(poolProspect),
    discovery: z.array(z.object({ key: z.string(), at: z.string(), found: z.number(),
      added: z.number(), error: z.string().nullable() })),
  }),
]);
export const poolCommand = z.union([
  z.object({ domain: z.string().min(3).max(253), action: z.enum(["APPROVE", "DISCARD", "SUPPRESS"]) }).strict(),
  z.object({
    action: z.literal("CREATE_CAMPAIGN"), name: z.string().trim().min(1).max(80),
    personas: z.array(z.string().max(40)).min(1).max(8), countries: z.array(z.string().length(2)).min(1).max(40),
    target: z.number().int().min(1).max(500), endsOn: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable(),
  }).strict(),
  z.object({ action: z.literal("CANCEL_CAMPAIGN"), campaign: z.string().min(3).max(40) }).strict(),
]);
export const poolReading = z.object({
  name: z.string(), domain: z.string(), language: z.string().nullable(),
  studiedAt: z.string().nullable(), findings: z.array(finding),
  authority: z.literal("OPERATIONAL_NOT_CANONICAL"),
});
export type PoolSnapshot = z.infer<typeof poolSnapshot>;
export type PoolProspect = z.infer<typeof poolProspect>;
export type PoolCampaign = z.infer<typeof poolCampaign>;
export type PoolReading = z.infer<typeof poolReading>;
export const poolToken = /^[A-Za-z0-9_-]{8,64}$/;
