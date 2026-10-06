import { z } from "zod";
import { boundedSubscriberJson, subscriberAxent, subscriberProxy, subscriberSameOrigin } from "@/lib/subscriber-server";
import { subscriberOutputSchema } from "@/lib/subscriber-contracts";
import { cognitiveReadingPlan, cognitiveReadingRequestSchema } from "@/lib/subscriber-presentation";
import { explainRuntime } from "@/lib/runtime-axent";
import { runtimeFactsAt } from "@/lib/cognition/runtime-facts";

export const runtime = "nodejs";
const inputSchema = z.object({
  prompt: z.string().trim().min(1).max(1000),
  contextId: z.string().regex(/^[A-Za-z0-9:_-]{1,160}$/),
  revision: z.string().regex(/^[a-f0-9]{64}$/),
  signalId: z.string().min(1).max(200).optional(),
  locale: z.enum(["es", "en", "de", "pt", "fr", "it"]),
  cognition: cognitiveReadingRequestSchema.optional(),
  // Compact, non-authoritative memory of the previous turn; never a transcript.
  memory: z.object({}).passthrough().optional(),
}).strict();

export async function POST(request: Request) {
  const headers = { "Cache-Control": "no-store" };
  if (!subscriberSameOrigin(request)) return Response.json({ error: "ORIGIN_MISMATCH" }, { status: 403, headers });
  let input;
  try { input = inputSchema.parse(await boundedSubscriberJson(request, 8192)); }
  catch { return Response.json({ error: "INVALID_QUESTION" }, { status: 400, headers }); }
  const fresh = await subscriberProxy(request, `/subscriber/organizations/${encodeURIComponent(input.contextId)}/output`);
  if (!fresh.ok) return fresh;
  const output = subscriberOutputSchema.parse(await fresh.json());
  if (output.revision !== input.revision) return Response.json({ error: "READING_CHANGED" }, { status: 409, headers });
  try {
    const cut = input.cognition?.asOf ?? output.projection.cognition?.asOf;
    const projection = cut ? {
      ...output.projection,
      nodes: output.projection.nodes.filter(node => Date.parse(node.observedAt) <= Date.parse(cut)),
      today: { ...output.projection.today, items: output.projection.today.items.filter(item => Date.parse(item.observedAt) <= Date.parse(cut)) },
    } : output.projection;
    // Grounded AXENT (authorized retrieval, verified claims) when the runtime serves it;
    // otherwise the deterministic explanation of the same authorized reading.
    // Off unless this environment enables it (staged rollout, like the reasoner behind it).
    const grounded = process.env.AXIGNAL_AXENT_GROUNDED === "true"
      ? await subscriberAxent(request, input.contextId, {
          question: input.prompt, locale: input.locale, ...(input.memory ? { memory: input.memory } : {}),
        })
      : null;
    const answer = grounded ? (grounded as unknown as ReturnType<typeof explainRuntime>) : explainRuntime(projection, input.prompt, input.signalId, input.locale);
    const plan = input.cognition ? cognitiveReadingPlan(output.projection, input.cognition) : null;
    if (input.cognition) {
      const facts = runtimeFactsAt(output.projection, input.cognition.family, input.cognition.asOf);
      const unique = (values: string[]) => [...new Set(values)];
      answer.sourceRefs = unique([...answer.sourceRefs, ...facts.sources.map(source => source.sourceRef)]);
      answer.observedAt = unique([...answer.observedAt, ...facts.sources.map(source => source.observedAt)]);
      answer.currentness = unique([...answer.currentness, ...facts.sources.map(source => source.currentness)]);
    }
    return Response.json({ ...answer, revision: output.revision,
      ...(plan && input.cognition ? { cognition: { request: input.cognition, plan } } : {}),
    }, { headers });
  } catch { return Response.json({ error: "FOCUS_OUTSIDE_READING" }, { status: 409, headers }); }
}
