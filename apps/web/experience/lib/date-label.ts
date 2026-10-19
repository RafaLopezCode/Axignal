import type { Locale } from "./languages";

const unsupportedDate: Record<Locale, string> = {
  es: "Sin fecha acreditada",
  en: "No supported date",
  de: "Kein belegtes Datum",
  pt: "Sem data comprovada",
  fr: "Aucune date étayée",
  it: "Nessuna data supportata",
};
export function dateLabel(date: string | null, locale: Locale) {
  const instant = date
    ? new Date(/^\d{4}-\d{2}-\d{2}$/.test(date) ? date + "T12:00:00Z" : date)
    : null;
  return instant && Number.isFinite(instant.getTime())
    ? new Intl.DateTimeFormat(locale === "en" ? "en-GB" : locale, {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }).format(instant)
    : unsupportedDate[locale];
}
