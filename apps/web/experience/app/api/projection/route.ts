import { NextRequest } from "next/server";
import { makeContext, project, type FamilyId } from "@/lib/projection";
import { validateContext } from "@/lib/governance";
export function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams;
  const context = makeContext(
    q.get("organization") ?? "norte",
    (q.get("family") ?? "markets") as FamilyId,
    q.get("asOf") ?? "2026-10-03",
    q.get("signal"),
  );
  const valid = validateContext(context);
  return valid.success
    ? Response.json(project(valid.data), {
        headers: { "Cache-Control": "no-store" },
      })
    : Response.json({ error: valid.error }, { status: 400 });
}
