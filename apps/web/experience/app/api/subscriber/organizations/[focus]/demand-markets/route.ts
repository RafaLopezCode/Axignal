import { subscriberDemandMarkets } from "@/lib/subscriber-server";
export const runtime = "nodejs";
export async function POST(request: Request, context: { params: Promise<{ focus: string }> }) {
  return subscriberDemandMarkets(request, (await context.params).focus);
}
