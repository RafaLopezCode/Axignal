"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, LogOut, Plus, RefreshCw } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { approvedPaymentUrl, monthlyCapacityCents, pilotRedemptionSchema, portfolioSchema, subscriberOutputSchema, subscriberResultSchema, type SubscriberPortfolio } from "@/lib/subscriber-contracts";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { pendingPilotInvite, clearPilotInvite } from "@/lib/pilot-invite";
import { PublicShell } from "./public-shell";
import { SubscriberReading } from "./subscriber-reading";
import { SubscriberRepresentation } from "./subscriber-representation";
import "./subscriber-portfolio.css";

export function SubscriberPortfolioExperience() {
  const { t, locale } = useLocale();
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
  }, []);
  useEffect(() => { void readPortfolio(); }, [readPortfolio]);
  useEffect(() => {
    if (access !== "ready" || pilotRedeemed.current) return;
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
  }, [access, readPortfolio]);
  async function command(input: Record<string, unknown>) {
    if (busy) return;
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
        : result.observationState === "NOT_READY" ? t("Tu atención está guardada. La observación necesita un plan autorizado; aún no se ha ejecutado.", "Your attention is saved. Observation requires an authorized plan; it has not run yet.")
        : result.observationState?.startsWith("BLOCKED") ? t("La observación se ha detenido por sus límites de ejecución. No hay una conclusión nueva.", "Observation stopped at its execution limits. There is no new conclusion.")
        : result.observationState === "PARTIAL" ? t("La observación es parcial. Lee las evidencias y sus límites antes de interpretar el resultado.", "Observation is partial. Read the evidence and its limits before interpreting the result.")
        : result.state === "IDENTITY_PENDING" || result.state === "IDENTITY_UNRESOLVED" ? t("Identidad por resolver. Tu solicitud está guardada; todavía no hay una organización ni una conclusión.", "Identity unresolved. Your request is saved; there is no organization or conclusion yet.")
        : result.state === "CAPACITY_UNKNOWN" ? t("La capacidad aún no está confirmada. Comprueba el estado antes de repetir la operación.", "Capacity is not confirmed yet. Check its state before repeating the operation.")
        : t("La operación está registrada. La lectura conserva sus fuentes y límites.", "The operation is recorded. The reading retains its sources and limits."));
      if (!link && ["ACCEPTED", "CREATED", "ALREADY_PRESENT", "ACTIVE", "PAUSED", "REMOVED", "CANCELLED", "REFRESHED", "success"].includes(result.state)) attempts.current.delete(signature);
      if (input.action === "replace" && ["CREATED", "ACTIVE"].includes(result.state)) { setReplacing(null); setReplacementLocator(""); }
      await readPortfolio();
    } catch { if (!controller.signal.aborted && epoch === sessionEpoch.current) setMessage(t("No pudimos confirmar la operación. Lee el estado antes de repetirla; tu contexto no se ha sustituido.", "The operation could not be confirmed. Read its state before repeating it; your context has not been replaced.")); }
    finally { requests.current.delete(controller); if (epoch === sessionEpoch.current) setBusy(false); }
  }
  const readOutput = useCallback(async (focusId: string, pushHistory = true) => {
    outputRequest.current?.abort();
    const controller = new AbortController(); outputRequest.current = controller; requests.current.add(controller);
    const epoch = ++outputEpoch.current, session = sessionEpoch.current;
    if (pushHistory) { const url = new URL(window.location.href); url.searchParams.set("organization", focusId); window.history.pushState(null, "", url); }
    setReading(true); setSelected(focusId); setProjection(null);
    try {
      const response = await fetch(`/api/subscriber/organizations/${encodeURIComponent(focusId)}/output`, { cache: "no-store", signal: controller.signal });
      if (!response.ok) throw new Error("READ_FAILED");
      const result = subscriberOutputSchema.parse(await response.json());
      if (controller.signal.aborted || epoch !== outputEpoch.current || session !== sessionEpoch.current) return;
      setProjection(result.projection); setRevision(result.revision ?? null);
    } catch { if (!controller.signal.aborted) setMessage(t("La lectura autorizada no está disponible. Vuelve a comprobar el estado.", "The authorized reading is unavailable. Check the state again.")); }
    finally { requests.current.delete(controller); if (epoch === outputEpoch.current) setReading(false); }
  }, [t]);
  useEffect(() => {
    if (access !== "ready" || !portfolio) return;
    const navigate = () => {
      const focus = new URL(window.location.href).searchParams.get("organization");
      const entry = portfolio.organizations.find(item => item.focusId === focus && item.organizationId && !["REMOVED", "RESOLVED", "CANCELLED"].includes(item.state));
      if (entry) void readOutput(entry.focusId, false);
      else { outputRequest.current?.abort(); ++outputEpoch.current; setSelected(null); setProjection(null); setRevision(null); setReading(false); }
    };
    const focus = new URL(window.location.href).searchParams.get("organization");
    if ((focus && focus !== selected) || (selected && !portfolio.organizations.some(item => item.focusId === selected && item.organizationId && !["REMOVED", "RESOLVED", "CANCELLED"].includes(item.state)))) navigate();
    window.addEventListener("popstate", navigate);
    return () => window.removeEventListener("popstate", navigate);
  }, [access, portfolio, readOutput, selected]);
  useEffect(() => { setTotal(value => Math.max(value, (portfolio?.capacity ?? 0) + 1)); }, [portfolio?.capacity]);
  async function logout() {
    if (busy) return;
    setBusy(true);
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok) throw new Error("SIGN_OUT_FAILED");
      ++sessionEpoch.current; ++outputEpoch.current;
      for (const controller of requests.current) controller.abort();
      clearPilotInvite(() => window.sessionStorage); pilotRedeemed.current = false;
      attempts.current.clear(); setSelected(null); setRevision(null); setPaymentUrl(null); setReading(false);
      setPortfolio(null); setProjection(null); setAccess("required");
    } catch { setMessage(t("No se pudo confirmar el cierre de sesión.", "Sign-out could not be confirmed.")); }
    finally { setBusy(false); }
  }
  const used = portfolio?.organizations.filter(item => item.state === "ACTIVE" || item.state === "PAUSED").length ?? 0;
  return <PublicShell className="subscriber-page">
    <div className="subscriber-content" aria-busy={busy}>
      <header className="subscriber-heading"><div><span className="eyebrow">AXIGNAL</span><h1>{t("Tu mirada continúa.", "Your perspective continues.")}</h1><p>{t("Organizaciones, contexto y evidencias para comprender lo que merece tu atención.", "Organizations, context and evidence to understand what deserves your attention.")}</p></div>
        {access === "ready" && <button className="text-link" disabled={busy} onClick={() => void logout()}><LogOut size={16} />{t("Cerrar sesión", "Sign out")}</button>}
      </header>
      {access === "loading" && <p role="status">{t("Leyendo tu contexto…", "Reading your context…")}</p>}
      {access === "required" && <section className="subscriber-notice"><h2>{t("Tu identidad abre el acceso.", "Your identity opens access.")}</h2><p>{t("Accede para leer tu cartera privada y sus evidencias.", "Sign in to read your private portfolio and its evidence.")}</p><Link className="button primary" href="/login">{t("Acceder", "Sign in")}<ArrowRight size={16} /></Link></section>}
      {access === "failure" && <section className="subscriber-notice" role="alert"><h2>{t("No pudimos leer tu contexto.", "We could not read your context.")}</h2><button className="button secondary" onClick={() => void readPortfolio()}><RefreshCw size={16}/>{t("Volver a comprobar", "Check again")}</button></section>}
      {access === "ready" && portfolio && <>
        <div className="subscriber-grid"><section className="subscriber-organizations" aria-labelledby="portfolio-title"><div className="subscriber-section-heading"><h2 id="portfolio-title">{t("Tus organizaciones", "Your organizations")}</h2><button className="text-link" disabled={busy} onClick={() => void readPortfolio()}><RefreshCw size={16}/>{t("Actualizar", "Refresh")}</button></div>
          <p>{portfolio.capacity === null || portfolio.capacityCurrentness !== "CURRENT" ? t("Capacidad sin confirmar", "Unconfirmed capacity") : `${used} / ${portfolio.capacity}`} · {t("Las organizaciones pausadas conservan su espacio.", "Paused organizations retain their space.")}</p>
          {portfolio.entitlementSource === "DESIGN_PARTNER_PILOT" && <p className="limit-note">{t("Design Partner · 1 organización · 0 € durante el piloto de validación.", "Design Partner · 1 organization · €0 during the validation pilot.")}</p>}
          {!portfolio.organizations.filter(item => !["REMOVED", "RESOLVED", "CANCELLED"].includes(item.state)).length && <div className="subscriber-empty"><h3>{t("Empieza por una organización.", "Start with an organization.")}</h3><p>{t("Puedes explorar tu cuenta. La germinación empieza al añadir una organización y resolver su identidad y el acceso a observarla.", "You can explore your account. Germination starts when you add an organization and its identity and observation access are resolved.")}</p><p>{t("Indica dónde observar. El nombre o la URL orientan la investigación; no establecen lo que es verdad.", "Direct observation. A name or URL guides research; it does not establish truth.")}</p></div>}
          <ul className="subscriber-list">{portfolio.organizations.filter(item => !["REMOVED", "RESOLVED", "CANCELLED"].includes(item.state)).map(item => <li key={item.focusId}><div><h3>{item.label}</h3><p>{item.state === "IDENTITY_PENDING" ? t("Identidad por resolver", "Identity unresolved") : item.state === "IDENTITY_REJECTED" ? t("Identidad no admitida", "Identity not admitted") : item.state === "CAPACITY_UNKNOWN" ? t("Capacidad sin confirmar", "Unconfirmed capacity") : item.state === "CAPACITY_PENDING" ? t("Pendiente de capacidad", "Capacity pending") : item.state === "PURCHASE_AUTHORITY_REQUIRED" ? t("Autoridad de compra pendiente", "Purchase authority pending") : item.state === "PAUSED" ? t("Pausada", "Paused") : t("Observación activa", "Active observation")}</p></div><div className="subscriber-row-actions">
            {item.organizationId && <button className="text-link" disabled={busy} onClick={() => void readOutput(item.focusId)} aria-pressed={selected === item.focusId}>{t("Abrir la lectura", "Open the reading")}<ArrowRight size={15}/></button>}
            {item.organizationId && <button className="text-link" disabled={busy} onClick={() => void command({ action: item.state === "PAUSED" ? "resume" : "pause", focusId: item.focusId })}>{item.state === "PAUSED" ? t("Reanudar", "Resume") : t("Pausar", "Pause")}</button>}
            {item.state === "ACTIVE" && <button className="text-link" disabled={busy} onClick={() => void command({ action: "reobserve", focusId: item.focusId })}>{t("Volver a observar", "Observe again")}</button>}
            {!item.organizationId && <button className="text-link" disabled={busy} onClick={() => void command({ action: "retry_pending", focusId: item.focusId })}>{t("Volver a comprobar", "Check again")}</button>}
            {item.organizationId && <button className="text-link" disabled={busy} onClick={() => { setReplacing(item.focusId); setReplacementLocator(""); }}>{t("Sustituir organización", "Replace organization")}</button>}
            <button className="text-link" disabled={busy} onClick={() => void command({ action: item.organizationId ? "remove" : "cancel_pending", focusId: item.focusId })}>{t("Retirar de mi cartera", "Remove from my portfolio")}</button>
          </div>{replacing === item.focusId && <form className="subscriber-add" onSubmit={event => { event.preventDefault(); void command({ action: "replace", focusId: item.focusId, locator: replacementLocator }); }}><label htmlFor={`replacement-${item.focusId}`}>{t("Nombre o sitio público", "Name or public website")}</label><input id={`replacement-${item.focusId}`} required maxLength={2048} value={replacementLocator} onChange={event => setReplacementLocator(event.target.value)} disabled={busy}/><p>{t("La sustitución conserva el historial privado. La organización actual permanece hasta resolver la nueva identidad.", "Replacement preserves private history. The current organization remains until the new identity is resolved.")}</p><button className="button secondary" disabled={busy || !replacementLocator.trim()}>{t("Sustituir organización", "Replace organization")}</button><button type="button" className="text-link" onClick={() => setReplacing(null)}>{t("Cancelar", "Cancel")}</button></form>}</li>)}</ul>
          <form className="subscriber-add" onSubmit={event => { event.preventDefault(); void command({ action: "add", locator }); }}><label htmlFor="organization-locator">{t("Nombre o sitio público", "Name or public website")}</label><input id="organization-locator" required maxLength={2048} value={locator} onChange={event => setLocator(event.target.value)} disabled={busy}/><button className="button primary" disabled={busy || !locator.trim()}><Plus size={16}/>{t("Añadir organización", "Add organization")}</button></form>
        </section>
        <aside className="subscriber-capacity" aria-labelledby="capacity-title"><span className="eyebrow">{t("Espacio para observar", "Room to observe")}</span><h2 id="capacity-title">{t("Amplía tu mirada.", "Expand your perspective.")}</h2><p>{t("Elige el total de organizaciones que quieres observar. Las señales no se facturan por separado.", "Choose the total number of organizations to observe. Signals are not billed separately.")}</p><form onSubmit={event => { event.preventDefault(); void command({ action: portfolio.capacity === null || portfolio.capacity === 0 ? "purchase" : "expand", desiredOrganizationTotal: total }); }}><label htmlFor="organization-total">{t("Total de organizaciones", "Total organizations")}</label><input id="organization-total" type="number" min={portfolio.capacity ? portfolio.capacity + 1 : 1} max={100000} step={1} required value={total} onChange={event => setTotal(Number(event.target.value))} disabled={busy}/><p className="subscriber-price">{Number.isSafeInteger(total) && total >= 1 && total <= 100000 ? new Intl.NumberFormat(locale, { style: "currency", currency: "EUR" }).format(monthlyCapacityCents(total) / 100) : "—"}<small>{t("Total mensual sin IVA; el pago confirma los impuestos aplicables.", "Monthly total excluding VAT; checkout confirms applicable taxes.")}</small></p><button className="button secondary" disabled={busy || portfolio.canPurchase !== true || !portfolio.contractingEnabled}>{t("Revisar la compra", "Review the purchase")}<ArrowRight size={16}/></button></form>
          {!portfolio.contractingEnabled && <p className="limit-note">{t("La contratación todavía no está activa.", "Contracting is not active yet.")}</p>}
          <button className="text-link" disabled={busy} onClick={() => void command({ action: "refresh_purchase" })}><RefreshCw size={16}/>{t("Comprobar pago y capacidad", "Check payment and capacity")}</button>
          {portfolio.canPurchase !== true && <p>{t("La autoridad de compra no está confirmada para este contexto.", "Purchase authority is not confirmed for this context.")}</p>}
        </aside></div>
        <section className="subscriber-operation" aria-live="polite">{message && <p>{message}</p>}{paymentUrl && <a className="button primary" href={paymentUrl}>{t("Continuar al pago", "Continue to payment")}<ArrowRight size={16}/></a>}</section>
        {reading && <p role="status">{t("Leyendo las evidencias…", "Reading the evidence…")}</p>}
        {projection && <section className="subscriber-reading" aria-labelledby="reading-title"><span className="eyebrow">{t("Tu lectura", "Your reading")}</span><h2 id="reading-title">{projection.organization.name}</h2>{projection.digitalRepresentation && <SubscriberRepresentation measurement={projection.digitalRepresentation}/>}{canReadProjection && revision ? <SubscriberReading key={revision} projection={projection} revision={revision}/> : <p>{t("Todavía no hay evidencia suficiente para una conclusión. Una ausencia en esta lectura no demuestra ausencia en el mundo.", "Evidence is not yet sufficient for a conclusion. Absence in this reading does not prove absence in the world.")}</p>}</section>}
      </>}
    </div>
  </PublicShell>;
}
