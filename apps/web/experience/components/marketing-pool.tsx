"use client";
import { useEffect, useMemo, useState } from "react";
import { useLocale } from "@/lib/locale";
import { poolSnapshot, type PoolProspect, type PoolSnapshot } from "@/lib/marketing-pool";

type View = "review" | "approved" | "sent" | "held" | "studying" | "closed";
const VIEWS: Record<View, readonly string[]> = {
  review: ["DRAFTED"], approved: ["APPROVED"], sent: ["SENT", "SEND_FAILED"], held: ["HELD"],
  studying: ["STUDYING", "DISCOVERED"], closed: ["NOT_QUALIFIED", "STUDY_FAILED", "DISCARDED", "SUPPRESSED"],
};

/** AXIGNAL's own marketing pool: the agent finds and studies; a person approves every email. */
export function MarketingPool() {
  const { t, locale } = useLocale();
  const [data, setData] = useState<PoolSnapshot | null>(null);
  const [view, setView] = useState<View>("review");
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const failure = (code: unknown) => {
    if (code === "ADMIN_SESSION_REQUIRED") return t("Necesitas una sesión Admin activa.", "An active Admin session is required.");
    if (code === "ADMIN_SCOPE_REQUIRED") return t("Tu rol debe permitir gestionar adquisición.", "Your role must allow managing acquisition.");
    if (code === "STATE_CHANGED") return t("Su estado cambió mientras lo revisabas. Actualiza y vuelve a decidir.", "Its state changed while you reviewed it. Refresh and decide again.");
    return t("No se pudo completar. Actualiza el estado y reintenta.", "Could not complete. Refresh the state and retry.");
  };
  async function call(init?: RequestInit) {
    const response = await fetch("/api/admin/marketing-pool", { cache: "no-store", ...init });
    const raw = await response.json();
    if (!response.ok) throw new Error(failure(raw?.reason));
    setData(poolSnapshot.parse(raw));
  }
  async function run(work: () => Promise<void>) {
    if (busy) return; setBusy(true); setError(null);
    try { await work(); } catch (e) { setError(e instanceof Error ? e.message : failure(null)); }
    finally { setBusy(false); }
  }
  useEffect(() => { void run(() => call()); }, []);
  const decide = (domain: string, action: "APPROVE" | "DISCARD" | "SUPPRESS") =>
    run(() => call({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ domain, action }) }));
  const prospects = useMemo(() => data && data.enabled ? data.prospects.filter(p => VIEWS[view].includes(p.state)) : [], [data, view]);
  const current = prospects.find(p => p.domain === selected) ?? prospects[0] ?? null;
  const count = (states: readonly string[]) => data && data.enabled ? states.reduce((n, s) => n + (data.counts[s] ?? 0), 0) : 0;
  const tabs: [View, string][] = [
    ["review", t("Por revisar", "To review")], ["approved", t("Aprobados", "Approved")],
    ["sent", t("Enviados", "Sent")], ["held", t("Retenidos", "Held")],
    ["studying", t("Estudiando", "Studying")], ["closed", t("Cerrados", "Closed")],
  ];
  const reason = (code: string | null) => ({
    CHANNEL_POLICY_HOLD: t("Su país exige consentimiento previo o no está revisado: no se envía por correo.", "Its country requires prior consent or is not reviewed: not sent by email."),
    NO_ROLE_ADDRESS: t("Su web no publica una dirección genérica de contacto.", "Its website publishes no generic contact address."),
    NOT_A_TARGET_PERSONA: t("Su web no muestra que sea agencia o consultora de nuestro perfil.", "Its website does not show it is an agency or consultancy we serve."),
    TOO_FEW_EVIDENCED_FINDINGS: t("Pocos hallazgos con evidencia: el correo no sería específico.", "Too few evidenced findings: the email would not be specific."),
    TOO_FEW_FAMILIES: t("Hallazgos en muy pocas familias: el correo no sería específico.", "Findings in too few families: the email would not be specific."),
    DRAFT_NOT_GROUNDED: t("El borrador no citaba los hallazgos: descartado.", "The draft did not cite the findings: discarded."),
    RECIPIENT_OPT_OUT: t("Pidió no recibir más correos.", "Asked to receive no more emails."),
    STAFF_DECISION: t("Excluida por el equipo.", "Excluded by staff."),
  } as Record<string, string>)[code ?? ""] ?? code;
  if (data && !data.enabled) return <section className="admin-attention" aria-labelledby="pool-title">
    <h2 id="pool-title">{t("Pool de marketing", "Marketing pool")}</h2>
    <p>{t("Desactivado en este entorno. Se activa con AXIGNAL_MARKETING_POOL_ENABLED=true en la configuración del runtime.", "Disabled in this environment. Enable it with AXIGNAL_MARKETING_POOL_ENABLED=true in the runtime configuration.")}</p>
  </section>;
  return <section className="admin-attention pool" aria-labelledby="pool-title">
    <h2 id="pool-title">{t("Pool de marketing", "Marketing pool")}</h2>
    <p>{t("El agente busca agencias y consultoras en registros abiertos de todo el mundo, las estudia con AXIGNAL una sola vez y redacta un correo en su idioma solo con hallazgos que tienen evidencia. Nada se envía sin tu aprobación.", "The agent finds agencies and consultancies in open registries worldwide, studies each once with AXIGNAL and drafts an email in its language using only evidenced findings. Nothing is sent without your approval.")}</p>
    {data && data.enabled && <p className="pool-status">
      <span data-on={Boolean(data.sending)}>{data.sending ? t("Envío desde {from}", "Sending from {from}").replace("{from}", data.sending) : t("Envío apagado: falta configurar el buzón", "Sending off: mailbox not configured")}</span>
      <span data-on={data.drafting}>{data.drafting ? t("Redacción activa", "Drafting on") : t("Redacción apagada: falta el asistente", "Drafting off: assistant not configured")}</span>
      <span>{t("{n} estudios/día · {m} envíos/día", "{n} studies/day · {m} sends/day").replace("{n}", String(data.limits.studiesPerDay)).replace("{m}", String(data.limits.sendsPerDay))}</span>
      <span>{t("No volver a contactar", "Do not contact")}: {data.counts.SUPPRESSION_LIST ?? 0}</span>
    </p>}
    <nav className="customer-access-tabs" aria-label={t("Estados del pool", "Pool states")}>
      {tabs.map(([id, label]) => <button key={id} className="button secondary" aria-pressed={view === id} onClick={() => { setView(id); setSelected(null); }}>{label} · {count(VIEWS[id])}</button>)}
      <button className="button secondary" disabled={busy} onClick={() => void run(() => call())}>{t("Actualizar", "Refresh")}</button>
    </nav>
    {error && <p role="alert">{error}</p>}
    {!data && !error && <p role="status">{t("Cargando…", "Loading…")}</p>}
    {data && data.enabled && prospects.length === 0 && <p role="status">{t("Nada en este estado.", "Nothing in this state.")}</p>}
    {current && <div className="pool-grid">
      <ul className="pool-list" aria-label={t("Organizaciones", "Organizations")}>
        {prospects.map(p => <li key={p.domain}>
          <button type="button" aria-current={p.domain === current.domain} onClick={() => setSelected(p.domain)}>
            <strong>{p.name}</strong>
            <span>{p.domain} · {p.country}{p.persona ? " · " + p.persona : ""}</span>
          </button>
        </li>)}
      </ul>
      <Detail prospect={current} busy={busy} reason={reason} locale={locale} onDecide={decide} />
    </div>}
    {data && data.enabled && <details className="pool-policy">
      <summary>{t("Política de canal por país", "Channel policy by country")} · {data.versions.channelPolicy}</summary>
      <p>{t("Conservadora y revisable: no es asesoramiento legal. Donde el correo exige consentimiento previo, el estudio se guarda y no se envía.", "Conservative and reviewable: not legal advice. Where email requires prior consent, the study is kept and nothing is sent.")}</p>
      <ul>{data.markets.map(m => <li key={m.iso}><strong>{m.iso}</strong> · {m.channel === "EMAIL" ? t("Correo", "Email") : t("Retener", "Hold")} · {m.basis}</li>)}</ul>
    </details>}
  </section>;
}

