/**
 * Observatory model: deterministic presentation of an authorized subscriber output.
 *
 * It only regroups and words what the runtime already returned (HFX "No mental joins",
 * "Same truth, different density"). It never creates a finding, never raises POTENTIAL
 * to OBSERVED, never reads UNKNOWN as negative and never generates prose.
 */
import { activityLabel, discoveryCopy, placeLabel } from "@/components/first-observation";
import { causeCopy, dimensionCopy, proposalCopy, stateCopy } from "@/components/public-understanding";
import type { Discovery, FirstObservation, PublicUnderstanding } from "./subscriber-contracts";
import type { RuntimeProjection } from "./runtime-projection";
import { facetOfDiscovery, facetOfOpportunity, type Channel } from "./observation-families";
import type { FamilyId } from "./projection";

export type Translate = (es: string, en: string) => string;
type Opportunity = NonNullable<RuntimeProjection["cognition"]>["opportunities"][number];
type Dimension = PublicUnderstanding["dimensions"][number];

/** Human question each lane answers. Lanes group; they never rank truth. */
export type Lane = "matters" | "understood" | "unknown";
/** Epistemic or interpretive nature, always shown as text plus a shape. */
export type Nature = "OBSERVED" | "DECLARED" | "POTENTIAL" | "UNKNOWN" | "STRENGTH" | "CLARIFY" | "UNRESOLVED";

export type Proof = { label: string; value: string };
export type Source = { url: string | null; label: string; observedAt: string | null; quote: string | null };

export type Insight = {
  id: string;
  lane: Lane;
  nature: Nature;
  headline: string;
  why: string;
  observedAt: string | null;
  /** UNDERSTAND: what it means and what it does not. */
  meaning: string[];
  /** REASON: how AXIGNAL derives it, its limits and alternative explanations. */
  reasoning: string[];
  /** Conditional next step, only when the runtime supplied one. */
  proposal: string | null;
  /** PROVE: exact sources and recorded basis. */
  sources: Source[];
  proof: Proof[];
  /** Assessable dimensions of a potential opportunity (no score). */
  dimensions: Array<{ label: string; state: "OBSERVED" | "UNKNOWN" | "NOT_APPLICABLE"; outcome: string }>;
  /** What it was in the previous comparable reading, when the runtime compared them. */
  previous: string | null;
  /** Identity for "lit until seen": changes when what is shown materially changes. */
  changeKey: string;
  /** Thematic family and Presence channel, placed from typed contract values only; null when the contract cannot place it. */
  family: FamilyId | null;
  channel: Channel | null;
};

function hash(value: string): string {
  let h = 2166136261;
  for (let i = 0; i < value.length; i++) h = Math.imul(h ^ value.charCodeAt(i), 16777619);
  return (h >>> 0).toString(36);
}

const keyOf = (id: string, ...parts: Array<string | null | undefined>) => `${id}#${hash(parts.map(p => p ?? "").join("|"))}`;

function hostOf(url: string): string {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; }
}

function epistemicNature(state: Discovery["epistemicState"]): Nature {
  return state;
}

export function natureLabel(nature: Nature, t: Translate): string {
  switch (nature) {
    case "OBSERVED": return t("Observado", "Observed");
    case "DECLARED": return t("Declarado", "Declared");
    case "POTENTIAL": return t("Potencial", "Potential");
    case "UNKNOWN": return t("Desconocido", "Unknown");
    case "STRENGTH": return t("Se entiende bien", "Understood well");
    case "CLARIFY": return t("Conviene aclarar", "Worth clarifying");
    case "UNRESOLVED": return t("Sin conclusión", "No conclusion");
  }
}

