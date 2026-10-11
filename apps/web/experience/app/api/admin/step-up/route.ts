import { customerStepUpCookie } from "@/lib/customer-access-server";
import { cookies } from "next/headers";
import { customerZeroCookie, sameOrigin } from "@/lib/customer-zero-server";
import { staffStepUpCookie, validateStaffStepUp } from "@/lib/staff-capacity-server";

const noStore = { "Cache-Control": "no-store" };
const reply = (reason: string, status: number) => Response.json({ reason }, { status, headers: noStore });

/** Operator-issued, already-verified short-lived proof. No OTP or SSH credentials reach HTTP. */
export async function POST(request: Request) {
  if (!sameOrigin(request)) return reply("ORIGIN_REQUIRED", 403);
  if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json")
    return reply("JSON_REQUIRED", 415);
  const jar = await cookies();
  const primary = jar.get(customerZeroCookie)?.value;
  if (!primary) return reply("ADMIN_SESSION_REQUIRED", 401);
  try {
    const reader = request.body?.getReader();
    if (!reader) return reply("INVALID_SESSION", 400);
    let size = 0;
    const chunks: Uint8Array[] = [];
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.byteLength;
      if (size > 1024) {
        await reader.cancel();
        return reply("BODY_LIMIT", 413);
      }
      chunks.push(part.value);
    }
    const parsed: unknown = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    if (!parsed || typeof parsed !== "object" || Object.keys(parsed).length !== 1 ||
        !("token" in parsed) || typeof parsed.token !== "string" ||
        !/^[A-Za-z0-9_-]{48,512}$/.test(parsed.token))
      return reply("INVALID_SESSION", 400);
    if (!(await validateStaffStepUp(primary, parsed.token)))
      return reply("STEP_UP_REQUIRED", 403);
    jar.set(staffStepUpCookie, parsed.token, {
      httpOnly: true, sameSite: "strict",
      secure: request.headers.get("origin")?.startsWith("https:") === true,
      path: "/api/admin/staff-capacity", maxAge: 600,
    });
    jar.set(customerStepUpCookie, parsed.token, {
      httpOnly: true, sameSite: "strict",
      secure: request.headers.get("origin")?.startsWith("https:") === true,
      path: "/api/admin/customer-access", maxAge: 600,
    });
    return Response.json({ authorized: true, expiresInSeconds: 600 }, { headers: noStore });
  } catch (error) {
    return reply(error instanceof SyntaxError ? "INVALID_SESSION" : "RUNTIME_UNAVAILABLE",
      error instanceof SyntaxError ? 400 : 502);
  }
}

export async function DELETE(request: Request) {
  if (!sameOrigin(request)) return reply("ORIGIN_REQUIRED", 403);
  (await cookies()).set(staffStepUpCookie, "", {
    path: "/api/admin/staff-capacity", httpOnly: true, sameSite: "strict",
    secure: request.headers.get("origin")?.startsWith("https:") === true, maxAge: 0,
  });
  (await cookies()).set(customerStepUpCookie, "", {
    path: "/api/admin/customer-access", httpOnly: true, sameSite: "strict",
    secure: request.headers.get("origin")?.startsWith("https:") === true, maxAge: 0,
  });
  return Response.json({ authorized: false }, { headers: noStore });
}
