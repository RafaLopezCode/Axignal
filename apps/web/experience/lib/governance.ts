import { z } from "zod";
import {
  families,
  makeContext,
  organizations,
  project,
  snapshots,
  type ProjectionContext,
} from "./projection";
import { factsAt } from "./cognition/facts";
import { validateCognitivePlan } from "./cognition/compose";
const contextSchema = z
  .object({
    organizationId: z.string(),
    family: z.enum(families.map((f) => f.id)),
    signalId: z.string().nullable(),
    asOf: z.string(),
    revision: z.string().max(180),
  })
  .strict();
export function validateContext(input: unknown) {
  const result = contextSchema.safeParse(input);
  if (!result.success)
    return { success: false as const, error: "INVALID_CONTEXT" };
  const c = result.data;
  if (
    !organizations.some((o) => o.id === c.organizationId) ||
    !snapshots.some((s) => s.date === c.asOf) ||
    makeContext(c.organizationId, c.family, c.asOf, c.signalId).revision !==
      c.revision
  )
    return { success: false as const, error: "INVALID_SCOPE" };
  if (c.signalId && !project(c).signals.some((s) => s.id === c.signalId))
    return { success: false as const, error: "SIGNAL_OUTSIDE_SCOPE" };
  return { success: true as const, data: c };
}
const planSchema = z
  .object({
    version: z.literal(1),
    revision: z.string(),
    items: z
      .array(
        z
          .object({
            component: z.enum(["signal", "evidence", "context", "lens"]),
            ref: z.string().min(1),
            priority: z.enum(["primary", "supporting"]),
          })
          .strict(),
      )
      .min(1)
      .max(3),
  })
  .strict();
export type CompositionPlan = z.infer<typeof planSchema>;
/** A lens must be allowlisted, fit the family, have its data at this time and render its epistemic content. */
function lensAuthorized(ref: string, context: ProjectionContext) {
  return validateCognitivePlan(
    { version: 2, family: context.family, intent: "overview", items: [{ component: ref, layer: 1 }] },
    factsAt(context.organizationId, context.asOf),
  ).success;
}
export function validatePlan(input: unknown, context: ProjectionContext) {
  const parsed = planSchema.safeParse(input);
  if (!parsed.success || !validateContext(context).success)
    return { success: false as const, error: "INVALID_PLAN" };
  if (parsed.data.revision !== context.revision)
    return { success: false as const, error: "STALE_CONTEXT" };
  const p = project(context),
    seen = new Set<string>();
  for (const item of parsed.data.items) {
    const key = item.component + ":" + item.ref;
    if (seen.has(key))
      return { success: false as const, error: "DUPLICATE_REFERENCE" };
    seen.add(key);
    const authorized =
      item.component === "signal"
        ? p.signals.some((s) => s.id === item.ref)
        : item.component === "evidence"
          ? p.evidence.some((e) => e.id === item.ref)
          : item.component === "lens"
            ? lensAuthorized(item.ref, context)
            : item.ref === context.organizationId;
    if (!authorized)
      return { success: false as const, error: "REFERENCE_OUTSIDE_SCOPE" };
  }
  return { success: true as const, data: parsed.data };
}
export function denyAdminMutation() {
  return {
    status: 403,
    code: "AUTHORITY_REQUIRED",
    message:
      "An authorized privileged session and owning-service command are required.",
  };
}

/** Local demo boundary: Host reflects the public request; Next normalizes request.url to localhost. */
export function validateBrowserOrigin(
  origin: string | null,
  host: string | null,
) {
  if (!origin) return true;
  const allowed = new Set(["http://127.0.0.1:3810", "http://localhost:3810"]);
  return allowed.has(origin) && new URL(origin).host === host;
}
