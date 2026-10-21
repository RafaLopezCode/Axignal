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
import { PublicBrandVector } from "./public-brand-vector";
import { BackToTop } from "./back-to-top";
import { marketingCopy, marketingPath } from "@/lib/marketing-content";
import { PUBLIC_EDITORIAL_LABEL } from "@/lib/marketing-locale";

type LocaleRoute = { locale: Locale; href: string };
export function PublicHeader({
  landing = false,
  localeRoutes,
  catalog = false,
}: {
  landing?: boolean;
  localeRoutes?: LocaleRoute[];
  catalog?: boolean;
}) {
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
  // what is it → show me → what does it cost → learn more → contact.
  // Trust and data rights also remain directly accessible in the menu/footer.
  const links = catalog
    ? [
        {
          href: marketingPath("/data", locale),
          name: marketingCopy.observe[locale],
        },
        {
          href: marketingPath("/industries", locale),
          name: marketingCopy.sectors[locale],
        },
        {
          href: marketingPath("/pricing", locale),
          name: marketingCopy.price[locale],
        },
        { href: marketingPath("/knowledge", locale), name: PUBLIC_EDITORIAL_LABEL },
      ]
    : [
        {
          href: landing ? "#how" : marketingPath("/", locale) + "#how",
          name: t("Cómo funciona", "How it works"),
        },
        { href: "/demo", name: t("Ejemplo", "Example") },
        {
          href: landing ? "#pricing" : marketingPath("/", locale) + "#pricing",
          name: t("Precio", "Pricing"),
        },
        {
          href: marketingPath("/knowledge", locale),
          name: PUBLIC_EDITORIAL_LABEL,
        },
      ];
  links.push({ href: "/contact", name: t("Contacto", "Contact") });
  const secondary = [
    {
      href: "/policies",
      name: t("Confianza y políticas", "Trust and policies"),
    },
    { href: "/gdpr", name: t("Tus datos y derechos", "Your data and rights") },
  ];
  const languages = localeRoutes ? (
    <LocaleRouteSelector routes={localeRoutes} locale={locale} />
  ) : (
    <LocaleToggle />
  );
  return (
    <>
      <header className="landing-header public-header">
        {catalog ? (
          <Link prefetch={false}
            className="brand"
            href={marketingPath("/", locale)}
            aria-label={`AXIGNAL · ${marketingCopy.observation[locale]}`}
          >
            <PublicBrandVector />
          </Link>
        ) : (
          <Brand href={marketingPath("/", locale)} />
        )}
        <nav aria-label={t("Principal", "Main")}>
          {links.map((link) => (
            <Link prefetch={false}
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
          <Link prefetch={false}
            className="public-login-link"
            href="/login"
            onClick={() =>
              track({
                kind: "CTA_ACTIVATED",
                surface: "landing",
                cta: funnelCta.headerLogin,
              })
            }
          >
            {t("Acceder", "Sign in")}
          </Link>
          <Link prefetch={false}
            className="public-access-link"
            href="/signup"
            onClick={() =>
              track({
                kind: "CTA_ACTIVATED",
                surface: "landing",
                cta: funnelCta.headerStart,
              })
            }
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
              <Link prefetch={false}
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
            <Link prefetch={false} href="/login" onClick={() => setMenu(false)}>
              {t("Acceder", "Sign in")}
              <ArrowRight size={18} />
            </Link>
            <Link prefetch={false} className="public-access-link" href="/signup" onClick={() => setMenu(false)}>
              {t("Empezar", "Get started")}
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
  landing = false,
  catalog = false,
  footer,
}: {
  children: React.ReactNode;
  className?: string;
  localeRoutes?: LocaleRoute[];
  landing?: boolean;
  catalog?: boolean;
  footer?: React.ReactNode;
}) {
  return (
    <div className={"public-page " + className}>
      <PublicHeader
        landing={landing}
        localeRoutes={localeRoutes}
        catalog={catalog}
      />
      <main
        id="main"
        className={landing ? "public-main public-main-landing" : "public-main"}
        tabIndex={-1}
      >
        {children}
      </main>
      {footer ?? <MiniFooter />}
      <BackToTop />
    </div>
  );
}
function LocaleRouteSelector({
  routes,
  locale,
}: {
  routes: LocaleRoute[];
  locale: Locale;
}) {
  const router = useRouter();
  const { t } = useLocale();
  const current = routes.find((route) => route.locale === locale) ?? routes[0];
  if (!current) return null;
  return (
    <label className="locale-selector locale-route-selector">
      <span className="sr-only">{t("Idioma", "Language")}</span>
      <select
        aria-label={t(
          "Cambiar idioma de esta lectura",
          "Change this reading's language",
        )}
        value={current.locale}
        onChange={(event) => {
          const route = routes.find(
            (option) => option.locale === event.target.value,
          );
          if (route) router.push(route.href);
        }}
      >
        {routes.map((route) => (
          <option key={route.locale} value={route.locale} lang={route.locale}>
            {locales.find((item) => item.id === route.locale)?.name ??
              route.locale}
          </option>
        ))}
      </select>
    </label>
  );
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
        : t("AXIGNAL · España", "AXIGNAL · Spain")}
    </span>
  );
}
