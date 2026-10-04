import { cookies } from "next/headers";
import {
  customerZeroCookie,
  runtimeRequest,
  sameOrigin,
} from "@/lib/customer-zero-server";
export async function POST(request: Request) {
  if (!sameOrigin(request))
    return Response.json({ reason: "ORIGIN_REQUIRED" }, { status: 403 });
  if (
    request.headers.get("content-type")?.split(";")[0].trim() !==
    "application/json"
  )
    return Response.json({ reason: "JSON_REQUIRED" }, { status: 415 });
  try {
    const reader = request.body?.getReader();
    if (!reader)
      return Response.json({ reason: "INVALID_SESSION" }, { status: 400 });
    let size = 0;
    const chunks: Uint8Array[] = [];
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.byteLength;
      if (size > 1024) {
        await reader.cancel();
        return Response.json({ reason: "REQUEST_TOO_LARGE" }, { status: 413 });
      }
      chunks.push(part.value);
    }
    const body: unknown = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    if (
      !body ||
      typeof body !== "object" ||
      !("token" in body) ||
      typeof body.token !== "string" ||
      body.token.length < 20 ||
      body.token.length > 512
    )
      return Response.json({ reason: "INVALID_SESSION" }, { status: 400 });
    const access = await runtimeRequest(
      "/internal/admin/customer-zero/access",
      body.token,
    );
    if (!access.ok)
      return Response.json(
        { reason: "ADMIN_SESSION_REJECTED" },
        { status: access.status },
      );
    (await cookies()).set(customerZeroCookie, body.token, {
      httpOnly: true,
      sameSite: "strict",
      secure: request.headers.get("origin")?.startsWith("https:") === true,
      path: "/",
      maxAge: 8 * 3600,
    });
    return Response.json(
      { authorized: true },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return Response.json(
      {
        reason:
          error instanceof SyntaxError
            ? "INVALID_SESSION"
            : "RUNTIME_UNAVAILABLE",
      },
      { status: error instanceof SyntaxError ? 400 : 502 },
    );
  }
}
export async function DELETE(request: Request) {
  if (!sameOrigin(request))
    return Response.json({ reason: "ORIGIN_REQUIRED" }, { status: 403 });
  (await cookies()).delete(customerZeroCookie);
  return Response.json({ authorized: false });
}
