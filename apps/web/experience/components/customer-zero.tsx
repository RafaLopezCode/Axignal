"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowRight, RefreshCw } from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  customerZeroCommand,
  readCustomerZeroResponse,
  type CustomerZeroState,
} from "@/lib/runtime-projection";
import { RuntimeProductProjection } from "./runtime-product";
import { Brand, LocaleToggle } from "./ui";

export function CustomerZero() {
  return <RuntimeExperience staff />;
}
export function RuntimeExperience({ staff = false }: { staff?: boolean }) {
  const { t } = useLocale();
  const [result, setResult] = useState<CustomerZeroState>({ state: "loading" });
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const requestRevision = useRef(0);
  async function load(write = false) {
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
                body: JSON.stringify(customerZeroCommand),
              }
            : {}),
        },
      );
      const next = readCustomerZeroResponse(
        await response.json(),
        response.status,
      );
      if (revision === requestRevision.current) setResult(next);
    } catch {
      if (revision === requestRevision.current)
        setResult({ state: "failure", reason: "RUNTIME_UNAVAILABLE" });
    }
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
    <details className="staff-utility">
      <summary>
        Customer Zero · {t("Controles Staff", "Staff controls")}
      </summary>
      <div>
        <Link className="text-link" href="/admin">
          {t("Volver a Admin", "Return to Admin")}
        </Link>
        <button className="text-link" onClick={() => load()}>
          <RefreshCw size={15} />
          {t("Leer estado persistido", "Read persisted state")}
        </button>
        <button className="text-link" onClick={() => load(true)}>
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
  ) : undefined;
  if (result.state === "success")
    return (
      <RuntimeProductProjection
        projection={result.projection}
        staffControls={controls}
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
      <header className="product-topbar">
        <Brand />
        <LocaleToggle />
      </header>
      <main id="main" className="customer-zero">
        {staff && (
          <Link className="text-link" href="/admin">
            {t("Volver a Admin", "Return to Admin")}
          </Link>
        )}
        <span className="eyebrow">
          {staff ? "Customer Zero" : t("Panorama", "Panorama")}
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
            <button className="text-link" onClick={() => load(true)}>
              {t("Volver a observar la fuente", "Observe the source again")}
            </button>
          )}
        </section>
      </main>
    </div>
  );
}
