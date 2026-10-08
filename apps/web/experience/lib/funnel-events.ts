// Public funnel measurement through the existing AO-12 first-party endpoint
// (`/api/acquisition/events`, model OBSERVED_TOUCH_V1). No new event system, no
// cookies, no identity: an anonymous per-tab session reference only. Nothing is sent
// unless the runtime's status endpoint reports the model as enabled, so the operator
// switch (and the privacy notice that accompanies it) stays the single authority.

export const funnelCta = {
  heroExample: "hero-example",
  heroStart: "hero-start",
  headerStart: "header-start",
  headerLogin: "header-login",
  proofExample: "proof-example",
  audienceExample: "audience-example",
  pricingStart: "pricing-start",
  closingStart: "closing-start",
  closingExample: "closing-example",
  exampleStart: "example-start",
  signupGoogle: "signup-start",
  loginGoogle: "login-start",
} as const;
export type FunnelCta = (typeof funnelCta)[keyof typeof funnelCta];

// CHAPTER_VIEWED carries a bounded 1-15 index. Landing chapters and example depth
// share the same event kind but never the same surface.
export const landingChapters = { how: 2, proof: 3, audience: 4, trust: 5, pricing: 6 } as const;
export const exampleDepth = { opened: 1, family: 2, signal: 3, evidence: 4, history: 5 } as const;

type Surface = "landing" | "example" | "access";
type Event =
  | { kind: "LANDING_VIEWED"; surface: Surface }
  | { kind: "CHAPTER_VIEWED"; surface: Surface; chapter: number }
  | { kind: "CTA_ACTIVATED"; surface: Surface; cta: FunnelCta };

const STATUS_URL = "/api/acquisition/status";
const EVENT_URL = "/api/acquisition/events";
const SESSION_KEY = "axignal.acquisition.session.v1";
let enabled: Promise<boolean> | null = null;
const sent = new Set<string>();

function token(bytes: number): string {
  const data = new Uint8Array(bytes);
  crypto.getRandomValues(data);
  return Array.from(data, (value) => value.toString(16).padStart(2, "0")).join("");
}

function sessionRef(): string | null {
  try {
    let value = sessionStorage.getItem(SESSION_KEY);
    if (!value) {
      value = "session:" + token(16);
      sessionStorage.setItem(SESSION_KEY, value);
    }
    return value;
  } catch {
    return null;
  }
}

function measurementEnabled(): Promise<boolean> {
  enabled ??= fetch(STATUS_URL, { headers: { Accept: "application/json" } })
    .then(async (response) => {
      if (!response.ok) return false;
      const data: unknown = await response.json();
      return (
        typeof data === "object" && data !== null &&
        "enabled" in data && data.enabled === true &&
        "model" in data && data.model === "OBSERVED_TOUCH_V1"
      );
    })
    .catch(() => false);
  return enabled;
}

export function funnelPayload(event: Event, context: { session: string; locale: string; path: string; referrer: string | null; now: Date; id: string }) {
  return {
    eventId: "mkt:" + context.id,
    sessionRef: context.session,
    kind: event.kind,
    occurredAt: context.now.toISOString(),
    surface: event.surface,
    locale: context.locale.slice(0, 2),
    path: context.path.slice(0, 300),
    referrer: context.referrer,
    ...("chapter" in event ? { chapter: event.chapter } : {}),
    ...("cta" in event ? { cta: event.cta } : {}),
  };
}

/** Fire-and-forget. Telemetry can never block or degrade the public journey. */
export function track(event: Event): void {
  if (typeof window === "undefined") return;
  const once = event.kind === "CTA_ACTIVATED" ? null : JSON.stringify(event) + location.pathname;
  if (once) {
    if (sent.has(once)) return;
    sent.add(once);
  }
  void measurementEnabled().then((on) => {
    const session = on ? sessionRef() : null;
    if (!session) return;
    const body = funnelPayload(event, {
      session,
      locale: document.documentElement.lang || "es",
      path: location.pathname,
      referrer: document.referrer || null,
      now: new Date(),
      id: token(16),
    });
    void fetch(EVENT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
      keepalive: true,
    }).catch(() => undefined);
  });
}
