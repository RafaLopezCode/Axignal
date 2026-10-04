import { customerZeroProxy } from "@/lib/customer-zero-server";
export async function GET(request: Request) {
  return customerZeroProxy(request);
}
