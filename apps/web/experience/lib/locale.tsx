"use client";
import { createContext, useContext, useEffect, useState } from "react";
export type Locale = "es" | "en";
export type Copy = { es: string; en: string };
const LocaleContext = createContext({
  reducedMotion: false,
  setReducedMotion: (_: boolean) => {},
  locale: "es" as Locale,
  setLocale: (_: Locale) => {},
  t: (es: string, _en: string) => es,
  copy: (c: Copy) => c.es,
});
export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocale] = useState<Locale>("es");
  const [reducedMotion, setReducedMotion] = useState(false);
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  useEffect(() => {
    document.documentElement.dataset.motion = reducedMotion
      ? "reduced"
      : "system";
  }, [reducedMotion]);
  return (
    <LocaleContext.Provider
      value={{
        reducedMotion,
        setReducedMotion,
        locale,
        setLocale,
        t: (es, en) => (locale === "es" ? es : en),
        copy: (c) => c[locale],
      }}
    >
      {children}
    </LocaleContext.Provider>
  );
}
export const useLocale = () => useContext(LocaleContext);
export const c = (es: string, en: string): Copy => ({ es, en });
