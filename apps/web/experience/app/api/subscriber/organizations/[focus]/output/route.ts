import { subscriberProxy } from "@/lib/subscriber-server";
export const runtime = "nodejs";
export async function GET(request: Request, context: { params: Promise<{ focus: string }> }) {
  const focus = (await context.params).focus;
  if (!/^[A-Za-z0-9:_-]{1,160}$/.test(focus)) return Response.json({ code: "INVALID_REFERENCE" }, { status: 400 });
  return subscriberProxy(request, `/subscriber/organizations/${encodeURIComponent(focus)}/output`);
}
