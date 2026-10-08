"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { ShieldCheck, Info } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { Dialog } from "./ui";
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
            "Privacidad en esta versión",
            "Privacy in this version",
          )}
        >
          <div className="privacy-notice-heading">
            <ShieldCheck size={21} />
            <h2>{t("Una visita, con claridad.", "A visit, with clarity.")}</h2>
          </div>
          <p>
            {t(
              "Responsable: AXIGNAL · España. La página recuerda tu idioma y este aviso. El acceso utiliza cookies necesarias cuando te autenticas con un proveedor disponible; Admin tiene su sesión separada. Contacto y GDPR sólo registran datos cuando envías una solicitud por un canal habilitado.",
              "Controller: AXIGNAL · Spain. The page remembers your language and this notice. Access uses necessary cookies when you authenticate with an available provider; Admin has a separate session. Contact and GDPR register details only when you submit a request through an enabled channel.",
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
              "Información del servicio",
              "Service information",
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
              "Las solicitudes de Contacto y GDPR se conservan 90 días. La entrega depende de un canal autorizado por AXIGNAL y puede fallar después del registro. El recibo no garantiza entrega ni resolución.",
              "Contact and GDPR requests are retained for 90 days. Delivery depends on an AXIGNAL-authorized channel and may fail after registration. The receipt does not guarantee delivery or resolution.",
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
