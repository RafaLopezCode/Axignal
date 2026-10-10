"use client";
/**
 * Observatorio vivo: the subscriber workspace.
 *
 * One surface for one organization or a whole portfolio. Orientation stays in the rail and
 * header; meaning is the first thing read; depth (meaning, reasoning, proof, AXENT) unfolds
 * beside the finding it explains, never on another page. Every statement is the runtime's
 * own, worded by fixed copy (lib/observatory.ts); nothing here creates or upgrades truth.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal, flushSync } from "react-dom";
import Link from "next/link";
import { ArrowLeft, ArrowRight, ChevronDown, CornerRightUp, ExternalLink, LayoutGrid, LogOut, Menu, MessageCircleQuestion, Plus, RefreshCw, Settings2, X } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { LocaleToggle, useFocusTrap } from "./ui";
import { evidenceUrl, monthlyCapacityCents, pendingOutputSchema, subscriberOutputSchema, type FirstObservation, type SubscriberPortfolio } from "@/lib/subscriber-contracts";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { briefing, byLane, currentnessLabel, fill, insightsFor, laneCopy, natureLabel, type Insight, type Lane, type Nature, type Reading, type Translate } from "@/lib/observatory";
import { baseline, litKeys, markSeen, observedSinceVisit, readSeen, SEEN_DWELL_MS, SEEN_VISIBLE_RATIO, touch, writeSeen, type SeenStore } from "@/lib/observatory-seen";
import { activityLabel, FirstObservationView, observationStateCopy } from "./first-observation";
import { SubscriberReading } from "./subscriber-reading";
import { causeCopy, dimensionCopy, stateCopy } from "./public-understanding";
import { SubscriberRepresentation } from "./subscriber-representation";
import { SubscriberMcpConnections } from "./subscriber-mcp-connections";
import { RuntimeAxent, useRuntimeAxent } from "./runtime-axent";
import type { ObservatoryCapabilities } from "@/lib/observatory-source";
import { channelLabel, FamilyNav, scopeCopy, type FacetScope } from "./family-nav";
import { countByFacet, facetOfSourceType, facetParams, litByFamily, matchesFacet, parseFacet, type Facet } from "@/lib/observation-families";

type Item = SubscriberPortfolio["organizations"][number];
export type View = "summary" | "explore" | "evolution" | "evidence";
export type Screen = "desk" | "organization" | "account" | "add";

export type ObservatoryProps = {
  access: "loading" | "required" | "failure" | "ready";
  portfolio: SubscriberPortfolio | null;
  busy: boolean;
  message: string;
  paymentUrl: string | null;
  selected: string | null;
  reading: boolean;
  projection: RuntimeProjection | null;
  firstObservation: FirstObservation | null;
  revision: string | null;
  readOutput: (focusId: string, pushHistory?: boolean) => Promise<void> | void;
  clearSelection: () => void;
  command: (input: Record<string, unknown>) => Promise<void>;
  refresh: () => void;
  logout: () => void;
  locator: string; setLocator: (value: string) => void;
  total: number; setTotal: (value: number) => void;
  replacing: string | null; setReplacing: (value: string | null) => void;
  replacementLocator: string; setReplacementLocator: (value: string) => void;
  /** Account-only capabilities. False in the public demo: same components, synthetic data. */
  canAct: boolean;
  /**
   * Set when the Observatory lives inside a shell that already owns the page's navigation (the Admin's sidebar):
   * its portfolio navigation is then drawn in the shell's own sidebar instead of a second one beside the reading.
   */
  shell?: { host: HTMLElement | null };
  /** What the context offers around the reading; the demo declares all of it, an Admin has no account to manage. */
  capabilities: ObservatoryCapabilities;
  /** Organizations the context already authorizes, offered while adding one. */
  suggestions?: readonly string[];
  /** A statement above the reading, inside the main column (the demo's fictional-data notice). */
  notice?: React.ReactNode;
  /** The menu's name for an organization, when the mode names it differently (the demo shows its domain). */
  menuName?: (item: SubscriberPortfolio["organizations"][number]) => string;
  /** One reading source for the desk and the organization view: the account's read, or the demo snapshot. */
  loadReading: (focusId: string, signal: AbortSignal) => Promise<unknown>;
};

const CLOSED = new Set(["REMOVED", "RESOLVED", "CANCELLED"]);
const OBSERVING = new Set(["QUEUED", "OBSERVING_PUBLIC_PRESENCE"]);
const LOW_OBSERVABILITY = new Set(["SOURCE_UNAVAILABLE", "NO_PUBLIC_WEBSITE", "OBSERVATION_FAILED", "BUDGET_EXHAUSTED", "NOT_ENOUGH_CAPABILITY_EVIDENCE"]);
export const readable = (item: Item) => Boolean(item.organizationId || item.observation);
const visible = (item: Item) => !CLOSED.has(item.state);

/** Continuity across organizations and views, with a native fallback when unsupported. */
type ViewTransitionLike = { ready: Promise<void>; finished: Promise<void>; updateCallbackDone: Promise<void> };
let running: ViewTransitionLike | null = null;
function transition(update: () => void) {
  const doc = document as Document & { startViewTransition?: (cb: () => void) => ViewTransitionLike };
  // Instant update when unsupported, reduced, or while a transition is still running.
  if (!doc.startViewTransition || running || window.matchMedia("(prefers-reduced-motion: reduce)").matches) { update(); return; }
  const current = doc.startViewTransition(() => flushSync(update));
  running = current;
  // A skipped or interrupted transition is expected on fast clicks; the DOM update still happens.
  for (const promise of [current.ready, current.updateCallbackDone]) promise.catch(() => {});
  current.finished.catch(() => {}).finally(() => { if (running === current) running = null; });
}

function useUrlState() {
  const read = () => {
    const url = new URL(window.location.href);
    const view = url.searchParams.get("view");
    const screen = url.searchParams.get("screen");
    return {
      view: (["summary", "explore", "evolution", "evidence"].includes(view ?? "") ? view : "summary") as View,
      screen: (["account", "add"].includes(screen ?? "") ? screen : null) as "account" | "add" | null,
      item: url.searchParams.get("item"),
      family: url.searchParams.get("family"),
      channel: url.searchParams.get("channel"),
    };
  };
  const [state, setState] = useState<{ view: View; screen: "account" | "add" | null; item: string | null; family: string | null; channel: string | null }>({ view: "summary", screen: null, item: null, family: null, channel: null });
  useEffect(() => {
    setState(read());
    const listener = () => setState(read());
    window.addEventListener("popstate", listener);
    return () => window.removeEventListener("popstate", listener);
  }, []);
  const go = useCallback((next: Partial<{ view: View; screen: "account" | "add" | null; item: string | null; organization: string | null; family: string | null; channel: string | null }>, replace = false) => {
    const url = new URL(window.location.href);
    const set = (key: string, value: string | null | undefined) => { if (value === undefined) return; if (value === null) url.searchParams.delete(key); else url.searchParams.set(key, value); };
    set("view", next.view === "summary" ? null : next.view);
    set("screen", next.screen);
    set("item", next.item);
    set("organization", next.organization);
    set("family", next.family);
    set("channel", next.channel);
    window.history[replace ? "replaceState" : "pushState"](null, "", url);
    setState(read());
  }, []);
  return [state, go] as const;
}

function useSeen() {
  const [store, setStore] = useState<SeenStore>({});
  useEffect(() => { setStore(readSeen(() => window.localStorage)); }, []);
  const update = useCallback((change: (store: SeenStore) => SeenStore) => {
    setStore(previous => { const next = change(previous); if (next !== previous) writeSeen(() => window.localStorage, next); return next; });
  }, []);
  return [store, update] as const;
}

/** Bounded, cancellable reads for the portfolio desk (three at a time, at most 40). */
function useDeskReadings(items: Item[], enabled: boolean, loadReading: ObservatoryProps["loadReading"]) {
  const [readings, setReadings] = useState<Record<string, Reading | "failed">>({});
  const ids = items.filter(readable).slice(0, 40).map(i => i.focusId).join(",");
  useEffect(() => {
    if (!enabled || !ids) return;
    const controller = new AbortController();
    const queue = ids.split(",");
    const worker = async () => {
      while (queue.length && !controller.signal.aborted) {
        const id = queue.shift()!;
        try {
          const payload = await loadReading(id, controller.signal);
          const reading: Reading = (payload as { kind?: unknown })?.kind === "PENDING_ATTENTION"
            ? { projection: null, firstObservation: pendingOutputSchema.parse(payload).firstObservation }
            : (() => { const r = subscriberOutputSchema.parse(payload); return { projection: r.projection, firstObservation: r.firstObservation ?? null }; })();
          if (!controller.signal.aborted) setReadings(previous => ({ ...previous, [id]: reading }));
        } catch { if (!controller.signal.aborted) setReadings(previous => ({ ...previous, [id]: "failed" })); }
      }
    };
    void Promise.all([worker(), worker(), worker()]);
    return () => controller.abort();
  }, [enabled, ids, loadReading]);
  return readings;
}

function formatDate(value: string | null | undefined, locale: string, withTime = false): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(locale, withTime ? { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" } : { day: "numeric", month: "short", year: "numeric" }).format(date);
}

function relative(value: string | null | undefined, locale: string): string {
  if (!value) return "";
  const diff = (Date.parse(value) - Date.now()) / 1000;
  if (Number.isNaN(diff)) return "";
  const format = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  const abs = Math.abs(diff);
  if (abs < 3600) return format.format(Math.round(diff / 60), "minute");
  if (abs < 86400) return format.format(Math.round(diff / 3600), "hour");
  if (abs < 86400 * 30) return format.format(Math.round(diff / 86400), "day");
  return formatDate(value, locale);
}

function host(url: string): string { try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; } }

