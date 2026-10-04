"use client";
import { useRef, useState, type FormEvent } from "react";
import {
  ArrowRight,
  ArrowLeft,
  Download,
  FileText,
  Mail,
  Check,
  Info,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  localDraftSchema,
  draftText,
  type LocalDraft,
} from "@/lib/public-contracts";
import { Dialog, Observer } from "./ui";
import { PublicShell } from "./public-shell";

export function DraftForm({
  subject,
  rights = false,
}: {
  subject: string;
  rights?: boolean;
}) {
  const { t, locale } = useLocale();
  const formRef = useRef<HTMLFormElement>(null);
  const [values, setValues] = useState({ name: "", email: "", message: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<LocalDraft | null>(null);
  const [downloaded, setDownloaded] = useState(false);
  function submit(event: FormEvent) {
    event.preventDefault();
    const parsed = localDraftSchema.safeParse({ subject, ...values });
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
      formRef.current
        ?.querySelector<HTMLElement>('[name="' + Object.keys(next)[0] + '"]')
        ?.focus();
      return;
    }
    setErrors({});
    setDownloaded(false);
    setPreview(parsed.data);
  }
  function download() {
    if (!preview) return;
    const url = URL.createObjectURL(
      new Blob([draftText(preview, locale)], {
        type: "text/plain;charset=utf-8",
      }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = rights
      ? "axignal-rights-draft.txt"
      : "axignal-contact-draft.txt";
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setDownloaded(true);
  }
  return (
    <>
      <form
        ref={formRef}
        className="draft-form"
        noValidate
        onSubmit={submit}
        aria-describedby="draft-boundary"
      >
        <div className="form-heading">
          <span className="eyebrow">
            {rights
              ? t("Preparar un borrador", "Prepare a draft")
              : t("Tu mensaje", "Your message")}
          </span>
          <span className="mono">
            {t("Solo en esta página", "Only on this page")}
          </span>
        </div>
        <h2>{subject}</h2>
        <p className="draft-boundary" id="draft-boundary">
          <Info size={16} />
          {t(
            "El canal de envío está pendiente de publicación. Puedes revisar y descargar tu texto; no se envía ni se registra una solicitud.",
            "The sending channel is pending publication. You can review and download your text; nothing is sent or lodged as a request.",
          )}
        </p>
        <div className="form-fields">
          <div className="form-field">
            <label htmlFor="draft-name">
              {t("Nombre", "Name")}
              <input
                id="draft-name"
                name="name"
                autoComplete="name"
                value={values.name}
                maxLength={100}
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? "error-name" : undefined}
                onChange={(e) => setValues({ ...values, name: e.target.value })}
                required
              />
            </label>
            {errors.name && (
              <span id="error-name" className="field-error">
                {errors.name}
              </span>
            )}
          </div>
          <div className="form-field">
            <label htmlFor="draft-email">
              {t("Tu correo", "Your email")}
              <input
                id="draft-email"
                name="email"
                type="email"
                autoComplete="email"
                value={values.email}
                maxLength={254}
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "error-email" : undefined}
                onChange={(e) =>
                  setValues({ ...values, email: e.target.value })
                }
                required
              />
            </label>
            {errors.email && (
              <span id="error-email" className="field-error">
                {errors.email}
              </span>
            )}
          </div>
        </div>
        <label htmlFor="draft-message">
          {rights
            ? t("Qué quieres solicitar", "What you want to request")
            : t("Qué te gustaría conversar", "What would you like to discuss")}
          <textarea
            id="draft-message"
            name="message"
            rows={5}
            value={values.message}
            maxLength={3000}
            aria-invalid={!!errors.message}
            aria-describedby={errors.message ? "error-message" : "message-help"}
            onChange={(e) => setValues({ ...values, message: e.target.value })}
            required
          />
        </label>
        {errors.message && (
          <span id="error-message" className="field-error">
            {errors.message}
          </span>
        )}
        <div className="message-help">
          <span id="message-help">
            {t(
              "Evita contraseñas, documentos de identidad e información confidencial.",
              "Avoid passwords, identity documents and confidential information.",
            )}
          </span>
          <span className="mono">{values.message.length} / 3000</span>
        </div>
        {Object.keys(errors).length > 0 && (
          <p className="field-error" role="alert">
            {t(
              "Revisa los campos indicados antes de abrir la vista previa.",
              "Review the indicated fields before opening the preview.",
            )}
          </p>
        )}
        <div className="form-bottom">
          <p>
            {t(
              "El borrador se conserva mientras esta página permanece abierta. No se guarda en el servidor.",
              "The draft remains while this page stays open. It is not saved on the server.",
            )}
          </p>
          <button type="submit" className="button primary">
            {t("Revisar borrador", "Review draft")}
            <ArrowRight size={17} />
          </button>
        </div>
      </form>
      {preview && (
        <Dialog
          title={t(
            "Tu texto, antes de enviarlo.",
            "Your text, before sending.",
          )}
          onClose={() => setPreview(null)}
          className="draft-preview"
        >
          <span className="publication-note">
            <FileText size={13} />
            {t("Borrador local · no enviado", "Local draft · not sent")}
          </span>
          <pre>{draftText(preview, locale)}</pre>
          <div className="preview-actions">
            <button
              className="button secondary"
              onClick={() => setPreview(null)}
            >
              <ArrowLeft size={16} />
              {t("Seguir editando", "Keep editing")}
            </button>
            <button className="button primary" onClick={download}>
              <Download size={16} />
              {t("Descargar borrador", "Download draft")}
            </button>
          </div>
          <p className="download-receipt" role="status">
            {downloaded && (
              <>
                <Check size={16} />
                {t(
                  "Descarga preparada. Tu texto sigue sin enviarse; esta descarga no acredita recepción.",
                  "Download prepared. Your text is still unsent; this download does not prove receipt.",
                )}
              </>
            )}
          </p>
        </Dialog>
      )}
    </>
  );
}
export function Contact() {
  const { t } = useLocale();
  const options = [
    t("Conocer AXIGNAL", "Get to know AXIGNAL"),
    t("Una pregunta de producto", "A product question"),
    t("Privacidad y datos", "Privacy and data"),
  ];
  const [topic, setTopic] = useState(0);
  return (
    <PublicShell className="contact-page">
      <div className="contact-spread">
        <section className="contact-perspective">
          <span className="eyebrow">
            {t(
              "Contacto / Una conversación abierta",
              "Contact / An open conversation",
            )}
          </span>
          <h1>
            {t("Las buenas preguntas", "Good questions")}
            <br />
            <em>{t("nos acercan.", "bring us closer.")}</em>
          </h1>
          <p>
            {t(
              "Cuéntanos qué intentas comprender. El mejor punto de partida es una pregunta con contexto.",
              "Tell us what you are trying to understand. A question with context is the best place to start.",
            )}
          </p>
          <div
            className="contact-topics"
            role="group"
            aria-label={t("Tema del mensaje", "Message topic")}
          >
            {options.map((option, i) => (
              <button
                key={i}
                aria-pressed={topic === i}
                onClick={() => setTopic(i)}
              >
                {option}
                <ArrowRight size={16} />
              </button>
            ))}
          </div>
          <div className="contact-illustration">
            <div className="letter-paper">
              <Mail size={23} />
              <span>
                {t("Una pregunta.", "A question.")}
                <br />
                {t("Más perspectiva.", "More perspective.")}
              </span>
              <i />
              <i />
              <img src="/brand/isotope.svg" alt="" width={32} height={35} />
            </div>
            <Observer scene="contact" />
            <span className="hand-note">
              {t("te leemos con atención", "we read with care")}
            </span>
          </div>
          <p className="contact-publication">
            {t(
              "Responsable, país y correo público: pendientes de publicación.",
              "Controller, country and public email: pending publication.",
            )}
          </p>
        </section>
        <DraftForm subject={options[topic]} />
      </div>
    </PublicShell>
  );
}
