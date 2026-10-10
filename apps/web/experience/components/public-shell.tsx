"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, ArrowRight } from "lucide-react";
import { funnelCta, track } from "@/lib/funnel-events";
import { useLocale } from "@/lib/locale";
import { locales, type Locale } from "@/lib/languages";
import { useRouter } from "next/navigation";
import { Brand, LocaleToggle, Dialog, MiniFooter } from "./ui";

type LocaleRoute = { locale: Locale; href: string };
export function PublicHeader({ landing = false, localeRoutes }: { landing?: boolean; localeRoutes?: LocaleRoute[] }) {
  const { t, locale } = useLocale();
  const path = usePathname();
  const [menu, setMenu] = useState(false);
  const [hash, setHash] = useState("");
  useEffect(() => {
    const syncHash = () => setHash(window.location.hash);
    syncHash();
    window.addEventListener("hashchange", syncHash);
    window.addEventListener("popstate", syncHash);
    return () => {
      window.removeEventListener("hashchange", syncHash);
      window.removeEventListener("popstate", syncHash);
    };
  }, [path]);
  const isCurrentPage = (href: string) =>
    !href.includes("#") && (path === href || path.startsWith(href + "/"));
  const currentFor = (href: string) => {
    const fragment = href.indexOf("#");
    if (fragment >= 0)
      return path === "/" && hash === href.slice(fragment)
        ? ("location" as const)
        : undefined;
    return isCurrentPage(href) ? ("page" as const) : undefined;
  };
  const selectLink = (href: string) => {
    if (href.includes("#")) setHash(href.slice(href.indexOf("#")));
  };
  // The header follows the visitor's questions, not the architecture:
  // what is it → show me → what does it cost → learn more. Contact, trust and data
  // rights live in the footer and the menu, where people look for them.
  const links = [
    { href: landing ? "#how" : "/#how", name: t("Cómo funciona", "How it works") },
    { href: "/demo", name: t("Ejemplo", "Example") },
    { href: landing ? "#pricing" : "/#pricing", name: t("Precio", "Pricing") },
    { href: localeRoutes?.find((route) => route.locale === locale)?.href ?? "/knowledge", name: "Knowledge" },
  ];
  const secondary = [
    { href: "/contact", name: t("Contacto", "Contact") },
    { href: "/policies", name: t("Confianza y políticas", "Trust and policies") },
    { href: "/gdpr", name: t("Tus datos y derechos", "Your data and rights") },
  ];
  const languages = localeRoutes ? <LocaleRouteSelector routes={localeRoutes} locale={locale} /> : <LocaleToggle />;
  return (
    <>
      <header className="landing-header public-header">
        <Brand />
        <nav aria-label={t("Principal", "Main")}>
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              aria-current={currentFor(link.href)}
              onClick={() => selectLink(link.href)}
            >
              {link.name}
            </Link>
          ))}
        </nav>
        <div className="header-actions">
          <span className="header-languages">{languages}</span>
          <Link
            className="public-login-link"
            href="/login"
            onClick={() => track({ kind: "CTA_ACTIVATED", surface: "landing", cta: funnelCta.headerLogin })}
          >
            {t("Acceder", "Sign in")}
          </Link>
          <Link
            className="public-access-link"
            href="/signup"
            onClick={() => track({ kind: "CTA_ACTIVATED", surface: "landing", cta: funnelCta.headerStart })}
          >
            {t("Empezar", "Get started")}
            <ArrowRight size={15} />
          </Link>
          <button
            className="icon-button public-menu-button"
            onClick={() => setMenu(true)}
            aria-label={t("Abrir navegación", "Open navigation")}
          >
            <Menu size={21} />
          </button>
        </div>
      </header>
      {menu && (
        <Dialog
          title={t("Explora AXIGNAL", "Explore AXIGNAL")}
          onClose={() => setMenu(false)}
          className="public-menu"
        >
          <nav aria-label={t("Navegación móvil", "Mobile navigation")}>
            {[...links, ...secondary].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={currentFor(link.href)}
                onClick={() => {
                  selectLink(link.href);
                  setMenu(false);
                }}
              >
                {link.name}
                <ArrowRight size={18} />
              </Link>
            ))}
            <Link href="/login" onClick={() => setMenu(false)}>
              {t("Acceder", "Sign in")}
              <ArrowRight size={18} />
            </Link>
          </nav>
          <div className="public-menu-languages">{languages}</div>
        </Dialog>
      )}
    </>
  );
}
export function PublicShell({
  children,
  className = "",
  localeRoutes,
}: {
  children: React.ReactNode;
  className?: string;
  localeRoutes?: LocaleRoute[];
}) {
  return (
    <div className={"public-page " + className}>
      <PublicHeader localeRoutes={localeRoutes} />
      <main id="main" tabIndex={-1}>{children}</main>
      <MiniFooter />
    </div>
  );
}
function LocaleRouteSelector({ routes, locale }: { routes: LocaleRoute[]; locale: Locale }) {
  const router = useRouter();
  const { t } = useLocale();
  const current = routes.find((route) => route.locale === locale) ?? routes[0];
  if (!current) return null;
  return <label className="locale-selector locale-route-selector">
    <span className="sr-only">{t("Idioma", "Language")}</span>
    <select aria-label={t("Cambiar idioma de esta lectura", "Change this reading's language")} value={current.locale} onChange={(event) => {
      const route = routes.find((option) => option.locale === event.target.value);
      if (route) router.push(route.href);
    }}>
      {routes.map((route) => <option key={route.locale} value={route.locale} lang={route.locale}>{locales.find((item) => item.id === route.locale)?.name ?? route.locale}</option>)}
    </select>
  </label>;
}
export function PublicationNote({
  editorial = false,
}: {
  editorial?: boolean;
}) {
  const { t } = useLocale();
  return (
    <span className="publication-note">
      <span aria-hidden="true" />
      {editorial
        ? t("Cuaderno editorial · borrador", "Editorial notebook · draft")
        : t(
            "AXIGNAL · España",
            "AXIGNAL · Spain",
          )}
    </span>
  );
}
