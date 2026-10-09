import { z } from "zod";

// A read contract, not an economic model or a fixture fallback. Unknown fields
// are stripped so private operational extensions cannot reach product rendering.
const text = z.string().min(1);
const currentness = z.enum(["CURRENT", "STALE", "HISTORICAL", "UNKNOWN"]);
const familyId = z.enum([
  "presence",
  "reputation",
  "value",
  "markets",
  "relationships",
  "demand",
  "activity",
  "economics",
  "organization",
  "context",
]);
const instrument = z.object({ ref: text, version: text });
const pageMeasurementSchema = z.object({
  kind: z.literal("DRI_PUBLIC_PAGE_REPRESENTATION"), instrument,
  surface: z.literal("PUBLIC_WEB_PAGE"), resourceRef: text,
  source: z.object({ ref: text, policyRef: text, policyVersion: text,
    rightsBasisRef: z.string().nullable(), rightsStatus: text, accessStatus: text, reuseScope: text,
    retentionPolicyRef: z.string().nullable(), robotsPolicyRef: z.string().nullable() }),
  representation: z.object({ ref: text, fingerprint: text, representationVersion: text, normalizationVersion: text }),
  observedAt: text, conditions: z.object({ geography: text, language: text, deviceContext: text }),
  sample: z.object({ eligible: z.literal(1), informative: z.number().int().min(0).max(1) }),
  currentness,
  fields: z.array(z.object({ name: text, state: z.enum(["PRESENT", "MEASURED_ABSENCE_WITHIN_SCOPE", "NOT_MEASURED", "NON_INFORMATIVE"]), value: z.string().nullable() })).max(20),
  uncertainty: text, humanMeaning: text, scopeLimit: text,
  representationGap: z.object({ type: z.literal("INXIGHT_REPRESENTATION_GAP"), state: z.literal("MEASURED_ABSENCE_WITHIN_SCOPE"), expectedPhrase: text, measuredField: text, scope: text, cause: z.literal("UNKNOWN"), notEstablished: z.array(text),
    contextRecommendation: z.object({ state: z.literal("CONTEXT_REQUIRED"), condition: text,
      requiredContext: z.object({ pagePurpose: z.literal("UNKNOWN"), expectedPublicBrandName: z.literal("UNKNOWN") }),
      recommendedAction: text, actionMode: z.literal("HUMAN_REVIEW_ONLY"), performanceBenefit: z.literal("NOT_ESTABLISHED"),
    }).optional(),
  }).optional(),
  currentnessEvaluation: z.object({ previous: currentness, asOf: text, policyRef: text }).optional(),
});
export const digitalRepresentationSchema = z.union([
  pageMeasurementSchema,
  z.object({ state: z.literal("NOT_MEASURED"),
    reason: z.union([text, z.object({ code: text, explanation: text, detailCode: text.optional() })]),
    currentness: currentness.optional(), instrument: instrument.optional(),
    expectedInstrument: instrument.optional(), recordedMeasurement: pageMeasurementSchema.optional(),
    scopeLimit: text.optional(),
  }),
]);
export function safeSourceLink(ref: string): string | null {
  try {
    const uri = new URL(ref);
    if (
      uri.protocol !== "https:" ||
      uri.username ||
      uri.password ||
      uri.search ||
      uri.hash
    )
      return null;
    return uri.href;
  } catch {
    return null;
  }
}
const step = z.object({
  id: text,
  kind: text,
  label: text,
  sourceRef: z.string().nullable(),
  observedAt: z.string().nullable(),
  currentness: z.string().nullable(),
  artifactVerified: z.boolean().nullable(),
});
const cognitionSourceSchema = z.object({
  id: text,
  title: text,
  observedAt: text,
  currentness,
  currentnessEvaluatedAt: text,
  instrument: text,
  limitation: text,
  sourceRef: text,
  provenanceRef: text,
});
const cognitionSignalSchema = z.object({ id: text, familyId });
const opportunityFamily = z.enum([
  "PUBLIC_PROCUREMENT",
  "PUBLIC_INVESTMENT",
  "GRANTS_AND_SUBSIDIES",
  "PLANNING_AND_PERMITS",
  "PRIVATE_PROJECT_SIGNALS",
  "REGULATION_DRIVEN_DEMAND",
  "BUYER_EXPANSION_SIGNALS",
]);
const cognitionOpportunitySchema = z.object({
  id: text,
  familyId: z.enum(["value", "demand"]),
  opportunityFamily: opportunityFamily.optional(),
  title: text,
  buyer: text.nullable(),
  market: text,
  form: text,
  deadline: text.nullable(),
  epistemic: z.enum(["POTENTIAL", "UNKNOWN"]),
  capability: z.object({ label: text, excerpt: text, sourceId: text }),
  demand: z.object({ label: text, code: text.nullable(), sourceId: text }),
  known: z.array(z.object({ label: text, value: text })),
  unknown: z.array(text),
  matchBasis: z.array(text).optional(),
  whyPotential: text,
  whyLooked: z.array(text),
  // Economic relevance judgments the runtime already returns; read-only, dropped if malformed.
  relevance: z.object({
    relevantThrough: z.array(text).max(40),
    channels: z.array(z.object({
      judgments: z.array(z.object({ family: text, outcome: text, state: text })).max(40),
    })).max(40),
  }).partial().optional().catch(undefined),
  observedAt: text,
  currentness,
  currentnessEvaluatedAt: text,
});
// Spec 059 economic garden as persisted in the snapshot. Read-only presentation input:
// unknown fields are stripped and a missing garden simply renders nothing.
const gardenPlaceSchema = z.object({
  geography: text,
  label: z.string().min(1).nullable().optional(),
  mode: z.string().nullable(),
  stated: z.boolean(),
  current: z.boolean(),
  evidence: text,
  source: text.optional(),
  excerpt: text.optional(),
  observedAt: text.optional(),
});
const economicGardenSchema = z.object({
  operatingModelFingerprint: text,
  capabilities: z.array(z.object({
    capabilityId: text,
    label: text,
    deliveryModes: z.array(text),
    operating: z.array(gardenPlaceSchema),
    expansion: z.array(gardenPlaceSchema),
    excluded: z.array(gardenPlaceSchema),
    unknown: z.array(text),
  })).max(40),
  exposureChannels: z.array(text),
});
export const runtimeCognitionSchema = z.object({
  asOf: text,
  sources: z.array(cognitionSourceSchema),
  signals: z.array(cognitionSignalSchema),
  opportunities: z.array(cognitionOpportunitySchema),
  economicGarden: economicGardenSchema.optional().catch(undefined),
});
export type RuntimeEconomicGarden = z.infer<typeof economicGardenSchema>;
export const runtimeSignalSchema = z.object({
  id: text,
  nodeKind: z.literal("XIGNAL"),
  title: text,
  whyAttention: text,
  interpretation: text,
  uncertainty: text,
  epistemicState: z.enum(["OBSERVED", "POTENTIAL", "UNKNOWN"]),
  currentness: z.enum(["CURRENT", "STALE", "HISTORICAL", "UNKNOWN"]),
  observedAt: text,
  evidenceAccess: text,
  sourceRefs: z.array(text),
  observationSupportRefs: z.array(text),
  unknowns: z.array(text),
  evidenceNarrative: z.object({
    xignalId: text,
    focusStepId: text,
    steps: z.array(step),
  }),
});
export const runtimeProjectionSchema = z.object({
  realityLevel: text,
  runtimeCodeSha: text,
  lifecycleStatus: text,
  context: z.object({ id: text, label: text }),
  organization: z.object({ id: text, name: text }),
  nodes: z.array(runtimeSignalSchema),
  cognition: runtimeCognitionSchema.optional(),
  digitalRepresentation: digitalRepresentationSchema.optional(),
  temporalHistory: z.object({
    disposition: z.enum(["EMPTY", "SINGLE_OBSERVATION", "MULTIPLE_OBSERVATIONS"]),
    items: z.array(
      z.object({
        observationId: text,
        sourceRef: text,
        sourceType: text,
        observedAt: text,
        currentness: z.enum(["CURRENT", "STALE", "HISTORICAL", "UNKNOWN"]),
        normalizedStateChanged: z.boolean().nullable(),
      }),
    ),
  }),
  today: z.object({
    disposition: text,
    items: z.array(
      z.object({
        xignalId: text,
        whatChanged: text,
        whyItMatters: text,
        observedAt: text,
        showHowRef: text,
      }),
    ),
  }),
  reloadContinuity: z.literal("PERSISTED_RUNTIME_READ_MODEL"),
});
export type RuntimeProjection = z.infer<typeof runtimeProjectionSchema>;
export type RuntimeSignal = z.infer<typeof runtimeSignalSchema>;
export type RuntimeCognition = z.infer<typeof runtimeCognitionSchema>;
export type CustomerZeroState =
  | { state: "loading" | "planting" | "NO_XEED" }
  | {
      state: "INSUFFICIENT_EVIDENCE" | "rejected" | "failure" | "unauthorized";
      reason: string;
    }
  | { state: "success"; projection: RuntimeProjection };