// ---- marks: shape + text, never colour alone -------------------------------------------

export function NatureMark({ nature, label }: { nature: Nature; label: string }) {
  const shape = (() => {
    switch (nature) {
      case "OBSERVED": return <circle cx="6" cy="6" r="4" fill="currentColor"/>;
      case "DECLARED": return <><circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.5"/><path d="M6 2a4 4 0 0 1 0 8z" fill="currentColor"/></>;
      case "POTENTIAL": return <circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="2 1.6"/>;
      case "UNKNOWN": return <><circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.5"/><circle cx="6" cy="6" r="1" fill="currentColor"/></>;
      case "STRENGTH": return <><circle cx="6" cy="6" r="5" fill="currentColor"/><path d="M3.6 6.2 5.3 7.8 8.5 4.4" fill="none" stroke="var(--obs-paper)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></>;
      case "CLARIFY": return <><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5"/><path d="M6 3.8v4.4M3.8 6h4.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></>;
      case "UNRESOLVED": return <><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="1.4 1.6"/></>;
    }
  })();
  return <span className={`obs-mark obs-mark-${nature.toLowerCase()}`}><svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">{shape}</svg>{label}</span>;
}

type LensState = "observing" | "ready" | "paused" | "low" | "pending";
function lensState(item: Item): LensState {
  if (item.state === "PAUSED") return "paused";
  if (item.observation && OBSERVING.has(item.observation.state)) return "observing";
  if (item.observation && LOW_OBSERVABILITY.has(item.observation.state)) return "low";
  if (!item.organizationId && !item.observation) return "pending";
  return "ready";
}

function Lens({ state, lit }: { state: LensState; lit: boolean }) {
  return <span className={`obs-lens obs-lens-${state}`} aria-hidden="true">
    <svg viewBox="0 0 24 24" width="22" height="22"><circle className="obs-lens-ring" cx="12" cy="10.5" r="7.5"/><path className="obs-lens-stem" d="M12 18v3.5"/></svg>
    {lit && <span className="obs-lamp-dot"/>}
  </span>;
}

function itemStatus(item: Item, t: Translate): string {
  if (item.reason === "AUTHORIZATION_REVOKED") return t("Autorización revocada", "Authorization revoked");
  if (item.state === "PAUSED") return t("Pausada", "Paused");
  if (item.observation) return observationStateCopy(item.observation.state, t);
  if (item.state === "IDENTITY_PENDING") return item.reason?.startsWith("AMBIGUOUS") ? t("Varias organizaciones coinciden", "Several organizations match") : item.reason?.startsWith("CONFLICT") ? t("Datos en conflicto", "Conflicting details") : t("Identidad por resolver", "Identity unresolved");
  if (item.state === "IDENTITY_REJECTED") return t("Identidad no admitida", "Identity not admitted");
  if (item.state === "CAPACITY_PENDING" || item.state === "CAPACITY_UNKNOWN") return t("Pendiente de capacidad", "Capacity pending");
  if (item.state === "PURCHASE_AUTHORITY_REQUIRED") return t("Autoridad de compra pendiente", "Purchase authority pending");
  return t("Observación activa", "Active observation");
}

// ---- root --------------------------------------------------------------------------------

export function Observatory(props: ObservatoryProps) {
  const { t, locale } = useLocale();
  const { access, portfolio, selected } = props;
  const [url, go] = useUrlState();
  const [seen, updateSeen] = useSeen();
  const [railOpen, setRailOpen] = useState(false);
  // Lit findings per organization, as the views compute them, so rail, desk and briefing agree.
  const [litCounts, setLitCounts] = useState<Record<string, number>>({});
  const reportLit = useCallback((focusId: string, count: number) => setLitCounts(previous => previous[focusId] === count ? previous : { ...previous, [focusId]: count }), []);
  const [axentOpen, setAxentOpen] = useState(false);
  const items = useMemo(() => portfolio?.organizations.filter(visible) ?? [], [portfolio]);
  const readableItems = items.filter(readable);
  const screen: Screen = url.screen ?? (selected ? "organization" : readableItems.length || items.length ? "desk" : "add");
  const deskReadings = useDeskReadings(items, access === "ready" && screen === "desk", props.loadReading);
  const names = useRef(new Map<string, string>());
  if (props.projection && selected) names.current.set(selected, props.projection.organization.name);
  for (const [id, reading] of Object.entries(deskReadings)) if (reading !== "failed" && reading.projection) names.current.set(id, reading.projection.organization.name);
  const nameOf = useCallback((item: Item) => names.current.get(item.focusId) ?? item.label, []);

  // A direct subscriber with one organization lands on it; an agency lands on the desk.
  const autoOpened = useRef(false);
  useEffect(() => {
    if (access !== "ready" || autoOpened.current || selected || url.screen) return;
    if (new URL(window.location.href).searchParams.get("organization")) return;
    autoOpened.current = true;
    if (readableItems.length === 1 && items.length === 1) void props.readOutput(readableItems[0].focusId, false);
  }, [access, items.length, props, readableItems, selected, url.screen]);

  const openOrganization = (focusId: string, item: string | null = null) => {
    setRailOpen(false); setAxentOpen(false);
    transition(() => {
      go({ screen: null, view: "summary", item }, true);
      void props.readOutput(focusId);
    });
  };
  const openScreen = (next: "desk" | "account" | "add") => {
    setRailOpen(false); setAxentOpen(false);
    transition(() => {
      if (next === "desk") { props.clearSelection(); go({ screen: null, item: null, view: "summary", organization: null }); }
      else go({ screen: next, item: null });
    });
  };

  if (access === "loading") return <ObservatoryFrame><div className="obs-loading" role="status"><Lens state="observing" lit={false}/>{t("Leyendo tu contexto…", "Reading your context…")}</div></ObservatoryFrame>;
  if (access === "required") return <ObservatoryFrame><section className="obs-gate"><h1>{t("Tu identidad abre el acceso.", "Your identity opens access.")}</h1><p>{t("Accede para leer tu cartera privada y sus evidencias.", "Sign in to read your private portfolio and its evidence.")}</p><Link className="obs-button obs-primary" href="/login">{t("Acceder", "Sign in")}<ArrowRight size={16} aria-hidden="true"/></Link></section></ObservatoryFrame>;
  if (access === "failure" || !portfolio) return <ObservatoryFrame><section className="obs-gate" role="alert"><h1>{t("No pudimos leer tu contexto.", "We could not read your context.")}</h1><p>{t("Tu cartera sigue a salvo. Vuelve a comprobarlo en un momento.", "Your portfolio is safe. Check again in a moment.")}</p><button className="obs-button" onClick={props.refresh}><RefreshCw size={16} aria-hidden="true"/>{t("Volver a comprobar", "Check again")}</button></section></ObservatoryFrame>;

  const current = items.find(i => i.focusId === selected) ?? null;
  const rail = <Rail items={items} selected={selected} screen={screen} seen={seen} litCounts={litCounts} nameOf={props.menuName ?? nameOf} onOrganization={openOrganization} onScreen={openScreen} portfolio={portfolio} busy={props.busy} refresh={props.refresh} canAct={props.canAct} account={props.capabilities.account}/>;
  return <div className={`obs${props.shell ? " obs-shelled" : ""}`} data-product-surface="living-observatory" aria-busy={props.busy}>
    <a className="obs-skip" href="#obs-main">{t("Ir al contenido", "Skip to content")}</a>
    {props.shell ? (props.shell.host ? createPortal(<div className="obs obs-in-shell">{rail}</div>, props.shell.host) : null) : <div className="obs-rail-desktop">{rail}</div>}
    {!props.shell && <MobileBar title={screen === "organization" && current ? nameOf(current) : screen === "desk" ? t("Tu cartera", "Your portfolio") : screen === "account" ? t("Cuenta", "Account") : t("Añadir organización", "Add organization")} onMenu={() => setRailOpen(true)}/>}
    {!props.shell && railOpen && <RailSheet onClose={() => setRailOpen(false)}>{rail}</RailSheet>}
    <main id="obs-main" className="obs-main" tabIndex={-1}>
      {props.notice}
      {(props.message || props.paymentUrl) && <div className="obs-toast" role="status" aria-live="polite">{props.message && <p>{props.message}</p>}{props.paymentUrl && <a className="obs-button obs-primary" href={props.paymentUrl}>{t("Continuar al pago", "Continue to payment")}<ArrowRight size={16} aria-hidden="true"/></a>}</div>}
      {screen === "desk" && <DeskView items={items} readings={deskReadings} seen={seen} nameOf={nameOf} onOpen={openOrganization} onAdd={() => openScreen("add")} reportLit={reportLit}/>}
      {screen === "add" && <AddView {...props} first={!items.length} onDone={() => openScreen("desk")}/>}
      {screen === "account" && <AccountView {...props}/>}
      {screen === "organization" && current && <OrganizationView key={current.focusId} item={current} name={nameOf(current)} {...props} view={url.view} itemId={url.item} family={url.family} channel={url.channel} go={go} seen={seen} updateSeen={updateSeen} axentOpen={axentOpen} setAxentOpen={setAxentOpen} locale={locale} reportLit={reportLit}/>}
    </main>
  </div>;
}

