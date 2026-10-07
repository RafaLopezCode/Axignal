"use client";
import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { CustomerZero } from "./customer-zero";
import {
  ArrowUpRight,
  ArrowRight,
  LockKeyhole,
  Menu,
  X,
  Search,
  Filter,
  ShieldCheck,
  BookOpen,
  Info,
  ChevronRight,
  RotateCcw,
  Eye,
} from "lucide-react";
import {
  adminDomains,
  adminRecords,
  type AdminRecord,
} from "@/lib/admin-model";
import { useLocale } from "@/lib/locale";
import {
  Brand,
  AxentIdentity,
  LocaleToggle,
  DemoLabel,
  Dialog,
  IconButton,
  useFocusTrap,
} from "./ui";

export function Admin({
  initialDomain = "command",
}: {
  initialDomain?: "command" | "customer-zero";
}) {
  const { t, copy } = useLocale();
  const [domainId, setDomainId] = useState<string>(initialDomain),
    [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all"),
    [mobile, setMobile] = useState(false),
    [record, setRecord] = useState<AdminRecord | null>(null),
    [action, setAction] = useState<AdminRecord | null>(null),
    [denied, setDenied] = useState(false),
    [busy, setBusy] = useState(false),
    [guidance, setGuidance] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);
  const [productNavigationHost, setProductNavigationHost] = useState<HTMLDivElement | null>(null);
  const [productToolbarHost, setProductToolbarHost] = useState<HTMLDivElement | null>(null);
  const [productStarted, setProductStarted] = useState(
    initialDomain === "customer-zero",
  );
  useFocusTrap(mobile, sidebarRef, () => setMobile(false));
  const domain =
    domainId === "customer-zero"
      ? {
          name: {
            es: "AXIGNAL / Cliente cero",
            en: "AXIGNAL / Customer Zero",
          },
          question: { es: "Operaciones privadas", en: "Private operations" },
        }
      : adminDomains.find((d) => d.id === domainId)!;
  useEffect(() => {
    const navigate = () => {
      const id = window.location.hash.slice(1);
      // Content anchors (for example the skip link) do not change Admin domains.
      if (id && id !== "customer-zero" && !adminDomains.some((d) => d.id === id))
        return;
      const next = id === "customer-zero" || adminDomains.some((d) => d.id === id)
        ? id
        : window.location.pathname === "/admin/customer-zero"
          ? "customer-zero"
          : "command";
      if (next === "customer-zero") setProductStarted(true);
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
  const records = (
    domainId === "command"
      ? adminRecords.filter((r) => r.severity === "review")
      : adminRecords.filter((r) => r.domain === domainId)
  ).filter(
    (r) =>
      (filter === "all" || r.severity === filter) &&
      (copy(r.title) + " " + r.id).toLowerCase().includes(query.toLowerCase()),
  );
  function choose(id: string) {
    if (id === "customer-zero") setProductStarted(true);
    window.history.pushState(null, "", "/admin#" + id);
    setDomainId(id);
    setRecord(null);
    setQuery("");
    setFilter("all");
    setMobile(false);
    setGuidance(false);
  }
  async function verifyAuthority() {
    setBusy(true);
    try {
      const response = await fetch("/api/admin/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: action?.id }),
      });
      setDenied(response.status === 403);
    } catch {
      setDenied(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className={"product-shell admin-shell " +
      (domainId === "customer-zero" ? "admin-using-product" : "")}>
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
          <LockKeyhole size={17} />
          <div>
            <strong>AXIGNAL Admin</strong>
            <span>{t("Operaciones privadas", "Private operations")}</span>
          </div>
        </div>
        <nav>
          <div>
            <span className="nav-group-label">
              {t("USAR AXIGNAL", "USE AXIGNAL")}
            </span>
            <button
              className={
                "admin-nav-item " +
                (domainId === "customer-zero" ? "active" : "")
              }
              aria-current={domainId === "customer-zero" ? "page" : undefined}
              onClick={() => choose("customer-zero")}
            >
              <span className="admin-nav-line" />
              {t("AXIGNAL / Cliente cero", "AXIGNAL / Customer Zero")}
              <ChevronRight size={12} />
            </button>
          </div>
          <div ref={setProductNavigationHost} className="admin-product-navigation" hidden={domainId !== "customer-zero"} />
          <details className="admin-operations-navigation" open={domainId !== "customer-zero"}>
          <summary className="nav-group-label">{t("OPERAR AXIGNAL", "OPERATE AXIGNAL")}</summary>
          {["observe", "operate", "govern"].map((group) => (
            <div key={group}>
              <span className="nav-group-label">
                {group === "observe"
                  ? t("OBSERVAR", "OBSERVE")
                  : group === "operate"
                    ? t("OPERAR", "OPERATE")
                    : t("GOBERNAR", "GOVERN")}
              </span>
              {adminDomains
                .filter((d) => d.group === group)
                .map((d) => (
                  <button
                    className={
                      "admin-nav-item " + (domainId === d.id ? "active" : "")
                    }
                    key={d.id}
                    onClick={() => choose(d.id)}
                  >
                    <span className="admin-nav-line" />
                    {copy(d.name)}
                    <ChevronRight size={12} />
                  </button>
                ))}
            </div>
          ))}
          </details>
        </nav>
        <div className="sidebar-bottom">
          <Link
            href="/admin/customer-zero"
            className="nav-item"
          >
            <Eye size={17} />
            {t("Abrir producto por separado", "Open product separately")}
          </Link>
          <Link href="/design" className="sidebar-system">
            {t("Sistema AXIGNAL", "AXIGNAL system")}
            <ArrowUpRight size={12} />
          </Link>
        </div>
      </aside>
      <div className="product-workspace">
        <header className="product-topbar">
          <div className="admin-product-toolbar" ref={setProductToolbarHost} hidden={domainId !== "customer-zero"} />
          {domainId === "customer-zero" ? <IconButton className="mobile-only" label={t("Navegación Admin", "Admin navigation")} onClick={() => setMobile(true)}><Menu size={20} /></IconButton> : <>
          <div className="navigation-controls">
            <IconButton
              className="mobile-only"
              label={t("Navegación Admin", "Admin navigation")}
              onClick={() => setMobile(true)}
            >
              <Menu size={20} />
            </IconButton>
            <span className="breadcrumb-root">Admin</span>
            <ChevronRight size={12} />
            <span className="breadcrumb-family">{copy(domain.name)}</span>
          </div>
          <div className="topbar-right">
            {domainId === "customer-zero" ? (
              <span className="demo-label">
                <LockKeyhole size={12} />
                {t("Privado · producto real", "Private · real product")}
              </span>
            ) : (
              <DemoLabel privateMode />
            )}
            {domainId !== "customer-zero" && <LocaleToggle />}
            <span className="admin-session">
              <ShieldCheck size={15} />
              {t("Revisión local", "Local review")}
            </span>
          </div>
          </>}
        </header>
        <div className="workspace-content">
          {productStarted && (
            <div
              id={domainId === "customer-zero" ? "main" : "customer-zero-region"}
              className="admin-product-host"
              hidden={domainId !== "customer-zero"}
              tabIndex={-1}
            >
              <CustomerZero embedded navigationHost={productNavigationHost} toolbarHost={productToolbarHost} onNavigate={() => setMobile(false)} />
            </div>
          )}
          {domainId !== "customer-zero" && (
            <main id="main" className="panorama-main admin-main">
              <>
                <div className="panorama-intro">
                  <div>
                    <span className="eyebrow">
                      {t(
                        "PLANO OPERATIVO PRIVADO",
                        "PRIVATE OPERATIONAL PLANE",
                      )}
                    </span>
                    <h1>
                      {domainId === "command"
                        ? t(
                            "Atención, con autoridad.",
                            "Attention, with authority.",
                          )
                        : copy(domain.name)}
                    </h1>
                    <p>{copy(domain.question)}</p>
                  </div>
                  <span className="admin-readonly">
                    <LockKeyhole size={14} />
                    {t("Read models ilustrativos", "Illustrative read models")}
                  </span>
                </div>
                {domainId === "command" && <PilotTestAccounts />}
                {domainId === "command" && (
                  <div className="admin-attention">
                    <div>
                      <span className="eyebrow">
                        {t("LA REVISIÓN IMPORTA", "REVIEW MATTERS")}
                      </span>
                      <h2>
                        {t(
                          "Un cambio de fuente puede cambiar una lectura.",
                          "A source change can change a reading.",
                        )}
                      </h2>
                      <p>
                        {t(
                          "La operación correcta es reevaluar desde su servicio. Una interfaz no edita la verdad que observa.",
                          "The right operation is reassessment through its service. An interface does not edit the truth it observes.",
                        )}
                      </p>
                      <button
                        className="text-link"
                        onClick={() => {
                          choose("quality");
                          setRecord(
                            adminRecords.find((r) => r.domain === "quality")!,
                          );
                        }}
                      >
                        {t("Inspeccionar el caso", "Inspect the case")}
                        <ArrowRight size={17} />
                      </button>
                    </div>
                  </div>
                )}
                <div className="operational-boundary">
                  <ShieldCheck size={18} />
                  <span>
                    {t(
                      "Cada acción conserva alcance, servicio propietario y nivel de autoridad.",
                      "Every action retains scope, owning service and authority level.",
                    )}
                  </span>
                  <button
                    className="text-link"
                    onClick={() => setGuidance(true)}
                  >
                    {t("Entender el límite", "Understand the boundary")}
                    <ArrowUpRight size={14} />
                  </button>
                </div>
                <div className="admin-table-toolbar">
                  <label className="search-field">
                    <Search size={16} />
                    <input
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder={t(
                        "Buscar en esta vista…",
                        "Search this view…",
                      )}
                      aria-label={t(
                        "Buscar registros operativos",
                        "Search operational records",
                      )}
                    />
                  </label>
                  <label className="filter-field">
                    <Filter size={15} />
                    <select
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                      aria-label={t("Filtrar por estado", "Filter by state")}
                    >
                      <option value="all">
                        {t("Todos los estados", "All states")}
                      </option>
                      <option value="review">
                        {t("Necesita revisión", "Needs review")}
                      </option>
                      <option value="stable">
                        {t("Base conservada", "Basis retained")}
                      </option>
                      <option value="unknown">
                        {t("Información limitada", "Limited information")}
                      </option>
                    </select>
                  </label>
                </div>
                <div className="admin-records">
                  <div className="admin-table-head">
                    <span>{t("REGISTRO / CONTEXTO", "RECORD / CONTEXT")}</span>
                    <span>{t("ESTADO", "STATE")}</span>
                    <span>{t("AUTORIDAD", "AUTHORITY")}</span>
                  </div>
                  {records.length ? (
                    records.map((r) => (
                      <button
                        className={
                          "admin-record " +
                          (record?.id === r.id ? "selected" : "")
                        }
                        key={r.id}
                        onClick={() => {
                          setRecord(r);
                          setGuidance(false);
                        }}
                      >
                        <span className="admin-record-name">
                          <small className="mono">{r.id}</small>
                          <strong>{copy(r.title)}</strong>
                        </span>
                        <span
                          className={"operation-status status-" + r.severity}
                        >
                          {copy(r.status)}
                        </span>
                        <span className="authority-badge">
                          {r.authority}
                          <ArrowUpRight size={15} />
                        </span>
                      </button>
                    ))
                  ) : (
                    <div className="admin-no-results">
                      <p>
                        {t(
                          "No hay registros para este filtro.",
                          "No records match this filter.",
                        )}
                      </p>
                      <button
                        className="text-link"
                        onClick={() => {
                          setQuery("");
                          setFilter("all");
                        }}
                      >
                        {t("Limpiar filtros", "Clear filters")}
                        <RotateCcw size={14} />
                      </button>
                    </div>
                  )}
                </div>
                {record && (
                  <article className="admin-detail">
                    <div className="admin-detail-heading">
                      <span className="mono">
                        {record.id} /{" "}
                        {
                          adminDomains.find((d) => d.id === record.domain)
                            ?.service
                        }
                      </span>
                      <IconButton
                        label={t("Cerrar detalle", "Close detail")}
                        onClick={() => setRecord(null)}
                      >
                        <X size={17} />
                      </IconButton>
                    </div>
                    <h2>{copy(record.title)}</h2>
                    <p>{copy(record.detail)}</p>
                    <div className="admin-detail-facts">
                      <div>
                        <span>{t("Plano de datos", "Data plane")}</span>
                        <strong>
                          {t(
                            "Privado · operativo · ilustrativo",
                            "Private · operational · illustrative",
                          )}
                        </strong>
                      </div>
                      <div>
                        <span>
                          {t("Autoridad requerida", "Required authority")}
                        </span>
                        <strong>
                          {record.authority === "CRITICAL"
                            ? t(
                                "Dos principales distintos",
                                "Two distinct principals",
                              )
                            : record.authority === "SENSITIVE"
                              ? t(
                                  "Sesión privilegiada + step-up",
                                  "Privileged session + step-up",
                                )
                              : record.authority === "WRITE"
                                ? t(
                                    "Permiso de escritura y alcance",
                                    "Write permission and scope",
                                  )
                                : t("Lectura autorizada", "Authorized read")}
                        </strong>
                      </div>
                    </div>
                    <button
                      className="button secondary"
                      onClick={() => {
                        setAction(record);
                        setDenied(false);
                      }}
                    >
                      {copy(record.action)}
                      <ArrowRight size={16} />
                    </button>
                  </article>
                )}
                <div className="admin-lineage">
                  <BookOpen size={15} />
                  <div>
                    <strong>
                      {t(
                        "La interfaz observa el servicio.",
                        "The interface observes the service.",
                      )}
                    </strong>
                    <p>
                      {t(
                        "Esta aplicación local no tiene sesión privilegiada ni realiza operaciones reales. El servicio propietario conserva la autoridad.",
                        "This local app has no privileged session and performs no real operations. The owning service retains authority.",
                      )}
                    </p>
                  </div>
                </div>
              </>
            </main>
          )}
          {domainId !== "customer-zero" && (
            <aside className="axent-desktop admin-guide">
              <header className="axent-header">
                <AxentIdentity />
                <span className="admin-context-chip">
                  {t("Operación", "Operations")}
                </span>
              </header>
              <div className="axent-scope">
                <span className="mono">
                  {t(
                    "CONTEXTO PRIVILEGIADO SEPARADO",
                    "SEPARATE PRIVILEGED CONTEXT",
                  )}
                </span>
                <div>{copy(domain.name)}</div>
                <small>
                  {t(
                    "Guía ilustrativa · sin investigación en vivo",
                    "Illustrative guide · no live research",
                  )}
                </small>
              </div>
              <div className="admin-guide-content">
                <h2>
                  {guidance
                    ? t(
                        "La autoridad precede a la acción.",
                        "Authority comes before action.",
                      )
                    : t(
                        "Inspeccionemos antes de actuar.",
                        "Let’s inspect before acting.",
                      )}
                </h2>
                <p>{record ? copy(record.detail) : copy(domain.question)}</p>
                <div className="guide-authority">
                  <LockKeyhole size={18} />
                  <strong>
                    {t(
                      "La conversación no concede permisos.",
                      "Conversation does not grant permission.",
                    )}
                  </strong>
                  <p>
                    {t(
                      "El alcance y la sesión se validan en el servicio. Ni el rol visible ni una recomendación autorizan cambios.",
                      "Scope and session are validated in the service. Neither a visible role nor a recommendation authorizes changes.",
                    )}
                  </p>
                </div>
                <button
                  className="axent-question"
                  onClick={() => setGuidance(!guidance)}
                >
                  {guidance
                    ? t("Volver al contexto", "Return to context")
                    : t(
                        "¿Qué autoridad requiere?",
                        "What authority does it require?",
                      )}
                  <ArrowRight size={15} />
                </button>
                {guidance && (
                  <div className="guide-levels">
                    {["READ", "WRITE", "SENSITIVE", "CRITICAL"].map(
                      (level, i) => (
                        <div key={level}>
                          <span className="mono">{level}</span>
                          <p>
                            {
                              [
                                t(
                                  "Lectura tras autorización de alcance.",
                                  "Read after scope authorization.",
                                ),
                                t(
                                  "Permiso de comando en el servicio propietario.",
                                  "Command permission in the owning service.",
                                ),
                                t(
                                  "Sesión privilegiada y verificación adicional.",
                                  "Privileged session and additional verification.",
                                ),
                                t(
                                  "Aprobación de dos principales distintos.",
                                  "Approval by two distinct principals.",
                                ),
                              ][i]
                            }
                          </p>
                        </div>
                      ),
                    )}
                  </div>
                )}
              </div>
            </aside>
          )}
        </div>
        <footer className="admin-footer">
          <LockKeyhole size={13} />
          {t(
            "AXIGNAL · Operaciones propias · La información privada no es evidencia económica canónica.",
            "AXIGNAL · First-party operations · Private information is not canonical economic evidence.",
          )}
        </footer>
      </div>
      {action && (
        <Dialog title={copy(action.action)} onClose={() => setAction(null)}>
          <DemoLabel privateMode />
          <h3>{copy(action.title)}</h3>
          <p>{copy(action.detail)}</p>
          <div className="fact-row">
            <span>
              {t(
                "Proyección de lectura ilustrativa",
                "Illustrative read projection",
              )}
            </span>
            <strong>
              {adminDomains.find((d) => d.id === action.domain)?.service}
            </strong>
          </div>
          <div className="fact-row">
            <span>{t("Autoridad", "Authority")}</span>
            <strong>{action.authority}</strong>
          </div>
          <div className="fact-row">
            <span>{t("Autoridad propietaria", "Owning authority")}</span>
            <strong>
              {t(
                action.domain === "quality"
                  ? "EvidenceAdmission · conexión pendiente"
                  : "Servicio del dominio · conexión pendiente",
                action.domain === "quality"
                  ? "EvidenceAdmission · connection pending"
                  : "Domain service · connection pending",
              )}
            </strong>
          </div>
          <div className="fact-row">
            <span>{t("Alcance de esta revisión", "Scope of this review")}</span>
            <strong>
              {action.id} ·{" "}
              {copy(adminDomains.find((d) => d.id === action.domain)!.name)}
            </strong>
          </div>
          <div className="limit-note">
            <p>
              {t(
                "Impacto de esta demo: comprobar autoridad del comando. No escribe, concilia, aprueba ni altera registros. La ejecución real requeriría el contrato y la sesión del servicio propietario.",
                "Demo impact: check command authority. No records are written, reconciled, approved or altered. Real execution would require the owning service’s contract and session.",
              )}
            </p>
          </div>
          <div className="limit-note">
            <ShieldCheck size={19} />
            <p>
              {t(
                "Este panel prepara una revisión. Para ejecutar se necesita identidad privilegiada, alcance y autorización del servicio existente. La sesión de demo no los tiene.",
                "This panel prepares a review. Execution requires privileged identity, scope and authorization from the existing service. The demo session does not have them.",
              )}
            </p>
          </div>
          {denied ? (
            <div className="authority-denied" role="status">
              <LockKeyhole size={19} />
              <strong>
                {t("Sin autoridad de ejecución", "No execution authority")}
              </strong>
              <p>
                {t(
                  "El servidor denegó el comando. No se modificó ningún dato.",
                  "The server denied the command. No data was changed.",
                )}
              </p>
            </div>
          ) : (
            <button
              className="button primary"
              onClick={() => void verifyAuthority()}
              disabled={busy}
            >
              {busy
                ? t("Comprobando autoridad…", "Checking authority…")
                : t(
                    "Comprobar autoridad del comando",
                    "Check command authority",
                  )}
              <ArrowRight size={16} />
            </button>
          )}
        </Dialog>
      )}
    </div>
  );
}

function PilotTestAccounts() {
  const { t } = useLocale();
  const [accounts, setAccounts] = useState({ a: "", b: "" });
  return (
    <section className="admin-attention" aria-labelledby="pilot-accounts-title">
      <h2 id="pilot-accounts-title">{t("Cuentas para la prueba del piloto", "Pilot test accounts")}</h2>
      <p>{t("AXIGNAL · https://axignal.com/ · 1 organización, sin pagos.", "AXIGNAL · https://axignal.com/ · 1 organization, no payments.")}</p>
      <p>{t("Indica las cuentas Google que utilizarás. Este borrador se mantiene mientras esta vista está abierta; no concede acceso ni envía invitaciones. El acceso requiere Google verificado y una invitación de un solo uso.", "Enter the Google accounts you will use. This draft lasts while this view is open; it grants no access and sends no invitations. Access requires verified Google sign-in and a single-use invitation.")}</p>
      <div className="admin-table-toolbar">
        {(["a", "b"] as const).map((tenant) => (
          <label className="search-field" key={tenant}>
            <span>{t("Cuenta Google", "Google account")} {tenant.toUpperCase()}</span>
            <input type="email" autoComplete="off" value={accounts[tenant]}
              onChange={(event) => setAccounts((previous) => ({ ...previous, [tenant]: event.target.value }))}
              aria-label={t("Cuenta Google", "Google account") + " " + tenant.toUpperCase()} />
          </label>
        ))}
      </div>
      <button type="button" className="button secondary" onClick={() => setAccounts({ a: "", b: "" })}>
        {t("Vaciar cuentas", "Clear accounts")}
      </button>
    </section>
  );
}
