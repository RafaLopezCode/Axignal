import {readAdminRuntimePayload} from "@/lib/admin-runtime-response";
import { cookies } from "next/headers";
import { customerZeroCookie, resolveRuntimeOrigin } from "@/lib/customer-zero-server";
import { operationalDomains, domainSections, type OperationalDomain } from "@/lib/admin-projections";
export const runtime = "nodejs";
const reply = (body: unknown, status = 200) => Response.json(body, {status, headers:{"Cache-Control":"no-store", "Referrer-Policy":"no-referrer"}});
export async function GET(_request: Request, context: {params: Promise<{domain: string}>}) {
  const {domain} = await context.params;
  if (!Object.hasOwn(operationalDomains, domain)) return reply({reason:"INVALID_DOMAIN"},404);
  const token = (await cookies()).get(customerZeroCookie)?.value;
  if (!token) return reply({reason:"ADMIN_SESSION_REQUIRED"},401);
  try {
    const configured = process.env.AXIGNAL_RUNTIME_ORIGIN;
    if (!configured) throw new Error("unavailable");
    const slug = operationalDomains[domain as OperationalDomain];
    const read = (target:string) => fetch(new URL("/admin/"+target, resolveRuntimeOrigin(configured)), {cache:"no-store",redirect:"error",signal:AbortSignal.timeout(15_000),headers:{Authorization:"Bearer "+token,Accept:"application/json"}});
    const response=await read(slug);
    if (!response.ok) return reply({reason:response.status===401?"ADMIN_SESSION_REQUIRED":response.status===403?"ADMIN_SCOPE_REQUIRED":"ADMIN_READ_UNAVAILABLE"},[401,403].includes(response.status)?response.status:502);
    let parsed=await readAdminRuntimePayload(response);
    if(parsed.currentSlug!==slug)throw new Error("scope mismatch");
    // Older AO-02 shells expose executive metrics only at command-center.
    // This fallback requires that additional scope; denial never bypasses RBAC.
    if(response.headers.get("content-type")?.startsWith("text/html") && ["revenue","system"].includes(domain) && !parsed.commandCenter){
      const executive=await read("command-center");
      if(!executive.ok)return reply({reason:executive.status===401?"ADMIN_SESSION_REQUIRED":executive.status===403?"ADMIN_SCOPE_REQUIRED":"ADMIN_READ_UNAVAILABLE"},[401,403].includes(executive.status)?executive.status:502);
      const legacy=await readAdminRuntimePayload(executive);
      if(legacy.currentSlug!=="command-center"||!legacy.commandCenter)throw new Error("invalid projection");
      const ids=domain==="revenue"?["mrr","arr","paying_accounts"]:["source_health","provider_health","system_health"];
      const metrics=legacy.commandCenter.metrics;
      if(!Array.isArray(metrics))throw new Error("invalid metrics");
      parsed={mode:"ADMIN",currentSlug:slug,commandCenter:{...legacy.commandCenter,metrics:metrics.filter(item=>item!==null&&typeof item==="object"&&!Array.isArray(item)&&typeof item.metricId==="string"&&ids.includes(item.metricId))}};
    }
    const authorized: Record<string,unknown>={mode:parsed.mode,currentSlug:parsed.currentSlug};
    for(const key of domainSections[domain as OperationalDomain]) {
      const value=(parsed as Record<string,unknown>)[key];
      if(!value) throw new Error("missing projection");
      authorized[key]=value;
    }
    return reply(authorized);
  } catch { return reply({reason:"ADMIN_READ_UNAVAILABLE"},502); }
}
