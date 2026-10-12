import { subscriberIdentityCandidates } from "@/lib/subscriber-server";

export const runtime = "nodejs";

export function POST(request: Request) {
  return subscriberIdentityCandidates(request);
}
