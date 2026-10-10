"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import {
  DEFAULT_LOCALE,
  resolveInitialLocale,
  type Locale,
  type Copy,
} from "./languages";
import { translate } from "./copy-catalog";
import { HOME_METADATA } from "./public-home-metadata";

export type { Locale, Copy } from "./languages";

const LocaleContext = createContext({
  reducedMotion: false,
  setReducedMotion: (_: boolean) => {},
  locale: DEFAULT_LOCALE,
  setLocale: (_: Locale) => {},
  t: (_es: string, en: string) => en,
  copy: (c: Copy) => c.en,
});

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [locale, setLocale] = useState<Locale>(DEFAULT_LOCALE);
  const [ready, setReady] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    let savedLocale: string | null = null;
    try {
      savedLocale = localStorage.getItem("axignal.locale.v1");
    } catch {}

    const routeLocale = pathname.split("/")[1];
    const browserLanguages =
      typeof navigator === "undefined"
        ? []
        : navigator.languages.length
          ? navigator.languages
          : [navigator.language];

    setLocale(
      resolveInitialLocale({
        routeLocale,
        savedLocale,
        browserLanguages,
      }),
    );
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
    if (pathname !== "/") return;
    const home = HOME_METADATA[locale];
    const sync = () => {
      // Next may insert static server metadata after client hydration. Keep the
      // visible title aligned with the reader's language without fighting other routes.
      if (document.title !== home.title) document.title = home.title;
      const ensure = (selector: string, value: string) => {
        const meta = document.querySelector(selector);
        if (meta?.getAttribute("content") !== value) meta?.setAttribute("content", value);
      };
      ensure('meta[name="description"]', home.description);
      ensure('meta[property="og:title"]', home.title);
      ensure('meta[property="og:description"]', home.description);
    };
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.head, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, [locale, pathname]);

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
