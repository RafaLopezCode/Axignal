import translations from "./translations.json";
import type { Locale } from "./languages";
export const translatedLanguages = ["de", "pt", "fr", "it"] as const;
const catalog: Record<string, string[]> = translations;
export function translate(es: string, en: string, locale: Locale): string {
  const human = (value: string) => value.replace(/\bAXENT\b/g, "Axent");
  if (locale === "es") return human(es);
  if (locale === "en") return human(en);
  const column = translatedLanguages.indexOf(locale);
  return human(catalog[en]?.[column] ?? en);
}
