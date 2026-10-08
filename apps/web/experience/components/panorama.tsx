"use client";
import Link from "next/link";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Chat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import type { AxentMessage } from "@/lib/axent-contract";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Home,
  Compass,
  Building2,
  Layers3,
  Settings2,
  ChevronDown,
  ChevronRight,
  BookOpen,
  List,
  Network,
  Menu,
  MessageCircle,
  X,
  CalendarDays,
  Info,
  Search,
  RotateCcw,
} from "lucide-react";
import {
  families,
  organizations,
  snapshots,
  makeContext,
  project,
  dateLabel,
  type FamilyId,
  type Signal,
  type ProjectionContext,
} from "@/lib/projection";
import { useLocale } from "@/lib/locale";
import { FamilyLens } from "./cognition/lenses";
import { familiesForText, familyTerms } from "@/lib/family-vocabulary";
import { funnelLayers, type FunnelLayer } from "@/lib/funnel";
import {
  Brand,
  LocaleToggle,
  Badge,
  DemoLabel,
  Observer,
  IconButton,
  Dialog,
  StatePanel,
  type ViewState,
  useFocusTrap,
} from "./ui";
import { EvidenceDialog, EvidenceList } from "./evidence";
import { Axent } from "./axent";
import { ObservationAtelier } from "./observation-atelier";
import { ProductNavigation } from "./product-navigation";
import { EconomicGarden } from "./economic-garden";
import { ExampleChanges, ExampleOpenQuestions } from "./example-story";
import { gardenAt } from "@/lib/cognition/facts";
import { exampleDepth, funnelCta, track } from "@/lib/funnel-events";

