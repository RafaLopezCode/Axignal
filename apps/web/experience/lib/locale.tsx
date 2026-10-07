"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { isLocale, type Locale, type Copy } from "./languages";
import { translate } from "./copy-catalog";
export type { Locale, Copy } from "./languages";
const LocaleContext = createContext({
  reducedMotion: false,
  setReducedMotion: (_: boolean) => {},
  locale: "es" as Locale,
  setLocale: (_: Locale) => {},
  t: (es: string, _en: string) => es,
  copy: (c: Copy) => c.es,
});
export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [locale, setLocale] = useState<Locale>("es");
  const [ready, setReady] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  useEffect(() => {
    try {
      const routeLocale = pathname.split("/")[1];
      if (isLocale(routeLocale)) {
        setLocale(routeLocale);
      } else {
        const saved = localStorage.getItem("axignal.locale.v1");
        if (isLocale(saved)) setLocale(saved);
      }
    } catch {}
    setReady(true);
  }, [pathname]);
  useEffect(() => {
    document.documentElement.lang = locale;
    if (ready) {
      try {
        localStorage.setItem("axignal.locale.v1", locale);
      } catch {}
    }
  }, [locale, ready]);
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
        t: (es, en) => translate(es, en, locale),
        copy: (c) => translate(c.es, c.en, locale),
      }}
    >
      {children}
    </LocaleContext.Provider>
  );
}
export const useLocale = () => useContext(LocaleContext);
export const c = (es: string, en: string): Copy => ({ es, en });
