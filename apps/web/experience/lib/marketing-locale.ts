import type { Locale } from "./languages";

export type LocalizedText = Readonly<Record<Locale, string>>;
export function words(
  es: string,
  en: string,
  fr: string,
  de: string,
  it: string,
  pt: string,
): LocalizedText {
  return { es, en, fr, de, it, pt };
}

export function marketingPath(path: string, locale: Locale): string {
  return `/${locale}${path === "/" ? "" : path}`;
}
