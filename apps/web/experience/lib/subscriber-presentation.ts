import type { UIMessage } from "ai";
import { z } from "zod";
import type { RuntimeProjection } from "./runtime-projection";

export const readingRequestSchema = z.object({
  focusId: z.string().regex(/^[A-Za-z0-9:_-]{1,160}$/),
  revision: z.string().regex(/^[a-f0-9]{64}$/),
  intent: z.enum(["summary", "evidence", "limits"]),
  locale: z.enum(["es", "en", "de", "pt", "fr", "it"]),
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
}).strict();
export type ReadingPlan = z.infer<typeof readingPlanSchema>;
export type SubscriberReadingMessage = UIMessage<{ revision: string }, { presentation: ReadingPlan }>;
export function acceptsReadingPlan(plan: unknown, projection: RuntimeProjection, revision: string): plan is ReadingPlan {
  const parsed = readingPlanSchema.safeParse(plan);
  if (!parsed.success || parsed.data.revision !== revision) return false;
  const allowed = new Set(projection.nodes.map(item => item.id));
  return new Set(parsed.data.refs).size === parsed.data.refs.length && parsed.data.refs.every(ref => allowed.has(ref));
}
