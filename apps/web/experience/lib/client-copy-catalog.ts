import { use } from "react";
import type { Locale } from "./languages";

type Catalog = Record<string, string>;
const loaders = {
  de: () =>
    import("./translation-delivery/de.json").then((module) => module.default),
  pt: () =>
    import("./translation-delivery/pt.json").then((module) => module.default),
  fr: () =>
    import("./translation-delivery/fr.json").then((module) => module.default),
  it: () =>
    import("./translation-delivery/it.json").then((module) => module.default),
};
const requests = new Map<Locale, Promise<Catalog>>();
function loadCatalog(locale: keyof typeof loaders): Promise<Catalog> {
  let pending = requests.get(locale);
  if (!pending) {
    pending = loaders[locale]();
    requests.set(locale, pending);
  }
  return pending;
}

export function translateLoaded(
  es: string,
  en: string,
  locale: Locale,
  catalog?: Catalog,
): string {
  const value =
    locale === "es" ? es : locale === "en" ? en : (catalog?.[en] ?? en);
  return value.replace(/\bAXENT\b/g, "Axent");
}

/** A cached module resource keeps SSR and hydration in the requested language.
 * Spanish/English already arrive with each copy, so need no catalog download.
 * Other languages request one canonical column rather than all four.
 */
export function useTranslator(locale: Locale) {
  const catalog =
    locale === "es" || locale === "en" ? undefined : use(loadCatalog(locale));
  return (es: string, en: string) => translateLoaded(es, en, locale, catalog);
}