function ObservatoryFrame({ children }: { children: React.ReactNode }) {
  return <div className="obs obs-frame" data-product-surface="living-observatory"><div className="obs-frame-brand"><Link href="/" aria-label="AXIGNAL"><img src="/brand/logo-light.svg" alt="AXIGNAL" width={147} height={43}/></Link></div>{children}</div>;
}

// ---- rail: where am I, which organization, what changed -----------------------------------

function Rail({ items, selected, screen, seen, litCounts, nameOf, onOrganization, onScreen, portfolio, busy, refresh, canAct, account }: {
  items: Item[]; selected: string | null; screen: Screen; seen: SeenStore; litCounts: Record<string, number>; nameOf: (item: Item) => string;
  onOrganization: (id: string) => void; onScreen: (screen: "desk" | "account" | "add") => void;
  portfolio: SubscriberPortfolio; busy: boolean; refresh: () => void; canAct: boolean; account: boolean;
}) {
  const { t } = useLocale();
  const [filter, setFilter] = useState("");
  const shown = filter.trim() ? items.filter(i => nameOf(i).toLocaleLowerCase().includes(filter.trim().toLocaleLowerCase())) : items;
  const isLit = (i: Item) => observedSinceVisit(seen, i.focusId, i.observation?.observedAt) || (litCounts[i.focusId] ?? 0) > 0;
  const lamps = items.filter(isLit).length;
  return <nav className="obs-rail" aria-label={t("Cartera", "Portfolio")}>
    <Link className="obs-rail-brand" href="/" aria-label={t("AXIGNAL · Inicio", "AXIGNAL · Home")}><img src="/brand/logo-light.svg" alt="AXIGNAL" width={124} height={36}/></Link>
    <button className="obs-scope" aria-current={screen === "desk" ? "page" : undefined} onClick={() => onScreen("desk")}>
      <LayoutGrid size={16} aria-hidden="true"/><span>{t("Toda la cartera", "Whole portfolio")}</span>
      {lamps > 0 && <span className="obs-scope-lamp"><span aria-hidden="true">{lamps}</span><span className="sr-only">{fill(t("{n} con observaciones nuevas", "{n} with new observations"), { n: lamps })}</span></span>}
    </button>
    <div className="obs-rail-head"><h2>{t("Organizaciones", "Organizations")}</h2><span className="obs-rail-count">{portfolio.capacity === null || portfolio.capacityCurrentness !== "CURRENT" ? items.length : `${items.filter(i => i.state === "ACTIVE" || i.state === "PAUSED").length}/${portfolio.capacity}`}</span>
      <button className="obs-icon" onClick={refresh} disabled={busy} aria-label={t("Actualizar la cartera", "Refresh the portfolio")}><RefreshCw size={15} aria-hidden="true"/></button></div>
    {items.length > 6 && <label className="obs-filter"><span className="sr-only">{t("Buscar en tu cartera", "Search your portfolio")}</span><input value={filter} onChange={e => setFilter(e.target.value)} placeholder={t("Buscar organización…", "Find an organization…")}/></label>}
    <ul className="obs-orgs">
      {shown.map(item => {
        const lit = isLit(item);
        const fresh = litCounts[item.focusId] ?? 0;
        const state = lensState(item);
        return <li key={item.focusId}>
          <button className="obs-org" aria-current={selected === item.focusId ? "page" : undefined} disabled={!readable(item)} onClick={() => onOrganization(item.focusId)}>
            <Lens state={state} lit={lit}/>
            <span className="obs-org-text"><span className="obs-org-name">{nameOf(item)}</span><span className={`obs-org-sub${lit ? " obs-org-sub-lit" : ""}`}>{fresh > 0 ? fill(fresh === 1 ? t("{n} hallazgo nuevo", "{n} new finding") : t("{n} hallazgos nuevos", "{n} new findings"), { n: fresh }) : lit ? t("Nueva observación", "New observation") : itemStatus(item, t)}</span></span>
          </button>
        </li>;
      })}
      {!items.length && <li className="obs-org-empty">{t("Todavía no observas ninguna organización.", "You are not observing any organization yet.")}</li>}
      {filter && !shown.length && <li className="obs-org-empty">{t("Ninguna organización coincide.", "No organization matches.")}</li>}
    </ul>
    <div className="obs-rail-foot">
      <button className="obs-rail-action obs-rail-cta" aria-current={screen === "add" ? "page" : undefined} disabled={!canAct} onClick={() => onScreen("add")}><Plus size={16} aria-hidden="true"/>{t("Añadir organización", "Add organization")}</button>
      {account && <button className="obs-rail-action" aria-current={screen === "account" ? "page" : undefined} disabled={!canAct} onClick={() => onScreen("account")}><Settings2 size={16} aria-hidden="true"/>{t("Cuenta y conexiones", "Account and connections")}</button>}
      {!canAct && <p className="obs-rail-note">{t("Acciones de cuenta disponibles al crear tu cuenta.", "Account actions are available once you create your account.")}</p>}
      <div className="obs-rail-locale"><LocaleToggle/></div>
    </div>
  </nav>;
}

function MobileBar({ title, onMenu }: { title: string; onMenu: () => void }) {
  const { t } = useLocale();
  return <header className="obs-mobilebar">
    <button className="obs-icon obs-mobilebar-menu" onClick={onMenu} aria-label={t("Abrir la cartera", "Open the portfolio")}><Menu size={20} aria-hidden="true"/></button>
    <span className="obs-mobilebar-title">{title}</span>
    <Link href="/" aria-label="AXIGNAL"><img src="/brand/isotope.svg" alt="" width={26} height={26}/></Link>
  </header>;
}

