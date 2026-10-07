import { subscriberMcpRequest } from "@/lib/subscriber-server";
export const runtime = "nodejs";
export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  return subscriberMcpRequest(request, (await context.params).id, false);
}
export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  return subscriberMcpRequest(request, (await context.params).id, true);
}
