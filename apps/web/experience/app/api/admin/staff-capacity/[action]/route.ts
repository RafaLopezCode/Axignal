import { staffAction, staffCapacityProxy } from "@/lib/staff-capacity-server";
export const runtime = "nodejs";
export async function POST(request: Request, context: { params: Promise<{ action: string }> }) {
  const action = staffAction((await context.params).action);
  if (action === null) return Response.json({ reason: "INVALID_REQUEST" }, { status: 404, headers: { "Cache-Control": "no-store" } });
  return staffCapacityProxy(request, action);
}
