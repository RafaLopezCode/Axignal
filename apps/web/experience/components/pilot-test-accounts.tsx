"use client";
import { useEffect, useState } from "react";
import { useLocale } from "@/lib/locale";
import { pilotAccountsSnapshot, type PilotAccountsSnapshot } from "@/lib/pilot-test-accounts";

export function PilotTestAccounts() {
  const { t } = useLocale();
  const [accounts, setAccounts] = useState({ a: "", b: "" });
  const [saved, setSaved] = useState<PilotAccountsSnapshot | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  async function load() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/admin/pilot-test-accounts", { cache: "no-store" });
      if (!response.ok) throw new Error("LOAD_FAILED");
      const result = pilotAccountsSnapshot.parse(await response.json());
      setAccounts({ a: result.a, b: result.b }); setSaved(result);
    } catch { setError("LOAD_FAILED"); }
    finally { setLoading(false); setBusy(false); }
  }
  useEffect(() => { void load(); }, []);
  const dirty = saved !== null && (accounts.a !== saved.a || accounts.b !== saved.b);
  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!saved || busy) return;
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/admin/pilot-test-accounts", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ a: accounts.a.trim(), b: accounts.b.trim(), expectedRevision: saved.revision }),
      });
      if (!response.ok) throw new Error(response.status === 409 ? "REVISION_CONFLICT" : "SAVE_FAILED");
      const result = pilotAccountsSnapshot.parse(await response.json());
      setSaved(result); setAccounts({ a: result.a, b: result.b });
    } catch (failure) { setError(failure instanceof Error ? failure.message : "SAVE_FAILED"); }
    finally { setBusy(false); }
  }
  return (
    <section className="admin-attention admin-pilot-accounts" aria-labelledby="pilot-accounts-title">
      <h2 id="pilot-accounts-title">{t("Cuentas para la prueba del piloto", "Pilot test accounts")}</h2>
      <p>{t("AXIGNAL · https://axignal.com/ · 1 organización, sin pagos.", "AXIGNAL · https://axignal.com/ · 1 organization, no payments.")}</p>
      <p id="pilot-accounts-help">{t("Guarda las dos cuentas Google para autorizar la prueba del piloto. Puedes cambiarlas y guardar de nuevo. El acceso requiere Google verificado y una invitación de un solo uso.", "Save both Google accounts to authorize the pilot test. You can change them and save again. Access requires verified Google sign-in and a single-use invitation.")}</p>
      <form onSubmit={save} aria-describedby="pilot-accounts-help">
        <div className="admin-table-toolbar">
          {(["a", "b"] as const).map(account => (
            <label className="search-field" key={account}>
              <span>{t("Cuenta Google", "Google account")} {account.toUpperCase()}</span>
              <input type="email" autoComplete="off" maxLength={254} value={accounts[account]} disabled={busy}
                onChange={event => setAccounts(previous => ({ ...previous, [account]: event.target.value }))}
                aria-label={t("Cuenta Google", "Google account") + " " + account.toUpperCase()} />
            </label>
          ))}
        </div>
        <div className="admin-table-toolbar">
          <button type="submit" className="button primary" disabled={busy || !saved || !dirty}>
            {busy && !loading ? t("Guardando…", "Saving…") : t("Guardar cuentas", "Save accounts")}
          </button>
          <button type="button" className="button secondary" disabled={busy || !saved} onClick={() => setAccounts({ a: "", b: "" })}>
            {t("Vaciar cuentas", "Clear accounts")}
          </button>
        </div>
      </form>
      <p role="status" aria-live="polite">
        {loading ? t("Cargando cuentas…", "Loading accounts…") : dirty ? t("Cambios sin guardar.", "Unsaved changes.") : saved?.authorizedForTest ? t("Las dos cuentas están guardadas y autorizadas para la prueba.", "Both accounts are saved and authorized for the test.") : t("La prueba espera a que guardes dos cuentas distintas.", "The test awaits two distinct saved accounts.")}
        {saved?.savedAt && <> {t("Último guardado:", "Last saved:")} <time dateTime={saved.savedAt}>{new Date(saved.savedAt).toLocaleString()}</time></>}
      </p>
      {error && <div role="alert">
        <p>{error === "REVISION_CONFLICT" ? t("Las cuentas han cambiado en otra sesión. Tus cambios siguen aquí; recarga las cuentas guardadas antes de volver a guardar.", "The accounts changed in another session. Your draft remains here; reload saved accounts before saving again.") : error === "LOAD_FAILED" ? t("No se pudieron cargar las cuentas. Necesitas una sesión Admin autorizada. Reintenta cuando esté disponible.", "Accounts could not be loaded. An authorized Admin session is required. Retry when available.") : t("No se guardaron las cuentas. Revisa que sean dos correos distintos o déjalos vacíos; puedes reintentar.", "Accounts were not saved. Use two distinct addresses or leave them blank; you can retry.")}</p>
        <button type="button" className="button secondary" disabled={busy} onClick={() => void load()}>
          {t("Recargar cuentas guardadas", "Reload saved accounts")}
        </button>
      </div>}
    </section>
  );
}
