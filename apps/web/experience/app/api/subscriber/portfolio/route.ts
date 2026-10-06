import { subscriberProxy } from "@/lib/subscriber-server";
export const runtime = "nodejs";
export function GET(request: Request) { return subscriberProxy(request, "/subscriber/portfolio"); }
export function POST(request: Request) { return subscriberProxy(request, "/subscriber/portfolio", true); }
