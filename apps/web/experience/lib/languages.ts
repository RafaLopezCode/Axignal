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
export const isLocale = (value: unknown): value is Locale =>
  locales.some((l) => l.id === value);
