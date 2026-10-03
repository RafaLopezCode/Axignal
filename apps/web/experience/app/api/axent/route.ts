import { createUIMessageStream, createUIMessageStreamResponse } from "ai";
import { z } from "zod";
import {
  validateContext,
  validatePlan,
  validateBrowserOrigin,
  type CompositionPlan,
} from "@/lib/governance";
import { project } from "@/lib/projection";
import type { AxentMessage } from "@/lib/axent-contract";

const requestSchema = z
  .object({
    context: z.unknown(),
    locale: z.enum(["es", "en"]).default("es"),
    messages: z
      .array(
        z
          .object({
            role: z.enum(["user", "assistant"]),
            parts: z.array(z.unknown()).max(50),
          })
          .passthrough(),
      )
      .min(1)
      .max(30),
  })
  .passthrough();
async function boundedBody(request: Request) {
  const reader = request.body?.getReader();
  if (!reader) throw new Error("EMPTY_BODY");
  let size = 0;
  const chunks: Uint8Array[] = [];
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > 32768) {
      await reader.cancel();
      throw new Error("BODY_LIMIT");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}
export async function POST(request: Request) {
  if (
    !validateBrowserOrigin(
      request.headers.get("origin"),
      request.headers.get("host"),
    )
  )
    return Response.json({ error: "ORIGIN_MISMATCH" }, { status: 403 });
  let input: unknown;
  try {
    input = await boundedBody(request);
  } catch {
    return Response.json(
      { error: "INVALID_OR_OVERSIZED_BODY" },
      { status: 400 },
    );
  }
  const parsed = requestSchema.safeParse(input);
  if (!parsed.success)
    return Response.json({ error: "INVALID_REQUEST" }, { status: 400 });
  const validated = validateContext(parsed.data.context);
  if (!validated.success)
    return Response.json({ error: validated.error }, { status: 400 });
  const context = validated.data,
    p = project(context),
    locale = parsed.data.locale;
  const user = parsed.data.messages.findLast((m) => m.role === "user");
  const prompt =
    user?.parts
      .filter(
        (v): v is { type: "text"; text: string } =>
          typeof v === "object" &&
          v !== null &&
          "type" in v &&
          v.type === "text" &&
          "text" in v &&
          typeof v.text === "string",
      )
      .map((v) => v.text)
      .join(" ")
      .slice(0, 1000) ?? "";
  const signal =
    p.signals.find((s) => s.id === context.signalId) ??
    p.signals.find((s) => s.family === context.family);
  const sourceIntent = /evidenc|fuente|source|basis|base|sostiene/i.test(
      prompt,
    ),
    reasonIntent =
      /por qué|why|razon|reason|encaj|fit|limit|abierto|open/i.test(prompt);
  const supported =
    sourceIntent ||
    reasonIntent ||
    /context|contexto|cambi|change|señal|signal|explic|explain|panorama|comprend|understand|investig/i.test(
      prompt,
    );
  const items: CompositionPlan["items"] = signal
    ? [{ component: "signal", ref: signal.id, priority: "primary" }]
    : [
        {
          component: "context",
          ref: context.organizationId,
          priority: "primary",
        },
      ];
  if (sourceIntent && signal?.evidenceIds[0])
    items.push({
      component: "evidence",
      ref: signal.evidenceIds[0],
      priority: "supporting",
    });
  const plan = { version: 1 as const, revision: context.revision, items };
  const planResult = validatePlan(plan, context);
  if (!planResult.success)
    return Response.json({ error: "COMPOSITION_REJECTED" }, { status: 422 });
  const prefix =
    locale === "es"
      ? "Esta es una explicación ilustrativa, sin investigación en vivo. "
      : "This is an illustrative explanation, without live research. ";
  const answer = !supported
    ? locale === "es"
      ? "En esta demo puedo explicar el contexto seleccionado, sus límites y su evidencia. Para una investigación nueva haría falta un proveedor y herramientas autorizados."
      : "In this demo I can explain the selected context, its limits and evidence. New research would require an authorized provider and tools."
    : signal
      ? sourceIntent
        ? [signal.derivation[locale], signal.limitation[locale]].join("\n\n")
        : reasonIntent
          ? [signal.why[locale], signal.limitation[locale]].join("\n\n")
          : [signal.summary[locale], signal.next[locale]].join("\n\n")
      : locale === "es"
        ? "No hay una señal sustentada en este corte. La ausencia de conocimiento no permite concluir que algo no existe."
        : "There is no supported signal at this time. Absence of knowledge does not allow us to conclude that something does not exist.";
  const stream = createUIMessageStream<AxentMessage>({
    execute: ({ writer }) => {
      writer.write({
        type: "start",
        messageMetadata: { revision: context.revision },
      });
      writer.write({ type: "text-start", id: "explanation" });
      writer.write({
        type: "text-delta",
        id: "explanation",
        delta: prefix + answer,
      });
      writer.write({ type: "text-end", id: "explanation" });
      writer.write({
        type: "tool-input-available",
        toolCallId: "compose-context",
        toolName: "compose",
        input: { intent: sourceIntent ? "evidence" : "understand" },
      });
      writer.write({
        type: "tool-output-available",
        toolCallId: "compose-context",
        output: planResult.data,
      });
      writer.write({ type: "finish", finishReason: "stop" });
    },
    onError: () =>
      locale === "es"
        ? "La explicación no está disponible. Puedes volver a intentarlo."
        : "The explanation is unavailable. You can try again.",
  });
  return createUIMessageStreamResponse({
    stream,
    headers: { "Cache-Control": "no-store" },
  });
}
