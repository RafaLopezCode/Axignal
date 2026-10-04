"use client";
import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { PublicShell } from "@/components/public-shell";
import { useLocale } from "@/lib/locale";

export default function PageError({ retry }: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  const { t } = useLocale();
  return <PublicShell className="public-recovery">
    <section className="recovery-copy">
      <span className="eyebrow">{t("Lectura interrumpida", "Reading interrupted")}</span>
      <h1>{t("Retomemos el hilo.", "Let's pick up the thread.")}</h1>
      <p>{t("No pudimos mostrar esta página. Puedes intentar recuperarla o volver al inicio. No repetiremos ninguna observación ni operación desde aquí.", "We could not display this page. Try recovering it or return home. We will not repeat any observation or operation from here.")}</p>
      <div className="recovery-actions">
        <button className="button primary" onClick={retry}><RefreshCw size={16} />{t("Volver a intentar", "Try again")}</button>
        <Link className="button secondary" href="/"><ArrowLeft size={16} />{t("Volver al inicio", "Return home")}</Link>
      </div>
    </section>
  </PublicShell>;
}
