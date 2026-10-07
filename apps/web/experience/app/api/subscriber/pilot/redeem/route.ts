import { subscriberPilotRedeem } from "@/lib/subscriber-server";

export const runtime = "nodejs";

export function POST(request: Request) {
  return subscriberPilotRedeem(request);
}
