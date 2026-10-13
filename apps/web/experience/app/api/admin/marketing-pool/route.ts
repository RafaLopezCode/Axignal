import { cookies } from "next/headers";
import { customerZeroCookie, resolveRuntimeOrigin, sameOrigin } from "@/lib/customer-zero-server";
import { poolCommand, poolSnapshot } from "@/lib/marketing-pool";

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
      const text = await request.text();
      if (text.length > 1024)
        return Response.json({ reason: "BODY_LIMIT" }, { status: 413, headers: noStore });
      const parsed = poolCommand.safeParse(JSON.parse(text));
      if (!parsed.success)
        return Response.json({ reason: "INVALID_MARKETING_POOL" }, { status: 400, headers: noStore });
      body = JSON.stringify(parsed.data);
    }
    const configured = process.env.AXIGNAL_RUNTIME_ORIGIN;
    if (!configured) throw new Error("runtime unavailable");
    const response = await fetch(new URL("/internal/admin/marketing-pool", resolveRuntimeOrigin(configured)), {
      method: write ? "POST" : "GET", cache: "no-store", redirect: "error",
      signal: AbortSignal.timeout(20_000),
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      ...(body ? { body } : {}),
    });
    if (!response.ok) {
      const raw = await response.json().catch(() => ({}));
      return Response.json({ reason: typeof raw?.reason === "string" ? raw.reason : "MARKETING_POOL_REJECTED" }, { status: response.status, headers: noStore });
    }
    return Response.json(poolSnapshot.parse(await response.json()), { headers: noStore });
  } catch (error) {
    return Response.json({ reason: error instanceof SyntaxError ? "INVALID_MARKETING_POOL" : "RUNTIME_UNAVAILABLE" }, { status: error instanceof SyntaxError ? 400 : 502, headers: noStore });
  }
}
export function GET(request: Request) { return proxy(request, false); }
export function POST(request: Request) { return proxy(request, true); }
