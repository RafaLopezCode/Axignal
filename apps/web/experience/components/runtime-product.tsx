"use client";
import { useEffect, useReducer, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  Compass,
  Home,
  Menu,
  X,
  MessageCircle,
  CalendarDays,
  ChevronDown,
  ArrowRight,
  Network,
  List,
} from "lucide-react";
import {
  focusHistory,
  productHome,
  type ProductFocus,
} from "@/lib/product-navigation";
import { ProductNavigation } from "./product-navigation";
import { RuntimeOrganizations } from "./runtime-organizations";
import { RuntimeAxent, useRuntimeAxent } from "./runtime-axent";
import { useLocale } from "@/lib/locale";
import {
  safeSourceLink,
  type RuntimeProjection,
  type RuntimeSignal,
} from "@/lib/runtime-projection";
import {
  Badge,
  Brand,
  LocaleToggle,
  IconButton,
  Dialog,
  useFocusTrap,
} from "./ui";

export function RuntimeSignalReading({
  signal,
  onEvidence,
}: {
  signal: RuntimeSignal;
  onEvidence?: () => void;
}) {
  const { t, locale } = useLocale();
  return (
    <article className="runtime-signal" id={signal.id} tabIndex={-1}>
      <div className="runtime-status">
        <Badge state={signal.epistemicState} />
        <span className="operation-status">{signal.currentness}</span>
      </div>
      <h2>{signal.title}</h2>
      <p>{signal.whyAttention}</p>
      <p>{signal.interpretation}</p>
      <div className="limit-note">
        <div>
          <strong>{t("Lo que sigue abierto", "What remains open")}</strong>
          <p>{signal.uncertainty}</p>
        </div>
      </div>
      <p className="runtime-date">
        {t("Observado", "Observed")}{" "}
        <time dateTime={signal.observedAt}>
          {new Date(signal.observedAt).toLocaleString(locale)}
        </time>
      </p>
      {onEvidence ? (
        <button className="button secondary" onClick={onEvidence}>
          {t("Cómo lo sabe AXIGNAL", "How AXIGNAL knows")}
        </button>
      ) : (
        <RuntimeEvidenceJourney signal={signal} />
      )}
    </article>
  );
}
export function RuntimeEvidenceJourney({ signal }: { signal: RuntimeSignal }) {
  const { t, locale } = useLocale();
  return (
    <section
      className="evidence-journey"
      aria-label={t("Cómo lo sabe AXIGNAL", "How AXIGNAL knows")}
    >
      <p className="evidence-intro">
        {t(
          "De la señal a la fuente, sin ocultar lo que sigue abierto.",
          "From signal to source, without hiding what remains open.",
        )}
      </p>
      <ol className="evidence-path">
          {signal.evidenceNarrative.steps.map((step) => (
            <li key={step.id}>
              <span className="mono">
                {step.kind === "XIGNAL"
                  ? t("Señal", "Signal")
                  : step.kind === "OBSERVATION"
                    ? t("Observación", "Observation")
                    : step.kind === "SOURCE"
                      ? t("Fuente", "Source")
                      : step.kind === "UNKNOWN"
                        ? t("Lo que sigue abierto", "What remains open")
                        : step.kind}
              </span>
              <p>{step.label}</p>
              {step.currentness && <small>{step.currentness}</small>}
              {step.observedAt && (
                <time dateTime={step.observedAt}>
                  {new Date(step.observedAt).toLocaleString(locale)}
                </time>
              )}
              {step.artifactVerified !== null && (
                <p>
                  {step.artifactVerified
                    ? t("Artefacto verificado", "Artifact verified")
                    : t("Artefacto no verificado", "Artifact not verified")}
                </p>
              )}
              {step.sourceRef && <SourceReference reference={step.sourceRef} />}
            </li>
          ))}
      </ol>
      <details className="evidence-technical">
        <summary>{t("Detalles técnicos", "Technical details")}</summary>
          <dl>
            <dt>Signal</dt>
            <dd>{signal.id}</dd>
            <dt>Observations</dt>
            <dd>{signal.observationSupportRefs.join("\n")}</dd>
            <dt>EvidenceNarrative</dt>
            <dd>{signal.evidenceNarrative.focusStepId}</dd>
          </dl>
      </details>
      <details className="runtime-sources">
        <summary>
          {t("Fuentes y límites", "Sources and limits")} (
          {signal.sourceRefs.length})
        </summary>
        <ul>
          {signal.sourceRefs.map((ref) => (
            <li key={ref}>
              <SourceReference reference={ref} />
            </li>
          ))}
        </ul>
        <ul>
          {signal.unknowns.map((unknown) => (
            <li key={unknown}>{unknown}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}
function SourceReference({ reference }: { reference: string }) {
  const href = safeSourceLink(reference);
  return href ? (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {reference}
    </a>
  ) : (
    <span className="runtime-reference">{reference}</span>
  );
}
export function RuntimeProductProjection({
  projection,
  staffControls,
  mainId = "main",
  embedded = false,
  navigationHost,
  toolbarHost,
  onNavigate,
}: {
  projection: RuntimeProjection;
  staffControls?: React.ReactNode;
  mainId?: string;
  embedded?: boolean;
  navigationHost?: HTMLElement | null;
  toolbarHost?: HTMLElement | null;
  onNavigate?: () => void;
}) {
  const { t, locale } = useLocale();
  const [history, dispatch] = useReducer(focusHistory, {
    trail: [productHome],
    cursor: 0,
  });
  const focus = history.trail[history.cursor];
  useEffect(() => {
    if (window.matchMedia("(max-width: 680px)").matches)
      dispatch({ type: "go", focus: { ...productHome, view: "today" } });
  }, []);
  const [nav, setNav] = useState(false),
    [axent, setAxent] = useState(false),
    [evidence, setEvidence] = useState<string | null>(null),
    [organizations, setOrganizations] = useState(false),
    [spatial, setSpatial] = useState(true);
  const sidebar = useRef<HTMLElement>(null),
    main = useRef<HTMLElement>(null);
  useFocusTrap(nav, sidebar, () => setNav(false));
  const selected = projection.nodes.find((s) => s.id === focus.signalId);
  const evidenceSignal = projection.nodes.find((s) => s.id === evidence);
  function go(next: ProductFocus) {
    dispatch({ type: "go", focus: next });
    setNav(false);
    setEvidence(null);
    onNavigate?.();
  }
  function enter(id: string) {
    if (projection.nodes.some((s) => s.id === id))
      go({ ...focus, signalId: id });
  }
  const dimensions = [
    { id: "signals", label: t("Señales", "Signals") },
    { id: "capabilities", label: t("Capacidades", "Capabilities") },
    { id: "markets", label: t("Mercados", "Markets") },
    { id: "activity", label: t("Actividad", "Activity") },
  ] as const;
  const dimension = dimensions.find((d) => d.id === focus.dimension)!;
  const focusLabel = selected
    ? t("Señal seleccionada", "Selected signal")
    : focus.view === "dimension" ? dimension.label
      : focus.view === "today" ? t("Hoy", "Today")
        : focus.view === "timeline" ? t("Tiempo y evidencia", "Time and evidence")
          : t("Panorama", "Panorama");
  const dates = [...new Set(projection.nodes.map((s) => s.observedAt))].sort();
  useEffect(() => {
    main.current?.scrollTo({ top: 0 });
    main.current
      ?.querySelector<HTMLElement>("h1")
      ?.focus({ preventScroll: true });
  }, [focus]);
  const showEvidence = () => {
    const id = selected?.id ?? projection.nodes[0]?.id;
    if (id) setEvidence(id);
  };
  const conversation = useRuntimeAxent(projection, selected?.id ?? null);
  const axentPanel = (
    <RuntimeAxent
      conversation={conversation}
      projection={projection}
      signalId={selected?.id ?? null}
      focusLabel={focusLabel}
      onEvidence={() => {
        setAxent(false);
        showEvidence();
      }}
      onSignal={(id) => {
        setAxent(false);
        enter(id);
      }}
    />
  );
  // The product owns these controls and their state; Admin supplies placement only.
  const productMenu = (
    <>
      <button className="organization-switch" onClick={() => {
        setOrganizations(true);
        onNavigate?.();
      }}>
        <span className="org-monogram">{projection.organization.name.slice(0, 1)}</span>
        <span><strong>{projection.organization.name}</strong><small>{t("Foco de observación", "Observation focus")}</small></span>
        <ChevronDown size={14} />
      </button>
      <nav aria-label={t("Navegación del producto", "Product navigation")}>
        <span className="nav-group-label">{t("OBSERVAR", "OBSERVE")}</span>
        <button className={"nav-item " + (focus.view === "today" && !selected ? "active" : "")} onClick={() => go({ ...productHome, view: "today" })}>
          <Home size={18} />{t("Hoy", "Today")}
        </button>
        <button className={"nav-item " + (focus.view === "panorama" && !selected ? "active" : "")} onClick={() => go(productHome)}>
          <Compass size={18} />{t("Panorama", "Panorama")}
        </button>
        <span className="nav-group-label">{t("DIMENSIONES", "DIMENSIONS")}</span>
        {dimensions.map((d) => <button key={d.id} className={"nav-item " + (focus.view === "dimension" && focus.dimension === d.id && !selected ? "active" : "")} onClick={() => go({ view: "dimension", dimension: d.id, signalId: null })}>{d.label}</button>)}
        <button className={"nav-item " + (focus.view === "timeline" && !selected ? "active" : "")} onClick={() => go({ ...focus, view: "timeline", signalId: null })}>
          <CalendarDays size={18} />{t("Tiempo y evidencia", "Time and evidence")}
        </button>
      </nav>
      <div className={embedded ? "admin-product-axent" : "sidebar-bottom"}>
        <button className="nav-item" onClick={() => { setAxent(true); onNavigate?.(); }}><MessageCircle size={18} />AXENT</button>
      </div>
    </>
  );
  const productToolbar = (<>
          <div className="navigation-controls">
            {!embedded && <IconButton
              className="mobile-only"
              label={t("Abrir navegación", "Open navigation")}
              onClick={() => setNav(true)}
            >
              <Menu size={20} />
            </IconButton>}
            <ProductNavigation
              onBack={() => dispatch({ type: "back" })}
              onForward={() => dispatch({ type: "forward" })}
              onHome={() => dispatch({ type: "home" })}
              canBack={history.cursor > 0}
              canForward={history.cursor < history.trail.length - 1}
            />
            <span className="breadcrumb-family">
              {focusLabel}
            </span>
          </div>
          <div className="topbar-right">
            <LocaleToggle />
            <IconButton
              label={t("Abrir AXENT", "Open AXENT")}
              onClick={() => setAxent(true)}
            >
              <MessageCircle size={20} />
            </IconButton>
          </div>
  </>);
  return (
    <div
      className={"product-shell canonical-product" + (embedded ? " product-with-host-navigation" : "")}
      data-runtime-state="success"
    >
      {embedded ? (navigationHost ? createPortal(productMenu, navigationHost) : null) : <aside
        ref={sidebar}
        className={"product-sidebar " + (nav ? "mobile-open" : "")}
        role={nav ? "dialog" : "complementary"}
        aria-modal={nav || undefined}
        aria-label={t("Navegación del producto", "Product navigation")}
      >
        <div className="sidebar-brand">
          <Brand />
          <IconButton
            className="mobile-only"
            label={t("Cerrar navegación", "Close navigation")}
            onClick={() => setNav(false)}
          >
            <X size={19} />
          </IconButton>
        </div>
        {productMenu}
      </aside>}
      <div className="product-workspace">
        {embedded ? (toolbarHost ? createPortal(productToolbar, toolbarHost) : null) : <header className="product-topbar">{productToolbar}</header>}
        <div className="workspace-content">
          <main
            id={mainId}
            ref={main}
            className="panorama-main"
            data-product-view={selected ? "focus" : focus.view}
          >
            <div className="focus-trail">
              <button className="text-link" onClick={() => go(productHome)}>
                {projection.organization.name}
              </button>
              {selected && (
                <>
                  <span>/</span>
                  <span>{t("Señal seleccionada", "Selected signal")}</span>
                </>
              )}
            </div>
            {selected ? (
              <>
                <h1 tabIndex={-1}>
                  {t("Una señal, con contexto.", "A signal, in context.")}
                </h1>
                <RuntimeSignalReading
                  signal={selected}
                  onEvidence={showEvidence}
                />
                <RuntimeTemporal projection={projection} signal={selected} />
              </>
            ) : (
              <>
                <div className="panorama-intro">
                  <div>
                    <span className="eyebrow">
                      {projection.organization.name}
                    </span>
                    <h1 tabIndex={-1}>
                      {focus.view === "today"
                        ? t(
                            "Lo que merece tu atención.",
                            "What deserves your attention.",
                          )
                        : focus.view === "timeline"
                          ? t("Tiempo y evidencia", "Time and evidence")
                          : focus.view === "dimension"
                            ? dimension.label
                            : t(
                                "Tu mundo, en contexto.",
                                "Your world, in context.",
                              )}
                    </h1>
                    <p>
                      {t(
                        "Acerca una señal. Entiende qué la sostiene y qué sigue abierto.",
                        "Bring a signal closer. Understand its basis and what remains open.",
                      )}
                    </p>
                  </div>
                  {focus.view === "panorama" && (
                    <div
                      className="view-toggle"
                      role="group"
                      aria-label={t("Forma de lectura", "Reading mode")}
                    >
                      <IconButton
                        label={t("Vista espacial", "Spatial view")}
                        className={spatial ? "selected" : ""}
                        onClick={() => setSpatial(true)}
                      >
                        <Network size={17} />
                      </IconButton>
                      <IconButton
                        label={t("Vista de lectura", "Reading view")}
                        className={!spatial ? "selected" : ""}
                        onClick={() => setSpatial(false)}
                      >
                        <List size={17} />
                      </IconButton>
                    </div>
                  )}
                </div>
                {focus.view === "timeline" ? (
                  <RuntimeTemporal projection={projection} />
                ) : focus.view === "dimension" &&
                  focus.dimension !== "signals" ? (
                  <section className="family-empty">
                    <Badge state="UNKNOWN" />
                    <h2>
                      {t(
                        "Esta lente todavía tiene preguntas.",
                        "This lens still has questions.",
                      )}
                    </h2>
                    <p>
                      {t(
                        "La proyección autorizada no expone datos de esta dimensión. Ausencia de evidencia no significa ausencia de capacidad, mercado o actividad.",
                        "The authorized projection exposes no data for this dimension. Absence of evidence does not mean absence of capability, market or activity.",
                      )}
                    </p>
                    <button
                      className="text-link"
                      onClick={() => setAxent(true)}
                    >
                      {t(
                        "Explorar el contexto con AXENT",
                        "Explore context with AXENT",
                      )}
                    </button>
                  </section>
                ) : focus.view === "today" ? (
                  <section className="today-list" aria-label="Today">
                    <span className="eyebrow">{t("Hoy", "Today")}</span>
                    {projection.today.items.length ? (
                      projection.today.items.map((item, i) => (
                        <div className="today-item" key={item.xignalId}>
                          <span className="today-number">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <article>
                            <h2>{item.whatChanged}</h2>
                            <p>{item.whyItMatters}</p>
                            <button
                              className="text-link"
                              onClick={() => enter(item.xignalId)}
                            >
                              {t(
                                "Ver señal y evidencia",
                                "Read signal and evidence",
                              )}
                              <ArrowRight size={16} />
                            </button>
                          </article>
                        </div>
                      ))
                    ) : (
                      <p>
                        {t(
                          "El runtime no tiene señales vigentes para Hoy. Esto no convierte las observaciones anteriores en falsas.",
                          "The runtime has no current signals for Today. Earlier observations do not become false.",
                        )}
                      </p>
                    )}
                  </section>
                ) : (
                  <>
                    <section
                      className={
                        "runtime-canvas " + (!spatial ? "reading-mode" : "")
                      }
                      aria-label={t("Panorama espacial", "Spatial panorama")}
                    >
                      <div className="runtime-organization-focus">
                        <img
                          src="/brand/isotope.svg"
                          width={40}
                          height={44}
                          alt=""
                        />
                        <h2>{projection.organization.name}</h2>
                        <span>
                          {t("Foco de observación", "Observation focus")}
                        </span>
                      </div>
                      <div className="runtime-canvas-signals">
                        {projection.nodes.map((signal) => (
                          <button
                            className="runtime-node"
                            key={signal.id}
                            onClick={() => enter(signal.id)}
                          >
                            <Badge state={signal.epistemicState} />
                            <h2>{signal.title}</h2>
                            <p>{signal.whyAttention}</p>
                            <small>{signal.currentness}</small>
                            <span className="text-link">
                              {t(
                                "Entender por qué importa",
                                "Understand why it matters",
                              )}
                              <ArrowRight size={15} />
                            </span>
                          </button>
                        ))}
                      </div>
                    </section>
                    <p className="temporal-note">
                      {t(
                        "No hay relaciones expuestas en esta proyección. La cercanía visual no afirma un vínculo económico.",
                        "No relationships are exposed in this projection. Visual proximity asserts no economic link.",
                      )}
                    </p>
                  </>
                )}
              </>
            )}
            <details className="runtime-technical">
              <summary>
                {t("Diagnóstico técnico", "Technical diagnostics")}
              </summary>
              <dl>
                <dt>Organization</dt>
                <dd>{projection.organization.id}</dd>
                <dt>Focus</dt>
                <dd>{projection.context.id}</dd>
                <dt>Runtime SHA</dt>
                <dd>{projection.runtimeCodeSha}</dd>
                <dt>Lifecycle</dt>
                <dd>{projection.lifecycleStatus}</dd>
                <dt>Reality</dt>
                <dd>{projection.realityLevel}</dd>
                <dt>Reload</dt>
                <dd>{projection.reloadContinuity}</dd>
              </dl>
            </details>
          </main>
          <aside className="axent-desktop" aria-label="AXENT">
            {axentPanel}
          </aside>
        </div>
        {staffControls}
        <footer className="global-timeline runtime-meridian">
          <div className="timeline-label">
            <CalendarDays size={17} />
            <div>
              <strong>
                {t(
                  "El tiempo cambia la mirada",
                  "Time changes the perspective",
                )}
              </strong>
              <span>
                {dates.length
                  ? new Date(dates.at(-1)!).toLocaleString(locale)
                  : t("Desconocido", "Unknown")}
              </span>
            </div>
          </div>
          <button
            className="text-link"
            onClick={() => go({ ...focus, view: "timeline", signalId: null })}
          >
            {t("Tiempo y evidencia", "Time and evidence")}
          </button>
        </footer>
        <nav
          className="runtime-mobile-tools"
          aria-label={t("Lectura móvil", "Mobile reading")}
        >
          <button onClick={() => go({ ...productHome, view: "today" })}>
            {t("Hoy", "Today")}
          </button>
          <button onClick={showEvidence} disabled={!projection.nodes.length}>
            {t("Evidencia", "Evidence")}
          </button>
          <button
            onClick={() => go({ ...focus, view: "timeline", signalId: null })}
          >
            {t("Tiempo", "Time")}
          </button>
          <button onClick={() => setAxent(true)}>AXENT</button>
        </nav>
      </div>
      {evidenceSignal && (
        <Dialog
          title={t("Cómo lo sabe AXIGNAL", "How AXIGNAL knows")}
          onClose={() => setEvidence(null)}
          className="runtime-evidence-dialog"
        >
          <RuntimeEvidenceJourney signal={evidenceSignal} />
        </Dialog>
      )}
      {axent && (
        <Dialog
          title={t(
            "AXENT · Investigar y comprender",
            "AXENT · Investigate and understand",
          )}
          onClose={() => setAxent(false)}
          className="axent-modal"
        >
          {axentPanel}
        </Dialog>
      )}
      {organizations && (
        <Dialog
          title={t("Tus organizaciones", "Your organizations")}
          onClose={() => setOrganizations(false)}
          className="runtime-organizations-dialog"
        >
          <RuntimeOrganizations name={projection.organization.name} internal={embedded}
            onReturn={() => setOrganizations(false)} />
        </Dialog>
      )}
    </div>
  );
}
function RuntimeTemporal({
  projection,
  signal,
}: {
  projection: RuntimeProjection;
  signal?: RuntimeSignal;
}) {
  const { t, locale } = useLocale();
  const nodes = signal ? [signal] : projection.nodes;
  return (
    <section
      className="runtime-temporal"
      aria-label={t("Tiempo y evidencia", "Time and evidence")}
    >
      <h2>{t("Tiempo y evidencia", "Time and evidence")}</h2>
      {nodes.map((s) => (
        <div className="temporal-observation" key={s.id}>
          <span>{s.currentness}</span>
          <time dateTime={s.observedAt}>
            {new Date(s.observedAt).toLocaleString(locale)}
          </time>
          <p>{s.title}</p>
        </div>
      ))}
      <p>
        {t(
          "El runtime expone la observación actual, no una serie de snapshots históricos navegables. Una fecha de observación no prueba cuándo ocurrió un cambio económico.",
          "The runtime exposes the current observation, not a navigable historical snapshot series. An observation date does not prove when an economic change happened.",
        )}
      </p>
    </section>
  );
}
