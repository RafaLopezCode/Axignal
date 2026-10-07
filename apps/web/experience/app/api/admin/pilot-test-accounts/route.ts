import { cookies } from "next/headers";
import { customerZeroCookie, resolveRuntimeOrigin, sameOrigin } from "@/lib/customer-zero-server";
import { pilotAccountsCommand, pilotAccountsSnapshot } from "@/lib/pilot-test-accounts";

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
      const reader = request.body?.getReader();
      if (!reader) throw new SyntaxError("empty body");
      const chunks: Uint8Array[] = [];
      let size = 0;
      while (true) {
        const part = await reader.read();
        if (part.done) break;
        size += part.value.byteLength;
        if (size > 2048) {
          await reader.cancel();
          return Response.json({ reason: "BODY_LIMIT" }, { status: 413, headers: noStore });
        }
        chunks.push(part.value);
      }
      const parsed = pilotAccountsCommand.safeParse(JSON.parse(Buffer.concat(chunks).toString("utf8")));
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
    if (!response.ok)
      return Response.json({ reason: response.status === 409 ? "REVISION_CONFLICT" : "PILOT_ACCOUNTS_REJECTED" }, { status: response.status, headers: noStore });
    const result = pilotAccountsSnapshot.parse(await response.json());
    return Response.json(result, { headers: noStore });
  } catch (error) {
    return Response.json({ reason: error instanceof SyntaxError ? "INVALID_PILOT_ACCOUNTS" : "RUNTIME_UNAVAILABLE" }, { status: error instanceof SyntaxError ? 400 : 502, headers: noStore });
  }
}
export function GET(request: Request) { return proxy(request, false); }
export function POST(request: Request) { return proxy(request, true); }
