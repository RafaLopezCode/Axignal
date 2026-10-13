import { poolUnsubscribe } from "@/lib/subscriber-server";

const noStore = { "Cache-Control": "no-store" };

// RFC 8058 one-click (List-Unsubscribe-Post) and the confirm button both POST here.
// The answer never says whether the token was known.
export async function POST(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const done = await poolUnsubscribe(token);
  return Response.json({ unsubscribed: done }, { status: done ? 200 : 503, headers: noStore });
}
