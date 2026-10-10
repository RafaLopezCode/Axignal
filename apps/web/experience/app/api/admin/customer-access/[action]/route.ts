import { customerAccessProxy } from "@/lib/customer-access-server";
import { customerActions, type CustomerAction } from "@/lib/customer-access";
export const runtime = "nodejs";
export async function POST(request: Request, context: { params: Promise<{ action: string }> }) {
  const { action } = await context.params;
  if (!(customerActions as readonly string[]).includes(action)) return Response.json({ reason: "INVALID_REQUEST" }, { status: 404 });
  return customerAccessProxy(request, action as CustomerAction);
}
