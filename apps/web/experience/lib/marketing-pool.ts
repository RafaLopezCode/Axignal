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
    prospects: z.array(poolProspect),
    discovery: z.array(z.object({ key: z.string(), at: z.string(), found: z.number(),
      added: z.number(), error: z.string().nullable() })),
  }),
]);
export const poolCommand = z.object({
  domain: z.string().min(3).max(253),
  action: z.enum(["APPROVE", "DISCARD", "SUPPRESS"]),
}).strict();
export const poolReading = z.object({
  name: z.string(), domain: z.string(), language: z.string().nullable(),
  studiedAt: z.string().nullable(), findings: z.array(finding),
  authority: z.literal("OPERATIONAL_NOT_CANONICAL"),
});
export type PoolSnapshot = z.infer<typeof poolSnapshot>;
export type PoolProspect = z.infer<typeof poolProspect>;
export type PoolReading = z.infer<typeof poolReading>;
export const poolToken = /^[A-Za-z0-9_-]{8,64}$/;
