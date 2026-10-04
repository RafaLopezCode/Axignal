"use client";
import Link from "next/link";
import { ArrowLeft, BookOpen } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { PublicShell } from "@/components/public-shell";

export default function NotFound() {
  const { t } = useLocale();
  return (
    <PublicShell className="public-not-found">
      <section className="recovery-scene">
        <div className="recovery-copy">
        <span className="eyebrow">
          404 / {t("Página no disponible", "Page unavailable")}
        </span>

        <h1>{t("Sigamos otro hilo.", "Let's follow another thread.")}</h1>
        <p>
          {t(
            "No encontramos esta página. Puedes volver al inicio o abrir el cuaderno para seguir explorando.",
            "We could not find this page. Return home or open the notebook to keep exploring.",
          )}
        </p>
        <div className="recovery-actions">
          <Link className="button primary" href="/">
            <ArrowLeft size={16} />
            {t("Volver al inicio", "Return home")}
          </Link>
          <Link className="button secondary" href="/knowledge">
            <BookOpen size={16} />
            {t("Abrir el cuaderno", "Open the notebook")}
          </Link>
        </div>
        </div>
        <figure className="recovery-art">
          <span className="recovery-code" aria-hidden="true">404</span>
          <img src="/observer/not-found-map.png" width={1024} height={1536} alt="" />
        </figure>
      </section>
    </PublicShell>
  );
}