export function Panorama() {
  const { t, copy, locale, reducedMotion, setReducedMotion } = useLocale();
  const params = useSearchParams(),
    router = useRouter();
  const pathname = usePathname();
  const organizationId = organizations.some(
    (o) => o.id === params.get("organization"),
  )
    ? params.get("organization")!
    : "norte";
  const asOf = snapshots.some((s) => s.date === params.get("asOf"))
    ? params.get("asOf")!
    : "2026-10-03";
  const familyId = families.some((f) => f.id === params.get("family"))
    ? (params.get("family") as FamilyId)
    : null;
  const view = params.get("view") === "today" ? "today" : "panorama";
  const base = makeContext(organizationId, familyId ?? "markets", asOf);
  const projection = project(base);
  const selected = projection.signals.find(
    (s) => s.id === params.get("signal"),
  );
  const context = makeContext(
    organizationId,
    selected?.family ?? familyId ?? "markets",
    asOf,
    selected?.id ?? null,
  );
  const chat = useMemo(
    () =>
      new Chat<AxentMessage>({
        id: "axent-" + context.revision + "-" + locale,
        transport: new DefaultChatTransport<AxentMessage>({
          api: "/api/axent",
          body: { context, locale },
        }),
      }),
    [context.revision, locale],
  );
  const [draft, setDraft] = useState("");
  useEffect(() => {
    setDraft("");
    return () => {
      void chat.stop();
    };
  }, [chat]);
  const organization = projection.organization;
  const garden = gardenAt(organizationId, asOf);
  useEffect(() => {
    const chapter =
      params.get("depth") === "prove"
        ? exampleDepth.evidence
        : params.get("signal")
          ? exampleDepth.signal
          : params.get("family")
            ? exampleDepth.family
            : params.get("asOf") && params.get("asOf") !== "2026-10-03"
              ? exampleDepth.history
              : exampleDepth.opened;
    track({ kind: "CHAPTER_VIEWED", surface: "example", chapter });
  }, [params]);
  const depth = params.get("depth") ?? "understand";
  const layout = params.get("layout") === "reading" ? "reading" : "spatial";
  const [mobileNav, setMobileNav] = useState(false),
    [mobileAxent, setMobileAxent] = useState(false);
  const [evidenceId, setEvidenceId] = useState<string | null>(null);
  const [utility, setUtility] = useState<
    "organizations" | "focus" | "settings" | null
  >(null);
  const [loading, setLoading] = useState(true),
    [loadError, setLoadError] = useState(false),
    [reload, setReload] = useState(0);
  const [search, setSearch] = useState("");
  const [familyQuery, setFamilyQuery] = useState("");
  const centreRef = useRef<HTMLElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  useFocusTrap(mobileNav, sidebarRef, () => setMobileNav(false));
  const forcedState = [
    "empty",
    "unknown",
    "loading",
    "error",
    "unavailable",
  ].includes(params.get("state") ?? "")
    ? (params.get("state") as ViewState)
    : null;
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setLoadError(false);
    const q = new URLSearchParams({
      organization: organizationId,
      asOf,
      family: familyId ?? "markets",
    });
    fetch("/api/projection?" + q, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error("PROJECTION_UNAVAILABLE");
        return r.json();
      })
      .then(() => {
        if (!controller.signal.aborted) setLoading(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
          setLoadError(true);
        }
      });
    return () => controller.abort();
  }, [organizationId, asOf, familyId, reload]);
  useEffect(() => {
    centreRef.current?.scrollTo({ top: 0, behavior: "instant" });
  }, [params.toString()]);
  function navigate(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params.toString());
    next.delete("state");
    Object.entries(changes).forEach(([k, v]) =>
      v === null ? next.delete(k) : next.set(k, v),
    );
    router.push(pathname + (next.size ? "?" + next.toString() : ""), {
      scroll: false,
    });
    setMobileNav(false);
    setEvidenceId(null);
  }
  function changeLayout(mode: "spatial" | "reading") {
    navigate({ layout: mode, view: "panorama", family: null, signal: null, depth: null });
    setUtility(null);
  }
  function focusSignal(s: Signal) {
    navigate({
      signal: s.id,
      family: s.family,
      depth: "understand",
      view: "panorama",
    });
  }
  const family = families.find((f) => f.id === familyId);
  const familySignals = projection.signals.filter(
    (s) => !familyId || s.family === familyId,
  );
  const heroSignal =
    projection.signals.find((s) => s.id === "renovation") ??
    projection.signals.find((s) => s.epistemic !== "UNKNOWN");
  const visibleEvidence = projection.evidence.find((e) => e.id === evidenceId);
  const state =
    forcedState ??
    (organizationId === "empty"
      ? "empty"
      : loadError
        ? "error"
        : loading
          ? "loading"
          : null);
  function resetView() {
    if (forcedState) navigate({ state: null });
    else if (organizationId === "empty") {
      setUtility("organizations");
    } else setReload((n) => n + 1);
  }
  return (
    <div className="product-shell">
      <aside
        ref={sidebarRef}
        role={mobileNav ? "dialog" : "complementary"}
        aria-modal={mobileNav ? true : undefined}
        className={"product-sidebar " + (mobileNav ? "mobile-open" : "")}
        aria-label={t("Navegación del producto", "Product navigation")}
      >
        <div className="sidebar-brand">
          <Brand />
          <IconButton
            label={t("Cerrar navegación", "Close navigation")}
            className="mobile-only"
            onClick={() => setMobileNav(false)}
          >
            <X size={19} />
          </IconButton>
        </div>
        <button
          className="organization-switch"
          onClick={() => setUtility("organizations")}
        >
          <span className="org-monogram">
            {organizationId === "atlas" ? "A" : "N"}
          </span>
          <span>
            <strong>{organization.name}</strong>
            <small>{t("Foco de observación", "Observation focus")}</small>
          </span>
          <ChevronDown size={14} />
        </button>
        <nav>
          <span className="nav-group-label">{t("OBSERVAR", "OBSERVE")}</span>
          <button
            className={
              view === "today" && !selected ? "nav-item active" : "nav-item"
            }
            onClick={() =>
              navigate({
                view: "today",
                family: null,
                signal: null,
                depth: null,
              })
            }
          >
            <Home size={18} />
            {t("Hoy", "Today")}
          </button>
          <button
            className={
              view === "panorama" && !selected && !familyId
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() =>
              navigate({ view: null, family: null, signal: null, depth: null })
            }
          >
            <Compass size={18} />
            {t("Panorama", "Panorama")}
          </button>
          <button
            className="nav-item"
            onClick={() => setUtility("organizations")}
          >
            <Building2 size={18} />
            {t("Organizaciones", "Organizations")}
          </button>
          <span className="nav-group-label family-group-label">
            {t("FAMILIAS", "FAMILIES")}
          </span>
          <label className="family-finder">
            <Search size={14} aria-hidden="true" />
            <input
              type="search"
              value={familyQuery}
              onChange={(event) => setFamilyQuery(event.target.value)}
              onKeyDown={(event) => {
                const first = familyQuery.trim() ? familiesForText(familyQuery)[0] : undefined;
                if (event.key === "Enter" && first) {
                  setFamilyQuery("");
                  navigate({ view: "panorama", family: first, signal: null, depth: null });
                }
              }}
              placeholder={t("SEO, clientes…", "SEO, customers…")}
              aria-label={t("Buscar un tema en las familias", "Find a topic in the families")}
            />
          </label>
          {(familyQuery.trim()
            ? familiesForText(familyQuery).map((id) => families.find((f) => f.id === id)!)
            : families
          ).map((f) => (
            <button
              className={"family-nav " + (familyId === f.id ? "active" : "")}
              key={f.id}
              aria-label={copy(f.name) + ": " + familyTerms(f.id, locale).join(", ")}
              title={familyTerms(f.id, locale).join(" · ")}
              onClick={() => {
                setFamilyQuery("");
                navigate({
                  view: "panorama",
                  family: f.id,
                  signal: null,
                  depth: null,
                });
              }}
            >
              <span className={"family-dot " + f.color} />
              {copy(f.name)}
              <ChevronRight size={12} />
            </button>
          ))}
          {familyQuery.trim() && !familiesForText(familyQuery).length && (
            <p className="family-finder-empty" role="status">
              {t("Sin resultados. Prueba otra palabra o pregunta a Axent.", "No results. Try another word or ask Axent.")}
            </p>
          )}
        </nav>
        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => setUtility("settings")}>
            <Settings2 size={17} />
            {t("Preferencias", "Preferences")}
          </button>
          <div className="example-exit">
            <Link
              href="/signup"
              className="button primary"
              onClick={() => track({ kind: "CTA_ACTIVATED", surface: "example", cta: funnelCta.exampleStart })}
            >
              {t("Empieza con tu organización", "Start with your organization")}
            </Link>
            <Link href="/" className="text-link">
              {t("Volver a AXIGNAL", "Back to AXIGNAL")}
            </Link>
          </div>
        </div>
      </aside>
      <div className="product-workspace">
        <header className="product-topbar">
          <div className="navigation-controls">
            <IconButton
              className="mobile-only"
              label={t("Abrir navegación", "Open navigation")}
              onClick={() => setMobileNav(true)}
            >
              <Menu size={20} />
            </IconButton>
            <ProductNavigation
              onBack={() => router.back()}
              onForward={() => router.forward()}
              onHome={() =>
                navigate({
                  view: null,
                  family: null,
                  signal: null,
                  depth: null,
                })
              }
            />
            <span className="nav-divider" />
            <button
              className="breadcrumb-root"
              onClick={() =>
                navigate({
                  view: null,
                  family: null,
                  signal: null,
                  depth: null,
                })
              }
            >
              {t("Panorama", "Panorama")}
            </button>
            {family && (
              <>
                <ChevronRight size={12} />
                <span className="breadcrumb-family">{copy(family.name)}</span>
              </>
            )}
          </div>
          <div className="topbar-right">
            <DemoLabel />
            <LocaleToggle />
            <IconButton
              className="mobile-only"
              label={t("Abrir AXENT", "Open AXENT")}
              onClick={() => setMobileAxent(true)}
            >
              <MessageCircle size={20} />
            </IconButton>
            <Link
              href="/signup"
              className="public-access-link example-start"
              onClick={() => track({ kind: "CTA_ACTIVATED", surface: "example", cta: funnelCta.exampleStart })}
            >
              {t("Empezar", "Get started")}
              <ArrowRight size={15} />
            </Link>
          </div>
        </header>
        <div className="workspace-content">
          <main id="main" className="panorama-main" ref={centreRef}>
            <ExampleBanner organization={organization} />
            {state ? (
              <StatePanel state={state} onRetry={resetView} />
            ) : selected ? (
              <SignalDetail
                signal={selected}
                depth={depth}
                asOf={asOf}
                onDepth={(value) => navigate({ depth: value })}
                onEvidence={setEvidenceId}
                onBack={() => navigate({ signal: null, depth: null })}
              />
            ) : (
              <>
                <div className="panorama-intro">
                  <div>
                    <span className="eyebrow">
                      {organization.name} /{" "}
                      {asOf === "2026-10-03"
                        ? t("Perspectiva actual", "Current perspective")
                        : dateLabel(asOf, locale)}
                    </span>
                    <h1>
                      {family
                        ? copy(family.name)
                        : view === "today"
                          ? t(
                              "Lo que merece tu atención.",
                              "What deserves your attention.",
                            )
                          : t("Lo que AXIGNAL ve alrededor de {org}.", "What AXIGNAL sees around {org}.").replace("{org}", organization.name)}
                    </h1>
                    {family && (
                      <p className="family-terms">{familyTerms(family.id, locale).join(" · ")}</p>
                    )}
                    <p>
                      {family
                        ? copy(family.intro)
                        : view === "today"
                          ? t(
                              "Una lectura breve de las señales disponibles en este corte temporal.",
                              "A brief reading of the signals available at this point in time.",
                            )
                          : t(
                              "Dónde trabaja, qué ha cambiado, por qué importa y qué falta por saber. Abre cualquier señal para ver su evidencia.",
                              "Where it works, what changed, why it matters and what is still unknown. Open any signal to see its evidence.",
                            )}
                    </p>
                  </div>
                  {!family && view === "panorama" && (
                    <div
                      className="view-toggle"
                      role="group"
                      aria-label={t("Forma de lectura", "Reading mode")}
                    >
                      <IconButton
                        label={t("Vista espacial", "Spatial view")}
                        className={layout === "spatial" ? "selected" : ""}
                        onClick={() => changeLayout("spatial")}
                      >
                        <Network size={17} />
                      </IconButton>
                      <IconButton
                        label={t("Vista de lectura", "Reading view")}
                        className={layout === "reading" ? "selected" : ""}
                        onClick={() => changeLayout("reading")}
                      >
                        <List size={17} />
                      </IconButton>
                    </div>
                  )}
                </div>
                {family ? (
                  <>
                    <div className="family-lenses">
                      <span className="mono">
                        {t("IR DIRECTO A", "JUMP TO")}
                      </span>
                      {(family.id === "markets"
                        ? [
                            t("El programa de ayudas", "The grant programme"),
                            t("Por qué encaja", "Why it fits"),
                            t("Qué falta saber", "What is still unknown"),
                          ]
                        : [
                            t("La señal", "The signal"),
                            t("Por qué importa", "Why it matters"),
                            t("Qué falta saber", "What is still unknown"),
                          ]
                      ).map((label, i) => (
                        <button
                          key={label}
                          onClick={() => {
                            if (familySignals[0]) {
                              focusSignal(familySignals[0]);
                              if (i === 2)
                                navigate({
                                  signal: familySignals[0].id,
                                  depth: "reason",
                                });
                            } else setSearch(label);
                          }}
                        >
                          {label}
                          <ArrowUpRight size={13} />
                        </button>
                      ))}
                    </div>
                    {family.id === "markets" && garden && (
                      <EconomicGarden organization={organization.name} garden={garden} />
                    )}
                    <FamilyLens
                      organizationId={organizationId}
                      family={family.id}
                      asOf={asOf}
                    />
                    {familySignals.length > 0 ? (
                      <div className="family-signals">
                        {familySignals.map((s) => (
                          <SignalCard
                            key={s.id}
                            signal={s}
                            onOpen={() => focusSignal(s)}
                            large
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="family-empty">
                        <Observer scene="unknown" className="family-observer" />
                        <h2>
                          {t(
                            "Esta lente todavía tiene preguntas.",
                            "This lens still has questions.",
                          )}
                        </h2>
                        <p>
                          {t(
                            "No hay una señal sustentada para esta familia en el corte seleccionado. El contexto sigue abierto.",
                            "There is no supported signal for this family at the selected time. Context remains open.",
                          )}
                        </p>
                        <button
                          className="text-link"
                          onClick={() => setMobileAxent(true)}
                        >
                          {t(
                            "Explorar el contexto con AXENT",
                            "Explore context with AXENT",
                          )}
                          <ArrowRight size={15} />
                        </button>
                        {search && <span className="mono">{search}</span>}
                      </div>
                    )}
                    <section className="related-families">
                      <span className="eyebrow">
                        {t("AMPLÍA LA PERSPECTIVA", "WIDEN THE PERSPECTIVE")}
                      </span>
                      <div>
                        {families
                          .filter((f) => f.id !== family.id)
                          .slice(0, 3)
                          .map((f) => (
                            <button
                              key={f.id}
                              onClick={() =>
                                navigate({
                                  family: f.id,
                                  signal: null,
                                  depth: null,
                                })
                              }
                            >
                              <span className={"family-dot " + f.color} />
                              {copy(f.name)}
                              <ArrowRight size={14} />
                            </button>
                          ))}
                      </div>
                    </section>
                  </>
                ) : view === "today" ? (
                  <div className="today-list">
                    {projection.signals
                      .filter((s) => s.epistemic !== "UNKNOWN")
                      .slice(0, 3)
                      .map((s, i) => (
                        <div className="today-item" key={s.id}>
                          <span className="today-number">0{i + 1}</span>
                          <SignalCard
                            signal={s}
                            onOpen={() => focusSignal(s)}
                            large
                          />
                        </div>
                      ))}
                    {projection.signals.filter((s) => s.epistemic !== "UNKNOWN")
                      .length === 0 && <StatePanel state="unknown" />}
                    <p className="temporal-note">
                      <Clock3Icon />
                      {t(
                        "Disponible en este corte. “Detectado” no significa que ocurrió hoy.",
                        "Available at this time. “Detected” does not mean it happened today.",
                      )}
                    </p>
                  </div>
                ) : (
                  <>
                    {garden && (
                      <EconomicGarden organization={organization.name} garden={garden} />
                    )}
                    <ExampleChanges organizationId={organizationId} asOf={asOf} />
                    {heroSignal && (
                      <div className="attention-feature">
                        <div className="attention-text">
                          <span className="eyebrow">
                            {t(
                              "UNA SEÑAL PARA MIRAR MÁS CERCA",
                              "A SIGNAL TO LOOK CLOSER",
                            )}
                          </span>
                          <Badge state={heroSignal.epistemic} />
                          <h2>{copy(heroSignal.title)}</h2>
                          <p>{copy(heroSignal.summary)}</p>
                          <button
                            className="text-link"
                            onClick={() => focusSignal(heroSignal)}
                          >
                            {t(
                              "Entender por qué importa",
                              "Understand why it matters",
                            )}
                            <ArrowRight size={17} />
                          </button>
                        </div>
                        <div className="attention-visual">
                          <div className="attention-ring" />
                          <img
                            src="/brand/isotope.svg"
                            alt=""
                            width={88}
                            height={96}
                          />
                          <span className="hand-note">
                            {t("una posibilidad,", "a possibility,")}
                            <br />
                            {t("con fundamento", "with a basis")}
                          </span>
                        </div>
                      </div>
                    )}
                    <ExampleOpenQuestions
                      signals={projection.signals.filter((s) => s.id !== heroSignal?.id)}
                      onOpen={focusSignal}
                    />
                    <section className="constellation-section">
                      <div className="constellation-heading">
                        <span className="eyebrow">
                          {t(
                            "DIEZ FORMAS DE ACERCAR EL MUNDO",
                            "TEN WAYS TO BRING THE WORLD CLOSER",
                          )}
                        </span>
                        <span>
                          {t(
                            "Familias de comprensión",
                            "Families of understanding",
                          )}
                        </span>
                      </div>
                      <div
                        className={
                          "family-constellation " +
                          (layout === "reading" ? "reading-mode" : "")
                        }
                      >
                        {layout === "spatial" && (
                          <ObservationAtelier
                            organization={organization.name}
                            onFocus={() => setUtility("focus")}
                          />
                        )}
                        {families.map((f, i) => {
                          const signal = projection.signals.find(
                            (s) => s.family === f.id,
                          );
                          return (
                            <button
                              className={
                                "family-tile tile-" +
                                i +
                                " tone-" +
                                f.color +
                                (signal ? " has-signal" : "")
                              }
                              key={f.id}
                              onClick={() =>
                                navigate({
                                  family: f.id,
                                  signal: null,
                                  depth: null,
                                  view: "panorama",
                                })
                              }
                            >
                              <span className="tile-order">
                                {String(i + 1).padStart(2, "0")}
                              </span>
                              <span className="tile-name">{copy(f.name)}</span>
                              <span className="tile-terms">{familyTerms(f.id, locale).join(" · ")}</span>
                              <span className="tile-description">
                                {signal ? copy(signal.title) : copy(f.intro)}
                              </span>
                              <span className="tile-tail">
                                {signal ? (
                                  <Badge state={signal.epistemic} />
                                ) : (
                                  <span className="tile-open">
                                    {t("Contexto abierto", "Open context")}
                                  </span>
                                )}
                                <ArrowUpRight size={16} />
                              </span>
                            </button>
                          );
                        })}
                      </div>
                      <p className="spatial-note">
                        {t(
                          "La posición orienta la atención; no representa relaciones económicas.",
                          "Position directs attention; it does not represent economic relationships.",
                        )}
                      </p>
                    </section>
                    <section className="continuity-note">
                      <div>
                        <span className="eyebrow">
                          {t("OBSERVACIÓN CONTINUA", "CONTINUOUS OBSERVATION")}
                        </span>
                        <h3>
                          {t(
                            "El panorama no termina aquí.",
                            "The panorama does not end here.",
                          )}
                        </h3>
                        <p>
                          {t(
                            "En tu cuenta la observación continúa: cada evidencia nueva puede cambiar la lectura y sus límites.",
                            "In your account observation continues: each new piece of evidence can change the reading and its limits.",
                          )}
                        </p>
                      </div>
                      <Link
                        className="text-link"
                        href="/signup"
                        onClick={() => track({ kind: "CTA_ACTIVATED", surface: "example", cta: funnelCta.exampleStart })}
                      >
                        {t("Observar mi propia organización", "Observe my own organization")}
                        <ArrowRight size={15} />
                      </Link>
                    </section>
                  </>
                )}
              </>
            )}
            <div className="projection-footnote">
              <Info size={12} />
              {t(
                "Ejemplo guiado: la organización, sus fuentes y sus fechas son ficticias. El método es el mismo que en tu cuenta.",
                "Guided example: the organization, its sources and dates are fictional. The method is the same as in your account.",
              )}
            </div>
          </main>
          <aside className="axent-desktop" aria-label="Axent">
            <Axent
              chat={chat}
              draft={draft}
              onDraft={setDraft}
              key={context.revision + locale}
              context={context}
              onSignal={(id) => {
                const s = projection.signals.find((s) => s.id === id);
                if (s) focusSignal(s);
              }}
              onEvidence={setEvidenceId}
              onFamily={(id) => navigate({ view: "panorama", family: id, signal: null, depth: null })}
            />
          </aside>
        </div>
        <footer className="global-timeline">
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
                {asOf === "2026-10-03"
                  ? t(
                      "Lo que se sabe hoy",
                      "What is known today",
                    )
                  : t(
                      "Vista histórica · sin conocimiento futuro",
                      "Historical view · no future knowledge",
                    )}
              </span>
            </div>
          </div>
          <div
            className="timeline-controls"
            role="group"
            aria-label={t("Corte temporal global", "Global as-of snapshot")}
          >
            {snapshots.map((s) => (
              <button
                key={s.date}
                className={asOf === s.date ? "active" : ""}
                aria-pressed={asOf === s.date}
                onClick={() =>
                  navigate({ asOf: s.date, signal: null, depth: null })
                }
              >
                <span className="time-dot" />
                <span>{copy(s.label)}</span>
                <small>{dateLabel(s.date, locale)}</small>
              </button>
            ))}
          </div>
        </footer>
      </div>
      {visibleEvidence && (
        <EvidenceDialog
          item={visibleEvidence}
          onClose={() => setEvidenceId(null)}
        />
      )}
      {mobileAxent && (
        <Dialog
          title={t(
            "AXENT · Investigar y comprender",
            "AXENT · Investigate and understand",
          )}
          onClose={() => setMobileAxent(false)}
          className="axent-modal"
        >
          <Axent
            chat={chat}
            draft={draft}
            onDraft={setDraft}
            key={context.revision + locale + "mobile"}
            context={context}
            onSignal={(id) => {
              const s = projection.signals.find((s) => s.id === id);
              if (s) {
                focusSignal(s);
                setMobileAxent(false);
              }
            }}
            onEvidence={(id) => {
              setMobileAxent(false);
              setEvidenceId(id);
            }}
            onFamily={(id) => {
              setMobileAxent(false);
              navigate({ view: "panorama", family: id, signal: null, depth: null });
            }}
          />
        </Dialog>
      )}
      {utility && (
        <Dialog
          title={
            utility === "organizations"
              ? t("Organizaciones del ejemplo", "Organizations in the example")
              : utility === "focus"
                ? t(
                    "Un foco persistente de observación",
                    "A persistent observation focus",
                  )
                : t("Preferencias de lectura", "Reading preferences")
          }
          onClose={() => setUtility(null)}
        >
          {utility === "organizations" ? (
            <>
              <p>
                {t(
                  "La organización es el sujeto económico. El foco es la atención que asignas alrededor de ella.",
                  "The organization is the economic subject. The focus is the attention you allocate around it.",
                )}
              </p>
              <div className="organization-options">
                {organizations.map((o) => (
                  <button
                    key={o.id}
                    className={organizationId === o.id ? "selected" : ""}
                    onClick={() => {
                      navigate({
                        organization: o.id,
                        family: null,
                        signal: null,
                        depth: null,
                        asOf: "2026-10-03",
                      });
                      setUtility(null);
                    }}
                  >
                    <span className="org-monogram">
                      {o.id === "atlas" ? "A" : o.id === "empty" ? "?" : "N"}
                    </span>
                    <span>
                      <strong>{o.name}</strong>
                      <small>{copy(o.sector)}</small>
                    </span>
                    <ArrowRight size={17} />
                  </button>
                ))}
              </div>
              <DemoLabel />
            </>
          ) : utility === "focus" ? (
            <>
              <h3>{organization.name}</h3>
              <p>
                {t(
                  "Este foco dirige atención persistente; no crea ni posee una copia de AXIGLAND. El conocimiento se conserva en la memoria económica compartida.",
                  "This focus directs persistent attention; it does not create or own a copy of AXIGLAND. Knowledge is retained in the shared economic memory.",
                )}
              </p>
              <div className="fact-row">
                <span>
                  {t("Observación", "Observation")}
                </span>
                <strong>
                  {organization.focusId
                    ? t("Persistente", "Persistent")
                    : t("Sin asignar", "Unassigned")}
                </strong>
              </div>
              <div className="fact-row">
                <span>{t("Desde", "Since")}</span>
                <strong>{dateLabel(organization.focusSince, locale)}</strong>
              </div>
              <DemoLabel />
            </>
          ) : (
            <>
              <p>
                {t(
                  "Elige cómo leer. El movimiento respeta la preferencia de tu sistema.",
                  "Choose how to read. Motion respects your system preference.",
                )}
              </p>
              <div className="settings-options">
                <button
                  className="button secondary"
                  aria-pressed={layout === "reading"}
                  onClick={() => changeLayout("reading")}
                >
                  <List size={17} />
                  {t("Lectura lineal", "Linear reading")}
                </button>
                <button
                  className="button secondary"
                  aria-pressed={layout === "spatial"}
                  onClick={() => changeLayout("spatial")}
                >
                  <Network size={17} />
                  {t("Composición espacial", "Spatial composition")}
                </button>
                <button
                  className="button secondary"
                  aria-pressed={reducedMotion}
                  onClick={() => setReducedMotion(!reducedMotion)}
                >
                  {t("Reducir movimiento", "Reduce motion")}
                </button>
                <LocaleToggle />
              </div>
            </>
          )}
        </Dialog>
      )}
    </div>
  );
}
function Clock3Icon() {
  return <CalendarDays size={15} />;
}
export function SignalCard({
  signal,
  onOpen,
  large = false,
}: {
  signal: Signal;
  onOpen: () => void;
  large?: boolean;
}) {
  const { copy, t, locale } = useLocale();
  const family = families.find((f) => f.id === signal.family)!;
  return (
    <button
      className={"signal-card " + (large ? "large" : "")}
      onClick={onOpen}
    >
      <div className="signal-card-meta">
        <span className="eyebrow">{copy(family.name)}</span>
        <Badge state={signal.epistemic} />
      </div>
      <h3>{copy(signal.title)}</h3>
      <p>{copy(signal.summary)}</p>
      <div className="signal-card-bottom">
        <span>
          <BookOpen size={14} />
          {signal.evidenceIds.length
            ? signal.evidenceIds.length +
              " " +
              t(
                signal.evidenceIds.length === 1
                  ? "fuente ilustrativa"
                  : "fuentes ilustrativas",
                signal.evidenceIds.length === 1
                  ? "illustrative source"
                  : "illustrative sources",
              )
            : t("Base insuficiente", "Insufficient basis")}
        </span>
        <ArrowUpRight size={20} />
      </div>
      <small>
        {t("Detectado", "Detected")} {dateLabel(signal.detectedAt, locale)}
      </small>
    </button>
  );
}
function SignalDetail({
  signal,
  depth,
  asOf,
  onDepth,
  onEvidence,
  onBack,
}: {
  signal: Signal;
  depth: string;
  asOf: string;
  onDepth: (value: string) => void;
  onEvidence: (id: string) => void;
  onBack: () => void;
}) {
  const { t, copy, locale, reducedMotion, setReducedMotion } = useLocale();
  const family = families.find((f) => f.id === signal.family)!;
  const tabs = (["glance", "understand", "reason", "prove"] as const).map(
    (id, i) => [id, copy(funnelLayers[(i + 1) as FunnelLayer].label), copy(funnelLayers[(i + 1) as FunnelLayer].question)] as const,
  );
  const active = tabs.some(([id]) => id === depth) ? depth : "understand";
  return (
    <article className="signal-detail">
      <button className="text-link back-to-family" onClick={onBack}>
        <ArrowLeft size={15} />
        {t("Volver a", "Return to")} {copy(family.name)}
      </button>
      <div className="signal-detail-heading">
        <span className="eyebrow">
          {copy(family.name)} / {t("SEÑAL ILUSTRATIVA", "ILLUSTRATIVE SIGNAL")}
        </span>
        <Badge state={signal.epistemic} />
        <h1>{copy(signal.title)}</h1>
        <p>{copy(signal.summary)}</p>
        <div className="signal-dates">
          <span>
            {t("Evento", "Event")}: {dateLabel(signal.eventAt, locale)}
          </span>
          <span>
            {t("Detectado", "Detected")}: {dateLabel(signal.detectedAt, locale)}
          </span>
        </div>
      </div>
      <div
        className="depth-tabs"
        role="tablist"
        aria-label={t("Profundidad de comprensión", "Depth of understanding")}
      >
        {tabs.map(([id, label, question], i) => (
          <button
            id={"depth-" + id}
            key={id}
            title={question}
            role="tab"
            aria-selected={active === id}
            aria-controls="depth-panel"
            onClick={() => onDepth(id)}
          >
            <span>0{i + 1}</span>
            {label}
          </button>
        ))}
      </div>
      <section
        id="depth-panel"
        className="depth-panel"
        role="tabpanel"
        aria-labelledby={"depth-" + active}
        key={active}
      >
        {active === "glance" ? (
          <>
            <h2>
              {t(
                "Lo esencial, con sus límites.",
                "What matters, with its limits.",
              )}
            </h2>
            <p className="large-reading">{copy(signal.summary)}</p>
            <div className="limit-note">
              <Info size={18} />
              <div>
                <strong>{t("Qué sigue abierto", "What remains open")}</strong>
                <p>{copy(signal.limitation)}</p>
              </div>
            </div>
          </>
        ) : active === "understand" ? (
          <>
            <span className="eyebrow">
              {t("POR QUÉ MERECE ATENCIÓN", "WHY IT DESERVES ATTENTION")}
            </span>
            <h2>
              {signal.epistemic === "POTENTIAL"
                ? t(
                    "El contexto acerca dos piezas.",
                    "Context brings two pieces closer.",
                  )
                : signal.epistemic === "UNKNOWN"
                  ? t(
                      "Una pregunta necesita mejor base.",
                      "A question needs a better basis.",
                    )
                  : t(
                      "Una observación tiene un alcance.",
                      "An observation has a scope.",
                    )}
            </h2>
            <p className="large-reading">{copy(signal.why)}</p>
            {signal.dimensions.length > 0 && (
              <div className="reason-dimensions">
                {signal.dimensions.map((d) => (
                  <div key={d.label.es}>
                    <span>{copy(d.label)}</span>
                    <strong>{copy(d.value)}</strong>
                  </div>
                ))}
              </div>
            )}
            <div className="next-question">
              <span className="hand-note">
                {t("la siguiente buena pregunta", "the next good question")}
              </span>
              <p>{copy(signal.next)}</p>
            </div>
          </>
        ) : active === "reason" ? (
          <>
            <span className="eyebrow">
              {t("DERIVACIÓN CONSERVADA", "PRESERVED DERIVATION")}
            </span>
            <h2>
              {t(
                "Cómo llegamos a esta lectura.",
                "How we reached this reading.",
              )}
            </h2>
            <p className="large-reading">{copy(signal.derivation)}</p>
            <div className="derivation-path">
              <span>{t("Base documentada", "Documented basis")}</span>
              <ArrowRight size={16} />
              <span>{t("Contexto temporal", "Temporal context")}</span>
              <ArrowRight size={16} />
              <Badge state={signal.epistemic} />
            </div>
            <div className="limit-note">
              <Info size={18} />
              <div>
                <strong>
                  {t("Lo que no podemos concluir", "What we cannot conclude")}
                </strong>
                <p>{copy(signal.limitation)}</p>
              </div>
            </div>
            <button className="text-link" onClick={() => onDepth("prove")}>
              {t("Revisar la base original", "Review the original basis")}
              <ArrowRight size={17} />
            </button>
          </>
        ) : (
          <>
            <span className="eyebrow">
              {t("BASE DE ESTA SEÑAL", "BASIS OF THIS SIGNAL")}
            </span>
            <h2>
              {t("La evidencia, a la vista.", "Evidence, in plain sight.")}
            </h2>
            <p>
              {t(
                "Una fuente sostiene una parte de la lectura. No le atribuimos más autoridad que la que tiene.",
                "A source supports part of the reading. We do not give it more authority than it has.",
              )}
            </p>
            <EvidenceList signal={signal} onOpen={onEvidence} />
          </>
        )}
      </section>
      <div className="signal-proof-shortcut">
        <BookOpen size={16} />
        <span>
          {t(
            "Cada lectura conserva su base y sus límites.",
            "Every reading retains its basis and limits.",
          )}
        </span>
        <button className="text-link" onClick={() => onDepth("prove")}>
          {t("Ver evidencia", "View evidence")}
          <ArrowUpRight size={15} />
        </button>
      </div>
      <div className="projection-footnote">
        {t("Corte temporal", "As-of snapshot")}: {dateLabel(asOf, locale)}
      </div>
    </article>
  );
}

/** Public example != your private AXIGNAL, said once, plainly, at the top. */
function ExampleBanner({ organization }: { organization: { name: string; does: { es: string; en: string } } }) {
  const { t, copy } = useLocale();
  return (
    <aside className="example-banner" aria-label={t("Sobre este ejemplo", "About this example")}>
      <p>
        <strong>{t("Ejemplo guiado con una organización ficticia.", "Guided example with a fictional organization.")}</strong>{" "}
        {organization.name}: {copy(organization.does)}{" "}
        {t(
          "En tu cuenta, AXIGNAL observa las organizaciones reales que tú eliges, con sus fuentes reales.",
          "In your account, AXIGNAL observes the real organizations you choose, with their real sources.",
        )}
      </p>
      <span className="example-banner-actions">
      <Link
        href="/signup"
        className="text-link"
        onClick={() => track({ kind: "CTA_ACTIVATED", surface: "example", cta: funnelCta.exampleStart })}
      >
        {t("Empieza con tu organización", "Start with your organization")}
        <ArrowRight size={15} />
      </Link>
      <Link href="/" className="text-link example-banner-back">
        {t("Volver a AXIGNAL", "Back to AXIGNAL")}
      </Link>
      </span>
    </aside>
  );
}
