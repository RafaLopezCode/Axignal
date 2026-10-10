import { cookies } from "next/headers";
import { customerZeroCookie, resolveRuntimeOrigin, sameOrigin } from "@/lib/customer-zero-server";
import { staffActions, staffCommands, staffReason, staffResults, staffState, tenantId, type StaffAction } from "@/lib/staff-capacity";

const noStore = { "Cache-Control": "no-store" };
export const staffStepUpCookie = "axignal-admin-stepup";
const route = "/internal/admin/staff-capacity";

export async function validateStaffStepUp(primary: string, elevated: string): Promise<boolean> {
  const origin = process.env.AXIGNAL_RUNTIME_ORIGIN;
  if (!origin) return false;
  const response = await fetch(new URL("/internal/admin/step-up/verify", resolveRuntimeOrigin(origin)), {
    method: "GET", cache: "no-store", redirect: "error", signal: AbortSignal.timeout(15_000),
    headers: { Authorization: `Bearer ${primary}`, "X-Axignal-Step-Up": `Bearer ${elevated}` },
  });
  return response.ok;
}
const reply = (body: unknown, status = 200) => Response.json(body, { status, headers: noStore });

async function readJson(request: Request): Promise<unknown | Response> {
  if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json")
    return reply({ reason: "JSON_REQUIRED" }, 415);
  const reader = request.body?.getReader();
  if (!reader) throw new SyntaxError("empty body");
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const part = await reader.read();
    if (part.done) break;
    size += part.value.byteLength;
    if (size > 4096) { await reader.cancel(); return reply({ reason: "BODY_LIMIT" }, 413); }
    chunks.push(part.value);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

/** Admin-only proxy: the httpOnly Admin cookie becomes the bearer; nothing is cached or logged. */
export async function staffCapacityProxy(request: Request, action: StaffAction | null): Promise<Response> {
  if (action !== null && !sameOrigin(request)) return reply({ reason: "ORIGIN_REQUIRED" }, 403);
  const jar = await cookies();
  const primary = jar.get(customerZeroCookie)?.value;
  if (!primary) return reply({ reason: "ADMIN_SESSION_REQUIRED" }, 401);
  const elevated = action === null ? null : jar.get(staffStepUpCookie)?.value;
  if (action !== null && !elevated) return reply({ reason: "STEP_UP_REQUIRED" }, 403);
  const token = elevated ?? primary;
  try {
    // Each sensitive write binds the independent proof to the live PRIMARY actor.
    if (elevated && !(await validateStaffStepUp(primary, elevated)))
      return reply({ reason: "STEP_UP_REQUIRED" }, 403);
    let path = route;
    let body: string | undefined;
    if (action === null) {
      const tenant = tenantId.safeParse(new URL(request.url).searchParams.get("tenantId"));
      if (!tenant.success) return reply({ reason: "INVALID_REQUEST" }, 400);
      path = `${route}?tenantId=${encodeURIComponent(tenant.data)}`;
    } else {
      const raw = await readJson(request);
      if (raw instanceof Response) return raw;
      const parsed = staffCommands[action].safeParse(raw);
      if (!parsed.success) return reply({ reason: "INVALID_REQUEST" }, 400);
      path = `${route}/${action}`;
      body = JSON.stringify(parsed.data);
    }
    const configured = process.env.AXIGNAL_RUNTIME_ORIGIN;
    if (!configured) throw new Error("runtime unavailable");
    const response = await fetch(new URL(path, resolveRuntimeOrigin(configured)), {
      method: action === null ? "GET" : "POST", cache: "no-store", redirect: "error",
      signal: AbortSignal.timeout(15_000),
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      ...(body ? { body } : {}),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const reason = payload && typeof payload === "object" && "reason" in payload ? payload.reason : null;
      return reply({ reason: staffReason(reason) }, response.status);
    }
    return reply(action === null ? staffState.parse(payload) : staffResults[action].parse(payload));
  } catch (error) {
    return error instanceof SyntaxError
      ? reply({ reason: "INVALID_REQUEST" }, 400)
      : reply({ reason: "RUNTIME_UNAVAILABLE" }, 502);
  }
}

export function staffAction(value: string): StaffAction | null {
  return (staffActions as readonly string[]).includes(value) ? (value as StaffAction) : null;
}
