"use client";
/**
 * Visibilidad as a full canvas (family workspace design base, phase 2). Four panels read the
 * stored measurements as they are: AI answers (presence, share of voice, position, who is
 * named instead, sources cited), search engines (each search, its position, a link to see it
 * on Google), its own website (the audit by section) and its reach (languages and country
 * versions). Every panel states its epistemic state in words and opens its proof; a panel
 * with nothing measured says so, never zero. Nothing is scored.
 */
import type { ReactNode } from "react";
import { ExternalLink } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { familyRank, fill, natureLabel, type Insight, type Nature, type Reading, type Translate } from "@/lib/observatory";
import type { FamilyId } from "@/lib/projection";
import { auditSection, auditStatus } from "@/lib/representation-audit";
import type { Discovery } from "@/lib/subscriber-contracts";
import { placeLabel } from "./first-observation";
import { NatureMark } from "./nature-mark";

type Row = [string, number];
const SECTIONS = ["SEARCH_FINDABILITY", "AI_ANSWER_READINESS", "SHARING_AND_MOBILE", "REAL_USER_EXPERIENCE"];
const STATUSES = ["PASS", "ATTENTION", "UNKNOWN"] as const;

function rows(value: unknown): Row[] {
  return Array.isArray(value)
    ? value.filter((r): r is [unknown, unknown] => Array.isArray(r) && r.length >= 2).map(r => [String(r[0]), Number(r[1]) || 0] as Row)
    : [];
}

function nature(d: Discovery): Nature {
  return d.epistemicState === "OBSERVED" ? "OBSERVED" : d.epistemicState === "DECLARED" ? "DECLARED"
    : d.epistemicState === "POTENTIAL" ? "POTENTIAL" : "UNKNOWN";
}

function Panel({ title, state, conditions, proof, onOpen, children, index }: {
  title: string; state: Nature; conditions?: string | null; proof?: Insight | null; onOpen: (insight: Insight) => void; children: ReactNode; index: number;
}) {
  const { t } = useLocale();
  return <section className="obs-canvas-panel" style={{ ["--i" as string]: index }} aria-label={title}>
    <header>
      <h3>{title}</h3>
      <NatureMark nature={state} label={natureLabel(state, t)}/>
    </header>
    {children}
    <footer>
      {conditions && <p className="obs-canvas-conditions">{conditions}</p>}
      {proof && <button className="obs-link" onClick={() => onOpen(proof)}>{t("Cómo lo sabe AXIGNAL", "Show me how AXIGNAL knows")}</button>}
    </footer>
  </section>;
}

function Ring({ share, label }: { share: number; label: string }) {
  const radius = 52;
  const length = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(1, share));
  return <svg className="obs-ring" viewBox="0 0 128 128" role="img" aria-label={label}>
    <circle cx="64" cy="64" r={radius} className="obs-ring-track"/>
    <circle cx="64" cy="64" r={radius} className="obs-ring-value" strokeDasharray={length.toFixed(1)}
      style={{ ["--ring-length" as string]: length.toFixed(1), ["--ring-to" as string]: (length * (1 - clamped)).toFixed(1) }}
      strokeDashoffset={(length * (1 - clamped)).toFixed(1)} transform="rotate(-90 64 64)"/>
    <text x="64" y="70" textAnchor="middle" className="obs-ring-text">{Math.round(clamped * 100)}%</text>
  </svg>;
}

function Bars({ items, highlight }: { items: Row[]; highlight?: string }) {
  const top = Math.max(1, ...items.map(([, n]) => n));
  return <ol className="obs-bars">{items.map(([name, n], index) => <li key={name} className={name === highlight ? "obs-bar-own" : undefined} style={{ ["--i" as string]: index }}>
    <span className="obs-bar-name">{name}</span>
    <span className="obs-bar-track" aria-hidden="true"><span style={{ inlineSize: `${(n / top) * 100}%` }}/></span>
    <span className="obs-bar-value">{n}</span>
  </li>)}</ol>;
}

