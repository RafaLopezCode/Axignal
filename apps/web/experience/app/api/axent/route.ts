import { createUIMessageStream, createUIMessageStreamResponse } from "ai";
import { z } from "zod";
import {
  validateContext,
  validatePlan,
  validateBrowserOrigin,
  type CompositionPlan,
} from "@/lib/governance";
import { project } from "@/lib/projection";
import { translate } from "@/lib/copy-catalog";
import type { AxentMessage } from "@/lib/axent-contract";
import { customerZeroProxy, sameOrigin } from "@/lib/customer-zero-server";
import { readCustomerZeroResponse } from "@/lib/runtime-projection";
import { explainRuntime } from "@/lib/runtime-axent";
import { factsAt } from "@/lib/cognition/facts";
import { composeFamily } from "@/lib/cognition/compose";
import type { Intent } from "@/lib/cognition/registry";
import { familiesForText, familyTerms, fold } from "@/lib/family-vocabulary";
import { families } from "@/lib/projection";
import { funnelLayers } from "@/lib/funnel";
import { locales } from "@/lib/languages";

const requestSchema = z
  .object({
    context: z.unknown(),
    locale: z.enum(["es", "en", "de", "pt", "fr", "it"]).default("es"),
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
    !sameOrigin(request) && !validateBrowserOrigin(
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
  // The real product branch never reads browser-supplied economic data or the
  // illustrative project(). AO-01 authorizes a fresh runtime read per question.
  if (
    typeof input === "object" &&
    input !== null &&
    "mode" in input &&
    input.mode === "runtime"
  ) {
    if (!sameOrigin(request)) return Response.json({error:"ORIGIN_MISMATCH"},{status:403});
    const question = z
      .object({
        mode: z.literal("runtime"),
        prompt: z.string().trim().min(1).max(1000),
         signalId: z.string().max(200).optional(),
         contextId: z.string().max(200).optional(),
         locale: z.enum(["es", "en", "de", "pt", "fr", "it"]).default("es"),
      })
      .strict()
      .safeParse(input);
    if (!question.success)
      return Response.json(
        { error: "INVALID_RUNTIME_QUESTION" },
        { status: 400 },
      );
    const response = await customerZeroProxy(request);
    const result = readCustomerZeroResponse(
      await response.json(),
      response.status,
    );
      if (result.state !== "success")
      return Response.json(
        { error: "AUTHORIZED_PROJECTION_UNAVAILABLE" },
        {
          status: response.ok ? 409 : response.status,
          headers: { "Cache-Control": "no-store" },
        },
      );
      if (question.data.contextId && question.data.contextId !== result.projection.context.id)
        return Response.json({error:"CONTEXT_CHANGED"},{status:409,headers:{"Cache-Control":"no-store"}});
    try {
      return Response.json(
        explainRuntime(
          result.projection,
          question.data.prompt,
          question.data.signalId,
          question.data.locale,
        ),
        { headers: { "Cache-Control": "no-store" } },
      );
    } catch {
      return Response.json(
        { error: "FOCUS_OUTSIDE_PROJECTION" },
        { status: 409 },
      );
    }
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
  const t = (es: string, en: string) => translate(es, en, locale);
  const copy = (value: { es: string; en: string }) => t(value.es, value.en);
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
  const howKnown = funnelLayers[3].question;
  const sourceIntent =
      /evidenc|fuente|source|basis|base|sostiene|beleg|quelle|fonte|preuve/i.test(prompt) ||
      locales.some(({ id }) =>
        fold(prompt).includes(fold(translate(howKnown.es, howKnown.en, id)).replace(/[¿?]/g, "").trim()),
      ),
    reasonIntent =
      /por qué|why|razon|reason|encaj|fit|limit|abierto|open|warum|porquê|pourquoi|perché|grenze/i.test(
        prompt,
      );
  const supported =
    sourceIntent ||
    reasonIntent ||
    /context|contexto|cambi|change|señal|signal|explic|explain|panorama|comprend|understand|investig|kontext|erklär|versteh|sinal|spieg|segnal|compreend/i.test(
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
  // A reason is only readable next to its basis: "why" also composes the evidence.
  if ((sourceIntent || reasonIntent) && signal?.evidenceIds[0])
    items.push({
      component: "evidence",
      ref: signal.evidenceIds[0],
      priority: "supporting",
    });
  // The family decides how this knowledge is best explained; the composer picks
  // allowlisted lenses for the question, and validatePlan re-checks every one.
  const changeIntent = /cambi|change|evoluci|evolution|cuándo|when|wann|quand|quando/i.test(prompt);
  const intent: Intent = sourceIntent
    ? "how_known"
    : reasonIntent
      ? "why"
      : changeIntent
        ? "change"
        : "overview";
  if (supported) {
    const lenses = composeFamily({
      family: context.family,
      intent,
      facts: factsAt(context.organizationId, context.asOf),
      device: "desktop",
    }).items.filter((item) => item.layer <= 2 || intent === "how_known");
    for (const lens of lenses.slice(0, Math.max(0, 3 - items.length)))
      items.push({ component: "lens", ref: lens.component, priority: "supporting" });
  }
  // Everyday words ("SEO", "reseñas", "clientes") point to their canonical family. When
  // that is not the family in view, Axent shows where the answer lives instead of guessing.
  // "What changed?" asks about the family in view; it is not a request to open Activity.
  const asked = familiesForText(prompt).find((id) => !(id === "activity" && changeIntent));
  const elsewhere = asked && asked !== context.family ? families.find((f) => f.id === asked) : undefined;
  if (elsewhere) items.splice(0, items.length, { component: "family", ref: elsewhere.id, priority: "primary" });
  const plan = { version: 1 as const, revision: context.revision, items };
  const planResult = validatePlan(plan, context);
  if (!planResult.success)
    return Response.json({ error: "COMPOSITION_REJECTED" }, { status: 422 });
  const prefix = t(
    "Esta es una explicación ilustrativa, sin investigación en vivo. ",
    "This is an illustrative explanation, without live research. ",
  );
  const stillUnknown = t("Todavía no sabemos: ", "Still unknown: ");
  const answer = elsewhere
    ? t("Eso está en", "That is in") + " " + copy(elsewhere.name) + " (" + familyTerms(elsewhere.id, locale).join(" · ") + "). " +
      t("Ábrela para ver lo observado y lo que aún no se sabe.", "Open it to see what has been observed and what is still unknown.")
    : !supported
    ? t(
        "En este ejemplo puedo explicar el contexto seleccionado, sus límites y su evidencia, pero no investigar algo nuevo.",
        "In this example I can explain the selected context, its limits and evidence, but not research something new.",
      )
    : signal
      ? sourceIntent
        ? [copy(signal.derivation), stillUnknown + copy(signal.limitation)].join("\n\n")
        : reasonIntent
          ? [copy(signal.why), stillUnknown + copy(signal.limitation)].join("\n\n")
          : [copy(signal.summary), copy(signal.next)].join("\n\n")
      : t(
          "No hay una señal sustentada en este corte. La ausencia de conocimiento no permite concluir que algo no existe.",
          "There is no supported signal at this time. Absence of knowledge does not allow us to conclude that something does not exist.",
        );
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
      t(
        "La explicación no está disponible. Puedes volver a intentarlo.",
        "The explanation is unavailable. You can try again.",
      ),
  });
  return createUIMessageStreamResponse({
    stream,
    headers: { "Cache-Control": "no-store" },
  });
}
