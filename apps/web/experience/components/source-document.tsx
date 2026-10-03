"use client";
import Link from "next/link";
import { Brand, LocaleToggle, DemoLabel } from "./ui";
import { useLocale } from "@/lib/locale";
import { dateLabel, type Evidence } from "@/lib/projection";
export function SourceDocument({ item }: { item: Evidence }) {
  const { copy, t, locale } = useLocale();
  return (
    <div className="document-page">
      <header>
        <Brand />
        <LocaleToggle />
      </header>
      <main id="main">
        <DemoLabel />
        <span className="eyebrow">
          {t(
            "Documento de demostración / " + item.id,
            "Demonstration document / " + item.id,
          )}
        </span>
        <h1>{copy(item.title)}</h1>
        <p className="document-deck">{copy(item.source)}</p>
        <p className="mono">
          {t("Publicado:", "Published:")} {dateLabel(item.publishedAt, locale)}{" "}
          / {t("Observado:", "Observed:")} {dateLabel(item.observedAt, locale)}
        </p>
        <hr />
        <h2>{t("Contenido ilustrativo", "Illustrative content")}</h2>
        <p>{copy(item.body)}</p>
        <h2>{t("Base y alcance", "Basis and scope")}</h2>
        <p>{copy(item.basis)}</p>
        {item.instrument && <p>{copy(item.instrument)}</p>}
        <blockquote>{copy(item.limitation)}</blockquote>
        <p>
          {t(
            "Esta página es una fuente ficticia para revisar la experiencia. No corresponde a un documento real ni acredita un hecho económico.",
            "This page is a fictional source for reviewing the experience. It does not correspond to a real document or establish an economic fact.",
          )}
        </p>
        <Link className="button secondary" href="/panorama">
          {t("Volver al Panorama", "Return to Panorama")}
        </Link>
      </main>
    </div>
  );
}
