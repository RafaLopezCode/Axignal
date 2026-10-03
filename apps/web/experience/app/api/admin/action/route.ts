import { denyAdminMutation } from "@/lib/governance";
export function POST() {
  const denied = denyAdminMutation();
  return Response.json(
    { error: denied.code, message: denied.message },
    { status: denied.status },
  );
}
