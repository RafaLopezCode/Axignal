import { subscriberAuthCallback } from "@/lib/subscriber-server";
export const runtime = "nodejs";
export async function GET(request: Request, context: { params: Promise<{ provider: string }> }) {
  return subscriberAuthCallback(request, (await context.params).provider);
}
