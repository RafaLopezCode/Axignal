import { subscriberResearch } from "@/lib/subscriber-server";
export const runtime = "nodejs";
// One search and up to three pages read by AXIGNAL, answered within seconds (spec 105).
export const maxDuration = 45;
export async function POST(request: Request, context: { params: Promise<{ focus: string }> }) {
  return subscriberResearch(request, (await context.params).focus);
}
