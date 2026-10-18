"use client";
import { useMemo, useState } from "react";
import { useLocale } from "@/lib/locale";
import { compareDays, seriesOf, type Evolution, type Row } from "@/lib/evolution";
import { FAMILY_ORDER, type Facet } from "@/lib/observation-families";
import type { FamilyId } from "@/lib/projection";
import { auditCopy } from "@/lib/representation-audit";

type Translate = (es: string, en: string) => string;

/** Human names of the timeline's metrics (application/timeline METRICS); a key is never shown. */
export function metricLabel(key: string, t: Translate): string {
  switch (key) {
    case "presence.ai_named_share": return t("Respuestas de IA que la nombran", "AI answers that name it");
    case "presence.search_ranked_share": return t("Búsquedas de su actividad en las que aparece", "Searches for its activity where it appears");
    case "presence.ai_knows_brand": return t("La IA conoce la marca", "AI knows the brand");
    case "presence.audit_attention": return t("Comprobaciones de su web por revisar", "Website checks to review");
    case "presence.audit_passed": return t("Comprobaciones de su web superadas", "Website checks passed");
    case "presence.lcp_ms": return t("Carga real de la página (LCP)", "Real page load (LCP)");
    case "presence.inp_ms": return t("Respuesta real a la interacción (INP)", "Real interaction response (INP)");
    case "presence.languages": return t("Idiomas publicados", "Published languages");
    case "reputation.press_mentions": return t("Menciones en prensa", "Press mentions");
    case "reputation.review_profiles": return t("Perfiles de opiniones enlazados", "Linked review profiles");
    case "reputation.wikipedia_views": return t("Visitas a su artículo de Wikipedia", "Views of its Wikipedia article");
    case "reputation.wikipedia_languages": return t("Idiomas de su artículo de Wikipedia", "Languages of its Wikipedia article");
    case "reputation.self_rating": return t("Valoración que publica", "Rating it publishes");
    case "activity.own_publications": return t("Publicaciones propias", "Own publications");
    case "activity.publications_90d": return t("Publicaciones en 90 días (canal propio)", "Posts in 90 days (own channel)");
    case "activity.job_postings": return t("Ofertas de empleo en su web", "Job postings on its website");
    case "activity.hiring_channel": return t("Canal de empleo", "Hiring channel");
    case "activity.open_positions": return t("Puestos abiertos", "Open positions");
    case "value.activities": return t("Actividades establecidas", "Established activities");
    case "value.credentials": return t("Certificaciones declaradas", "Declared credentials");
    case "markets.premises": return t("Sedes declaradas", "Declared premises");
    case "markets.group_countries": return t("Países con sociedades del grupo", "Countries with group entities");
    case "markets.hiring_countries": return t("Países donde contrata", "Countries where it hires");
    case "relationships.public_clients": return t("Compradores públicos que le adjudicaron", "Public buyers that awarded it");
    case "relationships.partners": return t("Socios en contratos públicos", "Partners in public contracts");
    case "relationships.competitors": return t("Competidores observados", "Observed competitors");
    case "relationships.technology": return t("Tecnología que usa su web", "Technology its website uses");
    case "relationships.declared_clients": return t("Clientes que declara", "Clients it declares");
    case "relationships.declared_partners": return t("Socios que declara", "Partners it declares");
    case "demand.open_public_calls": return t("Licitaciones abiertas que encajan", "Open tenders that fit");
    case "demand.recurrent_buyers": return t("Compradores públicos recurrentes", "Recurrent public buyers");
    case "economics.revenue": return t("Facturación", "Revenue");
    case "economics.employees": return t("Empleados", "Employees");
    case "organization.identifiers": return t("Identificadores que declara", "Identifiers it declares");
    case "context.sector_headlines": return t("Titulares del sector", "Sector headlines");
    case "context.regulation": return t("Normas que le afectan", "Rules that affect it");
    default: return t("Otra métrica", "Other metric");
  }
}

function familyLabel(family: FamilyId, t: Translate): string {
  switch (family) {
    case "presence": return t("Visibilidad (SEO, GEO y web)", "Visibility (SEO, GEO and web)");
    case "reputation": return t("Reputación", "Reputation");
    case "value": return t("Valor", "Value");
    case "markets": return t("Mercados", "Markets");
    case "relationships": return t("Relaciones", "Relationships");
    case "demand": return t("Demanda", "Demand");
    case "activity": return t("Actividad", "Activity");
    case "economics": return t("Economía", "Economics");
    case "organization": return t("Organización", "Organization");
    default: return t("Contexto", "Context");
  }
}

function formatValue(key: string, value: unknown, locale: string, t: Translate): string {
  if (value === undefined || value === null) return t("No medido", "Not measured");
  if (Array.isArray(value)) return value.length === 1 ? t("1 elemento", "1 item") : t("{n} elementos", "{n} items").replace("{n}", String(value.length));
  if (typeof value === "number") {
    if (key === "presence.ai_named_share" || key === "presence.search_ranked_share") return `${Math.round(value * 100)} %`;
    if (key === "presence.ai_knows_brand" || key === "activity.hiring_channel") return value ? t("Sí", "Yes") : t("No", "No");
    if (key.endsWith("_ms")) return `${Math.round(value).toLocaleString(locale)} ms`;
    return value.toLocaleString(locale, { maximumFractionDigits: 2 });
  }
  return String(value);
}

