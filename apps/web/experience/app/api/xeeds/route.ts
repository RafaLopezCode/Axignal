import { customerZeroProxy } from "@/lib/customer-zero-server";
export async function POST(request: Request) {
  return customerZeroProxy(request, true);
}
