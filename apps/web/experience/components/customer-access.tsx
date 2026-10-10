"use client";
import { useEffect, useState, useRef } from "react";
import { useLocale } from "@/lib/locale";
import { customerAccess, issuedInvite, pilotLink, activationCause, type CustomerAccess, type CustomerAction } from "@/lib/customer-access";
import { StaffCapacity } from "./staff-capacity";
import { PilotTestAccounts } from "./pilot-test-accounts";

export function CustomerAccessPanel() {
  const { t, locale } = useLocale();
  const [tab, setTab] = useState("invites"), [data, setData] = useState<CustomerAccess | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState(""), [hours, setHours] = useState(168);
  const [link, setLink] = useState(""), [copied, setCopied] = useState(false);
  const [query, setQuery] = useState(""), [filter, setFilter] = useState("ALL");
  const [revocation, setRevocation] = useState<{ reference: string; action: CustomerAction } | null>(null);
  const [revokeReason, setRevokeReason] = useState("");
  const commandKey = useRef(""), revokeKey = useRef(""), linkField = useRef<HTMLInputElement>(null);
  const failure = (code: unknown) => {
    if (code === "ADMIN_SESSION_REQUIRED") return t("Necesitas una sesión Admin activa.", "An active Admin session is required.");
    if (code === "STEP_UP_OR_SCOPE_REQUIRED" || code === "ADMIN_SCOPE_REQUIRED") return t("Activa la verificación reforzada en Operaciones. Tu rol debe permitir gestionar clientes.", "Activate step-up in Operations. Your role must allow client management.");
    if (code === "INVITE_ALREADY_ISSUED") return t("La invitación ya se creó. El enlace no se vuelve a mostrar; revócala antes de crear otra.", "The invitation was already created. Its link cannot be shown again; revoke it before creating another.");
    if (code === "CUSTOMER_ACCESS_UNAVAILABLE") return t("El servicio de clientes no está disponible. Revisa la conexión y el estado del runtime.", "The client service is unavailable. Check the connection and runtime state.");
    if (code === "RATE_LIMITED") return t("Has alcanzado el límite de 20 invitaciones por hora.", "You have reached the limit of 20 invitations per hour.");
    return t("No se pudo completar. Actualiza el estado y revisa los permisos antes de reintentar.", "Could not complete. Refresh the state and check permissions before retrying.");
  };
  async function refresh() {
    const r = await fetch("/api/admin/customer-access", { cache: "no-store" }), raw = await r.json();
    if (!r.ok) throw new Error(failure(raw?.reason));
    setData(customerAccess.parse(raw));
  }
  async function run(work: () => Promise<void>) {
    if (busy) return; setBusy(true); setError(null);
    try { await work(); } catch (e) { setError(e instanceof Error ? e.message : failure(null)); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const r = await fetch("/api/admin/customer-access", { cache: "no-store" }), raw = await r.json();
        if (!active) return;
        if (!r.ok) throw new Error(failure(raw?.reason));
        setData(customerAccess.parse(raw));
      } catch (e) { if (active) setError(e instanceof Error ? e.message : failure(null)); }
    };
    void load();
    const timer = setInterval(() => { if (!document.hidden) void load(); }, 30_000);
    return () => { active = false; clearInterval(timer); };
  }, []);
  async function mutate(action: CustomerAction, body: object) {
    const r = await fetch("/api/admin/customer-access/" + action, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const raw = await r.json(); if (!r.ok) throw new Error(failure(raw?.reason)); return raw;
  }
  const when = (v: string | null) => v ? new Date(v).toLocaleString(locale) : t("No disponible", "Unavailable");
  const state = (v: string) => ({ PENDING: t("Pendiente", "Pending"), REDEEMED: t("Canjeada", "Redeemed"), EXPIRED: t("Caducada", "Expired"), REVOKED: t("Revocada", "Revoked"), ACTIVE: t("Activo", "Active") }[v] ?? v);
  const diagnosis = {
    PAYMENT: t("Pago no confirmado. Revisa la autoridad de facturación; el usuario puede volver a comprobar el pago.", "Payment unconfirmed. Check the billing authority; the user can check payment again."),
    ACCESS: t("Sin capacidad confirmada. Revisa la invitación o la confirmación del pago.", "No confirmed capacity. Check the invitation or payment confirmation."),
    CAPACITY: t("Organización en espera. El usuario puede reintentar con capacidad confirmada.", "Organization waiting. The user can retry with confirmed capacity."),
    IDENTITY: t("Identidad pendiente. Revisa la referencia de la organización.", "Identity pending. Check the organization reference."),
    RUNTIME: t("Primera observación desactivada. Requiere autorización del runtime.", "First observation disabled. Runtime authorization is required."),
    OBSERVATION: t("Primera observación no disponible. Revisa su estado operativo.", "First observation unavailable. Check its operational state."),
    READY: t("Primera observación disponible.", "First observation available."),
  };
  const startRevoke = (reference: string, action: CustomerAction) => { setRevocation({ reference, action }); revokeKey.current = crypto.randomUUID(); setRevokeReason(""); };
  const filtered = data?.pilot?.invites.filter(i => (filter === "ALL" || i.state === filter) && (i.reason + i.invite_ref + (i.redeemed_tenant_id ?? "")).toLowerCase().includes(query.toLowerCase())) ?? [];
  const orgs = (c: CustomerAccess["customers"][number]) => c.organizations.map(o => <p key={o.focusId}>{o.label} · {o.state}{o.reason ? " · " + o.reason : ""}{o.observation ? " · " + o.observation.state : ""} · {o.observation?.headline ?? t("Primera observación no disponible.", "First observation unavailable.")}</p>);
  return <div className="customer-access">
    <nav className="customer-access-tabs" aria-label={t("Clientes y accesos", "Clients and access")}>
      <button className="button secondary" aria-pressed={tab === "invites"} onClick={() => { setTab("invites"); setLink(""); }}>{t("Invitaciones y pilotos", "Invitations and pilots")}</button>
      <button className="button secondary" aria-pressed={tab === "accounts"} onClick={() => { setTab("accounts"); setLink(""); }}>{t("Cuentas y suscripciones", "Accounts & subscriptions")}</button>
      <button className="button secondary" aria-pressed={tab === "operations"} onClick={() => { setTab("operations"); setLink(""); }}>{t("Operaciones", "Operations")}</button>
      <button className="button secondary" disabled={busy} onClick={() => void run(refresh)}>{t("Actualizar", "Refresh")}</button>
    </nav>
    {error && <p role="alert">{error}</p>}
    {!data && !error && <p role="status">{t("Cargando…", "Loading…")}</p>}
    {data && <p>{t("Estado consultado", "State checked")} · {when(data.asOf)}</p>}
    {tab === "operations" && <><StaffCapacity /><PilotTestAccounts /></>}
    {tab === "invites" && <>
      <section className="admin-attention staff-capacity">
        <h2>{t("Crear invitación", "Create invitation")}</h2>
        <p>{t("Una organización durante 60 días. El enlace privado se muestra una sola vez.", "One organization for 60 days. The private link is shown once.")}</p>
        {data && !data.pilotEnabled && <p role="status">{t("El piloto está desactivado en este entorno.", "Pilot access is disabled in this environment.")}</p>}
        <form className="admin-table-toolbar" onSubmit={e => {
          e.preventDefault(); setLink(""); setCopied(false);
          if (!commandKey.current) commandKey.current = crypto.randomUUID();
          void run(async () => {
            const invite = issuedInvite.parse(await mutate("issue", { reason: reason.trim(), inviteHours: hours, idempotencyKey: commandKey.current }));
            setLink(pilotLink(window.location.origin, invite.inviteToken)); commandKey.current = ""; setReason("");
            await refresh(); linkField.current?.focus();
          });
        }}>
          <label className="search-field"><span>{t("Propósito o destinatario interno", "Internal purpose or recipient")}</span><input required minLength={8} maxLength={500} value={reason} disabled={busy} autoComplete="off" onChange={e => { setReason(e.target.value); commandKey.current = ""; }} /></label>
          <label><span>{t("Caducidad en horas", "Expiry in hours")}</span><input type="number" min={1} max={720} required value={hours} disabled={busy} onChange={e => { setHours(Number(e.target.value)); commandKey.current = ""; }} /></label>
          <button className="button primary" disabled={busy || !data?.pilotEnabled || reason.trim().length < 8} type="submit">{t("Crear invitación", "Create invitation")}</button>
        </form>
        {link && <div className="customer-access-secret"><label>{t("Enlace privado de un solo uso", "Private one-use link")}<input ref={linkField} type="password" readOnly value={link} autoComplete="off" /></label>
          <button className="button secondary" disabled={busy} onClick={() => void run(async () => { try { await navigator.clipboard.writeText(link); setCopied(true); } catch { linkField.current?.focus(); linkField.current?.select(); throw new Error(t("Selecciona y copia el enlace privado.", "Select and copy the private link.")); } })}>{t("Copiar enlace", "Copy link")}</button>
          <button className="button secondary" onClick={() => setLink("")}>{t("Cerrar", "Close")}</button>
          {copied && <p role="status">{t("Enlace copiado. Compártelo únicamente con la persona invitada.", "Link copied. Share it only with the invited person.")}</p>}
        </div>}
      </section>
      <section className="admin-attention staff-capacity"><h2>{t("Invitaciones", "Invitations")}</h2>
        <div className="admin-table-toolbar"><label className="search-field"><span>{t("Buscar", "Search")}</span><input value={query} onChange={e => setQuery(e.target.value)} /></label>
          <label>{t("Estado", "State")}<select value={filter} onChange={e => setFilter(e.target.value)}><option value="ALL">{t("Todas", "All")}</option>{["PENDING", "REDEEMED", "EXPIRED", "REVOKED"].map(s => <option key={s} value={s}>{state(s)}</option>)}</select></label></div>
        {data && filtered.length === 0 && <p>{t("No hay invitaciones para este filtro.", "No invitations match this filter.")}</p>}
        <ul className="customer-access-records">{filtered.map(i => <li key={i.invite_ref}><strong>{i.reason}</strong><span>{state(i.state)} · {when(i.expires_at)}</span><code>{i.invite_ref}</code>
          {i.redeemed_tenant_id && <p>{i.redeemed_tenant_id} · {i.redeemed_principal_id} · {when(i.redeemed_at)}</p>}
          {i.state === "PENDING" && <button className="button secondary" onClick={() => startRevoke(i.invite_ref, "revoke-invite")}>{t("Revocar", "Revoke")}</button>}
        </li>)}</ul>
        <h2>{t("Concesiones piloto", "Pilot grants")}</h2>
        {data?.pilot?.grants.length === 0 && <p>{t("No hay concesiones piloto.", "No pilot grants.")}</p>}
        <ul className="customer-access-records">{data?.pilot?.grants.map(g => {
          const c = data.customers.find(c => c.tenantId === g.tenant_id && c.principalId === g.principal_id);
          return <li key={g.grant_ref}><strong>{g.tenant_id}</strong><span>{state(g.state)} · {g.capacity} · {when(g.granted_at)} → {when(g.expires_at)}</span><code>{g.grant_ref}</code><p>{g.principal_id}</p>
            <p>{c ? diagnosis[activationCause(c)] : t("Membresía no disponible", "Membership unavailable")}</p>{c && orgs(c)}
            {g.state === "ACTIVE" && <button className="button secondary" onClick={() => startRevoke(g.grant_ref, "revoke-grant")}>{t("Revocar", "Revoke")}</button>}
          </li>;
        })}</ul>
        <details><summary>{t("Registro de acciones", "Action history")}</summary><ul className="customer-access-records">{data?.pilot?.audit.map(a => <li key={a.sequence}><span>{a.action} · {a.actor} · {when(a.occurred_at)}</span><code>{a.reference}</code><span>{a.reason}</span></li>)}</ul></details>
      </section>
    </>}
    {revocation && <section className="admin-attention staff-capacity" aria-label={t("Confirmar revocación", "Confirm revocation")}><h2>{t("Confirmar revocación", "Confirm revocation")}</h2><code>{revocation.reference}</code>
      <p>{t("Retira los derechos del piloto y conserva las organizaciones y la evidencia histórica.", "Withdraws pilot rights and preserves organizations and historical evidence.")}</p>
      <label>{t("Motivo", "Reason")}<input autoFocus minLength={8} maxLength={500} value={revokeReason} disabled={busy} onChange={e => setRevokeReason(e.target.value)} /></label>
      <button className="button primary" disabled={busy || revokeReason.trim().length < 8} onClick={() => void run(async () => { await mutate(revocation.action, { reference: revocation.reference, reason: revokeReason.trim(), idempotencyKey: revokeKey.current }); setRevocation(null); await refresh(); })}>{t("Confirmar revocación", "Confirm revocation")}</button>
      <button className="button secondary" disabled={busy} onClick={() => setRevocation(null)}>{t("Cancelar", "Cancel")}</button>
    </section>}
    {tab === "accounts" && data && <section className="admin-attention staff-capacity"><h2>{t("Cuentas y suscripciones", "Accounts & subscriptions")}</h2>
      {data.customers.length === 0 && <p>{t("No hay cuentas con membresía activa.", "No accounts with active membership.")}</p>}
      <ul className="customer-access-records">{data.customers.map(c => {
        const a = data.accountOperations.customers.find(a => a.tenantId === c.tenantId);
        return <li key={c.tenantId + c.principalId}><strong>{a?.displayName ?? c.tenantId}</strong><code>{c.tenantId} · {c.principalId}</code>
          <p>{c.entitlementSource} · {c.capacityCurrentness === "CURRENT" && c.capacity !== null ? c.capacity : t("No disponible", "Unavailable")}</p>
          <p>{diagnosis[activationCause(c)]}</p><p>{t("Suscripción", "Subscription")}: {c.billing ? c.billing.status + " · " + c.billing.paymentState : t("No disponible", "Unavailable")}</p>
          {c.billing && <p>{t("Capacidad contratada", "Contracted capacity")}: {c.billing.contractedCapacity ?? t("No disponible", "Unavailable")} · {when(c.billing.verifiedAt)}</p>}
          {a && <p>{t("Cuenta", "Account")}: {a.accountId} · {a.accountStatus}</p>}{orgs(c)}
        </li>;
      })}</ul>
      {data.accountOperations.customers.filter(a => !data.customers.some(c => c.tenantId === a.tenantId)).map(a => <p key={a.accountId}>{a.displayName} · {a.accountId} · {t("Membresía no disponible", "Membership unavailable")}</p>)}
    </section>}
  </div>;
}