function changeLabel(row: Row, t: Translate): string {
  switch (row.direction) {
    case "EVOLUTION": return t("Mejora", "Improved");
    case "REGRESSION": return t("Empeora", "Worsened");
    case "UP": return t("Sube", "Up");
    case "DOWN": return t("Baja", "Down");
    case "ADDED": return t("Aparecen", "Appeared");
    case "REMOVED": return t("Desaparecen", "Disappeared");
    case "CHANGED": return t("Cambia", "Changed");
    case "NOT_COMPARABLE": return t("No comparable: cambió el instrumento", "Not comparable: the instrument changed");
    case "NOT_MEASURED": return t("No medido uno de los días", "Not measured on one of the days");
    default: return t("Sin cambios", "No change");
  }
}

/** Items as people read them: an audit check by its plain title, never its code. */
function itemLabel(key: string, item: string, t: Translate): string {
  return key === "presence.audit_attention" ? auditCopy(item, t).title : item;
}

function Trend({ points }: { points: Array<[string, number | null]> }) {
  const values = points.map(p => p[1]).filter((v): v is number => v !== null);
  if (values.length < 2) return null;
  const min = Math.min(...values), max = Math.max(...values), span = max - min || 1;
  const step = 80 / Math.max(1, points.length - 1);
  const d = points.map(([, v], i) => v === null ? null : `${i * step},${18 - ((v - min) / span) * 16}`).filter(Boolean).join(" ");
  return <svg className="obs-evo-trend" viewBox="0 0 80 20" width="80" height="20" aria-hidden="true"><polyline points={d} fill="none" stroke="currentColor" strokeWidth="1.5"/></svg>;
}

function shortDay(day: string, locale: string): string {
  return new Date(`${day}T12:00:00Z`).toLocaleDateString(locale, { day: "numeric", month: "short", year: "numeric" });
}

/** Day X against day Y for every family with values (spec 076). */
export function EvolutionCompare({ evolution, facet }: { evolution: Evolution; facet: Facet }) {
  const { t, locale } = useLocale();
  const days = evolution.days;
  const [x, setX] = useState(days[0]);
  const [y, setY] = useState(days[days.length - 1]);
  const rows = useMemo(() => compareDays(evolution, x, y, facet), [evolution, x, y, facet]);
  const moved = rows.filter(r => !["SAME", "NOT_COMPARABLE", "NOT_MEASURED"].includes(r.direction));
  const better = rows.filter(r => r.direction === "EVOLUTION").length, worse = rows.filter(r => r.direction === "REGRESSION").length;
  if (days.length < 2) return null;
  return <section className="obs-evo" aria-labelledby="obs-evo-title">
    <h2 id="obs-evo-title">{t("Comparar dos días", "Compare two days")}</h2>
    <div className="obs-evo-pick">
      <label>{t("Del día", "From")} <select value={x} onChange={e => setX(e.target.value)}>{days.map(d => <option key={d} value={d}>{shortDay(d, locale)}</option>)}</select></label>
      <label>{t("al día", "to")} <select value={y} onChange={e => setY(e.target.value)}>{days.map(d => <option key={d} value={d}>{shortDay(d, locale)}</option>)}</select></label>
    </div>
    <p className="obs-evo-summary" aria-live="polite">{x === y
      ? t("Elige dos días distintos para ver qué cambió.", "Choose two different days to see what changed.")
      : [t("{n} métricas cambian", "{n} metrics changed").replace("{n}", String(moved.length)),
        better ? t("{n} mejoran", "{n} improved").replace("{n}", String(better)) : null,
        worse ? t("{n} empeoran", "{n} worsened").replace("{n}", String(worse)) : null].filter(Boolean).join(" · ")}</p>
    {FAMILY_ORDER.map(family => {
      const own = rows.filter(r => r.family === family);
      if (!own.length) return null;
      return <div key={family} className="obs-evo-family">
        <h3>{familyLabel(family, t)}</h3>
        <table className="obs-evo-table">
          <thead><tr><th scope="col">{t("Métrica", "Metric")}</th><th scope="col">{shortDay(x, locale)}</th><th scope="col">{shortDay(y, locale)}</th><th scope="col">{t("Cambio", "Change")}</th></tr></thead>
          <tbody>{own.map(row => <tr key={row.key} className={`obs-evo-${row.direction.toLowerCase()}`}>
            <th scope="row">{metricLabel(row.key, t)} <Trend points={seriesOf(evolution, row.key)}/></th>
            <td>{formatValue(row.key, row.before, locale, t)}</td>
            <td>{formatValue(row.key, row.after, locale, t)}</td>
            <td><span className="obs-evo-change">{changeLabel(row, t)}{typeof row.delta === "number" && row.delta !== 0 && !["SAME"].includes(row.direction) ? ` (${row.delta > 0 ? "+" : ""}${row.key === "presence.ai_named_share" || row.key === "presence.search_ranked_share" ? `${Math.round(row.delta * 100)} pp` : row.delta.toLocaleString(locale)})` : ""}</span>
              {row.added?.length ? <span className="obs-evo-items">+ {row.added.slice(0, 5).map(i => itemLabel(row.key, i, t)).join(" · ")}{row.added.length > 5 ? "…" : ""}</span> : null}
              {row.removed?.length ? <span className="obs-evo-items">− {row.removed.slice(0, 5).map(i => itemLabel(row.key, i, t)).join(" · ")}{row.removed.length > 5 ? "…" : ""}</span> : null}</td>
          </tr>)}</tbody>
        </table>
      </div>;
    })}
    <p className="obs-evo-note">{t("Un cambio es lo que difiere entre dos lecturas del mismo instrumento, no su causa. Mejora o empeora solo se dice donde más es claramente mejor o peor.", "A change is what differs between two readings by the same instrument, not its cause. Improved or worsened is said only where more is clearly better or worse.")}</p>
  </section>;
}
