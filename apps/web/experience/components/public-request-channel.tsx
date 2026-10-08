"use client";
import Link from "next/link";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { ArrowRight, Info } from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  publicRequestError,
  publicRequestFieldsSchema,
  publicRequestReceiptSchema,
  publicRequestStatusSchema,
  type PublicRequestCategory,
  type PublicRequestStatus,
} from "@/lib/public-requests";
import "./public-request-channel.css";

export function PublicRequestChannel({
  subject,
  category = "contact",
}: {
  subject: string;
  category?: PublicRequestCategory;
}) {
  const { t, locale } = useLocale();
  const id = useId();
  const form = useRef<HTMLFormElement>(null);
  const sending = useRef(false);
  const reference = useRef<{ body: string; ref: string } | null>(null);
  const controller = useRef<AbortController | null>(null);
  const [channel, setChannel] = useState<PublicRequestStatus | null>(null);
  const [statusError, setStatusError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [busy, setBusy] = useState(false);
  const [values, setValues] = useState({ name: "", email: "", message: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [reason, setReason] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<string | null>(null);
  const rights = category !== "contact";
  useEffect(() => {
    const current = new AbortController();
    setChannel(null);
    setStatusError(false);
    void fetch(rights ? "/api/gdpr/status" : "/api/contact/status", {
      cache: "no-store",
      signal: current.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("STATUS_UNAVAILABLE");
        const data = publicRequestStatusSchema.parse(await response.json());
        if (!current.signal.aborted) setChannel(data);
      })
      .catch(() => {
        if (!current.signal.aborted) setStatusError(true);
      });
    return () => current.abort();
  }, [rights, retry]);
  useEffect(() => () => controller.current?.abort(), []);
  function edit(key: keyof typeof values, value: string) {
    setValues((previous) => ({ ...previous, [key]: value }));
    setReceipt(null);
    setReason(null);
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (sending.current || !channel?.enabled || receipt) return;
    const parsed = publicRequestFieldsSchema.safeParse(values);
    if (!parsed.success) {
      const next: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const key = String(issue.path[0]);
        next[key] =
          key === "name"
            ? t(
                "Indica un nombre (máximo 100 caracteres).",
                "Enter a name (maximum 100 characters).",
              )
            : key === "email"
              ? t("Indica un correo válido.", "Enter a valid email.")
              : t(
                  "Escribe entre 15 y 3.000 caracteres.",
                  "Write between 15 and 3,000 characters.",
                );
      }
      setErrors(next);
      form.current
        ?.querySelector<HTMLElement>(`[name="${Object.keys(next)[0]}"]`)
        ?.focus();
      return;
    }
    const payload = {
      ...parsed.data,
      subject,
      category,
      locale,
      noticeVersion: rights
        ? "privacy-rights-notice-v1"
        : "contact-request-notice-v1",
    };
    const body = JSON.stringify(payload);
    if (reference.current?.body !== body)
      reference.current = {
        body,
        ref: crypto.randomUUID().replaceAll("-", ""),
      };
    sending.current = true;
    setBusy(true);
    setReason(null);
    setErrors({});
    const current = new AbortController();
    controller.current = current;
    const timeout = setTimeout(() => current.abort(), 25000);
    try {
      const response = await fetch(
        rights ? "/api/privacy/request" : "/api/contact",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: current.signal,
          body: JSON.stringify({
            ...payload,
            requestRef: reference.current.ref,
          }),
        },
      );
      const data = await response.json();
      if (response.status === 202)
        setReceipt(publicRequestReceiptSchema.parse(data).requestId);
      else {
        setReason(
          typeof data.reason === "string" ? data.reason : "REQUEST_UNAVAILABLE",
        );
        if (data.reason === "CHANNEL_UNAVAILABLE")
          setChannel({ ...channel, enabled: false });
      }
    } catch {
      setReason("REQUEST_UNAVAILABLE");
    } finally {
      clearTimeout(timeout);
      sending.current = false;
      setBusy(false);
    }
  }
  if (!channel?.enabled)
    return (
      <section className="draft-form" aria-busy={!channel && !statusError}>
        <div className="form-heading">
          <span className="eyebrow">{t("Tu solicitud", "Your request")}</span>
        </div>
        <h2>{subject}</h2>
        <p role="status" className="draft-boundary">
          <Info size={16} />
          {statusError
            ? t(
                "No hemos podido comprobar el canal. Vuelve a intentarlo.",
                "We could not check the channel. Please try again.",
              )
            : !channel
              ? t("Comprobando el canal…", "Checking the channel…")
              : t(
                  "El canal no está disponible en este momento. No se ha recibido tu solicitud.",
                  "The channel is unavailable right now. Your request has not been received.",
                )}
        </p>
        {channel?.publicEmail && (
          <a className="text-link" href={`mailto:${channel.publicEmail}`}>
            {channel.publicEmail}
            <ArrowRight size={16} />
          </a>
        )}
        {statusError && (
          <button
            className="button secondary"
            onClick={() => setRetry((n) => n + 1)}
          >
            {t("Volver a comprobar", "Check again")}
          </button>
        )}
      </section>
    );
  return (
    <form
      ref={form}
      className="draft-form"
      noValidate
      onSubmit={submit}
      aria-busy={busy}
      aria-describedby={`${id}-notice`}
    >
      <div className="form-heading">
        <span className="eyebrow">{t("Tu solicitud", "Your request")}</span>
        <span className="mono">AXIGNAL · {t("España", "Spain")}</span>
      </div>
      <h2>{subject}</h2>
      <p id={`${id}-notice`} className="draft-boundary">
        <Info size={16} />
        {t(
          "AXIGNAL utiliza estos datos para atender tu solicitud. El recibo confirma el registro, no la entrega ni la resolución. Retención: 90 días.",
          "AXIGNAL uses these details to handle your request. The receipt confirms registration, not delivery or resolution. Retention: 90 days.",
        )}{" "}
        <Link href="/policies/privacy">{t("Privacidad", "Privacy")}</Link>
      </p>
      <div className="form-fields">
        {(["name", "email"] as const).map((key) => (
          <div className="form-field" key={key}>
            <label htmlFor={`${id}-${key}`}>
              {key === "name"
                ? t("Nombre", "Name")
                : t("Tu correo", "Your email")}
              <input
                id={`${id}-${key}`}
                name={key}
                type={key === "email" ? "email" : "text"}
                autoComplete={key}
                value={values[key]}
                maxLength={key === "name" ? 100 : 254}
                required
                disabled={busy}
                aria-invalid={!!errors[key]}
                aria-describedby={
                  errors[key] ? `${id}-error-${key}` : undefined
                }
                onChange={(e) => edit(key, e.target.value)}
              />
            </label>
            {errors[key] && (
              <span className="field-error" id={`${id}-error-${key}`}>
                {errors[key]}
              </span>
            )}
          </div>
        ))}
      </div>
      <label htmlFor={`${id}-message`}>
        {rights
          ? t("Qué quieres solicitar", "What you want to request")
          : t("Qué te gustaría conversar", "What would you like to discuss")}
        <textarea
          id={`${id}-message`}
          name="message"
          rows={5}
          required
          disabled={busy}
          value={values.message}
          maxLength={3000}
          aria-invalid={!!errors.message}
          aria-describedby={
            errors.message ? `${id}-error-message` : `${id}-help`
          }
          onChange={(e) => edit("message", e.target.value)}
        />
      </label>
      {errors.message && (
        <span className="field-error" id={`${id}-error-message`}>
          {errors.message}
        </span>
      )}
      <div className="message-help">
        <span id={`${id}-help`}>
          {t(
            "Evita contraseñas, documentos de identidad e información confidencial.",
            "Avoid passwords, identity documents and confidential information.",
          )}
        </span>
        <span className="mono">{values.message.length} / 3000</span>
      </div>
      {reason && (
        <p className="field-error" role="alert">
          {t(...publicRequestError(reason))}
        </p>
      )}
      {receipt && (
        <div className="request-receipt" role="status">
          <strong>{t("Solicitud recibida", "Request received")}</strong>
          <p>
            {t("Referencia", "Reference")}: {receipt}
          </p>
          <p>
            {t(
              "Este recibo no confirma entrega, aceptación legal ni resolución. Tu solicitud no modifica información económica canónica.",
              "This receipt does not confirm delivery, legal acceptance or resolution. Your request does not change canonical economic information.",
            )}
          </p>
        </div>
      )}
      <div className="form-bottom">
        <p>
          {t(
            "Se registra únicamente al enviar la solicitud.",
            "It is registered only when you submit the request.",
          )}
        </p>
        <button
          type="submit"
          className="button primary"
          disabled={busy || !!receipt}
        >
          {busy
            ? t("Enviando…", "Sending…")
            : t("Enviar solicitud", "Send request")}
          <ArrowRight size={17} />
        </button>
      </div>
    </form>
  );
}