function conditionsOf(d: Discovery | undefined, t: Translate): string | null {
  if (!d) return null;
  const detail = d.detail as Record<string, unknown>;
  const instrument = detail.instrument && typeof detail.instrument === "object" ? (detail.instrument as Record<string, unknown>) : null;
  const parts = [
    typeof detail.sample === "string" ? detail.sample : null,
    instrument && typeof instrument.model === "string" ? instrument.model : instrument && typeof instrument.name === "string" ? instrument.name : typeof detail.instrument === "string" ? detail.instrument : null,
    typeof detail.measuredAt === "string" ? fill(t("medido el {d}", "measured on {d}"), { d: detail.measuredAt.slice(0, 10) }) : d.observedAt ? fill(t("observado el {d}", "observed on {d}"), { d: d.observedAt.slice(0, 10) }) : null,
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}

export function VisibilityCanvas({ reading, insights, onOpen }: {
  reading: Reading; insights: Insight[]; onOpen: (insight: Insight) => void;
}) {
  const { t, locale } = useLocale();
  const ds = reading.firstObservation?.discoveries ?? [];
  const proofOf = (d: Discovery | undefined): Insight | null => {
    if (!d) return null;
    const id = `${d.kind}:${d.code}:${ds.indexOf(d)}`;
    return insights.find(i => i.id === id) ?? insights.find(i => i.id.startsWith(`${d.kind}:`)) ?? null;
  };
  // A finding in the reader's words: its insight's headline, never the raw statement.
  const said = (d: Discovery) => proofOf(d)?.headline ?? d.statement;
  const find = (kind: string, ...codes: string[]) => ds.find(d => d.kind === kind && (!codes.length || codes.includes(d.code)));

  // AI answers.
  const geo = find("GENERATIVE_VISIBILITY", "AI_NAMED_FOR_CATEGORY", "AI_NOT_NAMED_FOR_CATEGORY");
  const geoLegacy = geo ? undefined : find("GENERATIVE_VISIBILITY");
  const brand = find("GENERATIVE_VISIBILITY", "AI_KNOWS_BRAND", "AI_DOES_NOT_KNOW_BRAND");
  const cited = find("GENERATIVE_VISIBILITY", "AI_CITED_SOURCES");
  const geoDetail = (geo?.detail ?? {}) as Record<string, unknown>;
  const [named, asked] = (geo?.statement ?? "").split("/").map(Number);
  const share = typeof geoDetail.shareOfVoice === "number" ? geoDetail.shareOfVoice : asked ? named / asked : null;
  const rivals = rows(geoDetail.competitorFrequency).slice(0, 5);
  const sites = rows((cited?.detail as Record<string, unknown> | undefined)?.sitesCited).slice(0, 5);

  // Search engines.
  const rank = find("SEARCH_VISIBILITY", "SEARCH_RANKS_MEASURED", "SEARCH_NOT_RANKED");
  const searchLegacy = rank ? [] : ds.filter(d => d.kind === "SEARCH_VISIBILITY");
  const searches = Array.isArray((rank?.detail as Record<string, unknown> | undefined)?.rows)
    ? ((rank!.detail as Record<string, unknown>).rows as Array<Record<string, unknown>>) : [];

  // Its own website.
  const web = find("WEB_REPRESENTATION");
  const audit = (web?.detail as Record<string, unknown> | undefined)?.audit as { checks?: Array<{ section: string; status: string }> } | undefined;
  const checks = Array.isArray(audit?.checks) ? audit!.checks : [];
  const gaps = ds.filter(d => d.kind === "REPRESENTATION_GAP");

  // Reach.
  const languages = find("LANGUAGES");
  const versions = find("DECLARED_SERVICE_AREA", "SITE_VERSIONS_FOR_COUNTRIES");
  const countries = Object.keys(((versions?.detail as Record<string, unknown> | undefined)?.countries ?? {}) as Record<string, unknown>);
  const langs = Array.isArray((languages?.detail as Record<string, unknown> | undefined)?.languages) ? ((languages!.detail as Record<string, unknown>).languages as unknown[]).map(String) : [];

  let index = 0;
  return <div className="obs-canvas" aria-label={t("Visibilidad a fondo", "Visibilidad in depth")}>
    <Panel index={index++} title={t("Respuestas de asistentes de IA", "AI assistant answers")} state={geo ? nature(geo) : geoLegacy ? nature(geoLegacy) : "UNKNOWN"}
      conditions={conditionsOf(geo ?? geoLegacy, t)} proof={proofOf(geo ?? geoLegacy)} onOpen={onOpen}>
      {geo && share !== null ? <div className="obs-canvas-ai">
        <Ring share={share} label={fill(t("Cuota de voz: {p} % de las organizaciones nombradas", "Share of voice: {p}% of the organizations named"), { p: Math.round(share * 100) })}/>
        <dl className="obs-canvas-facts">
          <div><dt>{t("Cuota de voz", "Share of voice")}</dt><dd>{t("de las organizaciones que nombra la IA", "of the organizations the AI names")}</dd></div>
          {asked > 0 && <div><dt>{fill(t("{n} de {m}", "{n} of {m}"), { n: named, m: asked })}</dt><dd>{t("respuestas sobre su actividad la nombran", "answers about its activity name it")}</dd></div>}
          {typeof geoDetail.averagePosition === "number" && <div><dt>{geoDetail.averagePosition.toLocaleString(locale)}</dt><dd>{t("posición media cuando la nombra", "average position when named")}</dd></div>}
          {brand && <div><dt>{brand.code === "AI_KNOWS_BRAND" ? t("Sí", "Yes") : t("No", "No")}</dt><dd>{t("la IA conoce la marca", "the AI knows the brand")}</dd></div>}
        </dl>
      </div> : geoLegacy ? <p className="obs-canvas-statement">{said(geoLegacy)}</p>
        : <p className="obs-canvas-empty">{t("Aún sin medir. Se mide sola, con preguntas fijas sobre su actividad, y aparecerá aquí con sus condiciones.", "Not measured yet. It is measured on its own, with fixed questions about its activity, and will appear here with its conditions.")}</p>}
      {rivals.length > 0 && <><h4>{t("A quién nombra la IA en su lugar", "Who the AI names instead")}</h4><Bars items={rivals}/></>}
      {sites.length > 0 && <><h4>{t("Webs que cita al responder", "Websites it cites when answering")}</h4><Bars items={sites}/></>}
    </Panel>

    <Panel index={index++} title={t("Buscadores", "Search engines")} state={rank ? nature(rank) : searchLegacy[0] ? nature(searchLegacy[0]) : "UNKNOWN"}
      conditions={conditionsOf(rank ?? searchLegacy[0], t)} proof={proofOf(rank ?? searchLegacy[0])} onOpen={onOpen}>
      {searches.length > 0 ? <ul className="obs-canvas-searches">{searches.map(row => <li key={String(row.keyword)}>
        <span className="obs-search-keyword">«{String(row.keyword)}»</span>
        <span className="obs-search-position">{typeof row.position === "number" ? fill(t("posición {n}", "position {n}"), { n: row.position }) : t("no aparece en los 20 primeros", "not in the top 20")}</span>
        {typeof row.googleUrl === "string" && row.googleUrl.startsWith("https://www.google.com/search?") && <a href={row.googleUrl} target="_blank" rel="noopener noreferrer">{t("Ver esta búsqueda en Google", "See this search on Google")}<ExternalLink size={13} aria-hidden="true"/><span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a>}
      </li>)}</ul> : searchLegacy.length ? <ul className="obs-canvas-list">{searchLegacy.map((d, i) => <li key={i}>{said(d)}</li>)}</ul>
        : <p className="obs-canvas-empty">{t("Aún sin medir. Cuando se active, mostrará su posición en las búsquedas de su actividad y quién aparece antes.", "Not measured yet. Once enabled, it will show its position in the searches for its activity and who appears first.")}</p>}
    </Panel>

    <Panel index={index++} title={t("Su propia web", "Its own website")} state={web ? nature(web) : "UNKNOWN"}
      conditions={conditionsOf(web, t)} proof={proofOf(web)} onOpen={onOpen}>
      {checks.length > 0 ? <ul className="obs-canvas-audit">{SECTIONS.filter(s => checks.some(c => c.section === s)).map(section => {
        const inSection = checks.filter(c => c.section === section);
        return <li key={section}>
          <span className="obs-audit-section">{auditSection(section, t)}</span>
          <span className="obs-audit-stack" role="img" aria-label={STATUSES.map(s => `${auditStatus(s, t)}: ${inSection.filter(c => c.status === s).length}`).join(", ")}>
            {STATUSES.map(s => { const n = inSection.filter(c => c.status === s).length; return n ? <span key={s} className={`obs-audit-${s.toLowerCase()}`} style={{ flexGrow: n }}/> : null; })}
          </span>
          <span className="obs-audit-counts">{STATUSES.map(s => `${inSection.filter(c => c.status === s).length} ${auditStatus(s, t).toLocaleLowerCase(locale)}`).join(" · ")}</span>
        </li>;
      })}</ul> : web ? <p className="obs-canvas-statement">{t("Su web se ha leído; el detalle de lo que comunica está en «Cómo se entiende».", "Its website was read; the detail of what it conveys is under “How it is understood”.")}</p>
        : <p className="obs-canvas-empty">{t("Su web aún no se ha podido leer.", "Its website could not be read yet.")}</p>}
      {gaps.length > 0 && <p className="obs-canvas-note">{fill(gaps.length === 1 ? t("{n} punto conviene aclararlo: está en «Cómo se entiende».", "{n} point is worth clarifying: see “How it is understood”.") : t("{n} puntos conviene aclararlos: están en «Cómo se entiende».", "{n} points are worth clarifying: see “How it is understood”."), { n: gaps.length })}</p>}
    </Panel>

    <Panel index={index++} title={t("Idiomas y países a los que se dirige", "Languages and countries it addresses")} state={versions ? nature(versions) : languages ? nature(languages) : "UNKNOWN"}
      conditions={conditionsOf(versions ?? languages, t)} proof={proofOf(versions ?? languages)} onOpen={onOpen}>
      {langs.length > 0 || countries.length > 0 ? <div className="obs-canvas-reach">
        {langs.length > 0 && <p><strong>{t("Idiomas", "Languages")}</strong> {langs.join(", ")}</p>}
        {countries.length > 0 && <p><strong>{t("Versiones para", "Versions for")}</strong> {countries.map(c => placeLabel(c, locale)).join(", ")}</p>}
      </div> : <p className="obs-canvas-empty">{t("Su web no declara idiomas ni versiones por país.", "Its website declares no languages or country versions.")}</p>}
    </Panel>
  </div>;
}

const NATURES: Nature[] = ["OBSERVED", "DECLARED", "POTENTIAL", "UNKNOWN"];
const MONTHS = 12;

/**
 * Any other family as a full canvas (design base, phase 3): what has been observed by state,
 * the most telling findings, when they were observed and where they come from. Each panel
 * opens its proof; counts are real counts of stored findings, never a score; a panel with
 * nothing says so. Family-specific panels can replace these one by one.
 */
export function FamilyCanvas({ family, title, insights, onOpen }: {
  family: FamilyId; title: string; insights: Insight[]; onOpen: (insight: Insight) => void;
}) {
  const { t, locale } = useLocale();
  const own = insights.filter(i => i.family === family && i.group !== "otherDemand");
  if (!own.length) return null;
  const known = own.filter(i => i.nature !== "UNKNOWN" && i.nature !== "UNRESOLVED");
  // Fewer than two known findings: the lanes already say what is (not) known; a canvas of
  // near-empty panels would only add noise.
  if (known.length < 2) return null;
  const top = [...known].sort((a, b) => familyRank(family, a.id) - familyRank(family, b.id)
    || Number(b.lane === "matters") - Number(a.lane === "matters")
    || Date.parse(b.observedAt ?? "") - Date.parse(a.observedAt ?? "") || 0).slice(0, 3);
  const byNature = NATURES.map(n => [n, own.filter(i => (i.nature === "UNRESOLVED" ? "UNKNOWN" : i.nature) === n).length] as const).filter(([, c]) => c > 0);
  // When: the month of each dated finding, over the last twelve months.
  const now = new Date();
  const months = Array.from({ length: MONTHS }, (_, k) => new Date(now.getFullYear(), now.getMonth() - (MONTHS - 1 - k), 1));
  const dated = own.filter(i => i.observedAt && !Number.isNaN(Date.parse(i.observedAt)));
  const perMonth = months.map(m => dated.filter(i => { const d = new Date(i.observedAt!); return d.getFullYear() === m.getFullYear() && d.getMonth() === m.getMonth(); }).length);
  const olderThanWindow = dated.filter(i => new Date(i.observedAt!) < months[0]).length;
  // Where from: the sources behind its findings.
  const hosts = new Map<string, number>();
  for (const i of own) for (const s of i.sources) if (s.label) hosts.set(s.label, (hosts.get(s.label) ?? 0) + 1);
  const sources = [...hosts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6) as Row[];
  const monthLabel = (m: Date) => m.toLocaleDateString(locale, { month: "short" });
  const strongest = (items: Insight[]) => items.find(i => i.nature === "OBSERVED") ?? items[0] ?? null;
  return <div className="obs-canvas obs-family-canvas" aria-label={fill(t("{family} en detalle", "{family} in depth"), { family: title })}>
    <Panel index={0} title={t("Lo que se ha observado", "What has been observed")} state={strongest(own)?.nature ?? "UNKNOWN"} proof={strongest(own)} onOpen={onOpen}
      conditions={t("Recuento de hallazgos guardados por su estado epistémico; no es una puntuación.", "Count of stored findings by epistemic state; it is not a score.")}>
      <ul className="obs-canvas-states">{byNature.map(([n, c]) => <li key={n}><NatureMark nature={n} label={natureLabel(n, t)}/><strong>{c.toLocaleString(locale)}</strong></li>)}</ul>
    </Panel>
    <Panel index={1} title={t("Lo más importante", "The most important")} state={top[0]?.nature ?? "UNKNOWN"} proof={top[0] ?? null} onOpen={onOpen}>
      {top.length ? <ul className="obs-canvas-list obs-canvas-top">{top.map(i => <li key={i.id}>
        <button className="obs-link obs-canvas-finding" onClick={() => onOpen(i)}>{i.headline}</button>
        <NatureMark nature={i.nature} label={natureLabel(i.nature, t)}/>
      </li>)}</ul> : <p className="obs-canvas-empty">{t("Solo hay incógnitas declaradas en esta familia; ver «Lo que aún no sabemos».", "There are only declared unknowns in this family; see “What we do not know yet”.")}</p>}
    </Panel>
    <Panel index={2} title={t("En el tiempo", "Over time")} state={strongest(dated)?.nature ?? "UNKNOWN"} proof={strongest(dated)} onOpen={onOpen}
      conditions={fill(t("Hallazgos con fecha por mes, últimos 12 meses{older}. Cuenta lo observado, no la actividad real.", "Dated findings per month, last 12 months{older}. It counts what was observed, not the actual activity."),
        { older: olderThanWindow ? fill(t(" ({n} anteriores)", " ({n} earlier)"), { n: olderThanWindow }) : "" })}>
      {dated.length ? <ol className="obs-months" aria-label={t("Hallazgos por mes", "Findings per month")}>{months.map((m, k) => <li key={k} style={{ ["--i" as string]: k }}>
        <span className="obs-month-bar" style={{ blockSize: `${perMonth[k] ? Math.max(8, (perMonth[k] / Math.max(...perMonth)) * 100) : 0}%` }} aria-hidden="true"/>
        <span className="obs-month-value">{perMonth[k] || ""}</span>
        <span className="obs-month-name">{monthLabel(m)}</span>
        <span className="sr-only">{fill(t("{month}: {n}", "{month}: {n}"), { month: monthLabel(m), n: perMonth[k] })}</span>
      </li>)}</ol> : <p className="obs-canvas-empty">{t("Ningún hallazgo de esta familia tiene fecha todavía.", "No finding in this family has a date yet.")}</p>}
    </Panel>
    <Panel index={3} title={t("De dónde viene", "Where it comes from")} state={strongest(own.filter(i => i.sources.length))?.nature ?? "UNKNOWN"} proof={strongest(own.filter(i => i.sources.length))} onOpen={onOpen}
      conditions={t("Fuentes de los hallazgos de esta familia, por número de hallazgos.", "Sources of this family's findings, by number of findings.")}>
      {sources.length ? <Bars items={sources}/> : <p className="obs-canvas-empty">{t("Sus hallazgos no tienen todavía una fuente pública enlazable.", "Its findings have no linkable public source yet.")}</p>}
    </Panel>
  </div>;
}
