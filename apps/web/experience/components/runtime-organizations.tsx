"use client";
import { useEffect, useState } from "react";
import { useLocale } from "@/lib/locale";
import { organizationInventorySchema, type OrganizationInventory, type AttentionCommand } from "@/lib/organization-attention";
import { readCustomerZeroResponse, type RuntimeProjection } from "@/lib/runtime-projection";

/** Server-owned attention inventory; form input never supplies economic conclusions. */
export function RuntimeOrganizations({ name, internal, onReturn, onProjection }: {
  name?: string; internal: boolean; onReturn: () => void;
  onProjection?: (projection: RuntimeProjection) => void;
}) {
  const { t } = useLocale();
  const [inventory, setInventory] = useState<OrganizationInventory | null>(null);
  const [loading, setLoading] = useState(true), [busy, setBusy] = useState(false);
  const [requestedName, setName] = useState(""), [targetUri, setTarget] = useState("");
  const [notice, setNotice] = useState("");
  async function refresh() {
    setLoading(true);
    try {
      const response = await fetch("/api/organizations", { cache: "no-store" });
      if (!response.ok) throw new Error("INVENTORY_UNAVAILABLE");
      setInventory(organizationInventorySchema.parse(await response.json()));
    } catch { setNotice(t("No se pudo leer el inventario autorizado. Vuelve a leer el estado antes de repetir una observación.", "The authorized inventory could not be read. Read its state before repeating an observation.")); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, []);
  async function command(body: AttentionCommand) {
    if (busy || !inventory?.canObserve) return;
    setBusy(true); setNotice("");
    try {
      const response = await fetch("/api/xeeds", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
      const payload: unknown = await response.json();
      if (response.status === 202) setNotice(t("La atención queda guardada. La identidad sigue sin resolver: no se ha creado una organización económica ni una señal.", "Attention is saved. Identity remains unresolved: no economic organization or signal has been created."));
      else if (response.status === 422) setNotice(t("La solicitud queda guardada, pero no hay evidencia suficiente para una señal. Tu lectura anterior sigue disponible.", "The request is saved, but evidence is insufficient for a signal. Your previous reading remains available."));
      else {
        const parsed = readCustomerZeroResponse(payload, response.status);
        if (parsed.state !== "success") throw new Error("OBSERVATION_UNAVAILABLE");
        // Always reread persistence, never rely on the POST's in-memory result.
        const persisted = await fetch("/api/subscriber-context", {cache:"no-store"});
        const result = readCustomerZeroResponse(await persisted.json(), persisted.status);
        if (result.state !== "success") throw new Error("PROJECTION_UNAVAILABLE");
        onProjection?.(result.projection); onReturn(); return;
      }
    } catch { setNotice(t("No se pudo confirmar la operación. Lee su estado antes de repetirla; tu contexto no se ha sustituido.", "The operation could not be confirmed. Read its state before repeating it; your context has not been replaced.")); }
    finally { setBusy(false); void refresh(); }
  }
  return <div className="runtime-organizations" aria-busy={busy || loading}>
    <p>{t("Estas son las organizaciones disponibles en tu contexto actual.", "These are the organizations available in your current context.")}</p>
    {loading && <p role="status">{t("Leyendo los focos guardados", "Reading saved focuses")}</p>}
    {inventory?.organizations.map(entry => <section className="organization-entry" key={entry.id}>
      <strong>{entry.name ?? entry.requestedLabel}</strong>
      <span>{entry.state === "LIVE" ? t("Observación disponible", "Observation available") : entry.state === "IDENTITY_UNRESOLVED" ? t("Identidad sin resolver", "Identity unresolved") : entry.state === "INSUFFICIENT_EVIDENCE" ? t("Evidencia insuficiente", "Insufficient evidence") : entry.state === "AUTHORIZATION_REVOKED" ? t("Autorización retirada", "Authorization withdrawn") : t("Observación interrumpida", "Observation interrupted")}</span>
      {entry.projectionContextId && entry.state !== "AUTHORIZATION_REVOKED" && <button className="organization-switch" disabled={busy || (entry.id !== inventory.selectedId && !inventory.canObserve)} onClick={() => entry.id === inventory.selectedId ? onReturn() : void command({action:"select",id:entry.id})}>
        {entry.id === inventory.selectedId ? t("Volver a la observación", "Return to observation") : t("Abrir esta organización", "Open this organization")}
      </button>}
      {!entry.projectionContextId && entry.state !== "AUTHORIZATION_REVOKED" && <button className="text-link" disabled={busy || !inventory.canObserve} onClick={() => void command({action:"add",name:entry.requestedLabel,targetUri:entry.targetUri})}>{t("Revisar y reintentar", "Review and retry")}</button>}
    </section>)}
    {!inventory && name && <button className="organization-switch" onClick={onReturn}>{name} · {t("Volver a la observación", "Return to observation")}</button>}
    {notice && <p role="status">{notice}</p>}
    <button className="text-link" disabled={busy || loading} onClick={() => void refresh()}>{t("Leer estado persistido", "Read persisted state")}</button>
    <section aria-labelledby="add-organization-heading">
      <h3 id="add-organization-heading">{t("Añadir otra organización", "Add another organization")}</h3>
      <p id="organization-availability">{t("Indica dónde observar. El servicio verificará la identidad y adquirirá evidencia; un nombre o una web no establecen una conclusión.", "Direct observation. The service will verify identity and acquire evidence; a name or website does not establish a conclusion.")}</p>
      <form onSubmit={event => {event.preventDefault(); void command({action:"add",name:requestedName,targetUri});}}>
        <label>{t("Nombre de la organización", "Organization name")}<input required maxLength={200} value={requestedName} list="authorized-organizations" onChange={event => {setName(event.target.value); const match=inventory?.available.find(item => item.name===event.target.value); if(match)setTarget(match.targetUri);}} /></label>
        <datalist id="authorized-organizations">{inventory?.available.map(item => <option key={item.targetUri} value={item.name} />)}</datalist>
        <label>{t("Web pública", "Public website")}<input type="url" required maxLength={2048} value={targetUri} placeholder="https://" onChange={event => setTarget(event.target.value)} /></label>
        <button className="button secondary" disabled={busy || loading || !inventory?.canObserve} aria-describedby="organization-availability">{busy ? t("Verificando identidad y evidencia", "Verifying identity and evidence") : t("Añadir organización", "Add organization")}</button>
      </form>
      <p>{internal
        ? t("Admin es de uso interno, sin checkout ni pago. Añadir otros focos requiere autorización interna del servicio, con las mismas reglas de evidencia.", "Admin is for internal use, without checkout or payment. Adding other focuses requires internal service authorization, with the same evidence rules.")
        : t("Este contexto no informa del plan ni de su capacidad disponible. No se puede deducir tu límite a partir de la organización visible.", "This context does not report your plan or its available capacity. Your limit cannot be inferred from the visible organization.")}</p>
    </section>
  </div>;
}
