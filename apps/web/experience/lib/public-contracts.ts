import { translate } from "./copy-catalog";
import type { Locale } from "./languages";
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
  const allowed = ["http://127.0.0.1:3810", "http://localhost:3810"];
  return allowed.includes(origin) && new URL(origin).host === host;
}
export const localDraftSchema = z
  .object({
    subject: z.string().trim().min(1).max(120),
    name: z.string().trim().min(1).max(100),
    email: z.email().max(254),
    message: z.string().trim().min(15).max(3000),
  })
  .strict();
export type LocalDraft = z.infer<typeof localDraftSchema>;
/** No transmission or persistence: this text is exactly the visible preview/download. */
export function draftText(draft: LocalDraft, locale: Locale) {
  const parsed = localDraftSchema.parse(draft);
  const t = (es: string, en: string) => translate(es, en, locale);
  return [
    t(
      "AXIGNAL · BORRADOR LOCAL · NO ENVIADO",
      "AXIGNAL · LOCAL DRAFT · NOT SENT",
    ),
    "",
    t(
      "Destinatario: pendiente de publicación",
      "Recipient: pending publication",
    ),
    t("Asunto: ", "Subject: ") + parsed.subject,
    t("Nombre: ", "Name: ") + parsed.name,
    "Email: " + parsed.email,
    "",
    parsed.message,
    "",
    t(
      "Este borrador no registra una solicitud ni acredita recepción.",
      "This draft does not lodge a request or prove receipt.",
    ),
  ].join("\n");
}
