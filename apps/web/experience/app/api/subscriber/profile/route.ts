import { subscriberAccount } from "@/lib/subscriber-server";
export const runtime = "nodejs";
export function GET(request: Request) { return subscriberAccount(request,"profile"); }
export function POST(request: Request) { return subscriberAccount(request,"profile",true); }
