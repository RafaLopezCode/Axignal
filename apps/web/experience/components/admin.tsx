"use client";
import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { ArrowUpRight, ChevronRight, Eye, LockKeyhole, Menu, X } from "lucide-react";
import { CustomerZero } from "./customer-zero";
import { CustomerAccessPanel } from "./customer-access";

import { adminDomains, connectedDomains } from "@/lib/admin-model";
import { useLocale } from "@/lib/locale";
import { Brand, IconButton, LocaleToggle, useFocusTrap } from "./ui";

const CUSTOMER_ZERO = "customer-zero";
const GROUPS = [
  { id: "observe", es: "OBSERVAR", en: "OBSERVE" },
  { id: "operate", es: "OPERAR", en: "OPERATE" },
  { id: "govern", es: "GOBERNAR", en: "GOVERN" },
] as const;

/**
 * The Admin shell: one sidebar and one top bar. Customer Zero is the Admin's own AXIGNAL, mounted as the
 * product; its portfolio navigation is drawn in this sidebar, under its entry. The other domains are
 * functional panels over authorized services, with no sample records.
 */
export function Admin({ initialDomain = CUSTOMER_ZERO }: { initialDomain?: string }) {
  const { t, copy } = useLocale();
  const known = (id: string) => id === CUSTOMER_ZERO || adminDomains.some(d => d.id === id);
  const [domainId, setDomainId] = useState<string>(known(initialDomain) ? initialDomain : CUSTOMER_ZERO);
  const [mobile, setMobile] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);
  const [productNavigationHost, setProductNavigationHost] = useState<HTMLDivElement | null>(null);
  const [productToolbarHost, setProductToolbarHost] = useState<HTMLDivElement | null>(null);
  useFocusTrap(mobile, sidebarRef, () => setMobile(false));
  // An open drawer is modal: the page behind it does not scroll.
  useEffect(() => {
    if (!mobile) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previous; };
  }, [mobile]);
  const inProduct = domainId === CUSTOMER_ZERO;
  const domain = adminDomains.find(d => d.id === domainId);

  useEffect(() => {
    const navigate = () => {
      const id = window.location.hash.slice(1);
      // Content anchors (for example the skip link) do not change Admin domains; a retired id opens Customer Zero.
      if (id && !known(id) && id !== "main") return;
      const next = known(id) ? id : CUSTOMER_ZERO;
      setDomainId(next);
      setMobile(false);
    };
    navigate();
    window.addEventListener("hashchange", navigate);
    window.addEventListener("popstate", navigate);
    return () => {
      window.removeEventListener("hashchange", navigate);
      window.removeEventListener("popstate", navigate);
    };
  }, []);

  function choose(id: string) {
    // The home is the address itself, /admin; the other domains hang from it as /admin#domain.
    window.history.pushState(null, "", id === CUSTOMER_ZERO ? "/admin" : "/admin#" + id);
    setDomainId(id);
    setMobile(false);
  }

  return (
    <div className={"product-shell admin-shell " + (inProduct ? "admin-using-product" : "")}>
      {mobile && <div className="admin-scrim" aria-hidden="true" onClick={() => setMobile(false)} />}
      <aside
        ref={sidebarRef}
        role={mobile ? "dialog" : "complementary"}
        aria-label={t("Navegación Admin", "Admin navigation")}
        aria-modal={mobile ? true : undefined}
        className={"product-sidebar " + (mobile ? "mobile-open" : "")}
      >
        <div className="sidebar-brand">
          <Brand />
          <IconButton
            className="mobile-only"
            label={t("Cerrar navegación", "Close navigation")}
            onClick={() => setMobile(false)}
          >
            <X size={19} />
          </IconButton>
        </div>
        <div className="admin-plane">
          <LockKeyhole size={17} aria-hidden="true" />
          <div>
            <strong>AXIGNAL Admin</strong>
            <span>{t("Operaciones privadas", "Private operations")}</span>
          </div>
        </div>
        <nav aria-label={t("Secciones de Admin", "Admin sections")}>
          <div ref={setProductNavigationHost} className="admin-product-navigation" />
          {GROUPS.map(group => (
            <div className="admin-nav-group" key={group.id}>
              <span className="nav-group-label">{t(group.es, group.en)}</span>
              {adminDomains.filter(d => d.group === group.id).map(d => (
                <button
                  key={d.id}
                  className={"admin-nav-item " + (domainId === d.id ? "active" : "")}
                  aria-current={domainId === d.id ? "page" : undefined}
                  onClick={() => choose(d.id)}
                >
                  {copy(d.name)}
                  <ChevronRight size={14} aria-hidden="true" />
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <Link href="/admin#command" className="nav-item">
            <Eye size={17} aria-hidden="true" />
            {t("Centro de atención", "Attention centre")}
          </Link>
          <Link href="/design" className="sidebar-system">
            {t("Sistema AXIGNAL", "AXIGNAL system")}
            <ArrowUpRight size={12} aria-hidden="true" />
          </Link>
        </div>
      </aside>
      <div className="product-workspace">
        <header className="product-topbar">
          <div className="admin-product-toolbar" ref={setProductToolbarHost} hidden={!inProduct} />
          {inProduct ? (
            <IconButton className="mobile-only" label={t("Navegación Admin", "Admin navigation")} onClick={() => setMobile(true)}>
              <Menu size={20} />
            </IconButton>
          ) : (
            <>
              <div className="navigation-controls">
                <IconButton className="mobile-only" label={t("Navegación Admin", "Admin navigation")} onClick={() => setMobile(true)}>
                  <Menu size={20} />
                </IconButton>
                <span className="breadcrumb-root">Admin</span>
                <ChevronRight size={12} aria-hidden="true" />
                <span className="breadcrumb-family">{domain ? copy(domain.name) : ""}</span>
              </div>
              <div className="topbar-right">
                <LocaleToggle />
              </div>
            </>
          )}
        </header>
        <div className="workspace-content">
          {(
            <div
              id={inProduct ? "main" : "customer-zero-region"}
              className="admin-product-host"
              hidden={!inProduct}
              tabIndex={-1}
            >
              <CustomerZero embedded active={inProduct} navigationHost={productNavigationHost} toolbarHost={productToolbarHost} onNavigate={() => { if (!inProduct) choose(CUSTOMER_ZERO); setMobile(false); }} />
            </div>
          )}
          {domain && (
            <main id="main" className="admin-panel" tabIndex={-1}>
              <header className="admin-panel-head">
                <h1>{copy(domain.name)}</h1>
                <p>{copy(domain.question)}</p>
              </header>
              {domain.id === "customers" && <CustomerAccessPanel />}
              {!connectedDomains.has(domain.id) && (
                <section className="admin-notice" aria-labelledby="admin-notice-title">
                  <h2 id="admin-notice-title">{t("Todavía no conectado a esta interfaz", "Not connected to this interface yet")}</h2>
                  <p>{t("Esta superficie leerá el servicio", "This surface will read the service")} <code>{domain.service}</code>. {t("Hasta entonces no se muestra ningún registro: un dato de ejemplo no sustituye a una lectura real.", "Until then no record is shown: sample data does not stand in for a real reading.")}</p>
                </section>
              )}
            </main>
          )}
        </div>
      </div>
    </div>
  );
}
