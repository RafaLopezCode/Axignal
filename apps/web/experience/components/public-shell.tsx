"use client";
import { useLocale } from "@/lib/locale";
import type { PublicLocaleRoute as LocaleRoute } from "@/lib/public-navigation";
import { MiniFooter } from "./ui";
import { PublicHeader } from "./public-header";
import { BackToTop } from "./back-to-top";
export { PublicHeader } from "./public-header";

export function PublicShell({
  children,
  className = "",
  localeRoutes,
  landing = false,
  footer,
}: {
  children: React.ReactNode;
  className?: string;
  localeRoutes?: LocaleRoute[];
  landing?: boolean;
  footer?: React.ReactNode;
}) {
  return (
    <>
      <PublicHeader localeRoutes={localeRoutes} />
      <div className={"public-page " + className}>
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
    </>
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
