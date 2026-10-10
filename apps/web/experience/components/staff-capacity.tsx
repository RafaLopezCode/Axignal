"use client";
import { useState } from "react";
import type { z } from "zod";
import { useLocale } from "@/lib/locale";
import {
  staffReason, staffResults, staffState,
  type StaffAction, type StaffAddResult, type StaffPreview, type StaffReason, type StaffState,
} from "@/lib/staff-capacity";

type Destination = "CUSTOMER_ACCOUNT" | "AXIGNAL_INTERNAL";
const DAY = 86_400_000;
const key = (prefix: string) => `${prefix}:${crypto.randomUUID()}`;

async function call<A extends StaffAction>(action: A, body: object): Promise<z.infer<(typeof staffResults)[A]>> {
  const response = await fetch(`/api/admin/staff-capacity/${action}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(staffReason(payload && typeof payload === "object" && "reason" in payload ? payload.reason : null));
  return staffResults[action].parse(payload) as z.infer<(typeof staffResults)[A]>;
}

/** Staff-provisioned capacity: add organizations for clients or for AXIGNAL itself, never via checkout. */
export function StaffCapacity() {
  const { t, locale } = useLocale();
  const [stepUpToken, setStepUpToken] = useState("");
  const [stepUpReady, setStepUpReady] = useState(false);
  const [stepUpBusy, setStepUpBusy] = useState(false);
  const [stepUpError, setStepUpError] = useState(false);
  async function activateStepUp(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStepUpBusy(true); setStepUpError(false);
    try {
      const result = await fetch("/api/admin/step-up", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: stepUpToken.trim() }),
      });
      if (!result.ok) { setStepUpReady(false); setStepUpError(true); return; }
      setStepUpReady(true); setStepUpToken("");
    } catch { setStepUpReady(false); setStepUpError(true); }
    finally { setStepUpToken(""); setStepUpBusy(false); }
  }
  const [tenant, setTenant] = useState("");
  const [state, setState] = useState<StaffState | null>(null);
  const [destination, setDestination] = useState<Destination>("CUSTOMER_ACCOUNT");
  const [capacity, setCapacity] = useState(1);
  const [days, setDays] = useState(90);
  const [reason, setReason] = useState("");
  const [preview, setPreview] = useState<{ value: StaffPreview; expiresAt: string; key: string } | null>(null);
  const [locator, setLocator] = useState("");
  const [addReason, setAddReason] = useState("");
  const [added, setAdded] = useState<StaffAddResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<StaffReason | null>(null);
  const [notice, setNotice] = useState("");
  const [revoking, setRevoking] = useState<string | null>(null);
  const [revokeReason, setRevokeReason] = useState("");

  async function run(task: () => Promise<void>) {
    setBusy(true); setError(null); setNotice("");
    try { await task(); }
    catch (failure) { setError(staffReason(failure instanceof Error ? failure.message : null)); }
    finally { setBusy(false); }
  }
  async function refresh(reference: string) {
    const response = await fetch(`/api/admin/staff-capacity?tenantId=${encodeURIComponent(reference)}`, { cache: "no-store" });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) throw new Error(staffReason(payload && typeof payload === "object" && "reason" in payload ? payload.reason : null));
    setState(staffState.parse(payload));
  }
  const load = () => run(async () => { setPreview(null); setAdded(null); await refresh(tenant.trim()); });
  const review = () => run(async () => {
    const expiresAt = new Date(Date.now() + days * DAY).toISOString();
    const value = await call("preview", { tenantId: state!.tenantId, destination, capacity, expiresAt });
    setPreview({ value, expiresAt, key: key("grant") });
  });
  const confirm = () => run(async () => {
    await call("grant", {
      tenantId: state!.tenantId, destination, capacity, expiresAt: preview!.expiresAt,
      reason: reason.trim(), idempotencyKey: preview!.key,
    });
    setReason(""); setPreview(null); setAdded(null); await refresh(state!.tenantId);
    setNotice(t("Capacidad concedida. La cuenta ya puede añadir organizaciones sin pagar.", "Capacity granted. The account can now add organizations without paying."));
  });
  const revoke = (grantRef: string) => run(async () => {
    await call("revoke", { grantRef, reason: revokeReason.trim() });
    setRevoking(null); setRevokeReason(""); setAdded(null);
    await refresh(state!.tenantId);
    setNotice(t("Capacidad retirada. Las organizaciones ya añadidas se conservan.", "Capacity revoked. Organizations already added are kept."));
  });
  const addOrganization = () => run(async () => {
    const result = await call("organizations", {
      tenantId: state!.tenantId, locator: locator.trim(), reason: addReason.trim(), idempotencyKey: key("staff-add"),
    });
    setAdded(result);
    if (result.status === "CREATED" || result.status === "ALREADY_PRESENT") { setLocator(""); setAddReason(""); }
    await refresh(state!.tenantId);
  });

  const reasonOk = reason.trim().length >= 8;
  const addOk = locator.trim().length >= 2 && addReason.trim().length >= 8;
  const sourceLabel: Record<StaffState["entitlementSource"], string> = {
    BILLING: t("Suscripción pagada", "Paid subscription"),
    "BILLING+STAFF_GRANT": t("Suscripción pagada + capacidad Staff", "Paid subscription + staff capacity"),
    STAFF_GRANT: t("Capacidad Staff (sin pago)", "Staff capacity (no payment)"),
    DESIGN_PARTNER_PILOT: t("Piloto", "Pilot"),
    UNKNOWN: t("Sin capacidad confirmada", "No confirmed capacity"),
  };
  const addStatus: Record<string, string> = {
    CREATED: t("Organización añadida. El cliente ya la ve en su espacio.", "Organization added. The client already sees it in their workspace."),
    ALREADY_PRESENT: t("La organización ya estaba en ese espacio; no se duplicó.", "The organization was already in that workspace; nothing was duplicated."),
    CAPACITY_REQUIRED: t("El espacio está lleno. Concede más capacidad Staff; nunca se crea un pago.", "The workspace is full. Grant more staff capacity; no payment is ever created."),
    CAPACITY_UNKNOWN: t("La cuenta no tiene capacidad confirmada. Concede capacidad primero.", "The account has no confirmed capacity. Grant capacity first."),
    IDENTITY_PENDING: t("Identidad pendiente: AXIGNAL no pudo confirmar esa organización. Prueba con su web o nombre legal.", "Identity pending: AXIGNAL could not confirm that organization. Try its website or legal name."),
    IDENTITY_REJECTED: t("Identidad rechazada: la referencia no corresponde a una organización verificable.", "Identity rejected: the reference does not match a verifiable organization."),
  };
  const errors: Record<StaffReason, string> = {
    ADMIN_SESSION_REQUIRED: t("Necesitas una sesión Admin activa.", "An active Admin session is required."),
    STEP_UP_REQUIRED: t("Esta acción exige una verificación reforzada reciente (menos de 15 minutos). Tu sesión actual solo permite consultar.", "This action requires recent step-up verification (under 15 minutes). Your current session can only read."),
    ADMIN_SCOPE_REQUIRED: t("Tu rol no permite gestionar cuentas de clientes.", "Your role cannot manage client accounts."),
    SCOPE_REQUIRED: t("Tu rol no permite gestionar cuentas de clientes.", "Your role cannot manage client accounts."),
    TENANT_UNKNOWN: t("No existe una cuenta activa con esa referencia.", "No active account has that reference."),
    GRANT_NOT_FOUND: t("Esa concesión ya no existe.", "That grant no longer exists."),
    IDEMPOTENCY_CONFLICT: t("Ya se envió una concesión distinta con esta confirmación. Revisa de nuevo antes de confirmar.", "A different grant was already sent with this confirmation. Review again before confirming."),
    INVALID_REQUEST: t("Revisa los datos: capacidad 1–500, caducidad dentro de un año y motivo de al menos 8 caracteres. La capacidad interna solo vale para la cuenta AXIGNAL configurada.", "Check the details: capacity 1–500, expiry within a year and a reason of at least 8 characters. Internal capacity only applies to the configured AXIGNAL account."),
    STAFF_CAPACITY_DISABLED: t("La capacidad Staff está desactivada en este entorno.", "Staff capacity is disabled in this environment."),
    ORIGIN_REQUIRED: t("Abre el Admin desde su origen autorizado.", "Open Admin from its authorized origin."),
    FAILED: t("No se pudo completar. No se ha creado ningún pago ni cambio parcial; puedes reintentar.", "This could not be completed. No payment or partial change was made; you can retry."),
  };
  const when = (value: string) => new Date(value).toLocaleDateString(locale);

  return (
    <section className="admin-attention staff-capacity" aria-labelledby="staff-capacity-title">
      <h2 id="staff-capacity-title">{t("Añadir organizaciones sin checkout", "Add organizations without checkout")}</h2>
      <p id="staff-capacity-help">
        {t("Concede capacidad Staff a la cuenta de un cliente, o a la cuenta interna de AXIGNAL para usarla desde Admin, y añade organizaciones en su nombre. Nunca crea pagos, suscripciones ni checkout. Cada acción queda auditada y puede caducar o retirarse.",
          "Grant staff capacity to a client account, or to AXIGNAL's internal account to use it from Admin, and add organizations on its behalf. It never creates payments, subscriptions or checkout. Every action is audited and can expire or be revoked.")}
      </p>
      <form className="admin-table-toolbar" onSubmit={event => { void activateStepUp(event); }}>
        <label className="search-field">
          <span>{t("Credencial temporal de verificación reforzada (SSH + autenticador)", "Temporary step-up credential (SSH + authenticator)")}</span>
          <input type="password" value={stepUpToken} autoComplete="off" spellCheck={false}
            onChange={event => setStepUpToken(event.target.value)} disabled={stepUpBusy}
            placeholder={t("Emitida por el operador · 10 minutos", "Issued by operator · 10 minutes")} />
        </label>
        <button type="submit" className="button secondary" disabled={stepUpBusy || stepUpToken.trim().length < 48}>
          {t("Activar 10 minutos", "Activate for 10 minutes")}
        </button>
      </form>
      {stepUpReady && <p role="status">{t("Verificación reforzada activada. La sesión Admin normal sigue abierta.", "Step-up active. Your normal Admin session remains open.")}</p>}
      {stepUpError && <p role="alert">{t("Credencial rechazada, caducada o de otro operador.", "Credential rejected, expired or issued for another operator.")}</p>}
      <form className="admin-table-toolbar" onSubmit={event => { event.preventDefault(); void load(); }} aria-describedby="staff-capacity-help">
        <label className="search-field">
          <span>{t("Referencia de cuenta", "Account reference")}</span>
          <input value={tenant} onChange={event => setTenant(event.target.value)} autoComplete="off" spellCheck={false}
            maxLength={160} placeholder="tenant_…" disabled={busy} />
        </label>
        <button type="submit" className="button secondary" disabled={busy || tenant.trim().length < 3}>
          {t("Abrir cuenta", "Open account")}
        </button>
      </form>

      {state && <>
        <dl className="staff-capacity-summary">
          <div><dt>{t("Cuenta", "Account")}</dt><dd><code>{state.tenantId}</code></dd></div>
          <div><dt>{t("Origen de la capacidad", "Capacity source")}</dt><dd>{sourceLabel[state.entitlementSource]}</dd></div>
          <div><dt>{t("Capacidad Staff activa", "Active staff capacity")}</dt><dd>{state.activeStaffCapacity}</dd></div>
        </dl>

        <fieldset className="staff-capacity-step" disabled={busy}>
          <legend>{t("1 · Conceder capacidad", "1 · Grant capacity")}</legend>
          <div role="radiogroup" aria-label={t("Destino", "Destination")} className="staff-capacity-choice">
            {(["CUSTOMER_ACCOUNT", "AXIGNAL_INTERNAL"] as const).map(value => (
              <label key={value}>
                <input type="radio" name="staff-destination" checked={destination === value}
                  onChange={() => { setDestination(value); setPreview(null); }} />
                {value === "CUSTOMER_ACCOUNT"
                  ? t("Cuenta de cliente", "Client account")
                  : t("AXIGNAL interno · Admin", "AXIGNAL internal · Admin")}
              </label>
            ))}
          </div>
          <div className="admin-table-toolbar">
            <label className="search-field"><span>{t("Organizaciones", "Organizations")}</span>
              <input type="number" min={1} max={500} value={capacity}
                onChange={event => { setCapacity(Math.max(1, Math.min(500, Number(event.target.value) || 1))); setPreview(null); }} />
            </label>
            <label className="search-field"><span>{t("Días de vigencia", "Days valid")}</span>
              <input type="number" min={1} max={365} value={days}
                onChange={event => { setDays(Math.max(1, Math.min(365, Number(event.target.value) || 1))); setPreview(null); }} />
            </label>
          </div>
          <label className="search-field staff-capacity-reason"><span>{t("Motivo (queda en la auditoría)", "Reason (kept in the audit trail)")}</span>
            <input value={reason} maxLength={500} onChange={event => setReason(event.target.value)}
              placeholder={t("Ej.: investigación propia del sector energético", "E.g. own research on the energy sector")} />
          </label>
          {!preview
            ? <button type="button" className="button secondary" disabled={!reasonOk} onClick={() => void review()}>
                {t("Revisar antes de conceder", "Review before granting")}
              </button>
            : <div className="staff-capacity-preview" role="group" aria-label={t("Resumen de la concesión", "Grant summary")}>
                <p>
                  {t("Capacidad Staff", "Staff capacity")}: <strong>{preview.value.currentStaffCapacity} → {preview.value.staffCapacityAfter}</strong>
                  {" · "}{t("hasta", "until")} {when(preview.value.expiresAt)}
                </p>
                <p>{t("Sin cobro · Sin checkout · Sin cambios en Stripe", "No charge · No checkout · No Stripe changes")}</p>
                <div className="admin-table-toolbar">
                  <button type="button" className="button primary" onClick={() => void confirm()}>
                    {t("Confirmar concesión", "Confirm grant")}
                  </button>
                  <button type="button" className="button secondary" onClick={() => setPreview(null)}>
                    {t("Cambiar", "Change")}
                  </button>
                </div>
              </div>}
        </fieldset>

        <fieldset className="staff-capacity-step" disabled={busy}>
          <legend>{t("2 · Añadir una organización", "2 · Add an organization")}</legend>
          <label className="search-field"><span>{t("Web o nombre legal", "Website or legal name")}</span>
            <input value={locator} maxLength={2048} onChange={event => setLocator(event.target.value)}
              placeholder="https://www.example.com/" />
          </label>
          <label className="search-field staff-capacity-reason"><span>{t("Motivo", "Reason")}</span>
            <input value={addReason} maxLength={500} onChange={event => setAddReason(event.target.value)} />
          </label>
          <button type="button" className="button primary" disabled={!addOk} onClick={() => void addOrganization()}>
            {t("Añadir a esta cuenta", "Add to this account")}
          </button>
          {added?.status && <p role="status">{addStatus[added.status] ?? added.status}</p>}
          <p className="staff-capacity-note">
            {t("La primera observación llega con el ciclo programado de AXIGNAL, no al instante: el Staff no actúa como el cliente.",
              "The first observation arrives with AXIGNAL's scheduled cycle, not instantly: staff never acts as the client.")}
          </p>
        </fieldset>

        <section aria-labelledby="staff-grants-title">
          <h3 id="staff-grants-title">{t("Concesiones", "Grants")}</h3>
          {state.grants.length === 0
            ? <p>{t("Esta cuenta no tiene concesiones Staff.", "This account has no staff grants.")}</p>
            : <ul className="staff-capacity-list">
                {state.grants.map(grant => (
                  <li key={grant.grantRef}>
                    <span><strong>{grant.capacity}</strong> · {grant.destination === "AXIGNAL_INTERNAL" ? t("interno", "internal") : t("cliente", "client")}
                      {" · "}{grant.state === "ACTIVE" ? t("activa hasta", "active until") + " " + when(grant.expiresAt)
                        : grant.state === "REVOKED" ? t("retirada", "revoked") : t("caducada", "expired")}</span>
                    <span className="staff-capacity-muted">{grant.reason} · {grant.grantedBy}</span>
                    {grant.state === "ACTIVE" && (revoking !== grant.grantRef
                      ? <button type="button" className="button secondary" disabled={busy} onClick={() => { setRevoking(grant.grantRef); setRevokeReason(""); }}>
                          {t("Retirar", "Revoke")}
                        </button>
                      : <span className="staff-capacity-revoke">
                          <label className="search-field"><span>{t("Motivo de la retirada", "Reason for revoking")}</span>
                            <input value={revokeReason} maxLength={500} autoFocus onChange={event => setRevokeReason(event.target.value)} />
                          </label>
                          <button type="button" className="button primary" disabled={busy || revokeReason.trim().length < 8} onClick={() => void revoke(grant.grantRef)}>
                            {t("Confirmar retirada", "Confirm revocation")}
                          </button>
                          <button type="button" className="button secondary" onClick={() => setRevoking(null)}>{t("Cancelar", "Cancel")}</button>
                        </span>)}
                  </li>
                ))}
              </ul>}
        </section>

        <section aria-labelledby="staff-audit-title">
          <h3 id="staff-audit-title">{t("Auditoría", "Audit trail")}</h3>
          {state.audit.length === 0
            ? <p>{t("Sin acciones registradas.", "No recorded actions.")}</p>
            : <ol className="staff-capacity-list">
                {state.audit.map((row, index) => (
                  <li key={`${row.occurredAt}-${index}`}>
                    <time dateTime={row.occurredAt}>{new Date(row.occurredAt).toLocaleString(locale)}</time>
                    <span>{row.action === "CAPACITY_GRANTED" ? t("Capacidad concedida", "Capacity granted")
                      : row.action === "CAPACITY_REVOKED" ? t("Capacidad retirada", "Capacity revoked")
                      : row.action === "ORGANIZATION_ADDED_BY_STAFF" ? t("Organización añadida por Staff", "Organization added by staff")
                      : row.action}</span>
                    <span className="staff-capacity-muted">{row.actor}</span>
                  </li>
                ))}
              </ol>}
        </section>
      </>}

      <p role="status" aria-live="polite">{busy ? t("Procesando…", "Working…") : notice}</p>
      {error && <p role="alert">{errors[error]}</p>}
    </section>
  );
}
