"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { ShieldCheck, Info } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { Dialog } from "./ui";
import { legalIdentity } from "@/lib/legal";
const key = "axignal.privacy-notice.v1";
const maximumAge = 180 * 24 * 60 * 60 * 1000;
export function PrivacyNotice() {
  const { t } = useLocale();
  const path = usePathname();
  const [notice, setNotice] = useState(false);
  const [details, setDetails] = useState(false);
  const publicPage = !/^\/(panorama|admin|design|sources|api)(\/|$)/.test(path);
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(key) ?? "null");
      if (
        !saved ||
        typeof saved.dismissedAt !== "number" ||
        Date.now() - saved.dismissedAt > maximumAge
      )
        setNotice(true);
    } catch {
      setNotice(true);
    }
  }, []);
  function dismiss() {
    try {
      localStorage.setItem(key, JSON.stringify({ dismissedAt: Date.now() }));
    } catch {}
    setNotice(false);
    setDetails(false);
  }
  if (!publicPage) return null;
  return (
    <>
      <button
        className="privacy-preferences-button"
        onClick={() => setDetails(true)}
      >
        <ShieldCheck size={15} />
        {t("Privacidad", "Privacy")}
      </button>
      {notice && (
        <aside
          className="privacy-notice"
          aria-label={t(
            "Privacidad en AXIGNAL",
            "Privacy at AXIGNAL",
          )}
        >
          <div className="privacy-notice-heading">
            <ShieldCheck size={21} />
            <h2>{t("Una visita, con claridad.", "A visit, with clarity.")}</h2>
          </div>
          <p>
            {t(
              `La navegación pública no activa analítica, publicidad ni cookies de acceso. Recuerda tu idioma y este aviso. Customer Zero utiliza una cookie necesaria cuando el personal conecta una sesión Admin. Responsable: ${legalIdentity.controller} (${legalIdentity.country}). Contacto: ${legalIdentity.publicEmail}.`,
              `Public navigation activates no analytics, advertising or sign-in cookies. It remembers your language and this notice. Customer Zero uses a necessary cookie when staff connect an Admin session. Controller: ${legalIdentity.controller} (${legalIdentity.country}). Contact: ${legalIdentity.publicEmail}.`,
            )}
          </p>
          <div>
            <button
              className="button secondary"
              onClick={() => setDetails(true)}
            >
              {t("Ver detalles", "See details")}
            </button>
            <button className="button primary" onClick={dismiss}>
              {t("Solo lo necesario", "Necessary only")}
            </button>
          </div>
          <Link href="/gdpr">
            {t("Tus datos y derechos", "Your data and rights")}
          </Link>
        </aside>
      )}
      {details && (
        <Dialog
          title={t("Privacidad y preferencias", "Privacy and preferences")}
          onClose={() => setDetails(false)}
          className="privacy-details"
        >
          <span className="publication-note">
            <Info size={14} />
            {t(
              "Información de esta superficie pública",
              "Information about this public surface",
            )}
          </span>
          <h3>
            {t("Preferencias en tu navegador", "Preferences in your browser")}
          </h3>
          <p>
            {t(
              "El idioma se conserva hasta que lo cambies o borres los datos del sitio. La visualización del aviso se recuerda hasta 180 días. Puedes abrir estos detalles cuando quieras desde Privacidad.",
              "Your language remains until you change it or clear site data. Notice dismissal is remembered for up to 180 days. Open these details whenever you want through Privacy.",
            )}
          </p>
          <h3>
            {t(
              "Sin tecnologías opcionales activas",
              "No optional technologies active",
            )}
          </h3>
          <p>
            {t(
              "Esta aplicación no integra píxeles de publicidad ni herramientas de analítica. Las fuentes tipográficas y las imágenes se sirven localmente. Cerrar este aviso no activa seguimiento ni supone aceptar un contrato.",
              "This application integrates no advertising pixels or analytics tools. Fonts and images are served locally. Closing this notice activates no tracking and does not accept a contract.",
            )}
          </p>
          <p>
            {t(
              "Los formularios mantienen los borradores en la página y no los envían. El canal público de contacto es contacto@axignal.com. Este aviso describe el comportamiento verificable de esta superficie; no constituye una certificación de cumplimiento.",
              "Forms keep drafts in the page and do not send them. The public contact channel is contacto@axignal.com. This notice describes the verifiable behaviour of this surface; it is not a compliance certification.",
            )}
          </p>
          <div className="privacy-document-links">
            <Link href="/policies/cookies">
              {t("Cookies y almacenamiento", "Cookies and storage")}
            </Link>
            <Link href="/policies/privacy">
              {t("Política de privacidad", "Privacy policy")}
            </Link>
            <Link href="/gdpr">
              {t("Tus datos y derechos", "Your data and rights")}
            </Link>
          </div>
          <button className="button primary" onClick={dismiss}>
            {t("Mantener solo lo necesario", "Keep necessary only")}
          </button>
        </Dialog>
      )}
    </>
  );
}
