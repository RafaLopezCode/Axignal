"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, RefreshCw } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { approvedMcpRedirect, clearMcpConnect, mcpConsentSchema, mcpDecisionSchema, mcpRequestId, rememberMcpConnect, type McpConsent } from "@/lib/mcp-connect";
import { PublicShell } from "./public-shell";
import "./subscriber-portfolio.css";

type State = "loading" | "required" | "expired" | "failure" | "ready" | "leaving";

/** Consent for an external assistant to read this subscriber's AXIGNAL (ADR-0086). Read-only. */
export function SubscriberMcpConsent() {
  const { t } = useLocale();
  const [state, setState] = useState<State>("loading");
  const [request, setRequest] = useState<string | null>(null);
  const [consent, setConsent] = useState<McpConsent | null>(null);
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const id = new URL(window.location.href).searchParams.get("request");
    if (!id || !mcpRequestId.test(id)) { setState("expired"); return; }
    setRequest(id);
    const controller = new AbortController();
    void (async () => {
      try {
        const response = await fetch(`/api/subscriber/mcp/requests/${encodeURIComponent(id)}`, { cache: "no-store", signal: controller.signal });
        if (response.status === 401) { rememberMcpConnect(id, () => window.sessionStorage); setState("required"); return; }
        if (response.status === 410) { clearMcpConnect(() => window.sessionStorage); setState("expired"); return; }
        if (!response.ok) throw new Error("READ_FAILED");
        const result = mcpConsentSchema.parse(await response.json());
        clearMcpConnect(() => window.sessionStorage);
        setConsent(result); setState("ready");
      } catch { if (!controller.signal.aborted) setState("failure"); }
    })();
    return () => controller.abort();
  }, [attempt]);
  async function decide(decision: "approve" | "deny") {
    if (!request || busy) return;
    setBusy(true);
    try {
      const response = await fetch(`/api/subscriber/mcp/requests/${encodeURIComponent(request)}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision }),
      });
      if (response.status === 401) { rememberMcpConnect(request, () => window.sessionStorage); setState("required"); return; }
      if (response.status === 410) { setState("expired"); return; }
      if (!response.ok) throw new Error("DECISION_FAILED");
      const redirect = approvedMcpRedirect(mcpDecisionSchema.parse(await response.json()).redirect);
      if (!redirect) throw new Error("REDIRECT_REJECTED");
      setState("leaving");
      window.location.assign(redirect);
    } catch { setState("failure"); }
    finally { setBusy(false); }
  }
  return <PublicShell className="subscriber-page">
    <div className="subscriber-content" aria-busy={busy || state === "loading"}>
      <header className="subscriber-heading"><div><span className="eyebrow">{t("Conectar un asistente", "Connect an assistant")}</span><h1>{t("Tu AXIGNAL, en tu asistente.", "Your AXIGNAL, in your assistant.")}</h1><p>{t("Un asistente como Claude o ChatGPT pide leer tu cartera. Decides tú; AXIGNAL comprueba tu acceso en cada consulta.", "An assistant such as Claude or ChatGPT is asking to read your portfolio. You decide; AXIGNAL checks your access on every query.")}</p></div></header>
      {state === "loading" && <p role="status">{t("Leyendo la solicitud…", "Reading the request…")}</p>}
      {state === "required" && <section className="subscriber-notice"><h2>{t("Accede para decidir.", "Sign in to decide.")}</h2><p>{t("Usa la misma identidad con la que lees tu cartera. Volverás aquí después.", "Use the same identity you read your portfolio with. You will come back here afterwards.")}</p><Link className="button primary" href="/login">{t("Acceder", "Sign in")}<ArrowRight size={16}/></Link></section>}
      {state === "expired" && <section className="subscriber-notice" role="alert"><h2>{t("Esta solicitud ya no es válida.", "This request is no longer valid.")}</h2><p>{t("Caduca a los 10 minutos y solo se puede usar una vez. Vuelve a conectar desde tu asistente.", "It expires after 10 minutes and can be used only once. Connect again from your assistant.")}</p><Link className="button secondary" href="/account">{t("Ir a tu cartera", "Go to your portfolio")}</Link></section>}
      {state === "failure" && <section className="subscriber-notice" role="alert"><h2>{t("No pudimos completar la conexión.", "We could not complete the connection.")}</h2><p>{t("No se ha concedido ningún acceso.", "No access has been granted.")}</p><button className="button secondary" onClick={() => { setState("loading"); setAttempt(value => value + 1); }}><RefreshCw size={16}/>{t("Volver a comprobar", "Check again")}</button></section>}
      {state === "leaving" && <p role="status">{t("Volviendo a tu asistente…", "Returning to your assistant…")}</p>}
      {state === "ready" && consent && <section className="subscriber-notice mcp-consent" aria-labelledby="consent-title">
        <h2 id="consent-title">{consent.client}</h2>
        <p className="mcp-consent-host">{t("Volverá a", "Returns to")} <strong>{consent.redirectHost}</strong></p>
        <h3>{t("Podrá leer", "It will be able to read")}</h3>
        <ul>
          <li>{t("Las organizaciones activas de tu cartera:", "The active organizations in your portfolio:")} {consent.xeeds.length ? <strong>{consent.xeeds.join(" · ")}</strong> : t("ninguna todavía", "none yet")}</li>
          <li>{t("Señales, oportunidades potenciales, evidencias e historial, con su estado epistémico.", "Signals, potential opportunities, evidence and history, with their epistemic state.")}</li>
        </ul>
        <h3>{t("No podrá", "It will not be able to")}</h3>
        <ul>
          <li>{t("Añadir evidencias, cambiar tu cartera ni leer otras cuentas.", "Add evidence, change your portfolio or read other accounts.")}</li>
        </ul>
        {consent.access === "ENTITLEMENT_INACTIVE" && <p className="limit-note">{t("Tu acceso a lecturas no está activo. El asistente no recibirá lecturas hasta que tu plan o tu piloto esté vigente.", "Your read access is not active. The assistant will not receive readings until your plan or pilot is current.")}</p>}
        <p>{t("El asistente interpreta las lecturas a su manera y puede equivocarse. Puedes retirar el acceso cuando quieras desde tu cartera.", "The assistant interprets readings in its own way and can be wrong. You can withdraw access at any time from your portfolio.")}</p>
        <div className="subscriber-row-actions">
          <button className="button primary" disabled={busy} onClick={() => void decide("approve")}>{t("Permitir lectura", "Allow read access")}<ArrowRight size={16}/></button>
          <button className="button secondary" disabled={busy} onClick={() => void decide("deny")}>{t("No permitir", "Don't allow")}</button>
        </div>
      </section>}
    </div>
  </PublicShell>;
}
