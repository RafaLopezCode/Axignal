export const locales = [
  { id: "es", name: "Español" },
  { id: "en", name: "English" },
  { id: "de", name: "Deutsch" },
  { id: "pt", name: "Português" },
  { id: "fr", name: "Français" },
  { id: "it", name: "Italiano" },
] as const;

export type Locale = (typeof locales)[number]["id"];
export type Copy = { es: string; en: string };

export const DEFAULT_LOCALE: Locale = "en";

export const isLocale = (value: unknown): value is Locale =>
  locales.some((locale) => locale.id === value);

export function localeFromLanguageTags(tags: readonly string[]): Locale | null {
  for (const tag of tags) {
    const normalized = tag.trim().toLowerCase().replace("_", "-");
    if (!normalized) continue;
    const exact = normalized.split("-")[0];
    if (isLocale(exact)) return exact;
  }
  return null;
}

export function resolveInitialLocale({
  routeLocale,
  savedLocale,
  browserLanguages,
}: {
  routeLocale?: unknown;
  savedLocale?: unknown;
  browserLanguages?: readonly string[];
}): Locale {
  if (isLocale(routeLocale)) return routeLocale;
  if (isLocale(savedLocale)) return savedLocale;
  return localeFromLanguageTags(browserLanguages ?? []) ?? DEFAULT_LOCALE;
}
