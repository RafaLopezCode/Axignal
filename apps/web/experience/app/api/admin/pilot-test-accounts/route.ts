import { cookies } from "next/headers";
import { customerZeroCookie, resolveRuntimeOrigin, sameOrigin } from "@/lib/customer-zero-server";
import { pilotAccountsCommand, pilotAccountsSnapshot } from "@/lib/pilot-test-accounts";
import { AdminBodyLimitError, readAdminRequestJson, readAdminResponseJson } from "@/lib/admin-json";

const noStore = { "Cache-Control": "no-store" };
async function proxy(request: Request, write: boolean) {
  if (write && !sameOrigin(request))
    return Response.json({ reason: "ORIGIN_REQUIRED" }, { status: 403, headers: noStore });
  const token = (await cookies()).get(customerZeroCookie)?.value;
  if (!token)
    return Response.json({ reason: "ADMIN_SESSION_REQUIRED" }, { status: 401, headers: noStore });
  try {
    let body: string | undefined;
    if (write) {
      if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json")
        return Response.json({ reason: "JSON_REQUIRED" }, { status: 415, headers: noStore });
      const parsed = pilotAccountsCommand.safeParse(await readAdminRequestJson(request, 2048));
      if (!parsed.success)
        return Response.json({ reason: "INVALID_PILOT_ACCOUNTS" }, { status: 400, headers: noStore });
      body = JSON.stringify(parsed.data);
    }
    const configured = process.env.AXIGNAL_RUNTIME_ORIGIN;
    if (!configured) throw new Error("runtime unavailable");
    const response = await fetch(new URL("/internal/admin/pilot-test-accounts", resolveRuntimeOrigin(configured)), {
      method: write ? "POST" : "GET", cache: "no-store", redirect: "error",
      signal: AbortSignal.timeout(15_000),
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      ...(body ? { body } : {}),
    });
    if (!response.ok) {
      try { void response.body?.cancel().catch(() => {}); } catch { /* retain the known denial */ }
      return Response.json({ reason: response.status === 409 ? "REVISION_CONFLICT" : "PILOT_ACCOUNTS_REJECTED" }, { status: response.status, headers: noStore });
    }
    const result = pilotAccountsSnapshot.parse(await readAdminResponseJson(response));
    return Response.json(result, { headers: noStore });
  } catch (error) {
    if (error instanceof AdminBodyLimitError)
      return Response.json({ reason: "BODY_LIMIT" }, { status: 413, headers: noStore });
    return Response.json({ reason: error instanceof SyntaxError ? "INVALID_PILOT_ACCOUNTS" : "RUNTIME_UNAVAILABLE" }, { status: error instanceof SyntaxError ? 400 : 502, headers: noStore });
  }
}
export function GET(request: Request) { return proxy(request, false); }
export function POST(request: Request) { return proxy(request, true); }