function RailSheet({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  const { t } = useLocale();
  const ref = useRef<HTMLDivElement>(null);
  useFocusTrap(true, ref, onClose);
  return <div className="obs-sheet-backdrop" onClick={onClose}>
    <div ref={ref} className="obs-sheet" role="dialog" aria-modal="true" aria-label={t("Cartera", "Portfolio")} onClick={e => e.stopPropagation()}>
      <button className="obs-icon obs-sheet-close" onClick={onClose} aria-label={t("Cerrar", "Close")}><X size={20} aria-hidden="true"/></button>
      {children}
    </div>
  </div>;
}

// ---- desk: the whole portfolio at a glance ------------------------------------------------

function DeskView({ items, readings, seen, nameOf, onOpen, onAdd, reportLit }: {
  items: Item[]; readings: Record<string, Reading | "failed">; seen: SeenStore; nameOf: (item: Item) => string;
  onOpen: (focusId: string, item?: string | null) => void; onAdd: () => void; reportLit: (focusId: string, count: number) => void;
}) {
  const { t, locale } = useLocale();
  const rows = items.map(item => {
    const reading = readings[item.focusId];
    const insights = reading && reading !== "failed" ? insightsFor(reading, t, locale) : [];
    const lit = reading && reading !== "failed" ? litKeys(seen, item.focusId, insights.map(i => i.changeKey)) : new Set<string>();
    return { item, reading, insights, lit };
  });
  const attention = rows.filter(r => lensState(r.item) === "low" || r.item.state === "IDENTITY_PENDING" && !r.item.observation || r.reading === "failed");
  const loaded = rows.filter(r => r.reading && r.reading !== "failed").length;
  const readableCount = items.filter(readable).length;
  const all = rows.flatMap(r => r.insights.map(insight => ({ ...r, insight })));
  const opportunities = all.filter(r => r.insight.lane === "matters" && r.insight.nature === "POTENTIAL");
  const clarify = all.filter(r => r.insight.nature === "CLARIFY");
  const fresh = all.filter(r => r.lit.has(r.insight.changeKey));
  const observing = items.filter(i => lensState(i) === "observing");
  const litSignature = rows.map(r => `${r.item.focusId}:${r.reading && r.reading !== "failed" ? r.lit.size : -1}`).join(",");
  useEffect(() => { for (const entry of litSignature.split(",")) { const [id, n] = entry.split(":"); if (id && Number(n) >= 0) reportLit(id, Number(n)); } }, [litSignature, reportLit]);
  return <section className="obs-desk" aria-labelledby="desk-title">
    <header className="obs-desk-head">
      <h1 id="desk-title">{t("Tu cartera", "Your portfolio")}</h1>
      <p className="obs-lede">{fill(items.length === 1 ? t("{n} organización observada.", "{n} organization observed.") : t("{n} organizaciones observadas.", "{n} organizations observed."), { n: items.length })}{" "}
        {fresh.length ? fill(fresh.length === 1 ? t("{n} hallazgo nuevo desde tu última visita.", "{n} new finding since your last visit.") : t("{n} hallazgos nuevos desde tu última visita.", "{n} new findings since your last visit."), { n: fresh.length }) : ""}{" "}
        {observing.length ? fill(t("{n} en observación ahora.", "{n} being observed now."), { n: observing.length }) : ""}</p>
      {loaded < readableCount && <p className="obs-progress" role="status"><span className="obs-progress-bar" style={{ inlineSize: `${Math.round(loaded / Math.max(1, readableCount) * 100)}%` }}/>{t("Leyendo las lecturas de tu cartera", "Reading your portfolio's readings")} · {loaded}/{readableCount}</p>}
    </header>
    <div className="obs-desk-grid">
      <DeskColumn title={t("Oportunidades potenciales", "Potential opportunities")} lane="matters" empty={t("Ninguna en las lecturas actuales. Sin resultado no es sin oportunidad.", "None in the current readings. No result is not no opportunity.")}
        rows={opportunities.map(r => ({ key: r.insight.id + r.item.focusId, org: nameOf(r.item), insight: r.insight, lit: r.lit.has(r.insight.changeKey), open: () => onOpen(r.item.focusId, r.insight.id) }))}/>
      <DeskColumn title={t("Comunicación que conviene aclarar", "Communication worth clarifying")} lane="understood" empty={t("Nada que aclarar en las lecturas actuales.", "Nothing to clarify in the current readings.")}
        rows={clarify.map(r => ({ key: r.insight.id + r.item.focusId, org: nameOf(r.item), insight: r.insight, lit: r.lit.has(r.insight.changeKey), open: () => onOpen(r.item.focusId, r.insight.id) }))}/>
      <section className="obs-desk-col obs-lane-unknown" aria-labelledby="desk-attention">
        <h2 id="desk-attention">{t("Necesitan tu atención", "Need your attention")}</h2>
        {attention.length ? <ul>{attention.map(r => <li key={r.item.focusId}><button className="obs-desk-row" onClick={() => readable(r.item) ? onOpen(r.item.focusId) : onAdd()}>
          <span className="obs-desk-org">{nameOf(r.item)}</span><span className="obs-desk-text">{r.reading === "failed" ? t("La lectura no está disponible ahora.", "The reading is unavailable right now.") : itemStatus(r.item, t)}</span>
        </button></li>)}</ul> : <p className="obs-empty">{t("Todas las organizaciones se pueden observar.", "Every organization can be observed.")}</p>}
      </section>
    </div>
    <section className="obs-desk-table" aria-labelledby="desk-orgs">
      <h2 id="desk-orgs">{t("Organizaciones", "Organizations")}</h2>
      <ul>{rows.map(r => {
        const lanes = byLane(r.insights);
        return <li key={r.item.focusId}><button className="obs-desk-org-row" disabled={!readable(r.item)} onClick={() => onOpen(r.item.focusId)}>
          <Lens state={lensState(r.item)} lit={observedSinceVisit(seen, r.item.focusId, r.item.observation?.observedAt) || r.lit.size > 0}/>
          <span className="obs-desk-org-name">{nameOf(r.item)}<small>{r.item.observation?.headline ? activityLabel(r.item.observation.headlineCode ?? "", r.item.observation.headline, t) : itemStatus(r.item, t)}</small></span>
          <span className="obs-desk-counts">{r.reading && r.reading !== "failed" ? <>
            <span className="obs-count obs-lane-matters">{t("Importa", "Matters")} <strong>{lanes.matters.length}</strong></span>
            <span className="obs-count obs-lane-understood">{t("Se entiende", "Understood")} <strong>{lanes.understood.length}</strong></span>
            <span className="obs-count obs-lane-unknown">{t("Por saber", "To learn")} <strong>{lanes.unknown.length}</strong></span>
          </> : r.reading === "failed" ? t("Sin lectura", "No reading") : readable(r.item) ? <span className="obs-shimmer" aria-hidden="true"/> : "—"}</span>
          <span className="obs-desk-when">{relative(r.item.observation?.observedAt, locale)}</span>
          <ArrowRight size={16} aria-hidden="true"/>
        </button></li>;
      })}</ul>
    </section>
  </section>;
}

type DeskRow = { key: string; org: string; insight: Insight; lit: boolean; open: () => void };

function DeskColumn({ title, lane, rows, empty }: { title: string; lane: Lane; empty: string; rows: DeskRow[] }) {
  const { t } = useLocale();
  const id = `desk-${lane}`;
  // The same finding in several organizations is one pattern, read once (no mental joins).
  const groups: DeskRow[][] = [];
  for (const row of rows) {
    const group = groups.find(g => g[0].insight.headline === row.insight.headline);
    if (group) group.push(row); else groups.push([row]);
  }
  return <section className={`obs-desk-col obs-lane-${lane}`} aria-labelledby={id}>
    <h2 id={id}>{title}<span className="obs-lane-count">{rows.length}</span></h2>
    {groups.length ? <ul>{groups.slice(0, 8).map(group => {
      const first = group[0];
      const lit = group.some(r => r.lit);
      return <li key={first.key}>
        <div className={`obs-desk-row${lit ? " obs-lit" : ""}`}>
          <button className="obs-desk-row-main" onClick={first.open}>
            <span className="obs-desk-text">{first.insight.headline}</span>
            <span className="obs-desk-meta"><NatureMark nature={first.insight.nature} label={natureLabel(first.insight.nature, t)}/>{lit && <span className="obs-new">{t("Nuevo", "New")}</span>}</span>
          </button>
          <span className="obs-desk-orgs">{group.length > 1 && <span className="obs-desk-in">{fill(t("{n} organizaciones:", "{n} organizations:"), { n: group.length })}</span>}
            {group.map(r => <button key={r.key} className="obs-org-chip" onClick={r.open}>{r.org}</button>)}</span>
        </div>
      </li>;
    })}</ul> : <p className="obs-empty">{empty}</p>}
    {groups.length > 8 && <p className="obs-more">{fill(t("Y {n} más dentro de cada organización.", "And {n} more inside each organization."), { n: groups.length - 8 })}</p>}
  </section>;
}

// ---- organization ---------------------------------------------------------------------------

type OrgProps = ObservatoryProps & {
  item: Item; name: string; view: View; itemId: string | null; family: string | null; channel: string | null; locale: string;
  go: (next: Partial<{ view: View; screen: "account" | "add" | null; item: string | null; organization: string | null; family: string | null; channel: string | null }>, replace?: boolean) => void;
  seen: SeenStore; updateSeen: (change: (store: SeenStore) => SeenStore) => void;
  axentOpen: boolean; setAxentOpen: (open: boolean) => void;
  reportLit: (focusId: string, count: number) => void;
};

function OrganizationView(props: OrgProps) {
  const { t, copy } = useLocale();
  const { item, name, view, itemId, go, seen, updateSeen, locale, projection, firstObservation, revision } = props;
  const ready = !props.reading && (projection || firstObservation);
  const reading: Reading = useMemo(() => ({ projection, firstObservation }), [projection, firstObservation]);
  const insights = useMemo(() => ready ? insightsFor(reading, t, locale) : [], [ready, reading, t, locale]);
  const keys = useMemo(() => insights.map(i => i.changeKey), [insights]);
  const lit = useMemo(() => litKeys(seen, item.focusId, keys), [seen, item.focusId, keys]);
  const facet = useMemo(() => parseFacet(props.family, props.channel), [props.family, props.channel]);
  const shown = useMemo(() => facet.family ? insights.filter(i => matchesFacet(i, facet)) : insights, [insights, facet]);
  const shownKeys = useMemo(() => shown.map(i => i.changeKey), [shown]);
  const litShown = useMemo(() => new Set(shownKeys.filter(k => lit.has(k))), [shownKeys, lit]);
  const counts = useMemo(() => countByFacet(insights), [insights]);
  const litFamilies = useMemo(() => litByFamily(insights, lit), [insights, lit]);
  const scope = useMemo(() => scopeCopy(facet, t, copy), [facet, t, copy]);
  const selectFacet = (next: Facet) => transition(() => props.go({ ...facetParams(next), item: null }));
  const { reportLit } = props;
  useEffect(() => { if (ready) reportLit(item.focusId, lit.size); }, [ready, item.focusId, lit.size, reportLit]);
  useEffect(() => {
    if (!ready) return;
    const now = new Date().toISOString();
    updateSeen(store => store[item.focusId] ? touch(store, item.focusId, now) : baseline(store, item.focusId, keys, now));
  }, [ready, item.focusId, keys, updateSeen]);
  // A finding that has been in view, in a visible tab, for a moment has been seen: it stops being lit without a click.
  useEffect(() => {
    if (!ready || view !== "summary" || litShown.size === 0 || typeof IntersectionObserver === "undefined") return;
    const keyOf = new Map(shown.map(insight => [insight.id, insight.changeKey]));
    const timers = new Map<Element, number>();
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        const key = keyOf.get((entry.target as HTMLElement).dataset.insight ?? "");
        if (!key || !litShown.has(key)) continue;
        const running = timers.get(entry.target);
        if (entry.isIntersecting && entry.intersectionRatio >= SEEN_VISIBLE_RATIO && document.visibilityState === "visible") {
          if (running === undefined) timers.set(entry.target, window.setTimeout(() => {
            timers.delete(entry.target);
            updateSeen(store => markSeen(store, item.focusId, [key], new Date().toISOString()));
          }, SEEN_DWELL_MS));
        } else if (running !== undefined) { window.clearTimeout(running); timers.delete(entry.target); }
      }
    }, { threshold: [0, SEEN_VISIBLE_RATIO] });
    document.querySelectorAll<HTMLElement>("[data-insight]").forEach(card => observer.observe(card));
    return () => { observer.disconnect(); timers.forEach(id => window.clearTimeout(id)); };
  }, [ready, view, shown, litShown, item.focusId, updateSeen]);
  const open = insights.find(i => i.id === itemId) ?? null;
  const [menu, setMenu] = useState(false);
  const opener = useRef<string | null>(null);
  const openInsight = (insight: Insight) => {
    opener.current = insight.id;
    props.setAxentOpen(false);
    transition(() => go({ item: insight.id }));
    if (lit.has(insight.changeKey)) window.setTimeout(() => updateSeen(store => markSeen(store, item.focusId, [insight.changeKey], new Date().toISOString())), 700);
  };
  const closeDepth = () => {
    transition(() => { go({ item: null }); props.setAxentOpen(false); });
    window.requestAnimationFrame(() => { if (opener.current) document.querySelector<HTMLElement>(`[data-insight="${CSS.escape(opener.current)}"]`)?.focus(); });
  };
  const observing = item.observation && OBSERVING.has(item.observation.state);
  const identified = Boolean(item.organizationId);
  const observedAt = projection?.cognition?.asOf ?? firstObservation?.observedAt ?? item.observation?.observedAt ?? null;
  const tabs: Array<[View, string]> = [["summary", t("Resumen", "Summary")], ["explore", t("Explorar", "Explore")], ["evolution", t("Evolución", "Evolution")], ["evidence", t("Evidencias", "Evidence")]];
  const depthOpen = Boolean(open) || props.axentOpen;
  return <div className={`obs-org-view${depthOpen ? " obs-has-depth" : ""}`}>
    <div className="obs-org-main">
      <header className="obs-org-head">
        <div className="obs-org-title">
          <span className="obs-focus-lens" aria-hidden="true"><img src="/brand/isotope.svg" alt="" width={34} height={34}/></span>
          <div>
            <h1>{name}</h1>
            <p className="obs-org-meta">
              <span className={`obs-chip${identified ? " obs-chip-ok" : ""}`}>{identified ? t("Identidad verificada por registro", "Identity verified by registry") : t("Identidad por resolver", "Identity unresolved")}</span>
              {observedAt && <span>{t("Observada", "Observed")} <time dateTime={observedAt}>{formatDate(observedAt, locale, true)}</time></span>}
              {props.projection?.cognition && <span>{props.projection.cognition.sources.length} {t("fuentes", "sources")}</span>}
            </p>
          </div>
        </div>
        <div className="obs-org-actions">
          {item.state === "ACTIVE" && <button className="obs-button" disabled={props.busy || !props.canAct} onClick={() => void props.command({ action: "reobserve", focusId: item.focusId })}><RefreshCw size={16} aria-hidden="true"/><span className="obs-collapse">{t("Volver a observar", "Observe again")}</span></button>}
          {!identified && props.capabilities.recheck && <button className="obs-button" disabled={props.busy || !props.canAct} onClick={() => void props.command({ action: "retry_pending", focusId: item.focusId })}><RefreshCw size={16} aria-hidden="true"/><span className="obs-collapse">{t("Volver a comprobar", "Check again")}</span></button>}
          {projection && revision && <span className="obs-axent-cta"><button className={`obs-button obs-axent-button${props.axentOpen && !open ? " obs-active" : ""}`} onClick={() => { transition(() => { go({ item: null }); props.setAxentOpen(true); }); }}><MessageCircleQuestion size={16} aria-hidden="true"/>{t("Preguntar a AXENT", "Ask AXENT")}</button><span className="obs-axent-note"><CornerRightUp size="1.15em" aria-hidden="true"/>{t("¿Dudas? Pregúntale a AXENT", "Any doubts? Ask AXENT")}</span></span>}
          {props.capabilities.manage && <div className="obs-menu">
            <button className="obs-icon" aria-expanded={menu} aria-haspopup="true" aria-label={t("Más acciones", "More actions")} onClick={() => setMenu(!menu)}><ChevronDown size={18} aria-hidden="true"/></button>
            {menu && <ul className="obs-menu-list" onKeyDown={e => { if (e.key === "Escape") setMenu(false); }}>
              {identified && <li><button disabled={props.busy || !props.canAct} onClick={() => { setMenu(false); void props.command({ action: item.state === "PAUSED" ? "resume" : "pause", focusId: item.focusId }); }}>{item.state === "PAUSED" ? t("Reanudar", "Resume") : t("Pausar", "Pause")}</button></li>}
              {identified && <li><button disabled={props.busy || !props.canAct} onClick={() => { setMenu(false); props.setReplacing(item.focusId); props.setReplacementLocator(""); }}>{t("Sustituir organización", "Replace organization")}</button></li>}
              <li><button disabled={props.busy || !props.canAct} onClick={() => { setMenu(false); void props.command({ action: identified ? "remove" : "cancel_pending", focusId: item.focusId }); }}>{t("Retirar de mi cartera", "Remove from my portfolio")}</button></li>
            </ul>}
          </div>}
        </div>
      </header>
      {props.replacing === item.focusId && <form className="obs-inline-form" onSubmit={e => { e.preventDefault(); void props.command({ action: "replace", focusId: item.focusId, locator: props.replacementLocator }); }}>
        <label htmlFor={`replacement-${item.focusId}`}>{t("Nombre o sitio público", "Name or public website")}</label>
        <input id={`replacement-${item.focusId}`} required maxLength={2048} value={props.replacementLocator} onChange={e => props.setReplacementLocator(e.target.value)} disabled={props.busy || !props.canAct}/>
        <p>{t("La sustitución conserva el historial privado. La organización actual permanece hasta resolver la nueva identidad.", "Replacement preserves private history. The current organization remains until the new identity is resolved.")}</p>
        <div className="obs-form-actions"><button className="obs-button obs-primary" disabled={props.busy || !props.replacementLocator.trim()}>{t("Sustituir organización", "Replace organization")}</button><button type="button" className="obs-link" onClick={() => props.setReplacing(null)}>{t("Cancelar", "Cancel")}</button></div>
      </form>}
      <div className="obs-tabs" role="tablist" aria-label={t("Profundidad", "Depth")}>
        {tabs.map(([id, label]) => <button key={id} role="tab" id={`tab-${id}`} aria-selected={view === id} aria-controls={`panel-${id}`} tabIndex={view === id ? 0 : -1}
          onClick={() => transition(() => go({ view: id, item: null }))}
          onKeyDown={e => {
            const index = tabs.findIndex(([v]) => v === id);
            const next = e.key === "ArrowRight" ? tabs[(index + 1) % tabs.length] : e.key === "ArrowLeft" ? tabs[(index + tabs.length - 1) % tabs.length] : null;
            if (next) { e.preventDefault(); go({ view: next[0], item: null }); window.requestAnimationFrame(() => document.getElementById(`tab-${next[0]}`)?.focus()); }
          }}>{label}</button>)}
      </div>
      {ready && !observing && view !== "explore" && <FamilyNav facet={facet} counts={counts} lit={litFamilies} onSelect={selectFacet}/>}
      <div className="obs-panel" role="tabpanel" id={`panel-${view}`} aria-labelledby={`tab-${view}`}>
        {props.reading && <ReadingSkeleton/>}
        {!props.reading && observing && <ObservingState state={item.observation!.state}/>}
        {!props.reading && !observing && view === "summary" && <SummaryView reading={reading} name={name} insights={shown} lit={litShown} openId={open?.id ?? null} onOpen={openInsight} scope={scope}
          onSeenAll={() => updateSeen(store => markSeen(store, item.focusId, shownKeys, new Date().toISOString()))} item={item}/>}
        {!props.reading && !observing && view === "explore" && <ExploreView projection={projection} revision={revision} firstObservation={firstObservation} onSummary={() => go({ view: "summary" })}/>}
        {!props.reading && !observing && view === "evolution" && <EvolutionView reading={reading} facet={facet} scope={scope}/>}
        {!props.reading && !observing && view === "evidence" && <EvidenceView reading={reading} facet={facet} scope={scope} insights={shown}/>}
      </div>
    </div>
    {depthOpen && <DepthPanel insight={open} projection={projection} revision={revision} axentOnly={!open} canAct={props.canAct} axent={props.capabilities.axent} onClose={closeDepth}
      onEvidence={() => transition(() => go({ view: "evidence", item: null }))} onExplore={() => transition(() => go({ view: "explore", item: null }))}/>}
  </div>;
}

