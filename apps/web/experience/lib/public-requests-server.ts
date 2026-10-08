import {
  boundedSubscriberJson,
  subscriberSameOrigin,
} from "./subscriber-server";
import {
  publicRequestSchema,
  publicRequestStatusSchema,
  publicRequestReceiptSchema,
  publicRequestRejectionSchema,
} from "./public-requests";
import { z } from "zod";

type Channel = "contact" | "gdpr";
const headers = {
  "Cache-Control": "no-store",
  "Referrer-Policy": "no-referrer",
};
const rejected = (reason: string, status = 503) =>
  Response.json({ status: "rejected", reason }, { status, headers });
function origin(): URL {
  const url = new URL(process.env.AXIGNAL_RUNTIME_ORIGIN ?? "");
  const compose =
    process.env.AXIGNAL_CONTAINERIZED === "true" &&
    url.hostname === "runtime" &&
    url.port === "18181";
  if (
    url.protocol !== "http:" ||
    (!compose && !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname !== "/"
  )
    throw new Error("RUNTIME_ORIGIN_REJECTED");
  return url;
}
async function read(response: Response): Promise<unknown> {
  if (!response.body) throw new Error("INVALID_RESPONSE");
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const item = await reader.read();
    if (item.done) break;
    size += item.value.byteLength;
    if (size > 4096) {
      await reader.cancel();
      throw new Error("BODY_LIMIT");
    }
    chunks.push(item.value);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}
export async function publicChannelStatus(channel: Channel): Promise<Response> {
  try {
    const response = await fetch(new URL(`/api/${channel}/status`, origin()), {
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) return rejected("REQUEST_UNAVAILABLE");
    return Response.json(
      publicRequestStatusSchema.parse(await read(response)),
      { headers },
    );
  } catch {
    return rejected("REQUEST_UNAVAILABLE");
  }
}
export async function publicChannelSubmit(
  request: Request,
  channel: Channel,
): Promise<Response> {
  if (!subscriberSameOrigin(request)) return rejected("ORIGIN_REJECTED", 403);
  let payload;
  try {
    payload = publicRequestSchema.parse(
      await boundedSubscriberJson(request, 16384),
    );
    if (
      (channel === "contact") !== (payload.category === "contact") ||
      payload.noticeVersion !==
        (channel === "contact"
          ? "contact-request-notice-v1"
          : "privacy-rights-notice-v1")
    )
      return rejected("INVALID_REQUEST", 400);
  } catch {
    return rejected("INVALID_REQUEST", 400);
  }
  try {
    const response = await fetch(
      new URL(
        channel === "contact" ? "/api/contact" : "/api/privacy/request",
        origin(),
      ),
      {
        method: "POST",
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(20000),
        headers: {
          "Content-Type": "application/json",
          Origin:
            process.env.AXIGNAL_EXPERIENCE_ORIGIN ?? "http://127.0.0.1:3810",
        },
        body: JSON.stringify(payload),
      },
    );
    const data = await read(response);
    if (response.status === 202)
      return Response.json(publicRequestReceiptSchema.parse(data), {
        status: 202,
        headers,
      });
    if (![400, 403, 409, 429, 503].includes(response.status))
      return rejected("REQUEST_UNAVAILABLE");
    return Response.json(publicRequestRejectionSchema.parse(data), {
      status: response.status,
      headers,
    });
  } catch {
    return rejected("REQUEST_UNAVAILABLE");
  }
}

const weeklyBriefSchema = z
  .object({
    companyName: z.string().trim().min(1).max(200),
    companyDomain: z.string().trim().min(1).max(253),
    professionalEmail: z.email().max(254),
    purpose: z.string().trim().min(15).max(3000),
    requestProcessingAcknowledged: z.literal(true),
    requestNoticeVersion: z.literal("weekly-brief-request-v1"),
    newsletterConsent: z.boolean(),
    newsletterNoticeVersion: z
      .literal("weekly-newsletter-consent-v1")
      .optional(),
  })
  .strict()
  .refine((data) => !data.newsletterConsent || !!data.newsletterNoticeVersion);
export async function publicWeeklyBriefStatus(): Promise<Response> {
  try {
    const response = await fetch(
      new URL("/api/weekly-brief/status", origin()),
      {
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(10000),
      },
    );
    if (!response.ok) return rejected("REQUEST_UNAVAILABLE");
    return Response.json(
      z
        .object({ enabled: z.boolean() })
        .strict()
        .parse(await read(response)),
      { headers },
    );
  } catch {
    return rejected("REQUEST_UNAVAILABLE");
  }
}
export async function publicWeeklyBriefSubmit(
  request: Request,
): Promise<Response> {
  if (!subscriberSameOrigin(request)) return rejected("ORIGIN_REJECTED", 403);
  let payload;
  try {
    payload = weeklyBriefSchema.parse(
      await boundedSubscriberJson(request, 16384),
    );
  } catch {
    return rejected("INVALID_REQUEST", 400);
  }
  try {
    const response = await fetch(
      new URL("/api/weekly-brief/requests", origin()),
      {
        method: "POST",
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(20000),
        headers: {
          "Content-Type": "application/json",
          Origin:
            process.env.AXIGNAL_EXPERIENCE_ORIGIN ?? "http://127.0.0.1:3810",
        },
        body: JSON.stringify(payload),
      },
    );
    if (response.status === 404) return rejected("CHANNEL_UNAVAILABLE");
    const data = await read(response);
    if (response.status !== 202)
      return rejected("INVALID_REQUEST", response.status === 400 ? 400 : 503);
    const receipt = z
      .object({
        status: z.literal("received"),
        requestId: z.string().regex(/^brief:[a-f0-9]{24}$/),
        reviewState: z.string().max(80),
      })
      .parse(data);
    return Response.json(
      { status: receipt.status, requestId: receipt.requestId },
      { status: 202, headers },
    );
  } catch {
    return rejected("REQUEST_UNAVAILABLE");
  }
}
