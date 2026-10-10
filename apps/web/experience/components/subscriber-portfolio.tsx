"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useLocale } from "@/lib/locale";
import { approvedPaymentUrl, pendingOutputSchema, pilotRedemptionSchema, portfolioSchema, subscriberOutputSchema, subscriberResultSchema, type FirstObservation, type SubscriberPortfolio } from "@/lib/subscriber-contracts";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { pendingPilotInvite, clearPilotInvite } from "@/lib/pilot-invite";
import { pendingMcpConnect, clearMcpConnect } from "@/lib/mcp-connect";
import { Observatory } from "./observatory";
import { syntheticOutput, syntheticPortfolio } from "@/lib/demo/synthetic-source";
import "./subscriber-portfolio.css";
import "./observatory.css";

type PortfolioItem = SubscriberPortfolio["organizations"][number];
/** A canonical Focus reading, or a pending attention whose First Observation exists. */
const readable = (item: PortfolioItem) => Boolean(item.organizationId || item.observation);

/**
 * The subscriber observatory, in two modes over the same components. `live` is the account's authorized read;
 * `synthetic` is the public demo: a fictional snapshot, with the account-only capabilities disabled.
 */
export function SubscriberPortfolioExperience({ source = "live", notice }: { source?: "live" | "synthetic"; notice?: ReactNode } = {}) {
  const { t, locale } = useLocale();
  const live = source === "live";
  // The demo's snapshot follows the reader's language; the account never re-reads on a language change.
  const demoLocale = live ? null : locale;
  // The Observatory keeps the callbacks it was first given, so the reader takes the current language from a ref.
  const localeRef = useRef(locale);
  localeRef.current = locale;
  const [portfolio, setPortfolio] = useState<SubscriberPortfolio | null>(null);
  const [access, setAccess] = useState<"loading" | "required" | "failure" | "ready">("loading");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const pilotRedeemed = useRef(false);
  const translate = useRef(t);
  translate.current = t;
  const [locator, setLocator] = useState("");
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
  const readPortfolio = useCallback(async () => {
    if (!live) { setPortfolio(syntheticPortfolio(demoLocale ?? "es")); setAccess("ready"); return; }
    const controller = new AbortController(); requests.current.add(controller);
    const epoch = sessionEpoch.current;
    try {
      const response = await fetch("/api/subscriber/portfolio", { cache: "no-store", signal: controller.signal });
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return;
      if (response.status === 401) { setAccess("required"); setPortfolio(null); return; }
      if (!response.ok) throw new Error("READ_FAILED");
      const result = portfolioSchema.parse(await response.json());
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return;
      setPortfolio(result); setAccess("ready");
    } catch { if (!controller.signal.aborted && epoch === sessionEpoch.current) setAccess("failure"); }
    finally { requests.current.delete(controller); }
  }, [live, demoLocale]);
  useEffect(() => { void readPortfolio(); }, [readPortfolio]);
  useEffect(() => {
    // Sign-in started from an assistant connection returns to its consent, unless a pilot invite is pending.
    if (!live || access !== "ready" || pendingPilotInvite(() => window.sessionStorage)) return;
    const request = pendingMcpConnect(() => window.sessionStorage);
    if (request) window.location.replace(`/account/connect?request=${encodeURIComponent(request)}`);
  }, [access]);
  useEffect(() => {
    if (!live || access !== "ready" || pilotRedeemed.current) return;
    const inviteToken = pendingPilotInvite(() => window.sessionStorage);
    if (!inviteToken) return;
    pilotRedeemed.current = true;
    const epoch = sessionEpoch.current;
    const controller = new AbortController();
    requests.current.add(controller);
    void (async () => {
      try {
        const response = await fetch("/api/subscriber/pilot/redeem", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ inviteToken }),
          signal: controller.signal,
        });
        if (controller.signal.aborted || epoch !== sessionEpoch.current) return;
        if (response.status === 401) {
          pilotRedeemed.current = false;
          setAccess("required");
          return;
        }
        if (!response.ok) throw new Error("PILOT_UNAVAILABLE");
        const result = pilotRedemptionSchema.parse(await response.json());
        if (controller.signal.aborted || epoch !== sessionEpoch.current) return;
        clearPilotInvite(() => window.sessionStorage);
        if (!result.accepted) {
          setMessage(translate.current(
            "La invitación de Design Partner no es válida o ha caducado.",
            "The Design Partner invitation is invalid or has expired.",
          ));
          return;
        }
        setMessage(translate.current(
          "Acceso Design Partner activado: una organización, con la experiencia completa de AXIGNAL.",
          "Design Partner access activated: one organization, with the full AXIGNAL experience.",
        ));
        await readPortfolio();
      } catch {
        if (!controller.signal.aborted && epoch === sessionEpoch.current) {
          pilotRedeemed.current = false;
          setMessage(translate.current(
            "No pudimos activar todavía la invitación. Puedes volver a cargar la cuenta para reintentarlo.",
            "We could not activate the invitation yet. Reload the account to retry.",
          ));
        }
      } finally {
        requests.current.delete(controller);
      }
    })();
    return () => { controller.abort(); pilotRedeemed.current = false; };
  }, [access, readPortfolio, live]);
  async function command(input: Record<string, unknown>) {
    if (!live || busy) return;
    const signature = JSON.stringify(input);
    let requestRef = attempts.current.get(signature);
    if (!requestRef) { requestRef = crypto.randomUUID(); attempts.current.set(signature, requestRef); }
    setBusy(true); setMessage(""); setPaymentUrl(null);
    const controller = new AbortController(); requests.current.add(controller);
    const epoch = sessionEpoch.current;
    try {
      const response = await fetch("/api/subscriber/portfolio", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...input, requestRef }), signal: controller.signal });
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return;
      if (response.status === 401) { setAccess("required"); setPortfolio(null); setProjection(null); return; }
      if (!response.ok) throw new Error("COMMAND_FAILED");
      const result = subscriberResultSchema.parse(await response.json());
      if (controller.signal.aborted || epoch !== sessionEpoch.current) return;
      const link = approvedPaymentUrl(result.checkoutUrl) ?? approvedPaymentUrl(result.paymentUrl);
      setPaymentUrl(link);
      setMessage(input.action === "refresh_purchase" ? result.state === "REFRESHED" ? t("La comprobación ha terminado. La cartera muestra la capacidad verificada.", "The check is complete. The portfolio shows verified capacity.") : t("El pago o la capacidad todavía no se han podido confirmar. No se ha concedido capacidad nueva.", "Payment or capacity could not be confirmed yet. No new capacity has been granted.")
        : link ? t("La compra espera tu confirmación. La capacidad solo cambia tras verificar el pago.", "The purchase awaits your confirmation. Capacity changes only after payment is verified.")
        : result.observationState === "QUEUED" ? t("Recibido. La primera observación empieza en segundo plano y verás su estado aquí. La identidad legal se verifica aparte.", "Received. The first observation starts in the background and you will see its state here. Legal identity is verified separately.")
        : result.observationState === "CAPACITY_REQUIRED" ? t("Tu solicitud está guardada, pero tu capacidad actual ya está en uso. Amplíala para observarla.", "Your request is saved, but your current capacity is already in use. Expand it to observe it.")
        : result.observationState === "NOT_READY" ? t("Tu atención está guardada. La observación necesita un plan autorizado; aún no se ha ejecutado.", "Your attention is saved. Observation requires an authorized plan; it has not run yet.")
        : result.observationState?.startsWith("BLOCKED") ? t("La observación se ha detenido por sus límites de ejecución. No hay una conclusión nueva.", "Observation stopped at its execution limits. There is no new conclusion.")
        : result.observationState === "PARTIAL" ? t("La observación es parcial. Lee las evidencias y sus límites antes de interpretar el resultado.", "Observation is partial. Read the evidence and its limits before interpreting the result.")
        : result.state === "IDENTITY_PENDING" && result.reason?.startsWith("AMBIGUOUS") ? t("Varias organizaciones coinciden. Añade su web o su código LEI para distinguirla; no elegimos por ti.", "Several organizations match. Add its website or LEI code to tell them apart; we do not choose for you.")
        : result.state === "IDENTITY_PENDING" && result.reason?.startsWith("CONFLICT") ? t("El nombre, la web o el identificador apuntan a organizaciones distintas. No se ha creado nada; revisa los datos.", "The name, website or identifier point to different organizations. Nothing was created; check the details.")
        : result.state === "IDENTITY_REJECTED" ? t("Introduce un nombre, una web pública o un código LEI. Los identificadores internos y los emails no sirven.", "Enter a name, a public website or an LEI code. Internal identifiers and emails are not accepted.")
        : result.state === "IDENTITY_PENDING" || result.state === "IDENTITY_UNRESOLVED" ? t("Identidad por resolver. Tu solicitud está guardada; todavía no hay una organización ni una conclusión.", "Identity unresolved. Your request is saved; there is no organization or conclusion yet.")
        : result.state === "CAPACITY_UNKNOWN" ? t("La capacidad aún no está confirmada. Comprueba el estado antes de repetir la operación.", "Capacity is not confirmed yet. Check its state before repeating the operation.")
        : t("La operación está registrada. La lectura conserva sus fuentes y límites.", "The operation is recorded. The reading retains its sources and limits."));
      if (!link && ["ACCEPTED", "CREATED", "ALREADY_PRESENT", "ACTIVE", "PAUSED", "REMOVED", "CANCELLED", "REFRESHED", "success"].includes(result.state)) attempts.current.delete(signature);
      if (input.action === "replace" && ["CREATED", "ACTIVE"].includes(result.state)) { setReplacing(null); setReplacementLocator(""); }
      await readPortfolio();
    } catch { if (!controller.signal.aborted && epoch === sessionEpoch.current) setMessage(t("No pudimos confirmar la operación. Lee el estado antes de repetirla; tu contexto no se ha sustituido.", "The operation could not be confirmed. Read its state before repeating it; your context has not been replaced.")); }
    finally { requests.current.delete(controller); if (epoch === sessionEpoch.current) setBusy(false); }
  }
  /** The same reading in both modes: the account's authorized read, or the demo snapshot. */
  const loadOutput = useCallback(async (focusId: string, signal: AbortSignal): Promise<unknown> => {
    if (!live) return syntheticOutput(focusId, localeRef.current);
    const response = await fetch(`/api/subscriber/organizations/${encodeURIComponent(focusId)}/output`, { cache: "no-store", signal });
    if (!response.ok) throw new Error("READ_FAILED");
    return response.json();
  }, [live]);
  const readOutput = useCallback(async (focusId: string, pushHistory = true) => {
    outputRequest.current?.abort();
    const controller = new AbortController(); outputRequest.current = controller; requests.current.add(controller);
    const epoch = ++outputEpoch.current, session = sessionEpoch.current;
    if (pushHistory) { const url = new URL(window.location.href); url.searchParams.set("organization", focusId); window.history.pushState(null, "", url); }
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
    } catch { if (!controller.signal.aborted) setMessage(t("La lectura autorizada no está disponible. Vuelve a comprobar el estado.", "The authorized reading is unavailable. Check the state again.")); }
    finally { requests.current.delete(controller); if (epoch === outputEpoch.current) setReading(false); }
  }, [t, loadOutput]);
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
  useEffect(() => { if (!live && selected) void readOutput(selected, false); }, [demoLocale]);
  useEffect(() => { setTotal(value => Math.max(value, (portfolio?.capacity ?? 0) + 1)); }, [portfolio?.capacity]);
  // Real progress, never fake loading: re-read while a First Observation is still running.
  const running = portfolio?.organizations.filter(item => item.observation && ["QUEUED", "OBSERVING_PUBLIC_PRESENCE"].includes(item.observation.state)).map(item => item.focusId).join(",") ?? "";
  const previousRunning = useRef("");
  useEffect(() => {
    if (access !== "ready") return;
    const finished = previousRunning.current.split(",").filter(id => id && !running.split(",").includes(id));
    previousRunning.current = running;
    if (selected && finished.includes(selected)) void readOutput(selected, false);
    if (!running || !live) return;
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
  return <Observatory notice={notice} canAct={live} loadReading={loadOutput} menuName={live ? undefined : item => "www." + item.label.toLowerCase().replace(" ", "-") + ".com"} access={access} portfolio={portfolio} busy={busy} message={message} paymentUrl={paymentUrl}
    selected={selected} reading={reading} projection={projection} firstObservation={firstObservation} revision={revision}
    readOutput={readOutput} clearSelection={clearSelection} command={command} refresh={() => void readPortfolio()} logout={() => void logout()}
    locator={locator} setLocator={setLocator} total={total} setTotal={setTotal}
    replacing={replacing} setReplacing={setReplacing} replacementLocator={replacementLocator} setReplacementLocator={setReplacementLocator}/>;
}
