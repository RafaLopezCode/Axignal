"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useLocale } from "@/lib/locale";
import { approvedPaymentUrl, pendingOutputSchema, pilotRedemptionSchema, subscriberOutputSchema, subscriberResultSchema, type FirstObservation, type SubscriberPortfolio } from "@/lib/subscriber-contracts";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { pendingPilotInvite, clearPilotInvite } from "@/lib/pilot-invite";
import { pendingMcpConnect, clearMcpConnect } from "@/lib/mcp-connect";
import { Observatory, type ObservatoryShell } from "./observatory";
import { accountSource, type ObservatorySource } from "@/lib/observatory-source";
import { billingReturn, capacityRoom, waitingItems, type ActivationPhase } from "@/lib/activation";

type PortfolioItem = SubscriberPortfolio["organizations"][number];
/** A canonical Focus reading, or a pending attention whose First Observation exists. */
const readable = (item: PortfolioItem) => Boolean(item.organizationId || item.observation);

/**
 * The subscriber Observatory. One experience, two contexts: the account's source, or the demonstration's.
 * Only the source differs (where data comes from and which operations exist); nothing below branches on it.
 */
export function SubscriberPortfolioExperience({ source = accountSource, notice, shell, onOutputProjection, onOutputStart }: { source?: ObservatorySource; notice?: ReactNode; shell?: ObservatoryShell; onOutputProjection?: (projection: RuntimeProjection) => void; onOutputStart?: (focusId: string) => void } = {}) {
  const { t, locale } = useLocale();
  const canAct = source.canAct;
  // A source whose reads follow the reader's language is read again when the language changes.
  const readerLocale = source.localized ? locale : null;
  // The Observatory keeps the callbacks it was first given, so the reader takes the current language from a ref.
  const localeRef = useRef(locale);
  localeRef.current = locale;
  const [portfolio, setPortfolio] = useState<SubscriberPortfolio | null>(null);
  const portfolioRef = useRef<SubscriberPortfolio | null>(null);
  portfolioRef.current = portfolio;
  const [access, setAccess] = useState<"loading" | "required" | "failure" | "ready">("loading");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const pilotRedeemed = useRef(false);
  // Activation is a sequence of real steps (an invitation redeemed, a payment confirmed, an observation started).
  const [activation, setActivation] = useState<ActivationPhase>("idle");
  const translate = useRef(t);
  translate.current = t;
  const [locator, setLocator] = useState("");
  const [suggestions, setSuggestions] = useState<readonly string[]>([]);
  const [total, setTotal] = useState(1);
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);
  const [projection, setProjection] = useState<RuntimeProjection | null>(null);
  const [firstObservation, setFirstObservation] = useState<FirstObservation | null>(null);
  const [revision, setRevision] = useState<string | null>(null);
  const canReadProjection = Boolean(projection && (
    projection.nodes.length > 0 ||
    (projection.cognition && (projection.cognition.sources.length > 0 || projection.cognition.opportunities.length > 0))
  ));
  const [reading, setReading] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [replacing, setReplacing] = useState<string | null>(null);
  const [replacementLocator, setReplacementLocator] = useState("");
  const sessionEpoch = useRef(0);
  const outputEpoch = useRef(0);
  const outputRequest = useRef<AbortController | null>(null);
  const attempts = useRef(new Map<string, string>());
  const requests = useRef(new Set<AbortController>());
  useEffect(() => () => { for (const controller of requests.current) controller.abort(); }, []);
  const readPortfolio = useCallback(async (): Promise<SubscriberPortfolio | null> => {
    const controller = new AbortController(); requests.current.add(controller);
    const epoch = sessionEpoch.current;
    try {
      const result = await source.readPortfolio(controller.signal, localeRef.current);
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return null;
      if (result === "SESSION_REQUIRED") { setAccess("required"); setPortfolio(null); return null; }
      portfolioRef.current = result;
      setPortfolio(result); setAccess("ready");
      return result;
    } catch { if (!controller.signal.aborted && epoch === sessionEpoch.current) setAccess("failure"); return null; }
    finally { requests.current.delete(controller); }
  }, [source, readerLocale]);
  useEffect(() => { void readPortfolio(); }, [readPortfolio]);
  // Organizations the context already authorizes are offered while adding one; their absence never blocks adding.
  useEffect(() => {
    if (!source.suggestions || access !== "ready") return;
    const controller = new AbortController();
    source.suggestions(controller.signal).then(names => { if (!controller.signal.aborted) setSuggestions(names); }, () => {});
    return () => controller.abort();
  }, [source, access, portfolio]);
  useEffect(() => {
    // Sign-in started from an assistant connection returns to its consent, unless a pilot invite is pending.
    if (!canAct || access !== "ready" || pendingPilotInvite(() => window.sessionStorage)) return;
    const request = pendingMcpConnect(() => window.sessionStorage);
    if (request) window.location.replace(`/account/connect?request=${encodeURIComponent(request)}`);
  }, [access]);
  /**
   * Redeem a Design Partner invitation: the one carried through sign-in, or one pasted on the activation screen.
   * Only the pilot service decides; an invitation that is not accepted grants nothing and says why.
   */
  const redeemInvite = useCallback(async (inviteToken: string): Promise<boolean> => {
    const epoch = sessionEpoch.current;
    const controller = new AbortController();
    requests.current.add(controller);
    setActivation("redeeming");
    try {
      const response = await fetch("/api/subscriber/pilot/redeem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ inviteToken }),
        signal: controller.signal,
      });
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return false;
      if (response.status === 401) { setAccess("required"); setActivation("idle"); return false; }
      if (!response.ok) throw new Error("PILOT_UNAVAILABLE");
      const result = pilotRedemptionSchema.parse(await response.json());
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return false;
      clearPilotInvite(() => window.sessionStorage);
      if (!result.accepted) { setActivation("invite_rejected"); return false; }
      // Accepted: the waiting organization starts as soon as the portfolio shows the confirmed place.
      setActivation("starting");
      await readPortfolio();
      return true;
    } catch {
      if (!controller.signal.aborted && epoch === sessionEpoch.current) setActivation("invite_failed");
      return false;
    } finally {
      requests.current.delete(controller);
    }
  }, [readPortfolio]);
  useEffect(() => {
    if (!canAct || access !== "ready" || pilotRedeemed.current) return;
    const inviteToken = pendingPilotInvite(() => window.sessionStorage);
    if (!inviteToken) return;
    pilotRedeemed.current = true;
    void redeemInvite(inviteToken);
  }, [access, redeemInvite, canAct]);
  async function command(input: Record<string, unknown>): Promise<void> {
    await run(input);
  }
  /** `quiet`: the activation screen explains this step itself, so no notice is added on top of it. */
  async function run(input: Record<string, unknown>, quiet = false): Promise<ReturnType<typeof subscriberResultSchema.parse> | null> {
    if (!canAct || busy || !source.command) return null;
    const signature = JSON.stringify(input);
    let requestRef = attempts.current.get(signature);
    if (!requestRef) { requestRef = crypto.randomUUID(); attempts.current.set(signature, requestRef); }
    setBusy(true); setMessage(""); setPaymentUrl(null);
    const controller = new AbortController(); requests.current.add(controller);
    const epoch = sessionEpoch.current;
    try {
      const outcome = await source.command!(input, requestRef, controller.signal);
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return null;
      if (outcome === "SESSION_REQUIRED") { setAccess("required"); setPortfolio(null); setProjection(null); return null; }
      const result = subscriberResultSchema.parse(outcome);
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return null;
      const link = approvedPaymentUrl(result.checkoutUrl) ?? approvedPaymentUrl(result.paymentUrl);
      setPaymentUrl(link);
      // An organization kept while access is not active is explained by the activation screen, not by a notice.
      const waitsForAccess = (input.action === "add" || input.action === "retry_pending")
        && ["CAPACITY_UNKNOWN", "CHECKOUT_REQUIRED", "ACCESS_DENIED"].includes(result.state);
      if (waitsForAccess) setActivation(previous => previous === "starting" || previous === "idle" ? "needs_access" : previous);
      setMessage(waitsForAccess || quiet ? "" : input.action === "refresh_purchase" ? result.state === "REFRESHED" ? t("La comprobación ha terminado. La cartera muestra la capacidad verificada.", "The check is complete. The portfolio shows verified capacity.") : t("El pago o la capacidad todavía no se han podido confirmar. No se ha concedido capacidad nueva.", "Payment or capacity could not be confirmed yet. No new capacity has been granted.")
        : link ? t("La compra espera tu confirmación. La capacidad solo cambia tras verificar el pago.", "The purchase awaits your confirmation. Capacity changes only after payment is verified.")
        : result.observationState === "QUEUED" ? t("Recibido. La primera observación empieza en segundo plano y verás su estado aquí. La identidad legal se verifica aparte.", "Received. The first observation starts in the background and you will see its state here. Legal identity is verified separately.")
        : result.observationState === "CAPACITY_REQUIRED" ? t("Tu solicitud está guardada, pero tu capacidad actual ya está en uso. Amplíala para observarla.", "Your request is saved, but your current capacity is already in use. Expand it to observe it.")
        : result.observationState === "NOT_READY" ? t("Tu atención está guardada. La observación necesita un plan autorizado; aún no se ha ejecutado.", "Your attention is saved. Observation requires an authorized plan; it has not run yet.")
        : result.observationState?.startsWith("BLOCKED") ? t("La observación se ha detenido por sus límites de ejecución. No hay una conclusión nueva.", "Observation stopped at its execution limits. There is no new conclusion.")
        : result.observationState === "PARTIAL" ? t("La observación es parcial. Lee las evidencias y sus límites antes de interpretar el resultado.", "Observation is partial. Read the evidence and its limits before interpreting the result.")
        : result.state === "IDENTITY_PENDING" && result.reason?.startsWith("AMBIGUOUS") ? t("Varias organizaciones coinciden. Añade su web o su código LEI para distinguirla; no elegimos por ti.", "Several organizations match. Add its website or LEI code to tell them apart; we do not choose for you.")
        : result.state === "IDENTITY_PENDING" && result.reason?.startsWith("CONFLICT") ? t("El nombre, la web o el identificador apuntan a organizaciones distintas. No se ha creado nada; revisa los datos.", "The name, website or identifier point to different organizations. Nothing was created; check the details.")
        : result.state === "WEBSITE_REQUIRED" ? t("Indica la dirección web pública de la organización, por ejemplo empresa.com. Una atención interna necesita un sitio que observar.", "Enter the organization's public website address, for example company.com. An internal attention needs a site to observe.")
        : result.state === "IDENTITY_REJECTED" ? t("Introduce un nombre, una web pública o un código LEI. Los identificadores internos y los emails no sirven.", "Enter a name, a public website or an LEI code. Internal identifiers and emails are not accepted.")
        : result.state === "IDENTITY_PENDING" || result.state === "IDENTITY_UNRESOLVED" ? t("Identidad por resolver. Tu solicitud está guardada; todavía no hay una organización ni una conclusión.", "Identity unresolved. Your request is saved; there is no organization or conclusion yet.")
        : result.state === "CAPACITY_UNKNOWN" ? t("La capacidad aún no está confirmada. Comprueba el estado antes de repetir la operación.", "Capacity is not confirmed yet. Check its state before repeating the operation.")
        : t("La operación está registrada. La lectura conserva sus fuentes y límites.", "The operation is recorded. The reading retains its sources and limits."));
      if (!link && ["ACCEPTED", "CREATED", "ALREADY_PRESENT", "ACTIVE", "PAUSED", "REMOVED", "CANCELLED", "REFRESHED", "success"].includes(result.state)) attempts.current.delete(signature);
      if (input.action === "replace" && ["CREATED", "ACTIVE"].includes(result.state)) { setReplacing(null); setReplacementLocator(""); }
      await readPortfolio();
      return result;
    } catch { if (!controller.signal.aborted && epoch === sessionEpoch.current) setMessage(t("No pudimos confirmar la operación. Lee el estado antes de repetirla; tu contexto no se ha sustituido.", "The operation could not be confirmed. Read its state before repeating it; your context has not been replaced.")); return null; }
    finally { requests.current.delete(controller); if (epoch === sessionEpoch.current) setBusy(false); }
  }
  // Long-lived callbacks (the payment confirmation loop) call the current `run`, with the current language.
  const runRef = useRef(run);
  runRef.current = run;

  /**
   * Start what was waiting for access, once the owning service has confirmed a place: one organization at a time,
   * only into confirmed free places, each attempted once. It never starts anything on unconfirmed capacity.
   */
  const startedWaiting = useRef(new Set<string>());
  useEffect(() => {
    if (!canAct || access !== "ready" || busy || !portfolio) return;
    const room = capacityRoom(portfolio);
    if (room === null || room <= 0) return;
    const next = waitingItems(portfolio).find(item => !startedWaiting.current.has(item.focusId));
    if (!next) return;
    startedWaiting.current.add(next.focusId);
    setActivation("starting");
    void run({ action: "retry_pending", focusId: next.focusId }).then(result => {
      if (result?.focusId && (result.state === "CREATED" || result.state === "ALREADY_PRESENT")) {
        setActivation("idle");
        void readOutput(result.focusId);
      } else if (result && (result.state === "IDENTITY_PENDING" || result.state === "IDENTITY_UNRESOLVED")) {
        // Admitted as attention: its first observation runs on the website while identity is resolved.
        setActivation("idle");
      }
    });
  }, [portfolio, access, busy, canAct]);

  /** The payment provider's return: confirm with the provider, never assume. */
  const billingHandled = useRef(false);
  const confirmPayment = useCallback(async () => {
    setActivation("confirming_payment");
    for (let attempt = 0; attempt < 8; attempt++) {
      await runRef.current({ action: "refresh_purchase" }, true);
      const latest = portfolioRef.current;
      if (latest && latest.capacityCurrentness === "CURRENT" && latest.capacity !== null && latest.capacity > 0) {
        setActivation(waitingItems(latest).length ? "starting" : "idle");
        return;
      }
      await new Promise(resolve => window.setTimeout(resolve, 3000));
    }
    setActivation("payment_unconfirmed");
  }, []);
  useEffect(() => {
    if (!canAct || access !== "ready" || billingHandled.current) return;
    const url = new URL(window.location.href);
    const outcome = billingReturn(url.searchParams);
    if (!outcome) return;
    billingHandled.current = true;
    url.searchParams.delete("billing"); url.searchParams.delete("purchase");
    window.history.replaceState(null, "", url);
    if (outcome === "cancelled") setActivation("payment_cancelled");
    else void confirmPayment();
  }, [access, canAct, confirmPayment]);

  /** Open the provider's secure checkout for a first subscription; capacity changes only once payment is verified. */
  async function startCheckout(totalOrganizations: number) {
    setActivation("checkout");
    const result = await run({ action: "purchase", desiredOrganizationTotal: totalOrganizations }, true);
    const link = result ? approvedPaymentUrl(result.checkoutUrl) ?? approvedPaymentUrl(result.paymentUrl) : null;
    if (link) { window.location.assign(link); return; }
    setActivation("checkout_failed");
  }
  /** The same reading in both modes: the account's authorized read, or the demo snapshot. */
  const loadOutput = useCallback((focusId: string, signal: AbortSignal): Promise<unknown> => source.readOutput(focusId, signal, localeRef.current), [source]);
  const readOutput = useCallback(async (focusId: string, pushHistory = true) => {
    outputRequest.current?.abort();
    const controller = new AbortController(); outputRequest.current = controller; requests.current.add(controller);
    const epoch = ++outputEpoch.current, session = sessionEpoch.current;
    if (pushHistory) { const url = new URL(window.location.href); url.searchParams.set("organization", focusId); window.history.pushState(null, "", url); }
    onOutputStart?.(focusId);
    setReading(true); setSelected(focusId); setProjection(null); setFirstObservation(null);
    try {
      const payload = await loadOutput(focusId, controller.signal);
      if (controller.signal.aborted || epoch !== outputEpoch.current || session !== sessionEpoch.current) return;
      if (typeof payload === "object" && payload !== null && (payload as { kind?: unknown }).kind === "PENDING_ATTENTION") {
        setFirstObservation(pendingOutputSchema.parse(payload).firstObservation); setRevision(null);
        return;
      }
      const result = subscriberOutputSchema.parse(payload);
      setProjection(result.projection); setRevision(result.revision ?? null); setFirstObservation(result.firstObservation ?? null);
      // Admin technical details must follow the selected organization, not the initial one.
      onOutputProjection?.(result.projection);
    } catch { if (!controller.signal.aborted) setMessage(t("La lectura autorizada no está disponible. Vuelve a comprobar el estado.", "The authorized reading is unavailable. Check the state again.")); }
    finally { requests.current.delete(controller); if (epoch === outputEpoch.current) setReading(false); }
  }, [t, loadOutput, onOutputProjection, onOutputStart]);
  useEffect(() => {
    if (access !== "ready" || !portfolio) return;
    const navigate = () => {
      const focus = new URL(window.location.href).searchParams.get("organization");
      const entry = portfolio.organizations.find(item => item.focusId === focus && readable(item) && !["REMOVED", "RESOLVED", "CANCELLED"].includes(item.state));
      if (entry) void readOutput(entry.focusId, false);
      else { outputRequest.current?.abort(); ++outputEpoch.current; setSelected(null); setProjection(null); setFirstObservation(null); setRevision(null); setReading(false); }
    };
    const focus = new URL(window.location.href).searchParams.get("organization");
    if ((focus && focus !== selected) || (selected && !portfolio.organizations.some(item => item.focusId === selected && readable(item) && !["REMOVED", "RESOLVED", "CANCELLED"].includes(item.state)))) navigate();
    window.addEventListener("popstate", navigate);
    return () => window.removeEventListener("popstate", navigate);
  }, [access, portfolio, readOutput, selected]);
  // A language change in the demo re-reads the open organization in the new locale.
  useEffect(() => { if (readerLocale && selected) void readOutput(selected, false); }, [readerLocale]);
  useEffect(() => { setTotal(value => Math.max(value, (portfolio?.capacity ?? 0) + 1)); }, [portfolio?.capacity]);
  // Real progress, never fake loading: re-read while a First Observation is still running.
  const running = portfolio?.organizations.filter(item => item.observation && ["QUEUED", "OBSERVING_PUBLIC_PRESENCE"].includes(item.observation.state)).map(item => item.focusId).join(",") ?? "";
  const previousRunning = useRef("");
  useEffect(() => {
    if (access !== "ready") return;
    const finished = previousRunning.current.split(",").filter(id => id && !running.split(",").includes(id));
    previousRunning.current = running;
    if (selected && finished.includes(selected)) void readOutput(selected, false);
    if (!running || !canAct) return;
    const timer = window.setTimeout(() => void readPortfolio(), 4000);
    return () => window.clearTimeout(timer);
  }, [access, portfolio, running, selected, readOutput, readPortfolio]);  // each read re-arms the poll
  async function logout() {
    if (busy) return;
    setBusy(true);
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok) throw new Error("SIGN_OUT_FAILED");
      ++sessionEpoch.current; ++outputEpoch.current;
      for (const controller of requests.current) controller.abort();
      clearPilotInvite(() => window.sessionStorage); clearMcpConnect(() => window.sessionStorage); pilotRedeemed.current = false;
      attempts.current.clear(); setSelected(null); setRevision(null); setPaymentUrl(null); setReading(false);
      setPortfolio(null); setProjection(null); setAccess("required");
    } catch { setMessage(t("No se pudo confirmar el cierre de sesión.", "Sign-out could not be confirmed.")); }
    finally { setBusy(false); }
  }
  const clearSelection = useCallback(() => {
    outputRequest.current?.abort(); ++outputEpoch.current;
    setSelected(null); setProjection(null); setFirstObservation(null); setRevision(null); setReading(false);
  }, []);
  return <Observatory activation={activation} onRedeemInvite={redeemInvite} onCheckout={startCheckout} onConfirmPayment={() => void confirmPayment()} onActivationReset={() => setActivation("idle")} notice={notice} shell={shell} canAct={canAct} capabilities={source.capabilities} landing={source.landing} firstLookUnread={source.firstLookUnread} rememberReading={source.remembersReading !== false} suggestions={suggestions} loadReading={loadOutput} menuName={source.menuName} access={access} portfolio={portfolio} busy={busy} message={message} paymentUrl={paymentUrl}
    selected={selected} reading={reading} projection={projection} firstObservation={firstObservation} revision={revision}
    readOutput={readOutput} clearSelection={clearSelection} command={command} refresh={() => void readPortfolio()} logout={() => void logout()}
    locator={locator} setLocator={setLocator} total={total} setTotal={setTotal}
    replacing={replacing} setReplacing={setReplacing} replacementLocator={replacementLocator} setReplacementLocator={setReplacementLocator}/>;
}
