"use client";

import { useCallback, useEffect, useState } from "react";
import { useLocale } from "@/lib/locale";
import { mcpConnectionsSchema, mcpRevokeSchema, type McpConnection } from "@/lib/mcp-connect";

/** Assistants with read access to this subscriber's AXIGNAL, and how to connect one (ADR-0086). */
export function SubscriberMcpConnections() {
  const { t, locale } = useLocale();
  const [connections, setConnections] = useState<McpConnection[] | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [endpoint, setEndpoint] = useState("");
  const read = useCallback(async () => {
    try {
      const response = await fetch("/api/subscriber/mcp/connections", { cache: "no-store" });
      if (!response.ok) throw new Error("READ_FAILED");
      setConnections(mcpConnectionsSchema.parse(await response.json()).connections);
    } catch { setConnections(null); }
  }, []);
  useEffect(() => { setEndpoint(`${window.location.origin}/mcp`); void read(); }, [read]);
  async function revoke(grantId: string) {
    if (busy) return;
    setBusy(true);
    try {
      const response = await fetch("/api/subscriber/mcp/connections", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "revoke", grantId }),
      });
      if (!response.ok || !mcpRevokeSchema.parse(await response.json()).revoked) throw new Error("REVOKE_FAILED");
      setMessage(t("Acceso retirado. Ese asistente ya no puede leer tu cartera.", "Access withdrawn. That assistant can no longer read your portfolio."));
      await read();
    } catch { setMessage(t("No pudimos confirmar la retirada. Vuelve a comprobar la lista.", "We could not confirm the withdrawal. Check the list again.")); }
    finally { setBusy(false); }
  }
  return <section className="subscriber-organizations mcp-connections" aria-labelledby="mcp-title" aria-busy={busy}>
    <span className="eyebrow">{t("Asistentes", "Assistants")}</span>
    <h2 id="mcp-title">{t("Lee tu AXIGNAL desde Claude o ChatGPT.", "Read your AXIGNAL from Claude or ChatGPT.")}</h2>
    <p>{t("Añade esta dirección como conector MCP personalizado en tu asistente. Solo lectura: tú autorizas la conexión y puedes retirarla aquí.", "Add this address as a custom MCP connector in your assistant. Read-only: you authorize the connection and can withdraw it here.")}</p>
    {endpoint && <p><code className="mcp-endpoint">{endpoint}</code></p>}
    {connections === null ? <p>{t("La lista de conexiones no está disponible ahora.", "The list of connections is not available right now.")}</p>
      : !connections.length ? <p>{t("Ningún asistente conectado.", "No assistant connected.")}</p>
      : <ul className="subscriber-list">{connections.map(item => <li key={item.grantId}><div><h3>{item.client}</h3><p>{t("Conectado el", "Connected on")} {new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(item.connectedAt))} · {t("Solo lectura", "Read-only")}</p></div><div className="subscriber-row-actions"><button className="text-link" disabled={busy} onClick={() => void revoke(item.grantId)}>{t("Retirar acceso", "Withdraw access")}</button></div></li>)}</ul>}
    {message && <p aria-live="polite">{message}</p>}
  </section>;
}
