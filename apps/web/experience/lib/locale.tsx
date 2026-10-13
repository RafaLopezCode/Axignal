"use client";
import { accountProfileSchema, type AccountProfile } from "./account-contracts";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import {
  DEFAULT_LOCALE,
  isLocale,
  resolveInitialLocale,
  type Locale,
  type Copy,
} from "./languages";
import { translate } from "./copy-catalog";
import { HOME_METADATA } from "./public-home-metadata";

export type { Locale, Copy } from "./languages";

const LocaleContext = createContext({
  profile: null as AccountProfile | null,
  profileLoading: false,
  profileSaving: false,
  profileError: false,
  reloadProfile: async () => {},
  saveProfile: async (_: {action:"locale";locale:Locale|null}|{action:"avatar";image:string}|{action:"remove_avatar"}) => false,
  resetProfile: () => {},
  reducedMotion: false,
  setReducedMotion: (_: boolean) => {},
  locale: DEFAULT_LOCALE,
  setLocale: (_: Locale) => {},
  t: (_es: string, en: string) => en,
  copy: (c: Copy) => c.en,
});

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // A language in the URL (/es, /en/knowledge…) is known before hydration, so the server renders
  // that page in its own language; saved and browser preferences only refine routes without one.
  const [locale, setLocalLocale] = useState<Locale>(() => {
    const routeLocale = pathname?.split("/")[1];
    return isLocale(routeLocale) ? routeLocale : DEFAULT_LOCALE;
  });
  const [ready, setReady] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  const [profile, setProfile] = useState<AccountProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState(false);
  const profileRef = useRef<AccountProfile | null>(null);
  const epoch = useRef(0);
  const choice = useRef(0);
  const saving = useRef(false);
  const profileRead = useRef(0);
  const resetProfile = () => { ++epoch.current; ++profileRead.current; saving.current=false; profileRef.current=null; setProfile(null); setProfileLoading(false); setProfileSaving(false); setProfileError(false); };
  async function reloadProfile() {
    const generation=epoch.current, selected=choice.current, request=++profileRead.current;
    setProfileLoading(true); setProfileError(false);
    try {
      const response=await fetch("/api/subscriber/profile",{cache:"no-store"});
      if (response.status === 401) { if(generation===epoch.current && request===profileRead.current) resetProfile(); return; }
      if (!response.ok) throw new Error("PROFILE_UNAVAILABLE");
      const value=accountProfileSchema.parse(await response.json());
      if(generation!==epoch.current || request!==profileRead.current) return;
      profileRef.current=value; setProfile(value); setProfileError(false);
      if (value.locale && selected===choice.current && !isLocale(pathname.split("/")[1])) setLocalLocale(value.locale);
    } catch { if(generation===epoch.current && request===profileRead.current) setProfileError(true); }
    finally { if(generation===epoch.current && request===profileRead.current) setProfileLoading(false); }
  }
  async function saveProfile(command:{action:"locale";locale:Locale|null}|{action:"avatar";image:string}|{action:"remove_avatar"}):Promise<boolean> {
    const current=profileRef.current, generation=epoch.current;
    if (!current || saving.current) return false;
    ++profileRead.current; setProfileLoading(false); saving.current=true; setProfileSaving(true); setProfileError(false);
    try {
      const response=await fetch("/api/subscriber/profile",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...command,version:current.version})});
      if(response.status===401) { if(generation===epoch.current) resetProfile(); return false; }
      if(!response.ok) { if(response.status===409) await reloadProfile(); throw new Error("PROFILE_NOT_SAVED"); }
      const value=accountProfileSchema.parse(await response.json());
      if(generation!==epoch.current) return false;
      profileRef.current=value; setProfile(value);
      if(command.action==="locale") setLocalLocale(value.locale ?? resolveInitialLocale({browserLanguages:navigator.languages}));
      return true;
    } catch { if(generation===epoch.current) setProfileError(true); return false; }
    finally { if(generation===epoch.current) {saving.current=false; setProfileSaving(false);} }
  }
  function changeLocale(value:Locale) {
    if(saving.current) return;
    ++choice.current; setLocalLocale(value);
    if(profileRef.current) void saveProfile({action:"locale",locale:value});
  }
  useEffect(() => { if(pathname.startsWith("/account")) void reloadProfile(); },[pathname]);

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

    setLocalLocale(
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
        setLocale: changeLocale,
        profile, profileLoading, profileSaving, profileError, reloadProfile, saveProfile, resetProfile,
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
