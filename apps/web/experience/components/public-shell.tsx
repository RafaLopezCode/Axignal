"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { ArrowUpRight, Menu, ArrowRight } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { Brand, LocaleToggle, Dialog, MiniFooter } from "./ui";

export function PublicHeader({ landing = false }: { landing?: boolean }) {
  const { t } = useLocale();
  const path = usePathname();
  const [menu, setMenu] = useState(false);
  const links = [
    {
      href: landing ? "#start" : "/#start",
      name: t("Cómo funciona", "How it works"),
    },
    { href: landing ? "#subscription" : "/#subscription", name: "Pricing" },
    { href: "/knowledge", name: "Knowledge" },
    { href: "/contact", name: t("Contacto", "Contact") },
    { href: "/policies", name: t("Confianza", "Trust") },
  ];
  return (
    <>
      <header className="landing-header public-header">
        <Brand />
        <nav aria-label={t("Principal", "Main")}>
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              aria-current={
                path.startsWith(link.href) &&
                link.href.startsWith("/") &&
                !link.href.includes("#")
                  ? "page"
                  : undefined
              }
            >
              {link.name}
            </Link>
          ))}
        </nav>
        <div className="header-actions">
          <LocaleToggle />
          <Link className="public-access-link" href="/login">
            {t("Acceder", "Sign in")}
            <ArrowUpRight size={15} />
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
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenu(false)}
              >
                {link.name}
                <ArrowRight size={18} />
              </Link>
            ))}
            <Link href="/gdpr" onClick={() => setMenu(false)}>
              {t("Tus datos y derechos", "Your data and rights")}
              <ArrowRight size={18} />
            </Link>
            <Link href="/panorama" onClick={() => setMenu(false)}>
              {t("Explorar la demo", "Explore the demo")}
              <ArrowRight size={18} />
            </Link>
          </nav>
        </Dialog>
      )}
    </>
  );
}
export function PublicShell({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={"public-page " + className}>
      <PublicHeader />
      <main id="main">{children}</main>
      <MiniFooter />
    </div>
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
        : t(
            "Borrador · pendiente de publicación",
            "Draft · pending publication",
          )}
    </span>
  );
}
