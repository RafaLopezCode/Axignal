import { cookies } from "next/headers";
import { customerZeroCookie, sameOrigin, resolveRuntimeOrigin } from "./customer-zero-server";
import { validateStaffStepUp } from "./staff-capacity-server";
import { customerCommands, customerAccess, issuedInvite, type CustomerAction } from "./customer-access";
export const customerStepUpCookie = "axignal-customer-stepup";
const reply = (body: unknown, status = 200) => Response.json(body, { status, headers: { "Cache-Control": "no-store", "Referrer-Policy": "no-referrer" } });
const safeReasons = new Set(["ADMIN_SESSION_REQUIRED", "STEP_UP_OR_SCOPE_REQUIRED", "ADMIN_SCOPE_REQUIRED", "PILOT_DISABLED", "CUSTOMER_ACCESS_UNAVAILABLE", "RATE_LIMITED", "INVITE_ALREADY_ISSUED", "IDEMPOTENCY_CONFLICT", "STATE_CONFLICT", "REFERENCE_NOT_FOUND", "INVALID_REQUEST", "BODY_LIMIT", "JSON_REQUIRED"]);
export async function customerAccessProxy(request: Request, action: CustomerAction | null): Promise<Response> {
  if (action && !sameOrigin(request)) return reply({ reason: "ORIGIN_REQUIRED" }, 403);
  const jar = await cookies(), primary = jar.get(customerZeroCookie)?.value;
  if (!primary) return reply({ reason: "ADMIN_SESSION_REQUIRED" }, 401);
  const elevated = action ? jar.get(customerStepUpCookie)?.value : undefined;
  if (action && !elevated) return reply({ reason: "STEP_UP_OR_SCOPE_REQUIRED" }, 403);
  try {
    if (elevated && !(await validateStaffStepUp(primary, elevated))) return reply({ reason: "STEP_UP_OR_SCOPE_REQUIRED" }, 403);
    let body: string | undefined;
    if (action) {
      if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json") return reply({ reason: "JSON_REQUIRED" }, 415);
      const reader = request.body?.getReader();
      if (!reader) return reply({ reason: "INVALID_REQUEST" }, 400);
      const chunks: Uint8Array[] = []; let size = 0;
      while (true) {
        const part = await reader.read(); if (part.done) break;
        size += part.value.byteLength;
        if (size > 4096) { await reader.cancel(); return reply({ reason: "BODY_LIMIT" }, 413); }
        chunks.push(part.value);
      }
      const parsed = customerCommands[action].safeParse(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      if (!parsed.success) return reply({ reason: "INVALID_REQUEST" }, 400);
      body = JSON.stringify(parsed.data);
    }
    const configured = process.env.AXIGNAL_RUNTIME_ORIGIN;
    if (!configured) throw new Error("unavailable");
    const response = await fetch(new URL("/internal/admin/customer-access" + (action ? "/" + action : ""), resolveRuntimeOrigin(configured)), {
      method: action ? "POST" : "GET", cache: "no-store", redirect: "error", signal: AbortSignal.timeout(15_000),
      headers: { Authorization: "Bearer " + (elevated ?? primary), "Content-Type": "application/json" }, ...(body ? { body } : {}),
    });
    const raw: unknown = await response.json();
    if (!response.ok) {
      const code = raw && typeof raw === "object" && "reason" in raw ? raw.reason : null;
      return reply({ reason: typeof code === "string" && safeReasons.has(code) ? code : "CUSTOMER_ACCESS_UNAVAILABLE" }, response.status);
    }
    if (!action) return reply(customerAccess.parse(raw));
    if (action === "issue") return reply(issuedInvite.parse(raw));
    if (!(raw && typeof raw === "object" && "revoked" in raw && raw.revoked === true)) throw new Error("invalid response");
    return reply({ revoked: true });
  } catch (error) {
    return reply({ reason: error instanceof SyntaxError ? "INVALID_REQUEST" : "CUSTOMER_ACCESS_UNAVAILABLE" }, error instanceof SyntaxError ? 400 : 502);
  }
}
