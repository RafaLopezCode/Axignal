import { cookies } from "next/headers";
import {
  customerZeroCommand,
  readCustomerZeroResponse,
} from "./runtime-projection";

export const customerZeroCookie = "axignal-admin-session";
const noStore = { "Cache-Control": "no-store" };
export function sameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  const allowed = process.env.AXIGNAL_EXPERIENCE_ORIGIN
    ? [process.env.AXIGNAL_EXPERIENCE_ORIGIN]
    : ["http://127.0.0.1:3810", "http://localhost:3810"];
  return (
    !!origin &&
    allowed.includes(origin) &&
    new URL(origin).host === request.headers.get("host")
  );
}
export function resolveRuntimeOrigin(
  configured: string,
  containerized = process.env.AXIGNAL_CONTAINERIZED === "true",
): URL {
  const origin = new URL(configured);
  const loopback = ["127.0.0.1", "localhost", "[::1]"].includes(
    origin.hostname,
  );
  const composeRuntime =
    containerized &&
    origin.protocol === "http:" &&
    origin.hostname === "runtime" &&
    origin.port === "18181";
  if (
    origin.protocol !== "http:" ||
    (!loopback && !composeRuntime) ||
    origin.username ||
    origin.password ||
    origin.search ||
    origin.hash ||
    origin.pathname !== "/"
  )
    throw new Error("RUNTIME_ORIGIN_REJECTED");
  return origin;
}
export async function runtimeRequest(
  path: string,
  token: string,
  write = false,
) {
  const configured = process.env.AXIGNAL_RUNTIME_ORIGIN;
  if (!configured) throw new Error("RUNTIME_NOT_CONFIGURED");
  const origin = resolveRuntimeOrigin(configured);
  return fetch(new URL(path, origin), {
    method: write ? "POST" : "GET",
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(write ? 120_000 : 15_000),
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    ...(write ? { body: JSON.stringify(customerZeroCommand) } : {}),
  });
}
export async function customerZeroProxy(request: Request, write = false) {
  if (write && !sameOrigin(request))
    return Response.json(
      { status: "rejected", reason: "ORIGIN_REQUIRED" },
      { status: 403, headers: noStore },
    );
  const token = (await cookies()).get(customerZeroCookie)?.value;
  if (!token)
    return Response.json(
      { status: "rejected", reason: "ADMIN_SESSION_REQUIRED" },
      { status: 401, headers: noStore },
    );
  try {
    const access = await runtimeRequest(
      "/internal/admin/customer-zero/access",
      token,
    );
    if (!access.ok)
      return Response.json(
        { status: "rejected", reason: "ADMIN_AUTHORITY_UNAVAILABLE" },
        { status: access.status, headers: noStore },
      );
    const grant: unknown = await access.json();
    if (
      write &&
      !(
        typeof grant === "object" &&
        grant !== null &&
        "canObserve" in grant &&
        grant.canObserve === true
      )
    )
      return Response.json(
        { status: "rejected", reason: "ADMIN_SCOPE_REQUIRED" },
        { status: 403, headers: noStore },
      );
    const response = await runtimeRequest(
      write ? "/api/xeeds" : "/api/subscriber-context",
      token,
      write,
    );
    const result = readCustomerZeroResponse(
      await response.json(),
      response.status,
    );
    return Response.json(
      result.state === "success" ? result.projection : result,
      { status: response.status, headers: noStore },
    );
  } catch {
    return Response.json(
      { state: "failure", reason: "RUNTIME_UNAVAILABLE" },
      { status: 502, headers: noStore },
    );
  }
}
