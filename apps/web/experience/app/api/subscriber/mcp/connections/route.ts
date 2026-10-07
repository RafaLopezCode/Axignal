import { subscriberMcpConnections } from "@/lib/subscriber-server";
export const runtime = "nodejs";
export function GET(request: Request) { return subscriberMcpConnections(request, false); }
export function POST(request: Request) { return subscriberMcpConnections(request, true); }