export function laneCopy(lane: Lane, t: Translate): { title: string; question: string; empty: string } {
  if (lane === "matters") return {
    title: t("Lo que importa", "What matters"),
    question: t("Oportunidades, demanda y cambios que merecen tu atención.", "Opportunities, demand and changes that deserve your attention."),
    empty: t("Nada pide tu atención en esta lectura. Una ausencia aquí no demuestra ausencia en el mundo.", "Nothing asks for your attention in this reading. Absence here does not prove absence in the world."),
  };
  if (lane === "understood") return {
    title: t("Cómo se entiende", "How it is understood"),
    question: t("Qué comunica bien su presencia pública y qué podría aclarar.", "What its public presence communicates well and what it could clarify."),
    empty: t("Todavía no hay una lectura de su comunicación pública.", "There is no reading of its public communication yet."),
  };
  return {
    title: t("Lo que aún no sabemos", "What we do not know yet"),
    question: t("Lo que AXIGNAL no ha podido establecer y por qué. Desconocido no es negativo.", "What AXIGNAL could not establish and why. Unknown is not negative."),
    empty: t("No hay incógnitas abiertas declaradas en esta lectura.", "No open unknowns are declared in this reading."),
  };
}

function judgmentFamily(family: string, t: Translate): string {
  switch (family) {
    case "GEOGRAPHIC_ECONOMIC_REACH": return t("Alcance geográfico", "Geographic reach");
    case "LOGISTICS_FEASIBILITY": return t("Logística", "Logistics");
    case "REGULATORY_ELIGIBILITY": return t("Requisitos regulatorios", "Regulatory requirements");
    case "TEMPORAL_ACTIONABILITY": return t("Plazo", "Timing");
    default: return family;
  }
}

function judgmentOutcome(outcome: string, t: Translate): string {
  switch (outcome) {
    case "COMPATIBLE": return t("Compatible", "Compatible");
    case "NOT_APPLICABLE": return t("No aplica", "Not applicable");
    case "UNRESOLVED": return t("Sin resolver", "Unresolved");
    case "INCOMPATIBLE": return t("Incompatible", "Incompatible");
    default: return outcome;
  }
}

export function currentnessLabel(value: string, t: Translate): string {
  switch (value) {
    case "CURRENT": return t("Vigente", "Current");
    case "STALE": return t("Desactualizada", "Stale");
    case "HISTORICAL": return t("Histórica", "Historical");
    default: return t("Vigencia desconocida", "Currentness unknown");
  }
}

function knownLabel(label: string, t: Translate): string {
  if (label === "Published demand title") return t("Título publicado", "Published title");
  if (label === "Matched demand code") return t("Código de demanda que coincide", "Matched demand code");
  return label;
}

function formLabel(form: string, t: Translate): string {
  if (form === "OPEN_CALL_FOR_TENDER") return t("Licitación abierta", "Open call for tender");
  return t("Demanda publicada", "Published demand");
}

function opportunityInsight(o: Opportunity, t: Translate, locale: string): Insight {
  const relevance = o.relevance;
  const capabilityCode = relevance?.relevantThrough?.[0] ?? "";
  const judgments = relevance?.channels?.flatMap(channel => channel.judgments ?? []) ?? [];
  const deadline = o.deadline ? new Intl.DateTimeFormat(locale, { day: "numeric", month: "short", year: "numeric" }).format(new Date(o.deadline)) : null;
  return {
    id: o.id, lane: "matters", nature: o.epistemic === "POTENTIAL" ? "POTENTIAL" : "UNKNOWN",
    headline: o.title,
    why: [o.buyer, formLabel(o.form, t), deadline ? fill(t("plazo {date}", "deadline {date}"), { date: deadline }) : null].filter(Boolean).join(" · "),
    observedAt: o.observedAt,
    meaning: [
      t("Una demanda publicada coincide con una capacidad que su web declara. Es una oportunidad potencial: no es un cliente, una invitación ni una relación.",
        "Published demand matches a capability its website declares. It is a potential opportunity: not a customer, an invitation or a relationship."),
      fill(t("Coincide con: {capability} · {place}", "Matches: {capability} · {place}"), { capability: activityLabel(capabilityCode, o.capability.label, t), place: placeLabel(o.market, locale) }),
    ],
    reasoning: [o.whyPotential],
    proposal: null,
    sources: [
      { url: null, label: t("Su web", "Its website"), observedAt: null, quote: o.capability.excerpt },
    ],
    proof: [
      ...o.known.map(k => ({ label: knownLabel(k.label, t), value: k.value })),
      ...(o.unknown.length ? [{ label: t("Sin verificar", "Not verified"), value: o.unknown.join(" · ") }] : []),
      { label: t("Vigencia", "Currentness"), value: currentnessLabel(o.currentness, t) },
      ...o.whyLooked.map(value => ({ label: t("Ruta de búsqueda", "Search route"), value })),
    ],
    dimensions: judgments.map(j => ({ label: judgmentFamily(j.family, t), outcome: judgmentOutcome(j.outcome, t),
      state: j.outcome === "NOT_APPLICABLE" ? "NOT_APPLICABLE" as const : j.state === "OBSERVED" ? "OBSERVED" as const : "UNKNOWN" as const })),
    previous: null,
    changeKey: keyOf(o.id, o.title, o.deadline, o.currentness),
    ...facetOfOpportunity(o),
  };
}

