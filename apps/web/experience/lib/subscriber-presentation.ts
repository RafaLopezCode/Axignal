import type { UIMessage } from "ai";
import { z } from "zod";
import type { RuntimeProjection } from "./runtime-projection";
import { composeFamily, validateCognitivePlan, type CognitivePlan } from "./cognition/compose";
import { runtimeFactsAt } from "./cognition/runtime-facts";

export const cognitiveReadingRequestSchema = z.object({
  family: z.enum(["presence", "reputation", "value", "markets", "relationships", "demand", "activity", "economics", "context", "organization"]),
  asOf: z.iso.datetime({ offset: true }),
  intent: z.enum(["overview", "why", "how_known", "change", "coverage"]),
  device: z.enum(["desktop", "mobile"]),
}).strict();
export type CognitiveReadingRequest = z.infer<typeof cognitiveReadingRequestSchema>;

export const readingRequestSchema = z.object({
  focusId: z.string().regex(/^[A-Za-z0-9:_-]{1,160}$/),
  revision: z.string().regex(/^[a-f0-9]{64}$/),
  intent: z.enum(["summary", "evidence", "limits"]),
  locale: z.enum(["es", "en", "de", "pt", "fr", "it"]),
  cognition: cognitiveReadingRequestSchema.optional(),
  id: z.string().max(160).optional(), trigger: z.string().max(80).optional(),
  messageId: z.string().max(160).optional(),
  messages: z.array(z.object({ id: z.string().max(160), role: z.enum(["user", "assistant"]),
    parts: z.array(z.object({ type: z.literal("text"), text: z.string().max(1000) }).strict()).max(4),
  }).strict()).max(1).optional(),
}).strict();
export const readingPlanSchema = z.object({
  version: z.literal(1), revision: z.string().regex(/^[a-f0-9]{64}$/),
  intent: z.enum(["summary", "evidence", "limits"]),
  refs: z.array(z.string().max(160)).max(100),
  method: z.literal("DETERMINISTIC_EVIDENCE_PRESENTATION"),
  cognition: z.object({ request: cognitiveReadingRequestSchema, plan: z.custom<CognitivePlan>() }).strict().optional(),
}).strict();
export type ReadingPlan = z.infer<typeof readingPlanSchema>;
export type SubscriberReadingMessage = UIMessage<{ revision: string }, { presentation: ReadingPlan }>;
export function acceptsReadingPlan(plan: unknown, projection: RuntimeProjection, revision: string): plan is ReadingPlan {
  const parsed = readingPlanSchema.safeParse(plan);
  if (!parsed.success || parsed.data.revision !== revision) return false;
  const allowed = new Set(projection.nodes.map(item => item.id));
  if (new Set(parsed.data.refs).size !== parsed.data.refs.length || !parsed.data.refs.every(ref => allowed.has(ref))) return false;
  if (!parsed.data.cognition) return true;
  try {
    const expected = cognitiveReadingPlan(projection, parsed.data.cognition.request);
    return expected !== null && JSON.stringify(expected) === JSON.stringify(parsed.data.cognition.plan);
  } catch { return false; }
}

export function cognitiveReadingPlan(projection: RuntimeProjection, input: CognitiveReadingRequest): CognitivePlan | null {
  if (!projection.cognition || Date.parse(input.asOf) > Date.parse(projection.cognition.asOf)) throw new Error("COLD_OR_FUTURE_READING");
  const facts = runtimeFactsAt(projection, input.family, input.asOf);
  const plan = composeFamily({ family: input.family, intent: input.intent, device: input.device, facts });
  return validateCognitivePlan(plan, facts).success ? plan : null;
}
