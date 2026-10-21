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

export const PUBLIC_EDITORIAL_LABEL = "Blog · Knowledge";

/** Public language changes stay public; the isolated preview keeps its own route. */
export function landingLanguagePath(path: string, locale: Locale, hash = ""): string {
  return marketingPath(path.endsWith("/landing-lab") ? "/landing-lab" : "/", locale) + hash;
}
