import { createUIMessageStream, createUIMessageStreamResponse } from "ai";
import { boundedSubscriberJson, subscriberProxy, subscriberSameOrigin } from "@/lib/subscriber-server";
import { subscriberOutputSchema } from "@/lib/subscriber-contracts";
import { acceptsReadingPlan, cognitiveReadingPlan, readingRequestSchema, type ReadingPlan, type SubscriberReadingMessage } from "@/lib/subscriber-presentation";
import { translate } from "@/lib/copy-catalog";
import { presentSignal, presentRuntimeText } from "@/lib/runtime-presentation";
export const runtime = "nodejs";
export async function POST(request: Request) {
  const headers = { "Cache-Control": "no-store" };
  if (!subscriberSameOrigin(request)) return Response.json({ code: "ORIGIN_REQUIRED" }, { status: 403, headers });
  let input;
  try { input = readingRequestSchema.parse(await boundedSubscriberJson(request, 8192)); }
  catch { return Response.json({ code: "INVALID_READING_REQUEST" }, { status: 400, headers }); }
  const fresh = await subscriberProxy(request, `/subscriber/organizations/${encodeURIComponent(input.focusId)}/output`);
  if (!fresh.ok) return fresh;
  const output = subscriberOutputSchema.parse(await fresh.json());
  if (output.revision !== input.revision) return Response.json({ code: "READING_CHANGED" }, { status: 409, headers });
  const plan: ReadingPlan = { version: 1, revision: input.revision, intent: input.intent,
    refs: output.projection.nodes.map(item => item.id), method: "DETERMINISTIC_EVIDENCE_PRESENTATION" };
  if (input.cognition) {
    try {
      const composed = cognitiveReadingPlan(output.projection, input.cognition);
      if (composed) plan.cognition = { request: input.cognition, plan: composed };
    } catch { return Response.json({ code: "INVALID_COGNITIVE_CUT" }, { status: 422, headers }); }
  }
  if (!acceptsReadingPlan(plan, output.projection, input.revision)) return Response.json({ code: "PRESENTATION_REJECTED" }, { status: 422, headers });
  const t = (es: string, en: string) => translate(es, en, input.locale);
  const explanation = !plan.refs.length ? t("Todavía no hay evidencia suficiente para una conclusión. Una ausencia en esta lectura no demuestra ausencia en el mundo.", "Evidence is not yet sufficient for a conclusion. Absence in this reading does not prove absence in the world.")
    : input.intent === "evidence" ? t("De la señal a la fuente, sin ocultar lo que sigue abierto.", "From signal to source, without hiding what remains open.")
    : input.intent === "limits" ? output.projection.nodes.map(item => presentRuntimeText(item.uncertainty, output.projection.organization.name, input.locale)).join("\n\n")
    : output.projection.nodes.map(item => presentSignal(item, output.projection.organization.name, input.locale).interpretation).join("\n\n");
  return createUIMessageStreamResponse({ headers, stream: createUIMessageStream<SubscriberReadingMessage>({
    execute: ({ writer }) => {
      writer.write({ type: "start", messageMetadata: { revision: input.revision } });
      writer.write({ type: "text-start", id: "reading" });
      writer.write({ type: "text-delta", id: "reading", delta: explanation });
      writer.write({ type: "text-end", id: "reading" });
      writer.write({ type: "data-presentation", data: plan });
      writer.write({ type: "finish", finishReason: "stop" });
    }, onError: () => "READING_UNAVAILABLE",
  }) });
}
