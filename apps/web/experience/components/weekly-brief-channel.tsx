"use client";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { publicRequestError } from "@/lib/public-requests";
import "./public-request-channel.css";

/** AO-15 request, with separately optional AO-16 newsletter consent. */
export function WeeklyBriefChannel() {
  const { t } = useLocale();
  const id = useId();
  const sending = useRef(false);
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/weekly-brief/status", {
      cache: "no-store",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) return;
        const data = await response.json();
        if (!controller.signal.aborted && typeof data.enabled === "boolean")
          setEnabled(data.enabled);
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sending.current || enabled !== true || receipt) return;
    const values = new FormData(event.currentTarget);
    const consent = values.get("newsletterConsent") === "on";
    const payload = {
      companyName: values.get("companyName"),
      companyDomain: values.get("companyDomain"),
      professionalEmail: values.get("professionalEmail"),
      purpose: values.get("purpose"),
      requestProcessingAcknowledged:
        values.get("requestProcessingAcknowledged") === "on",
      requestNoticeVersion: "weekly-brief-request-v1",
      newsletterConsent: consent,
      ...(consent
        ? { newsletterNoticeVersion: "weekly-newsletter-consent-v1" }
        : {}),
    };
    sending.current = true;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/weekly-brief/requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(25000),
      });
      const data = await response.json();
      if (
        response.status === 202 &&
        data.status === "received" &&
        /^brief:[a-f0-9]{24}$/.test(data.requestId)
      )
        setReceipt(data.requestId);
      else {
        setError(data.reason ?? "REQUEST_UNAVAILABLE");
        if (data.reason === "CHANNEL_UNAVAILABLE") setEnabled(false);
      }
    } catch {
      setError("REQUEST_UNAVAILABLE");
    } finally {
      sending.current = false;
      setBusy(false);
    }
  }
  if (enabled !== true) return null;
  return (
    <section className="rights-request">
      <div className="rights-request-copy">
        <span className="eyebrow">{t("Informe semanal", "Weekly brief")}</span>
        <h2>{t("Solicitar un informe", "Request a brief")}</h2>
        <p>
          {t(
            "Tu solicitud pasa a revisión. No garantiza un informe, investigación ni entrega automática.",
            "Your request goes to review. It does not guarantee a brief, research or automatic delivery.",
          )}
        </p>
      </div>
      <form
        className="draft-form weekly-brief-form"
        onSubmit={submit}
        aria-busy={busy}
      >
        <fieldset disabled={busy || !!receipt}>
          <legend>{t("Tu solicitud", "Your request")}</legend>
          <div className="form-fields">
            {(
              [
                ["companyName", t("Organización", "Organization"), "text", 200],
                [
                  "companyDomain",
                  t("Dominio de la organización", "Organization domain"),
                  "text",
                  253,
                ],
                [
                  "professionalEmail",
                  t("Correo profesional", "Professional email"),
                  "email",
                  254,
                ],
              ] as const
            ).map(([name, label, type, max]) => (
              <label key={name} htmlFor={`${id}-${name}`}>
                {label}
                <input
                  id={`${id}-${name}`}
                  name={name}
                  type={type}
                  required
                  maxLength={max}
                />
              </label>
            ))}
          </div>
          <label htmlFor={`${id}-purpose`}>
            {t("Qué quieres comprender", "What you want to understand")}
            <textarea
              id={`${id}-purpose`}
              name="purpose"
              required
              minLength={15}
              maxLength={3000}
              rows={5}
            />
          </label>
          <p>
            {t(
              "Evita contraseñas, documentos de identidad e información confidencial.",
              "Avoid passwords, identity documents and confidential information.",
            )}{" "}
            <Link href="/policies/privacy">{t("Privacidad", "Privacy")}</Link>
          </p>
          <label className="brief-consent">
            <input
              name="requestProcessingAcknowledged"
              type="checkbox"
              required
            />
            {t(
              "Entiendo que AXIGNAL usa estos datos para revisar mi solicitud de informe.",
              "I understand that AXIGNAL uses these details to review my brief request.",
            )}
          </label>
          <label className="brief-consent">
            <input name="newsletterConsent" type="checkbox" />
            {t(
              "Opcional: quiero recibir el informe semanal por correo. Puedo retirar este consentimiento.",
              "Optional: I want to receive the weekly brief by email. I can withdraw this consent.",
            )}
          </label>
          <div className="form-bottom">
            <button type="submit" className="button primary">
              {busy
                ? t("Enviando…", "Sending…")
                : t("Enviar solicitud", "Send request")}
              <ArrowRight size={17} />
            </button>
          </div>
        </fieldset>
        {error && (
          <p className="field-error" role="alert">
            {t(...publicRequestError(error))}
          </p>
        )}
        {receipt && (
          <div role="status">
            <strong>{t("Solicitud recibida", "Request received")}</strong>
            <p>
              {t("Referencia", "Reference")}: {receipt}
            </p>
            <p>
              {t(
                "Tu solicitud pasa a revisión. No garantiza un informe, investigación ni entrega automática.",
                "Your request goes to review. It does not guarantee a brief, research or automatic delivery.",
              )}
            </p>
          </div>
        )}
      </form>
    </section>
  );
}
