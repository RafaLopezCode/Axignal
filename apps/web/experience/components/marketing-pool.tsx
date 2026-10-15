"use client";
import { useEffect, useMemo, useState } from "react";
import { useLocale } from "@/lib/locale";
import { text } from "@/lib/admin-presentation";
import { poolSnapshot, type PoolCampaign, type PoolProspect, type PoolSnapshot } from "@/lib/marketing-pool";

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
  const [origin, setOrigin] = useState("ALL");
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
  const post = (body: object) => run(() => call({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }));
  const decide = (domain: string, action: "APPROVE" | "DISCARD" | "SUPPRESS") => post({ domain, action });
  const prospects = useMemo(() => data && data.enabled ? data.prospects.filter(p => VIEWS[view].includes(p.state)
    && (origin === "ALL" || (origin === "AUTO" ? !p.campaign : p.campaign === origin))) : [], [data, view, origin]);
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
    <p>{text("poolDisabled", locale)}</p>
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
    {data && data.enabled && <Campaigns data={data} busy={busy} onPost={post} />}
    {data && data.enabled && data.campaigns.length > 0 && <label className="search-field pool-origin">
      <span>{t("Origen", "Origin")}</span>
      <select value={origin} onChange={e => { setOrigin(e.target.value); setSelected(null); }}>
        <option value="ALL">{t("Todo el pool", "Whole pool")}</option>
        <option value="AUTO">{t("Automático", "Automatic")}</option>
        {data.campaigns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
    </label>}
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

/** Automatic mode, or a directed campaign that takes the daily budget until it ends. */
function Campaigns({ data, busy, onPost }: {
  data: Extract<PoolSnapshot, { enabled: true }>; busy: boolean; onPost: (body: object) => void;
}) {
  const { t, locale } = useLocale();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [personas, setPersonas] = useState<string[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [target, setTarget] = useState(30);
  const [endsOn, setEndsOn] = useState("");
  const active = data.campaigns.filter(c => c.state === "ACTIVE");
  const held = countries.filter(iso => data.markets.find(m => m.iso === iso)?.channel !== "EMAIL");
  const toggle = (list: string[], value: string) => list.includes(value) ? list.filter(x => x !== value) : [...list, value];
  const state = (c: PoolCampaign) => ({
    ACTIVE: t("Activa", "Active"), COMPLETED: t("Completada", "Completed"), ENDED: t("Fecha de fin alcanzada", "End date reached"),
    EXHAUSTED: t("Sin más candidatas en las fuentes", "No more candidates in the sources"), CANCELLED: t("Cancelada", "Cancelled"),
  }[c.state]);
  const valid = name.trim() && personas.length && countries.length && target >= 1 && target <= 500;
  return <div className="pool-campaigns">
    <p className="pool-mode" data-mode={active.length ? "campaign" : "auto"}>
      {active.length
        ? t("Modo campaña: el presupuesto diario va a {name}. Al terminar, el motor vuelve solo al modo automático.", "Campaign mode: the daily budget goes to {name}. When it ends, the engine returns to automatic mode by itself.").replace("{name}", active[0].name)
        : t("Modo automático: el motor elige las organizaciones más prometedoras, primero donde se puede enviar y según lo que mejor ha cualificado hasta ahora.", "Automatic mode: the engine picks the most promising organizations, first where sending is allowed and by what has qualified best so far.")}
    </p>
    {data.campaigns.length > 0 && <ul className="pool-campaign-list">
      {data.campaigns.map(c => <li key={c.id} data-state={c.state}>
        <div>
          <strong>{c.name}</strong> · {state(c)}
          <span>{c.countries.join(", ")} · {c.personas.map(id => data.personas.find(p => p.id === id)?.label ?? id).join(", ")}{c.endsAt ? " · " + t("hasta", "until") + " " + new Date(c.endsAt).toLocaleDateString(locale) : ""} · {c.createdBy}</span>
        </div>
        <span className="pool-bar" role="progressbar" aria-label={t("Estudiadas", "Studied")} aria-valuemin={0} aria-valuemax={c.target} aria-valuenow={Math.min(c.progress.studied, c.target)}><span style={{ width: `${Math.min(100, Math.round(100 * c.progress.studied / Math.max(1, c.target)))}%` }} /></span>
        <span className="pool-campaign-numbers">
          {t("{s} de {n} estudiadas", "{s} of {n} studied").replace("{s}", String(c.progress.studied)).replace("{n}", String(c.target))}
          {" · "}{c.progress.qualified} {t("cualificadas", "qualified")} · {c.progress.drafted} {t("por revisar", "to review")} · {c.progress.sent} {t("enviadas", "sent")} · {c.progress.held} {t("retenidas", "held")} · {c.progress.optedOut} {t("bajas", "opt-outs")}
        </span>
        {c.state === "ACTIVE" && <button className="button secondary" disabled={busy} onClick={() => onPost({ action: "CANCEL_CAMPAIGN", campaign: c.id })}>{t("Cancelar campaña", "Cancel campaign")}</button>}
      </li>)}
    </ul>}
    {!open && <button className="button primary" onClick={() => setOpen(true)}>{t("Nueva campaña", "New campaign")}</button>}
    {open && <form className="pool-campaign-form" onSubmit={e => {
      e.preventDefault(); if (!valid || busy) return;
      onPost({ action: "CREATE_CAMPAIGN", name: name.trim(), personas, countries, target, endsOn: endsOn || null });
      setOpen(false); setName(""); setPersonas([]); setCountries([]); setEndsOn("");
    }}>
      <label className="search-field"><span>{t("Nombre", "Name")}</span>
        <input value={name} maxLength={80} onChange={e => setName(e.target.value)} placeholder={t("p. ej. Agencias SEO Canadá", "e.g. SEO agencies Canada")} /></label>
      <fieldset><legend>{t("A quién", "Who")}</legend>
        {data.personas.map(p => <label key={p.id} className="pool-check"><input type="checkbox" checked={personas.includes(p.id)} onChange={() => setPersonas(toggle(personas, p.id))} />{p.label}</label>)}
      </fieldset>
      <fieldset><legend>{t("Dónde", "Where")}</legend>
        <div className="pool-countries">{data.markets.map(m => <label key={m.iso} className="pool-check" data-channel={m.channel}>
          <input type="checkbox" checked={countries.includes(m.iso)} onChange={() => setCountries(toggle(countries, m.iso))} />{m.iso}{m.channel !== "EMAIL" ? " · " + t("retener", "hold") : ""}
        </label>)}</div>
      </fieldset>
      {held.length > 0 && <p className="pool-reason">{t("En {list} se estudian y se redactan, pero no se envían por correo: allí exige consentimiento previo o no está revisado.", "In {list} they are studied and drafted but not emailed: prior consent is required there or it is not reviewed.").replace("{list}", held.join(", "))}</p>}
      <div className="admin-table-toolbar">
        <label className="search-field"><span>{t("Organizaciones a estudiar", "Organizations to study")}</span>
          <input type="number" min={1} max={500} value={target} onChange={e => setTarget(Number(e.target.value))} /></label>
        <label className="search-field"><span>{t("Hasta (opcional)", "Until (optional)")}</span>
          <input type="date" value={endsOn} onChange={e => setEndsOn(e.target.value)} /></label>
      </div>
      <p>{t("Al ritmo de {n} estudios al día. No todas cualificarán, y ningún correo sale sin tu aprobación.", "At {n} studies a day. Not all will qualify, and no email leaves without your approval.").replace("{n}", String(data.limits.studiesPerDay))}</p>
      <div className="admin-table-toolbar">
        <button type="submit" className="button primary" disabled={!valid || busy}>{t("Lanzar campaña", "Launch campaign")}</button>
        <button type="button" className="button secondary" onClick={() => setOpen(false)}>{t("Cancelar", "Cancel")}</button>
      </div>
    </form>}
  </div>;
}