function ReadingSkeleton() {
  const { t } = useLocale();
  return <div className="obs-skeleton" role="status" aria-label={t("Leyendo las evidencias…", "Reading the evidence…")}>
    <span className="obs-shimmer obs-shimmer-lead"/><span className="obs-shimmer obs-shimmer-line"/>
    <div className="obs-lanes">{[0, 1, 2].map(i => <span key={i} className="obs-shimmer obs-shimmer-card"/>)}</div>
  </div>;
}

/** Truthful progress: only the stage the runtime reports, never a fake percentage (MASTER §9.4). */
function ObservingState({ state }: { state: string }) {
  const { t } = useLocale();
  const stages: Array<[string, string, string]> = [
    ["QUEUED", t("En cola", "Queued"), t("La observación está guardada y empezará en segundo plano.", "The observation is saved and will start in the background.")],
    ["OBSERVING_PUBLIC_PRESENCE", t("Observando su presencia pública", "Observing its public presence"), t("Leemos sus páginas públicas respetando robots.txt y nuestros límites.", "We read its public pages within robots.txt and our limits.")],
    ["FIRST_PROOF_READY", t("Primera lectura con evidencias", "First reading with evidence"), t("Aparecerá aquí en cuanto exista, con sus fuentes.", "It will appear here as soon as it exists, with its sources.")],
  ];
  const at = stages.findIndex(([s]) => s === state);
  return <section className="obs-observing" aria-live="polite">
    <div className="obs-observing-lens" aria-hidden="true"><svg viewBox="0 0 120 120"><circle className="obs-scan-ring" cx="60" cy="60" r="44"/><circle className="obs-scan-sweep" cx="60" cy="60" r="44"/></svg><img src="/brand/isotope.svg" alt="" width={52} height={52}/></div>
    <h2>{t("AXIGNAL está observando esta organización.", "AXIGNAL is observing this organization.")}</h2>
    <ol className="obs-stages">{stages.map(([id, label, detail], i) => <li key={id} className={i < at ? "done" : i === at ? "current" : ""} aria-current={i === at ? "step" : undefined}><span className="obs-stage-dot" aria-hidden="true"/><span><strong>{label}</strong><small>{detail}</small></span></li>)}</ol>
    <p className="obs-quiet">{t("Puedes seguir trabajando: esta página se actualiza sola cuando cambia el estado real.", "You can keep working: this page updates itself when the real state changes.")}</p>
  </section>;
}

