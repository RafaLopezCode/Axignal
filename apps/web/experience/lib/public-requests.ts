import { z } from "zod";

export const rightsCategories = [
  "access",
  "rectification",
  "erasure",
  "restriction",
  "objection",
  "portability",
  "other",
] as const;
export const publicRequestStatusSchema = z
  .object({
    enabled: z.boolean(),
    controller: z.literal("AXIGNAL"),
    country: z.literal("Spain"),
    publicEmail: z.email().nullable(),
  })
  .strict();
export const publicRequestFieldsSchema = z.object({
  name: z.string().trim().min(1).max(100),
  email: z.email().max(254),
  message: z.string().trim().min(15).max(3000),
});
export const publicRequestSchema = publicRequestFieldsSchema
  .extend({
    requestRef: z.string().regex(/^[A-Za-z0-9_-]{16,64}$/),
    category: z.enum(["contact", ...rightsCategories]),
    subject: z.string().trim().min(1).max(120),
    locale: z.enum(["es", "en", "de", "pt", "fr", "it"]),
    noticeVersion: z.enum([
      "contact-request-notice-v1",
      "privacy-rights-notice-v1",
    ]),
  })
  .strict();
export const publicRequestReceiptSchema = z
  .object({
    status: z.literal("received"),
    requestId: z.string().regex(/^[a-f0-9]{32}$/),
  })
  .strict();
export const publicRequestRejectionSchema = z
  .object({
    status: z.literal("rejected"),
    reason: z.string().min(1).max(80),
  })
  .strict();
export type PublicRequestStatus = z.infer<typeof publicRequestStatusSchema>;
export type PublicRequestCategory = z.infer<
  typeof publicRequestSchema
>["category"];
const c = (es: string, en: string): [string, string] => [es, en];

export function publicRequestError(reason: string): [string, string] {
  switch (reason) {
    case "INVALID_EMAIL":
      return c("Revisa tu correo electrónico.", "Check your email address.");
    case "INVALID_MESSAGE":
      return c(
        "Escribe entre 15 y 3.000 caracteres.",
        "Write between 15 and 3,000 characters.",
      );
    case "REQUEST_RATE_LIMITED":
    case "RATE_LIMITED":
      return c(
        "Has enviado varias solicitudes. Espera unos minutos antes de volver a intentarlo.",
        "You have sent several requests. Wait a few minutes before trying again.",
      );
    case "REQUEST_REF_CONFLICT":
      return c(
        "La referencia corresponde a otra solicitud. Revisa tu mensaje antes de enviarlo de nuevo.",
        "This reference belongs to another request. Review your message before sending it again.",
      );
    case "CHANNEL_UNAVAILABLE":
      return c(
        "El canal no está disponible en este momento. No se ha recibido tu solicitud.",
        "The channel is unavailable right now. Your request has not been received.",
      );
    case "INVALID_REQUEST":
    case "INVALID_CATEGORY":
    case "INVALID_LOCALE":
      return c(
        "Revisa los datos de la solicitud antes de volver a enviarla.",
        "Review your request details before sending again.",
      );
    default:
      return c(
        "No hemos podido confirmar la recepción. Puedes volver a intentarlo con la misma referencia.",
        "We could not confirm receipt. You can retry with the same reference.",
      );
  }
}
