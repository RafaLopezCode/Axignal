import {
  authStartSchema,
  acceptsPublicAuthOrigin,
  preparedAuthStart,
} from "@/lib/public-contracts";
export const runtime = "nodejs";
export async function POST(request: Request) {
  const headers = { "Cache-Control": "no-store" };
  if (
    !acceptsPublicAuthOrigin(
      request.headers.get("origin"),
      request.headers.get("host"),
    )
  )
    return Response.json({ code: "ORIGIN_DENIED" }, { status: 403, headers });
  if (
    request.headers.get("content-type")?.split(";")[0].trim() !==
    "application/json"
  )
    return Response.json({ code: "JSON_REQUIRED" }, { status: 415, headers });
  // Bound streaming reads too; a forged or absent Content-Length cannot bypass the limit.
  const reader = request.body?.getReader();
  if (!reader)
    return Response.json({ code: "INVALID_REQUEST" }, { status: 400, headers });
  let count = 0;
  const chunks: Uint8Array[] = [];
  while (true) {
    const next = await reader.read();
    if (next.done) break;
    count += next.value.byteLength;
    if (count > 1024) {
      await reader.cancel();
      return Response.json(
        { code: "REQUEST_TOO_LARGE" },
        { status: 413, headers },
      );
    }
    chunks.push(next.value);
  }
  try {
    const raw = Buffer.concat(chunks).toString("utf8");
    const parsed = authStartSchema.safeParse(JSON.parse(raw));
    if (!parsed.success)
      return Response.json(
        { code: "INVALID_REQUEST" },
        { status: 400, headers },
      );
    return Response.json(preparedAuthStart(parsed.data), {
      status: 503,
      headers,
    });
  } catch {
    return Response.json({ code: "INVALID_REQUEST" }, { status: 400, headers });
  }
}