export function SummaryView({ reading, name, insights, lit, openId, onOpen, onSeenAll, item, exampleLead, scope }: {
  reading: Reading; name: string; insights: Insight[]; lit: Set<string>; openId: string | null;
  /** A selected family or channel: its header and empty state. Absent for the whole reading. */
  scope?: FacetScope | null;
  onOpen: (insight: Insight) => void; onSeenAll: () => void; item: Pick<Item, "observation">;
  /** Only the explicitly fictional public example supplies a fixture lead. */
  exampleLead?: string;
}) {
  const { t, locale } = useLocale();
  const brief = briefing(reading, name, insights, t, locale);
  if (exampleLead) brief.lead = exampleLead;
  const lanes = byLane(insights);
  const low = item.observation && LOW_OBSERVABILITY.has(item.observation.state);
  return <div className="obs-summary">
    <section className={`obs-brief${scope ? " obs-brief-scoped" : ""}`} aria-label={scope ? scope.title : t("En resumen", "In short")}>
      {scope && <h2 className="obs-scope-title">{scope.title}</h2>}
      <p className="obs-brief-lead">{scope ? scope.intro : brief.lead}</p>
      {scope ? <ul className="obs-tally"><li>{fill(insights.length === 1 ? t("{n} hallazgo", "{n} finding") : t("{n} hallazgos", "{n} findings"), { n: insights.length })}</li></ul>
        : brief.tally.length > 0 && <ul className="obs-tally">{brief.tally.map(x => <li key={x}>{x}</li>)}</ul>}
      {low && <p className="obs-brief-note">{observationStateCopy(item.observation!.state, t)}. {t("Lo que no se pudo observar aparece en «Lo que aún no sabemos», con su razón.", "What could not be observed appears under “What we do not know yet”, with its reason.")}</p>}
      {lit.size > 0 && <div className="obs-since" role="status">
        <span className="obs-since-lamp" aria-hidden="true"/>
        <span>{fill(lit.size === 1 ? t("{n} hallazgo nuevo o cambiado desde tu última visita.", "{n} finding new or changed since your last visit.") : t("{n} hallazgos nuevos o cambiados desde tu última visita.", "{n} findings new or changed since your last visit."), { n: lit.size })} <small>{t("Se recuerda en este dispositivo.", "Remembered on this device.")}</small></span>
        <button className="obs-link" onClick={onSeenAll}>{t("Marcar como visto", "Mark as seen")}</button>
      </div>}
    </section>
    {scope && !insights.length ? <section className="obs-empty-state"><h2>{scope.emptyTitle}</h2><p>{scope.emptyBody}</p></section> : <div className="obs-lanes">
      {(["matters", "understood", "unknown"] as Lane[]).map(lane => {
        const copy = laneCopy(lane, t);
        return <section key={lane} className={`obs-lane obs-lane-${lane}`} aria-labelledby={`lane-${lane}`}>
          <header><h2 id={`lane-${lane}`}>{copy.title}<span className="obs-lane-count">{lanes[lane].length}</span></h2><p>{copy.question}</p></header>
          {lanes[lane].length ? <ul>{lanes[lane].map((insight, index) => <li key={insight.id} style={{ ["--i" as string]: index }}><InsightCard insight={insight} lit={lit.has(insight.changeKey)} active={openId === insight.id} onOpen={() => onOpen(insight)}/></li>)}</ul>
            : <p className="obs-empty">{copy.empty}</p>}
        </section>;
      })}
    </div>}
  </div>;
}

export function InsightCard({ insight, lit, active, onOpen }: { insight: Insight; lit: boolean; active: boolean; onOpen: () => void }) {
  const { t, locale } = useLocale();
  const source = insight.sources[0];
  return <button className={`obs-card${lit ? " obs-lit" : ""}${active ? " obs-active" : ""}`} data-insight={insight.id} aria-expanded={active} aria-controls="obs-depth" onClick={onOpen}>
    <span className="obs-card-headline">{insight.headline}{lit && <span className="obs-new">{t("Nuevo", "New")}</span>}</span>
    {insight.why && <span className="obs-card-why">{insight.why}</span>}
    {insight.previous && <span className="obs-card-before">{t("Antes", "Before")}: {insight.previous}</span>}
    <span className="obs-card-foot">
      <NatureMark nature={insight.nature} label={natureLabel(insight.nature, t)}/>
      {insight.observedAt && <time dateTime={insight.observedAt}>{relative(insight.observedAt, locale)}</time>}
      {source?.url && <span>{host(source.url)}</span>}
      <span className="obs-card-go">{t("Por qué", "Why")}<ArrowRight size={14} aria-hidden="true"/></span>
    </span>
  </button>;
}

// ---- depth: meaning → reasoning → proof → AXENT, beside the finding ----------------------------

/** GLANCE → UNDERSTAND → REASON → PROVE for one finding; the same body wherever it is shown. */
export function InsightBody({ insight, onEvidence }: { insight: Insight; onEvidence?: () => void }) {
  const { t, locale } = useLocale();
  return <article className="obs-depth-body">
      <NatureMark nature={insight.nature} label={natureLabel(insight.nature, t)}/>
      <h2 tabIndex={-1}>{insight.headline}</h2>
      {insight.why && <p className="obs-depth-why">{insight.why}</p>}
      {insight.previous && <p className="obs-card-before">{t("En la lectura anterior comparable", "In the previous comparable reading")}: {insight.previous}. {t("Un cambio de interpretación no demuestra por sí solo una mejora comercial.", "An interpretation change alone does not prove a business improvement.")}</p>}
      <section><h3>{t("Qué significa", "What it means")}</h3>{insight.meaning.map(x => <p key={x}>{x}</p>)}</section>
      {insight.dimensions.length > 0 && <section><h3>{t("Lo que se ha comprobado", "What has been checked")}</h3>
        <ul className="obs-dimensions">{insight.dimensions.map(d => <li key={d.label} className={`obs-dim-${d.state.toLowerCase()}`}><NatureMark nature={d.state === "UNKNOWN" ? "UNKNOWN" : "OBSERVED"} label={d.label}/><span>{d.outcome}</span></li>)}</ul>
        <p className="obs-quiet">{t("Sin puntuación: cada dimensión se muestra con su estado.", "No score: each dimension is shown with its state.")}</p></section>}
      {insight.reasoning.length > 0 && <section><h3>{t("Por qué lo dice AXIGNAL", "Why AXIGNAL says so")}</h3>{insight.reasoning.map(x => <p key={x}>{x}</p>)}</section>}
      {insight.proposal && <section className="obs-proposal"><h3>{t("Propuesta condicionada", "Conditional proposal")}</h3><p>{insight.proposal}</p><p className="obs-quiet">{t("Una mejora sugerida no es una causa demostrada. Vuelve a observar después para comprobar si cambia la interpretación.", "A suggested improvement is not a demonstrated cause. Observe again afterwards to check whether the interpretation changes.")}</p></section>}
      {(insight.sources.length > 0 || insight.proof.length > 0) && <section><h3>{t("Pruebas", "Evidence")}</h3>
        {insight.sources.map((s, i) => { const link = evidenceUrl(s.url); return <figure key={i} className="obs-source">
          {s.quote && <blockquote>“{s.quote}”</blockquote>}
          <figcaption>{link ? <a href={link} target="_blank" rel="noopener noreferrer">{s.label}<ExternalLink size={13} aria-hidden="true"/><span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a> : <span>{s.label}</span>}{s.observedAt && <time dateTime={s.observedAt}>{formatDate(s.observedAt, locale)}</time>}</figcaption>
        </figure>; })}
        {insight.proof.length > 0 && <dl className="obs-proof">{insight.proof.map(p => <div key={p.label + p.value}><dt>{p.label}</dt><dd>{p.value}</dd></div>)}</dl>}
        {onEvidence && <button className="obs-link" onClick={onEvidence}>{t("Ver todas las evidencias de esta organización", "See all evidence for this organization")}<ArrowRight size={14} aria-hidden="true"/></button>}
      </section>}
  </article>;
}