function Detail({ prospect, busy, reason, locale, onDecide }: {
  prospect: PoolProspect; busy: boolean; locale: string;
  reason: (code: string | null) => string | null;
  onDecide: (domain: string, action: "APPROVE" | "DISCARD" | "SUPPRESS") => void;
}) {
  const { t } = useLocale();
  const subject = typeof prospect.draft?.subject === "string" ? prospect.draft.subject : null;
  return <article className="pool-detail" aria-labelledby="pool-detail-title">
    <header>
      <h3 id="pool-detail-title">{prospect.name}</h3>
      <p><a className="text-link" href={prospect.website} target="_blank" rel="noreferrer noopener">{prospect.domain}</a> · {prospect.country} · {prospect.source}{prospect.persona ? " · " + prospect.persona : ""}</p>
      {prospect.reason && <p className="pool-reason">{reason(prospect.reason)}</p>}
      {prospect.recipient && <p>{t("Para", "To")}: <strong>{prospect.recipient}</strong>{prospect.language ? " · " + prospect.language.toUpperCase() : ""}{prospect.sentAt ? " · " + t("enviado", "sent") + " " + new Date(prospect.sentAt).toLocaleString(locale) : ""}</p>}
    </header>
    {prospect.state === "DRAFTED" && <div className="admin-table-toolbar">
      <button className="button primary" disabled={busy} onClick={() => onDecide(prospect.domain, "APPROVE")}>{t("Aprobar envío", "Approve sending")}</button>
      <button className="button secondary" disabled={busy} onClick={() => onDecide(prospect.domain, "DISCARD")}>{t("Descartar", "Discard")}</button>
      <button className="button secondary" disabled={busy} onClick={() => onDecide(prospect.domain, "SUPPRESS")}>{t("No contactar nunca", "Never contact")}</button>
    </div>}
    {["HELD", "APPROVED", "NOT_QUALIFIED", "STUDY_FAILED"].includes(prospect.state) && <div className="admin-table-toolbar">
      <button className="button secondary" disabled={busy} onClick={() => onDecide(prospect.domain, "DISCARD")}>{t("Descartar", "Discard")}</button>
    </div>}
    {prospect.html
      ? <iframe className="pool-preview" title={subject ?? t("Vista previa del correo", "Email preview")} sandbox="" srcDoc={prospect.html} />
      : null}
    {prospect.findings.length > 0 && <>
      <h4>{t("Hallazgos con evidencia", "Evidenced findings")} · {prospect.families.length} {t("familias", "families")}</h4>
      <ul className="pool-findings">{prospect.findings.map(f => <li key={f.kind + f.code} data-state={f.state}>
        <span>{f.family}</span> {f.statement} {f.source && <a className="text-link" href={f.source} target="_blank" rel="noreferrer noopener">{t("fuente", "source")}</a>}
      </li>)}</ul>
    </>}
  </article>;
}
