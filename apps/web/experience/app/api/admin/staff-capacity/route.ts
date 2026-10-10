import { staffCapacityProxy } from "@/lib/staff-capacity-server";
export const runtime = "nodejs";
export function GET(request: Request) { return staffCapacityProxy(request, null); }