function DepthPanel({ insight, projection, revision, axentOnly, canAct, axent, onClose, onEvidence, onExplore }: {
  insight: Insight | null; projection: RuntimeProjection | null; revision: string | null; axentOnly: boolean; canAct: boolean; axent: "subscriber" | "admin";
  onClose: () => void; onEvidence: () => void; onExplore: () => void;
}) {
  const { t, locale } = useLocale();
  const ref = useRef<HTMLElement>(null);
  const [mobile, setMobile] = useState(false);
  useEffect(() => { const m = window.matchMedia("(max-width: 880px)"); const set = () => setMobile(m.matches); set(); m.addEventListener("change", set); return () => m.removeEventListener("change", set); }, []);
  useFocusTrap(mobile, ref, onClose);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    if (!mobile) ref.current?.querySelector<HTMLElement>("h2")?.focus();
    return () => window.removeEventListener("keydown", onKey);
  }, [insight?.id, mobile, onClose]);
  return <aside ref={ref} id="obs-depth" className={`obs-depth${insight ? ` obs-lane-${insight.lane}` : " obs-depth-axent-only"}`} aria-label={insight ? t("Profundizar", "Go deeper") : t("Preguntar a AXENT", "Ask AXENT")} {...(mobile ? { role: "dialog", "aria-modal": true } : {})}>
    <div className={`obs-depth-bar${insight ? "" : " obs-depth-bar-bare"}`}>
      <button className="obs-icon" onClick={onClose} aria-label={t("Volver", "Back")}>{mobile ? <ArrowLeft size={18} aria-hidden="true"/> : <X size={18} aria-hidden="true"/>}</button>
      {insight && <span>{laneCopy(insight.lane, t).title}</span>}
    </div>
    {insight && <InsightBody insight={insight} onEvidence={onEvidence}/>}
    {projection && revision ? <DepthAxent projection={projection} revision={revision} axent={axent} insight={insight} canAct={canAct} onEvidence={onEvidence} onExplore={onExplore} autoFocus={axentOnly}/>
      : <section className="obs-depth-axent obs-quiet"><h3>AXENT</h3><p>{t("AXENT podrá investigar con esta organización cuando su identidad esté verificada por un registro. Esta lectura ya muestra su evidencia.", "AXENT can investigate this organization once its identity is verified by a registry. This reading already shows its evidence.")}</p></section>}
  </aside>;
}

function DepthAxent({ projection, revision, axent, insight, canAct, onEvidence, onExplore, autoFocus }: {
  projection: RuntimeProjection; revision: string; axent: "subscriber" | "admin"; insight: Insight | null; canAct: boolean; onEvidence: () => void; onExplore: () => void; autoFocus: boolean;
}) {
  const { t } = useLocale();
  // The subscriber's questions are scoped to its reading; an Admin session asks through its own endpoint.
  const scope = useMemo(() => axent === "subscriber" ? { revision } : undefined, [axent, revision]);
  const conversation = useRuntimeAxent(projection, null, scope);
  const asked = useRef<string | null>(null);
  const question = insight ? fill(t("{finding}: ¿por qué importa y qué sigue abierto?", "{finding}: why does it matter and what remains open?"), { finding: insight.headline }) : null;
  useEffect(() => { asked.current = null; }, [insight?.id]);
  if (!canAct) return <section className="obs-depth-axent" aria-label="AXENT"><p className="obs-empty">{t("Las preguntas a AXENT se activan con tu cuenta.", "AXENT questions are available with your account.")}</p></section>;
  return <section className="obs-depth-axent" aria-label="AXENT">
    {question && asked.current !== insight?.id && conversation.messages.length === 0 && <button className="obs-button obs-ask" disabled={conversation.busy} onClick={() => { asked.current = insight?.id ?? null; void conversation.ask(question); }}>
      <MessageCircleQuestion size={16} aria-hidden="true"/>{t("Pregunta a AXENT sobre esto", "Ask AXENT about this")}</button>}
    <RuntimeAxent projection={projection} signalId={null} conversation={conversation} onEvidence={onEvidence} onSignal={onExplore} focusLabel={insight ? insight.headline : t("Toda la organización", "The whole organization")}/>
    {autoFocus && <span className="sr-only" role="status">{t("AXENT abierto en el contexto de esta organización.", "AXENT opened in this organization's context.")}</span>}
  </section>;
}

// ---- explore, evolution, evidence: the same object at other depths ------------------------------

function ExploreView({ projection, revision, firstObservation, onSummary }: { projection: RuntimeProjection | null; revision: string | null; firstObservation: FirstObservation | null; onSummary: () => void }) {
  const { t } = useLocale();
  const canRead = Boolean(projection && (projection.nodes.length > 0 || (projection.cognition && (projection.cognition.sources.length > 0 || projection.cognition.opportunities.length > 0))));
  if (projection && revision && canRead) return <div className="obs-explore"><p className="obs-section-lede">{t("Su mundo económico: dónde trabaja, dónde podría crecer, qué le afecta y las señales que lo sostienen.", "Its economic world: where it works, where it could grow, what affects it and the signals behind it.")}</p><SubscriberReading key={revision} projection={projection} revision={revision}/></div>;
  return <section className="obs-empty-state">
    <h2>{firstObservation ? t("El mundo económico se abre con la identidad verificada.", "The economic world opens with verified identity.") : t("Todavía no hay evidencia suficiente para explorar.", "There is not enough evidence to explore yet.")}</h2>
    <p>{t("Mientras tanto, el resumen y las evidencias muestran todo lo que AXIGNAL ha observado, con sus límites. Una ausencia aquí no demuestra ausencia en el mundo.", "Meanwhile, the summary and evidence show everything AXIGNAL has observed, with its limits. Absence here does not prove absence in the world.")}</p>
    <button className="obs-button" onClick={onSummary}>{t("Volver al resumen", "Back to the summary")}</button>
  </section>;
}

function EvolutionView({ reading, facet, scope }: { reading: Reading; facet: Facet; scope: FacetScope | null }) {
  const { t, locale } = useLocale();
  type Event = { at: string; title: string; detail: string; kind: "observation" | "reading" | "change"; facet: Facet };
  const events: Event[] = [];
  // Observations are grouped by moment and by the channel their source type belongs to; a change is only stated when the runtime compared them.
  const groups = new Map<string, { at: string; sources: string[]; changed: boolean | null; facet: Facet }>();
  for (const item of reading.projection?.temporalHistory.items ?? []) {
    const itemFacet = facetOfSourceType(item.sourceType);
    const key = item.observedAt.slice(0, 16) + "|" + itemFacet.family + "|" + itemFacet.channel;
    const group = groups.get(key) ?? { at: item.observedAt, sources: [], changed: null, facet: itemFacet };
    group.sources.push(host(item.sourceRef));
    if (item.normalizedStateChanged === true) group.changed = true; else if (item.normalizedStateChanged === false && group.changed === null) group.changed = false;
    groups.set(key, group);
  }
  for (const g of groups.values()) events.push({ at: g.at, kind: "observation", facet: g.facet,
    title: g.facet.channel === "SEO" ? t("Medición de visibilidad en buscadores", "Search visibility measurement")
      : g.facet.channel === "GEO" ? t("Medición en respuestas de IA", "AI answer measurement")
      : t("Observación de sus fuentes", "Observation of its sources"),
    detail: `${[...new Set(g.sources)].join(" · ")} — ${g.changed === true ? t("cambió lo observado", "what was observed changed") : g.changed === false ? t("sin cambios en lo observado", "no change in what was observed") : t("primera observación", "first observation")}` });
  const report = reading.firstObservation?.publicUnderstanding;
  if (report) {
    const value: Facet = { family: "value", channel: null };
    for (const old of report.history ?? []) events.push({ at: old.measuredAt, kind: "reading", facet: value, title: t("Lectura anterior de su oferta pública", "Previous reading of its public offer"), detail: old.status === "MEASURED" ? old.dimensions.map(d => `${dimensionCopy(d.dimension, t)}: ${stateCopy(d.state, t)}`).join(" · ") : causeCopy(old.cause, t) });
    events.push({ at: report.measuredAt, kind: report.comparison?.changes?.length ? "change" : "reading", facet: value, title: t("Lectura actual de su oferta pública", "Current reading of its public offer"),
      detail: report.comparison?.state === "COMPARABLE" ? (report.comparison.changes.length ? fill(t("{n} cambios de interpretación respecto a la lectura anterior; no demuestran por sí solos un resultado comercial.", "{n} interpretation changes since the previous reading; on their own they do not prove a business result."), { n: report.comparison.changes.length }) : t("Sin cambios de interpretación respecto a la lectura anterior.", "No interpretation change since the previous reading.")) : t("Primera lectura comparable.", "First comparable reading.") });
  }
  const visible = events.filter(e => matchesFacet(e.facet, facet));
  visible.sort((a, b) => b.at.localeCompare(a.at));
  if (!visible.length) return scope
    ? <section className="obs-empty-state"><h2>{fill(t("Todavía no hay observaciones de {scope} que comparar", "There are no observations of {scope} to compare yet"), { scope: scope.title })}</h2><p>{t("Un cambio solo se declara cuando hay dos observaciones comparables. Sin ellas no hay cambio que mostrar, ni a favor ni en contra.", "A change is only declared when there are two comparable observations. Without them there is no change to show, for or against.")}</p></section>
    : <section className="obs-empty-state"><h2>{t("La evolución empieza con la segunda observación.", "Evolution starts with the second observation.")}</h2><p>{t("AXIGNAL volverá a observar y te mostrará aquí qué cambió, cuándo y frente a qué.", "AXIGNAL will observe again and show you here what changed, when and against what.")}</p></section>;
  return <ol className="obs-timeline">{visible.map((e, i) => <li key={i} className={`obs-event obs-event-${e.kind}`}>
    <time dateTime={e.at}>{formatDate(e.at, locale, true)}</time><div><strong>{e.title}</strong>{e.facet.channel && !facet.channel && <span className="obs-event-tag">{channelLabel(e.facet.channel, t)}</span>}<p>{e.detail}</p></div>
  </li>)}</ol>;
}