function discoveryInsight(d: Discovery, index: number, t: Translate, locale: string): Insight {
  const copy = discoveryCopy(d, t, locale);
  const lane: Lane = d.kind === "SIGNIFICANT_UNKNOWN" ? "unknown"
    : d.kind === "DEMAND" ? "matters"
    : "understood";
  const nature: Nature = d.kind === "REPRESENTATION_GAP" ? "CLARIFY" : epistemicNature(d.epistemicState);
  const detail = d.detail;
  const proof: Proof[] = [];
  if (typeof detail.method === "string") proof.push({ label: t("Método", "Method"), value: String(detail.method) });
  if (typeof detail.model === "string") proof.push({ label: t("Evaluador", "Evaluator"), value: `${detail.model} · ${t("juicio no autoritativo, no es una probabilidad de verdad", "non-authoritative judgment, not a probability of truth")}` });
  if (typeof detail.source === "string") proof.push({ label: t("Fuente", "Source"), value: String(detail.source) });
  if (typeof detail.buyer === "string") proof.push({ label: t("Comprador", "Buyer"), value: String(detail.buyer) });
  if (typeof detail.deadline === "string") proof.push({ label: t("Plazo", "Deadline"), value: String(detail.deadline) });
  if (typeof detail.instrument === "string") proof.push({ label: t("Instrumento y versión", "Instrument and version"), value: String(detail.instrument) });
  if (typeof detail.conditions === "string") proof.push({ label: t("Condiciones de observación", "Observation conditions"), value: String(detail.conditions) });
  if (typeof detail.sample === "string") proof.push({ label: t("Muestra", "Sample"), value: String(detail.sample) });
  if (typeof detail.coverage === "string") proof.push({ label: t("Cobertura", "Coverage"), value: String(detail.coverage) });
  // A change is only stated against a comparable earlier observation; otherwise the proof says why not.
  const comparable = detail.comparison === "COMPARABLE" && typeof detail.previous === "string";
  if (detail.comparison === "FIRST_OBSERVATION") proof.push({ label: t("Comparación", "Comparison"), value: t("Primera observación: todavía no hay una anterior con la que compararla.", "First observation: there is no earlier one to compare it with.") });
  if (detail.comparison === "NOT_COMPARABLE") proof.push({ label: t("Comparación", "Comparison"), value: t("Condiciones distintas a las de la observación anterior: no se declara ningún cambio.", "Conditions differ from the earlier observation: no change is declared.") });
  if (typeof detail.limitation === "string") proof.push({ label: t("Límite", "Limitation"), value: String(detail.limitation) });
  return {
    id: `${d.kind}:${d.code}:${index}`, lane, nature,
    headline: copy.finding, why: copy.why, observedAt: d.observedAt,
    meaning: [copy.why],
    reasoning: d.kind === "REPRESENTATION_GAP"
      ? [t("Es una brecha posible en lo que leen las máquinas, no una causa demostrada de ningún resultado.", "It is a possible gap in what machines read, not a demonstrated cause of any result.")]
      : d.kind === "SIGNIFICANT_UNKNOWN"
        ? [t("AXIGNAL lo declara abierto en lugar de suponerlo.", "AXIGNAL declares it open instead of assuming it.")]
        : [],
    proposal: d.kind === "REPRESENTATION_GAP" && d.code !== "HOMEPAGE_NOINDEX"
      ? t("Si quieres que las máquinas relacionen tu oferta, decláralo también en datos estructurados (schema.org). Vuelve a observar después para comprobarlo.",
        "If you want machines to connect your offer, also declare it as structured data (schema.org). Observe again afterwards to check.")
      : null,
    sources: d.sourceUrl || d.excerpt ? [{ url: d.sourceUrl, label: d.sourceUrl ? hostOf(d.sourceUrl) : t("Fuente", "Source"), observedAt: d.observedAt, quote: d.excerpt }] : [],
    proof, dimensions: [],
    previous: comparable ? String(detail.previous) : null,
    changeKey: keyOf(`${d.kind}:${d.code}`, d.statement, d.excerpt, d.epistemicState),
    ...facetOfDiscovery(d),
  };
}

