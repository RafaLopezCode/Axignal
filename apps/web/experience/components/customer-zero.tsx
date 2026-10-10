"use client";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { ArrowRight, RefreshCw } from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  customerZeroCommand,
  readCustomerZeroResponse,
  type CustomerZeroState,
} from "@/lib/runtime-projection";
import { CustomerZeroObservatory } from "./customer-zero-observatory";
import { Brand, LocaleToggle } from "./ui";
import { organizationInventorySchema, type AttentionCommand } from "@/lib/organization-attention";
import {
  hasMaterialReobservationChange,
  latestObservationStatus,
} from "@/lib/reobservation-feedback";
import { presentRuntimeCode } from "@/lib/runtime-presentation";

export type RuntimeHost = {
  embedded?: boolean;
  navigationHost?: HTMLElement | null;
  toolbarHost?: HTMLElement | null;
  onNavigate?: () => void;
  /** False while the Admin shows another domain; the portfolio navigation then stays offered but unmarked. */
  active?: boolean;
};
export function CustomerZero(props: RuntimeHost) {
  return <RuntimeExperience staff {...props} />;
}
export function RuntimeExperience({
  staff = false,
  embedded = false,
  navigationHost,
  toolbarHost,
  onNavigate,
  active = true,
}: { staff?: boolean } & RuntimeHost) {
  const { t, locale } = useLocale();
  const [result, setResult] = useState<CustomerZeroState>({ state: "loading" });
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [reobserveFeedback, setReobserveFeedback] = useState<{
    observedAt: string | null;
    currentness: string | null;
    materialChange: boolean;
  } | null>(null);
  const requestRevision = useRef(0);
  async function load(write = false, command?: AttentionCommand) {
    const revision = ++requestRevision.current;
    setResult({ state: write ? "planting" : "loading" });
    try {
      const response = await fetch(
        write ? "/api/xeeds" : "/api/subscriber-context",
        {
          method: write ? "POST" : "GET",
          cache: "no-store",
          ...(write
            ? {
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(command ?? customerZeroCommand),
              }
            : {}),
        },
      );
      const next = readCustomerZeroResponse(
        await response.json(),
        response.status,
      );
      if (write && next.state === "success") {
        const persisted = await fetch("/api/subscriber-context", {cache:"no-store"});
        const reread = readCustomerZeroResponse(await persisted.json(), persisted.status);
        if (revision === requestRevision.current) setResult(reread);
        return reread;
      }
      if (revision === requestRevision.current) setResult(next);
      return next;
    } catch {
      if (revision === requestRevision.current)
        setResult({ state: "failure", reason: "RUNTIME_UNAVAILABLE" });
      return null;
    }
  }
  async function reobserveSelected() {
    try {
      const before = result.state === "success" ? result.projection : null;
      const response = await fetch("/api/organizations", {cache:"no-store"});
      const inventory = organizationInventorySchema.parse(await response.json());
      if (!response.ok || !inventory.canObserve || !inventory.selectedId) throw new Error("FOCUS_NOT_AVAILABLE");
      const after = await load(true, {action:"reobserve", id:inventory.selectedId});
      if (before && after?.state === "success") {
        const latest = latestObservationStatus(after.projection);
        setReobserveFeedback({
          observedAt: latest?.observedAt ?? null,
          currentness: latest?.currentness ?? null,
          materialChange: hasMaterialReobservationChange(before, after.projection),
        });
      }
    } catch { setResult({state:"rejected",reason:"FOCUS_NOT_AVAILABLE"}); }
  }
  useEffect(() => {
    void load();
    return () => {
      requestRevision.current++;
    };
  }, []);
  async function connect(event: React.FormEvent) {
    event.preventDefault();
    setConnecting(true);
    try {
      const response = await fetch("/api/admin/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      setToken("");
      if (response.ok) await load();
      else
        setResult({
          state: response.status >= 500 ? "failure" : "unauthorized",
          reason:
            response.status >= 500
              ? "RUNTIME_UNAVAILABLE"
              : "ADMIN_SESSION_REJECTED",
        });
    } catch {
      setResult({ state: "failure", reason: "RUNTIME_UNAVAILABLE" });
    } finally {
      setConnecting(false);
    }
  }
  const descriptions = {
    loading: t(
      "Leyendo la proyección persistida.",
      "Reading the persisted projection.",
    ),
    planting: t(
      "AXIGNAL está adquiriendo la fuente pública y evaluando su evidencia. Todavía no hay una conclusión disponible.",
      "AXIGNAL is acquiring the public source and evaluating its evidence. No conclusion is available yet.",
    ),
    NO_XEED: t(
      "Aún no hay un foco de autoobservación. Indica dónde mirar; la evidencia determinará qué puede sostener AXIGNAL.",
      "There is no self-observation focus yet. Direct attention; evidence determines what AXIGNAL can support.",
    ),
    INSUFFICIENT_EVIDENCE: t(
      "La adquisición no produjo evidencia suficiente. No se ha fabricado una señal. Revisa la causa antes de volver a observar.",
      "Acquisition did not yield sufficient evidence. No signal was fabricated. Review the cause before observing again.",
    ),
    rejected: t(
      "La solicitud no cumple la autoridad o las condiciones de observación. No se ha ejecutado una escritura económica.",
      "The request does not meet observation authority or conditions. No economic write was executed.",
    ),
    failure: t(
      "No se pudo completar la comunicación con el runtime. Vuelve a leer el estado antes de repetir una observación que podría haber terminado.",
      "Communication with the runtime could not complete. Read its state before repeating an observation that may have finished.",
    ),
    unauthorized: t(
      "Conecta una sesión Admin existente. La interfaz no concede roles ni sustituye la autorización del servicio.",
      "Connect an existing Admin session. This interface grants no roles and does not replace service authorization.",
    ),
  };
  const controls = staff ? (
    <>
      {reobserveFeedback && (
        <div className="reobserve-feedback" role="status">
          <strong>{t("Reobservación completada", "Reobservation completed")}</strong>
          <span>
            {reobserveFeedback.observedAt
              ? new Date(reobserveFeedback.observedAt).toLocaleString(locale)
              : t("Hora de observación no disponible", "Observation time unavailable")}
            {" · "}
            {reobserveFeedback.currentness
              ? presentRuntimeCode(reobserveFeedback.currentness, locale)
              : t("Vigencia no disponible", "Currentness unavailable")}
          </span>
          <p>
            {reobserveFeedback.materialChange
              ? t(
                  "La nueva proyección contiene diferencias materiales respecto a la lectura anterior. Esto no prueba por sí solo cuándo ocurrió un cambio económico.",
                  "The new projection contains material differences from the previous reading. By itself, this does not prove when an economic change occurred.",
                )
              : t(
                  "No se detectaron diferencias materiales en la proyección. La observación actual se renovó sin fabricar novedad.",
                  "No material differences were detected in the projection. The current observation was refreshed without fabricating novelty.",
                )}
          </p>
        </div>
      )}
      <details className="staff-utility">
      <summary>
        {t("Admin · Controles internos", "Admin · Staff controls")}
      </summary>
      <div>
        {!embedded && <Link className="text-link" href="/admin">
          {t("Volver a Admin", "Return to Admin")}
        </Link>}
        <button className="text-link" onClick={() => load()}>
          <RefreshCw size={15} />
          {t("Leer estado persistido", "Read persisted state")}
        </button>
        <button className="text-link" onClick={() => void reobserveSelected()}>
          {t("Reobservar la fuente pública", "Reobserve the public source")}
        </button>
      </div>
      <p>
        {t("Observar no es operar", "Observation is separate from operations")}.{" "}
        {t(
          "Los datos privados de cuentas, finanzas e integraciones no alimentan esta proyección. Solo el runtime gobernado puede producirla.",
          "Private account, finance and integration data do not feed this projection. Only the governed runtime can produce it.",
        )}
      </p>
      </details>
    </>
  ) : undefined;
  if (result.state === "success")
    return (
      <CustomerZeroObservatory
        key={result.projection.context.id}
        projection={result.projection}
        onProjection={projection => {requestRevision.current++; setReobserveFeedback(null); setResult({state:"success",projection});}}
        staffControls={controls}
        embedded={embedded}
        navigationHost={navigationHost}
        toolbarHost={toolbarHost}
        active={active}
        onNavigate={onNavigate}
      />
    );
  const headings = {
    loading: t("Recuperando contexto", "Retrieving context"),
    planting: t("Observación en curso", "Observation in progress"),
    unauthorized: t(
      "Tu sesión conserva la autoridad",
      "Your session retains authority",
    ),
    NO_XEED: t(
      "Una primera mirada, con evidencia.",
      "A first look, grounded in evidence.",
    ),
    INSUFFICIENT_EVIDENCE: t(
      "Lo desconocido sigue abierto",
      "The unknown remains open",
    ),
    rejected: t(
      "La observación no está autorizada",
      "Observation is not authorized",
    ),
    failure: t("El runtime no está disponible", "The runtime is unavailable"),
  };
  return (
    <div className="runtime-entry" data-runtime-state={result.state}>
      {embedded && toolbarHost && createPortal(<>
        <div className="navigation-controls"><span className="breadcrumb-root">Admin</span></div>
        <div className="topbar-right"><LocaleToggle /></div>
      </>, toolbarHost)}
      {!embedded && <header className="product-topbar">
        {!embedded && <Brand />}
        <LocaleToggle />
      </header>}
      <main id={embedded ? "customer-zero-main" : "main"} className="customer-zero">
        {staff && !embedded && (
          <Link className="text-link" href="/admin">
            {t("Volver a Admin", "Return to Admin")}
          </Link>
        )}
        <span className="eyebrow">
          {staff ? "Admin" : t("Panorama", "Panorama")}
        </span>
        <section
          className={`customer-zero-state state-${result.state}`}
          aria-live="polite"
          aria-busy={result.state === "loading" || result.state === "planting"}
        >
          <h1>{headings[result.state]}</h1>
          <p>{descriptions[result.state]}</p>
          <details>
            <summary>
              {t("Diagnóstico técnico", "Technical diagnostics")}
            </summary>
            <code>
              {result.state}
              {"reason" in result ? " · " + result.reason : ""}
            </code>
          </details>
          {result.state === "unauthorized" && (
            <form onSubmit={connect}>
              <label>
                {t("Credencial de sesión Admin", "Admin session credential")}
                <input
                  type="password"
                  autoComplete="off"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                />
              </label>
              <button className="button" disabled={connecting}>
                {connecting
                  ? t("Verificando sesión", "Verifying session")
                  : t("Conectar sesión", "Connect session")}
              </button>
            </form>
          )}
          {result.state === "NO_XEED" && (
            <button className="button" onClick={() => load(true)}>
              {t("Observar AXIGNAL", "Observe AXIGNAL")}
              <ArrowRight size={16} />
            </button>
          )}
          {["failure", "rejected", "INSUFFICIENT_EVIDENCE"].includes(
            result.state,
          ) && (
            <button className="button secondary" onClick={() => load()}>
              {t("Volver a leer el estado", "Read state again")}
            </button>
          )}
          {result.state === "INSUFFICIENT_EVIDENCE" && (
            <button className="text-link" onClick={() => void reobserveSelected()}>
              {t("Volver a observar la fuente", "Observe the source again")}
            </button>
          )}
        </section>
      </main>
    </div>
  );
}
