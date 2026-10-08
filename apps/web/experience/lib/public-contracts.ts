import { z } from "zod";

export const authStartSchema = z
  .object({
    provider: z.enum(["google", "openai"]),
    intent: z.enum(["login", "signup"]),
  })
  .strict();
export type AuthStartRequest = z.infer<typeof authStartSchema>;
export const preparedProviders = [
  {
    id: "google",
    label: "Google",
    status: "UNAVAILABLE",
    registrationRequired: true,
  },
  {
    id: "openai",
    label: "ChatGPT",
    status: "UNAVAILABLE",
    registrationRequired: true,
  },
] as const;

/** This is a presentation port, not an AuthenticationPort or an identity authority. */
export function preparedAuthStart(input: AuthStartRequest) {
  return {
    provider: input.provider,
    intent: input.intent,
    status: "UNAVAILABLE" as const,
    code: "AUTHENTICATION_PORT_NOT_CONNECTED" as const,
    verified: false,
    sessionCreated: false,
  };
}
export function acceptsPublicAuthOrigin(
  origin: string | null,
  host: string | null,
) {
  if (!origin || !host) return false;
  const allowed = process.env.AXIGNAL_EXPERIENCE_ORIGIN
    ? [process.env.AXIGNAL_EXPERIENCE_ORIGIN]
    : ["http://127.0.0.1:3810", "http://localhost:3810"];
  try { return allowed.includes(origin) && new URL(origin).host === host; }
  catch { return false; }
}
