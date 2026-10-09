import { z } from "zod";

const dimensionSchema = z.object({
  dimension: z.enum(["offer", "audience", "outcome"]),
  state: z.enum(["STRENGTH", "CONSTRUCTIVE_GAP", "UNCERTAIN", "UNRESOLVED"]),
  cause: z.string().max(100), citationIds: z.array(z.string().max(20)).max(16),
  proposal: z.string().max(100).nullable(), alternatives: z.array(z.string().max(100)).max(8),
  recheck: z.string().max(100),
});
const reportSchema = z.object({
  reportId: z.string().regex(/^[a-f0-9]{64}$/), measuredAt: z.string().datetime({ offset: true }),
  instrument: z.object({ id: z.string().max(100), version: z.string().max(30),
    representationVersion: z.string().max(100).optional(), interpretationVersion: z.string().max(100).optional(),
    evaluator: z.string().max(100).optional(), model: z.string().max(100).optional() }),
  status: z.enum(["MEASURED", "NOT_MEASURED", "NON_INFORMATIVE"]), cause: z.string().max(100),
  currentness: z.enum(["CURRENT", "STALE", "EXPIRED", "HISTORICAL"]),
  execution: z.enum(["NONE", "EVALUATED", "EXACT_JUDGMENT_REUSE"]),
  coverage: z.string().max(50),
  authority: z.literal("DERIVED_CONDITIONED_NOT_CANONICAL"),
  citations: z.array(z.object({ id: z.string().max(20), url: z.string().max(2048), quote: z.string().max(480),
    observedAt: z.string().datetime({ offset: true }), contentFingerprint: z.string().max(160) })).max(16),
  dimensions: z.array(dimensionSchema).max(3),
  sourceObservedAt: z.string().datetime({ offset: true }).nullable().optional(),
  validUntil: z.string().datetime({ offset: true }).optional(),
  contentExpiresAt: z.string().datetime({ offset: true }).optional(),
  conditions: z.object({ languages: z.array(z.string().max(50)).max(3),
    sourceSet: z.array(z.string().max(2048)).max(3), sampleSize: z.literal(1),
  }).optional(),
  sourceRights: z.array(z.object({ url: z.string().max(2048), basisRef: z.string().max(300).nullable(),
    policyVersion: z.string().max(100), providerInput: z.boolean(), publicOfferInput: z.boolean(),
  })).max(3).optional(),
});
export const publicUnderstandingSchema = reportSchema.extend({
  history: z.array(reportSchema).max(8).optional(),
  comparison: z.object({ previousReportId: z.string().max(64), previousMeasuredAt: z.string().max(64),
    state: z.enum(["COMPARABLE", "NOT_COMPARABLE"]), reason: z.string().max(100), meaning: z.string().max(100),
    changes: z.array(z.object({ dimension: z.enum(["offer", "audience", "outcome"]), before: z.string().max(50), after: z.string().max(50),
      kind: z.enum(["STATE_CHANGED", "INTERPRETATION_BASIS_CHANGED"]).optional(),
      beforeQuotations: z.array(z.string().max(480)).max(16).optional(),
      afterQuotations: z.array(z.string().max(480)).max(16).optional(),
    })).max(3),
  }).nullable().optional(),
});
export type PublicUnderstanding = z.infer<typeof publicUnderstandingSchema>;
export type UnderstandingDimension = z.infer<typeof dimensionSchema>;

/** Resolve a private AXENT citation against the already authorized report DTO. */
export function understandingReportReference(ref: string, report?: PublicUnderstanding): string | null {
  const parsed = /^public-understanding:([a-f0-9]{64}):(offer|audience|outcome):(q[1-9][0-9]?)$/.exec(ref);
  if (!parsed || !report) return null;
  const matched = [report, ...(report.history ?? [])].find(item => item.reportId === parsed[1]
    && item.status === "MEASURED" && item.currentness !== "EXPIRED");
  if (!matched || !matched.citations.some(item => item.id === parsed[3])
    || !matched.dimensions.some(item => item.dimension === parsed[2] && item.citationIds.includes(parsed[3]))) return null;
  return matched.reportId;
}