function EvidenceView({ reading, facet, scope, insights }: { reading: Reading; facet: Facet; scope: FacetScope | null; insights: Insight[] }) {
  const { t, locale } = useLocale();
  const sources = reading.projection?.cognition?.sources ?? [];
  if (facet.family) {
    // A selection shows the evidence behind exactly the findings it contains, and the web measurement where it is the web.
    const seen = new Set<string>();
    // Each finding keeps its own evidence row; only a source repeated inside one finding is shown once.
    const rows = insights.flatMap(insight => insight.sources.map(source => ({ insight, source }))).filter(({ insight, source }) => {
      const key = [insight.id, source.url, source.label, source.observedAt].join("|");
      return seen.has(key) ? false : (seen.add(key), true);
    });
    const measurement = facet.family === "presence" && (!facet.channel || facet.channel === "WEB") ? reading.projection?.digitalRepresentation : undefined;
    if (!rows.length && !measurement) return <section className="obs-empty-state"><h2>{scope?.emptyTitle}</h2><p>{scope?.emptyBody}</p></section>;
    return <div className="obs-evidence">
      {rows.length > 0 && <section className="obs-sources" aria-labelledby="obs-sources-title"><h2 id="obs-sources-title">{t("Evidencia de esta selección", "Evidence for this selection")}</h2>
        <ul>{rows.map(({ insight, source }, index) => { const link = source.url ? evidenceUrl(source.url) : null; return <li key={index}>
          {link ? <a href={link} target="_blank" rel="noopener noreferrer">{source.label}<ExternalLink size={13} aria-hidden="true"/><span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a> : <span>{source.label}</span>}
          <span>{source.observedAt ? formatDate(source.observedAt, locale, true) : t("sin fecha", "undated")} · {natureLabel(insight.nature, t)}</span>
          <span className="obs-evidence-finding">{insight.headline}</span>
        </li>; })}</ul></section>}
      {measurement && <SubscriberRepresentation measurement={measurement}/>}
    </div>;
  }
  return <div className="obs-evidence">
    {sources.length > 0 && <section className="obs-sources" aria-labelledby="obs-sources-title"><h2 id="obs-sources-title">{t("Fuentes autorizadas de esta lectura", "Authorized sources of this reading")}</h2>
      <ul>{sources.map(s => { const link = evidenceUrl(s.sourceRef); return <li key={s.id}>
        {link ? <a href={link} target="_blank" rel="noopener noreferrer">{host(s.sourceRef)}<ExternalLink size={13} aria-hidden="true"/><span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a> : <span>{s.title}</span>}
        <span>{formatDate(s.observedAt, locale, true)} · {currentnessLabel(s.currentness, t)}</span>
      </li>; })}</ul></section>}
    {reading.projection?.digitalRepresentation && <SubscriberRepresentation measurement={reading.projection.digitalRepresentation}/>}
    {reading.firstObservation ? <FirstObservationView observation={reading.firstObservation}/> : !sources.length && <p className="obs-empty">{t("Todavía no hay evidencias admitidas para esta organización.", "There is no admitted evidence for this organization yet.")}</p>}
  </div>;
}

// ---- add & account ----------------------------------------------------------------------------

function AddView(props: ObservatoryProps & { first: boolean; onDone: () => void }) {
  const { t } = useLocale();
  return <section className={`obs-add${props.first ? " obs-first" : ""}`} aria-labelledby="add-title">
    <div className="obs-add-lens" aria-hidden="true"><img src="/brand/isotope.svg" alt="" width={72} height={72}/></div>
    <h1 id="add-title">{props.first ? t("¿Qué organización quieres comprender?", "Which organization do you want to understand?") : t("Añade una organización a tu cartera", "Add an organization to your portfolio")}</h1>
    <p className="obs-lede">{t("Escribe su nombre o su web pública. AXIGNAL la observará y te mostrará qué hace, qué importa a su alrededor, cómo se entiende su comunicación y qué no sabe todavía, con las pruebas de cada cosa.", "Type its name or public website. AXIGNAL will observe it and show you what it does, what matters around it, how its communication is understood and what it does not know yet, with the evidence for each.")}</p>
    <form className="obs-add-form" onSubmit={e => { e.preventDefault(); void props.command({ action: "add", locator: props.locator }); }}>
      <label htmlFor="organization-locator">{t("Nombre o sitio público", "Name or public website")}</label>
      <div className="obs-add-row"><input id="organization-locator" required maxLength={2048} list={props.suggestions?.length ? "organization-suggestions" : undefined} value={props.locator} onChange={e => props.setLocator(e.target.value)} disabled={props.busy || !props.canAct} placeholder={t("p. ej. empresa.com o Empresa SL", "e.g. company.com or Company Ltd")} autoComplete="off"/>
        <button className="obs-button obs-primary" disabled={props.busy || !props.locator.trim()}><Plus size={16} aria-hidden="true"/>{t("Empezar a observar", "Start observing")}</button></div>
      {props.suggestions && props.suggestions.length > 0 && <datalist id="organization-suggestions">{props.suggestions.map(name => <option key={name} value={name}/>)}</datalist>}
    </form>
    <ol className="obs-add-steps">
      <li><strong>{t("Identidad", "Identity")}</strong><span>{t("Buscamos su identidad legal en un registro. Un nombre o URL orienta; no establece la verdad.", "We look for its legal identity in a registry. A name or URL guides; it does not establish truth.")}</span></li>
      <li><strong>{t("Primera observación", "First observation")}</strong><span>{t("Leemos su presencia pública respetando sus reglas de acceso. Verás el estado real, sin cargas fingidas.", "We read its public presence within its access rules. You will see the real state, no fake loading.")}</span></li>
      <li><strong>{t("Tu primera lectura", "Your first reading")}</strong><span>{t("Qué hace, oportunidades potenciales, cómo se entiende y qué falta por saber, cada cosa con su prueba.", "What it does, potential opportunities, how it is understood and what is still unknown, each with its evidence.")}</span></li>
    </ol>
    {!props.first && <button className="obs-link" onClick={props.onDone}><ArrowLeft size={14} aria-hidden="true"/>{t("Volver a la cartera", "Back to the portfolio")}</button>}
  </section>;
}

function AccountView(props: ObservatoryProps) {
  const { t, locale } = useLocale();
  const portfolio = props.portfolio!;
  const used = portfolio.organizations.filter(item => item.state === "ACTIVE" || item.state === "PAUSED").length;
  return <section className="obs-account" aria-labelledby="account-title">
    <h1 id="account-title">{t("Cuenta y conexiones", "Account and connections")}</h1>
    <div className="obs-account-grid">
      <section className="obs-account-card" aria-labelledby="capacity-title">
        <h2 id="capacity-title">{t("Espacio para observar", "Room to observe")}</h2>
        <p>{portfolio.capacity === null || portfolio.capacityCurrentness !== "CURRENT" ? t("Capacidad sin confirmar", "Unconfirmed capacity") : fill(t("{used} de {total} organizaciones en uso", "{used} of {total} organizations in use"), { used, total: portfolio.capacity })} · {t("Las organizaciones pausadas conservan su espacio.", "Paused organizations retain their space.")}</p>
        {portfolio.entitlementSource === "DESIGN_PARTNER_PILOT" && <p className="obs-note">{t("Design Partner · 1 organización · 0 € durante el piloto de validación.", "Design Partner · 1 organization · €0 during the validation pilot.")}</p>}
        <form onSubmit={e => { e.preventDefault(); void props.command({ action: portfolio.capacity === null || portfolio.capacity === 0 ? "purchase" : "expand", desiredOrganizationTotal: props.total }); }}>
          <label htmlFor="organization-total">{t("Total de organizaciones", "Total organizations")}</label>
          <input id="organization-total" type="number" min={portfolio.capacity ? portfolio.capacity + 1 : 1} max={100000} step={1} required value={props.total} onChange={e => props.setTotal(Number(e.target.value))} disabled={props.busy || !props.canAct}/>
          <p className="obs-price">{Number.isSafeInteger(props.total) && props.total >= 1 && props.total <= 100000 ? new Intl.NumberFormat(locale, { style: "currency", currency: "EUR" }).format(monthlyCapacityCents(props.total) / 100) : "—"}<small>{t("Total mensual sin IVA; el pago confirma los impuestos aplicables.", "Monthly total excluding VAT; checkout confirms applicable taxes.")}</small></p>
          <button className="obs-button" disabled={props.busy || portfolio.canPurchase !== true || !portfolio.contractingEnabled}>{t("Revisar la compra", "Review the purchase")}<ArrowRight size={16} aria-hidden="true"/></button>
        </form>
        {!portfolio.contractingEnabled && <p className="obs-note">{t("La contratación todavía no está activa.", "Contracting is not active yet.")}</p>}
        {portfolio.canPurchase !== true && <p className="obs-quiet">{t("La autoridad de compra no está confirmada para este contexto.", "Purchase authority is not confirmed for this context.")}</p>}
        <button className="obs-link" disabled={props.busy || !props.canAct} onClick={() => void props.command({ action: "refresh_purchase" })}><RefreshCw size={14} aria-hidden="true"/>{t("Comprobar pago y capacidad", "Check payment and capacity")}</button>
      </section>
      <section className="obs-account-card"><SubscriberMcpConnections/></section>
    </div>
    <button className="obs-button" disabled={props.busy || !props.canAct} onClick={props.logout}><LogOut size={16} aria-hidden="true"/>{t("Cerrar sesión", "Sign out")}</button>
  </section>;
}