export function readCustomerZeroResponse(
  payload: unknown,
  status: number,
): CustomerZeroState {
  const envelope = z
    .object({
      state: z.string().optional(),
      status: z.string().optional(),
      reason: z.string().optional(),
    })
    .safeParse(payload);
  if (status === 401)
    return { state: "unauthorized", reason: "ADMIN_SESSION_REQUIRED" };
  if (envelope.success && envelope.data.state === "INSUFFICIENT_EVIDENCE")
    return {
      state: "INSUFFICIENT_EVIDENCE",
      reason: envelope.data.reason ?? "SOURCE_NOT_EVALUABLE",
    };
  if (
    status === 403 ||
    (envelope.success &&
      (envelope.data.status === "rejected" ||
        envelope.data.state === "rejected"))
  )
    return {
      state: "rejected",
      reason: envelope.success
        ? (envelope.data.reason ?? "GOVERNED_REJECTION")
        : "GOVERNED_REJECTION",
    };
  if (
    status >= 200 &&
    status < 300 &&
    envelope.success &&
    envelope.data.state === "NO_XEED"
  )
    return { state: "NO_XEED" };
  const projection = runtimeProjectionSchema.safeParse(payload);
  if (status >= 200 && status < 300 && projection.success)
    return { state: "success", projection: projection.data };
  return {
    state: "failure",
    reason: envelope.success
      ? (envelope.data.reason ?? "INVALID_RUNTIME_RESPONSE")
      : "INVALID_RUNTIME_RESPONSE",
  };
}

export const customerZeroCommand = Object.freeze({
  label: "AXIGNAL self-observation",
  targetUri: "https://axignal.com/",
});
