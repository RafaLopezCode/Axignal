"use client";
import { useEffect, useId, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ArrowRight, ArrowUpRight, Menu, X } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { locales, isLocale } from "@/lib/languages";
import { landingLanguagePath } from "@/lib/marketing-locale";
import { isLandingSurfacePath } from "@/lib/surface-style-path";
import { publicNavigation, publicNavigationCopy as c, type PublicLocaleRoute } from "@/lib/public-navigation";
import { funnelCta, track } from "@/lib/funnel-events";

/** The one public header. Render outside page skins so route CSS cannot recompose it.
 * Native disclosure keeps every destination usable before hydration or without JavaScript.
 */
export function PublicHeader({ localeRoutes }: { localeRoutes?: PublicLocaleRoute[] }) {
  const { locale, setLocale } = useLocale();
  const path = usePathname() ?? "/";
  const router = useRouter();
  const nav = publicNavigation(locale, path.endsWith("/landing-lab"));
  const disclosure = useRef<HTMLDetailsElement>(null);
  const summary = useRef<HTMLElement>(null);
  const previousPath = useRef(path);
  const [open, setOpen] = useState(false);
  const [hash, setHash] = useState("");
  const panelId = useId();
  const titleId = useId();
  const close = () => disclosure.current?.removeAttribute("open");

  useEffect(() => {
    // Preserve a native disclosure opened before hydration; close only on navigation.
    if (previousPath.current !== path) close();
    previousPath.current = path;
    setOpen(disclosure.current?.open ?? false);
    const sync = () => setHash(window.location.hash);
    sync();
    window.addEventListener("hashchange", sync);
    window.addEventListener("popstate", sync);
    return () => {
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("popstate", sync);
    };
  }, [path]);
  useEffect(() => {
    if (!open) return;
    const escape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      close();
      summary.current?.focus();
    };
    const outside = (event: PointerEvent) => {
      if (event.target instanceof Node && !disclosure.current?.contains(event.target)) close();
    };
    document.addEventListener("keydown", escape);
    document.addEventListener("pointerdown", outside);
    return () => {
      document.removeEventListener("keydown", escape);
      document.removeEventListener("pointerdown", outside);
    };
  }, [open]);
  const current = (href: string) => {
    const [pathname, fragment] = href.split("#");
    if (fragment) return (path === pathname || (path === "/" && pathname === `/${locale}`)) && hash === "#" + fragment ? "location" as const : undefined;
    return path === pathname || path.startsWith(pathname + "/") ? "page" as const : undefined;
  };
  const activate = (cta: typeof funnelCta.headerStart | typeof funnelCta.headerLogin) =>
    track({ kind: "CTA_ACTIVATED", surface: "landing", cta });
  const routeOptions = localeRoutes ?? locales.map(({ id }) => ({ locale: id, href: "" }));
  return (
    <header className="ax-site-header" data-axignal-global-header="v1">
      <div className="ax-site-bar">
        <a className="ax-site-brand" href={nav.home} aria-label="AXIGNAL">
          <img src="/brand/logo-light.svg" width={147} height={43} alt="" decoding="async" fetchPriority="low" />
        </a>
        <div className="ax-site-actions">

          <a className="ax-site-signin" href="/login" onClick={() => activate(funnelCta.headerLogin)}>{c.signIn[locale]}</a>
          <a className="ax-site-start" href="/signup" onClick={() => activate(funnelCta.headerStart)}>{c.start[locale]}<ArrowUpRight size={16} aria-hidden="true" /></a>
          <details ref={disclosure} className="ax-site-navigation" onToggle={event => setOpen(event.currentTarget.open)} onBlur={event => {
            if (event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) close();
          }}>
            <summary ref={summary} className="ax-site-menu" aria-controls={panelId}>
              <span>{c.menu[locale]}</span>
              <Menu className="ax-site-open-icon" size={21} aria-hidden="true" />
              <X className="ax-site-close-icon" size={21} aria-hidden="true" />
            </summary>
            <div className="ax-site-panel" id={panelId}>
              <div className="ax-site-panel-inner">
                <h2 className="sr-only" id={titleId}>{c.explore[locale]}</h2>
                <div className="ax-site-destinations">
                  <nav className="ax-site-chapters" aria-labelledby={titleId}>
                    {nav.chapters.map(link => <a key={link.href} href={link.href} aria-current={current(link.href)} onClick={close}>{link.label}<ArrowUpRight size={23} aria-hidden="true" /></a>)}
                  </nav>
                  <nav className="ax-site-pages" aria-label={c.resources[locale]}>
                    {nav.pages.map(link => <a key={link.href} href={link.href} aria-current={current(link.href)} onClick={close}>{link.label}<ArrowRight size={18} aria-hidden="true" /></a>)}
                    <a className="ax-site-example" href="/demo" onClick={close}>{c.example[locale]}<ArrowUpRight size={18} aria-hidden="true" /></a>
                  </nav>
                </div>
                <div className="ax-site-panel-bottom">
                  <nav className="ax-site-trust" aria-label={c.trust[locale]}>
                    {nav.trust.map(link => <a key={link.href} href={link.href} aria-current={current(link.href)} onClick={close}>{link.label}</a>)}
                  </nav>
                  <label className="ax-site-language">
                    <span>{c.language[locale]}</span>
                    <select aria-label={c.language[locale]} value={locale} onChange={(event) => {
                      const value = event.target.value;
                      if (!isLocale(value)) return;
                      close();
                      summary.current?.focus();
                      const route = localeRoutes?.find(item => item.locale === value);
                      if (route) router.push(route.href);
                      else if (isLandingSurfacePath(path)) router.push(landingLanguagePath(path, value, window.location.hash));
                      else setLocale(value);
                    }}>
                      {routeOptions.map(route => <option key={route.locale} value={route.locale} lang={route.locale}>{locales.find(item => item.id === route.locale)?.name ?? route.locale}</option>)}
                    </select>
                  </label>
                  <div className="ax-site-panel-actions">
                    <a className="ax-site-signin" href="/login" onClick={() => { close(); activate(funnelCta.headerLogin); }}>{c.signIn[locale]}</a>
                    <a className="ax-site-start" href="/signup" onClick={() => { close(); activate(funnelCta.headerStart); }}>{c.start[locale]}<ArrowUpRight size={16} aria-hidden="true" /></a>
                  </div>
                </div>
              </div>
            </div>
          </details>
        </div>
      </div>
    </header>
  );
}