function understandingInsights(report: PublicUnderstanding, t: Translate): Insight[] {
  if (report.status !== "MEASURED") return [{
    id: `pu:${report.reportId}:status`, lane: "understood", nature: "UNKNOWN",
    headline: t("La lectura de tu oferta pública no está disponible", "The reading of your public offer is unavailable"),
    why: causeCopy(report.cause, t), observedAt: report.measuredAt,
    meaning: [causeCopy(report.cause, t)],
    reasoning: [t("La incertidumbre o el fallo del instrumento no es un defecto de la organización.", "Instrument uncertainty or failure is not a defect of the organization.")],
    proposal: null, sources: [], proof: [], dimensions: [],
    previous: null,
    changeKey: keyOf(`pu:status`, report.status, report.cause),
    family: "value", channel: null,
  }];
  return report.dimensions.map(d => dimensionInsight(report, d, t));
}

function dimensionInsight(report: PublicUnderstanding, d: Dimension, t: Translate): Insight {
  const quotes = report.citations.filter(q => d.citationIds.includes(q.id));
  const specific = d.state === "STRENGTH" ? quotes : [];
  const nature: Nature = d.state === "STRENGTH" ? "STRENGTH" : d.state === "CONSTRUCTIVE_GAP" ? "CLARIFY" : "UNRESOLVED";
  const name = dimensionCopy(d.dimension, t);
  return {
    id: `pu:${report.reportId}:${d.dimension}`, lane: "understood", nature,
    headline: d.state === "STRENGTH" && specific[0] ? `${name}: “${specific[0].quote}”` : name,
    why: d.state === "STRENGTH"
      ? t("Un lector externo lo vincula con una declaración pública explícita.", "An external reader links it to an explicit public statement.")
      : causeCopy(d.cause, t),
    observedAt: report.measuredAt,
    meaning: [causeCopy(d.cause, t)],
    reasoning: [
      t("Es la interpretación de un instrumento condicionado (un lector sin contexto privado sobre las páginas inspeccionadas), no una verificación del negocio.",
        "It is the interpretation of a conditioned instrument (a reader without private context over the inspected pages), not business verification."),
      ...(d.state !== "STRENGTH" ? [t("También puede haber una divulgación limitada deliberadamente, información fuera de esta muestra o un error del evaluador.",
        "There may also be deliberately limited disclosure, information outside this sample or an evaluator error.")] : []),
    ],
    proposal: d.proposal ? proposalCopy(d.dimension, d.cause === "CONTRADICTION", t) : null,
    sources: (specific.length ? specific : quotes.length < report.citations.length ? quotes : []).map(q => ({ url: q.url, label: hostOf(q.url), observedAt: q.observedAt, quote: q.quote })),
    proof: [
      { label: t("Instrumento", "Instrument"), value: `${report.instrument.id} ${report.instrument.version}` },
      { label: t("Cobertura", "Coverage"), value: report.coverage === "BOUNDED_COMPLETE" ? t("Páginas seleccionadas inspeccionadas; no es un censo del sitio.", "Selected pages inspected; not a site census.") : t("Adquisición o representación incompleta.", "Incomplete acquisition or representation.") },
    ],
    dimensions: [],
    previous: (() => {
      const change = report.comparison?.state === "COMPARABLE" ? report.comparison.changes.find(c => c.dimension === d.dimension) : undefined;
      if (!change || change.kind === "INTERPRETATION_BASIS_CHANGED" || !change.before) return null;
      return stateCopy(change.before, t);
    })(),
    changeKey: keyOf(`pu:${d.dimension}`, d.state, d.cause, quotes.map(q => q.quote).join("|")),
    family: "value", channel: null,
  };
}

