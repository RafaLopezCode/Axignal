import { customerAccessProxy } from "@/lib/customer-access-server";
export const runtime = "nodejs";
export function GET(request: Request) { return customerAccessProxy(request, null); }
