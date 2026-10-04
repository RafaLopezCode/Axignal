import { cookies } from "next/headers";
import { attentionCommandSchema, organizationInventorySchema } from "./organization-attention";
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
  body: Record<string,string> = customerZeroCommand,
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
    ...(write ? { body: JSON.stringify(body) } : {}),
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
    let command: Record<string,string> = customerZeroCommand;
    if(write){
      const raw = await request.text();
      if(new TextEncoder().encode(raw).length>8192) return Response.json({status:"rejected",reason:"BODY_LIMIT"},{status:413,headers:noStore});
      let body:unknown;
      try {body=JSON.parse(raw);} catch {return Response.json({status:"rejected",reason:"INVALID_JSON"},{status:400,headers:noStore});}
      const parsed=attentionCommandSchema.safeParse(body);
      if(parsed.success) command=parsed.data;
      else if(!(typeof body === "object" && body !== null && Object.keys(body).length===2 &&
          "label" in body && body.label===customerZeroCommand.label &&
          "targetUri" in body && body.targetUri===customerZeroCommand.targetUri))
        return Response.json({status:"rejected",reason:"INVALID_ATTENTION_COMMAND"},{status:400,headers:noStore});
    }
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
      command,
    );
    const payload:unknown = await response.json();
    if(response.status===202 && typeof payload==="object" && payload!==null && "state" in payload && payload.state==="IDENTITY_UNRESOLVED")
      return Response.json({state:"IDENTITY_UNRESOLVED"},{status:202,headers:noStore});
    const result = readCustomerZeroResponse(
      payload,
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

export async function organizationInventoryProxy() {
  const token=(await cookies()).get(customerZeroCookie)?.value;
  if(!token)return Response.json({reason:"ADMIN_SESSION_REQUIRED"},{status:401,headers:noStore});
  try {
    const response=await runtimeRequest("/api/organizations",token);
    if(!response.ok)return Response.json({reason:"ATTENTION_AUTHORITY_UNAVAILABLE"},{status:response.status,headers:noStore});
    const parsed=organizationInventorySchema.safeParse(await response.json());
    if(!parsed.success)throw new Error("INVALID_INVENTORY");
    return Response.json(parsed.data,{headers:noStore});
  }catch{return Response.json({reason:"RUNTIME_UNAVAILABLE"},{status:502,headers:noStore});}
}