/** Kinds that orient (shown in Evidence) but do not deserve a lane of their own. */
const CONTEXT_ONLY = new Set<Discovery["kind"]>(["PUBLIC_PRESENCE", "WEB_REPRESENTATION", "IDENTITY_HINT"]);

export type Reading = { projection: RuntimeProjection | null; firstObservation: FirstObservation | null };

export function insightsFor(reading: Reading, t: Translate, locale: string): Insight[] {
  const opportunities = reading.projection?.cognition?.opportunities ?? [];
  const titles = new Set(opportunities.map(o => o.title));
  const discoveries = reading.firstObservation?.discoveries ?? [];
  const report = reading.firstObservation?.publicUnderstanding ?? null;
  const out: Insight[] = [
    ...opportunities.map(o => opportunityInsight(o, t, locale)),
    ...discoveries.flatMap((d, i) => CONTEXT_ONLY.has(d.kind) || (d.kind === "DEMAND" && titles.has(String(d.detail.title ?? d.statement)))
      ? [] : [discoveryInsight(d, i, t, locale)]),
    ...(report ? understandingInsights(report, t) : []),
  ];
  // Within a lane: what to clarify first, then what is understood well, then context.
  const order: Record<Nature, number> = { CLARIFY: 0, UNRESOLVED: 1, STRENGTH: 2, POTENTIAL: 3, OBSERVED: 4, DECLARED: 5, UNKNOWN: 6 };
  return out.sort((a, b) => order[a.nature] - order[b.nature]);
}

export function byLane(insights: Insight[]): Record<Lane, Insight[]> {
  return {
    matters: insights.filter(i => i.lane === "matters"),
    understood: insights.filter(i => i.lane === "understood"),
    unknown: insights.filter(i => i.lane === "unknown"),
  };
}

/** Whole-sentence templates keep word order translatable: "{name}" and "{n}" are filled after translation. */
export function fill(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) => key in values ? String(values[key]) : match);
}

function count(n: number, one: string, many: string): string {
  return fill(n === 1 ? one : many, { n });
}

/** GLANCE: one truthful sentence built from the reading, never generated. */
export function briefing(reading: Reading, name: string, insights: Insight[], t: Translate, locale: string): { lead: string; tally: string[] } {
  const activity = reading.firstObservation?.discoveries.find(d => d.kind === "ACTIVITY");
  const place = reading.firstObservation?.discoveries.find(d => d.kind === "DECLARED_LOCATION");
  const where = place ? (place.code === "LOCATION_STATED_IN_TEXT" ? placeLabel(place.statement, locale) : placeLabel(place.statement.length <= 6 ? place.statement : "", locale) || place.statement) : null;
  const lead = activity
    ? fill(t("Por lo que publica, {name} probablemente se dedica a {activity}.", "From what it publishes, {name} most likely works in {activity}."),
      { name, activity: `${activityLabel(activity.code, activity.statement, t).toLocaleLowerCase(locale)}${where ? ` (${where})` : ""}` })
    : fill(t("AXIGNAL todavía no ha establecido a qué se dedica {name}.", "AXIGNAL has not yet established what {name} does."), { name });
  const lanes = byLane(insights);
  const potential = lanes.matters.filter(i => i.nature === "POTENTIAL").length;
  const clarify = insights.filter(i => i.nature === "CLARIFY").length;
  const strength = insights.filter(i => i.nature === "STRENGTH").length;
  const unknown = lanes.unknown.length;
  const tally = [
    potential ? count(potential, t("{n} oportunidad potencial", "{n} potential opportunity"), t("{n} oportunidades potenciales", "{n} potential opportunities")) : null,
    strength ? count(strength, t("{n} aspecto que se entiende bien", "{n} aspect understood well"), t("{n} aspectos que se entienden bien", "{n} aspects understood well")) : null,
    clarify ? count(clarify, t("{n} aspecto que conviene aclarar", "{n} aspect worth clarifying"), t("{n} aspectos que conviene aclarar", "{n} aspects worth clarifying")) : null,
    unknown ? count(unknown, t("{n} incógnita abierta", "{n} open unknown"), t("{n} incógnitas abiertas", "{n} open unknowns")) : null,
  ].filter((x): x is string => Boolean(x));
  return { lead, tally };
}
