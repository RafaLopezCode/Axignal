/**
 * Observatory model: deterministic presentation of an authorized subscriber output.
 *
 * It only regroups and words what the runtime already returned (HFX "No mental joins",
 * "Same truth, different density"). It never creates a finding, never raises POTENTIAL
 * to OBSERVED, never reads UNKNOWN as negative and never generates prose.
 */
import { activityLabel, auditRows, buyerSignalLabel, discoveryCopy, placeLabel } from "@/components/first-observation";
import { auditCopy, auditImpact } from "./representation-audit";
import { causeCopy, dimensionCopy, proposalCopy, stateCopy } from "@/components/public-understanding";
import type { Discovery, FirstObservation, PublicUnderstanding } from "./subscriber-contracts";
import type { RuntimeProjection } from "./runtime-projection";
import { facetOfDiscovery, facetOfOpportunity, type Channel } from "./observation-families";
import { runtimeText } from "./runtime-text";
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
  /** What the finding itself says it does not establish (its source's limitation). */
  limits?: string[];
  /** A potential buyer (ADR-0099): shown in its own block, never mixed with tenders. */
  group?: "buyers";
  /** How many independent kinds of signal agree on it (ordering only, never a score). */
  strength?: number;
};

type BuyerSignal = { type?: unknown; basis?: unknown; via?: unknown; sourceUrl?: unknown; observedAt?: unknown };

/** Each signal of a potential buyer is one source: its route, through whom, link and date. */
function buyerSources(d: Discovery, t: Translate): Source[] {
  const signals = Array.isArray(d.detail.signals) ? d.detail.signals as BuyerSignal[] : [];
  return signals.map(s => ({
    url: typeof s.sourceUrl === "string" ? s.sourceUrl : null,
    label: buyerSignalLabel(String(s.type ?? ""), t) + (typeof s.via === "string" && s.via ? ` · ${s.via}` : ""),
    observedAt: typeof s.observedAt === "string" ? s.observedAt : null,
    quote: typeof s.basis === "string" ? s.basis : null,
  }));
}

function buyerProof(d: Discovery, t: Translate): Proof[] {
  const ids = (d.detail.identifiers ?? {}) as Record<string, unknown>;
  const out: Proof[] = [];
  if (typeof d.detail.independentSignals === "number") out.push({ label: t("Señales independientes", "Independent signals"), value: String(d.detail.independentSignals) });
  if (typeof ids.website === "string") out.push({ label: t("Web", "Website"), value: ids.website });
  if (typeof ids.lei === "string") out.push({ label: "LEI", value: ids.lei });
  if (typeof ids.wikidata === "string") out.push({ label: "Wikidata", value: ids.wikidata });
  if (typeof ids.country === "string") out.push({ label: t("País", "Country"), value: ids.country });
  return out;
}

/** Potential buyers, most independent signals first (stable within the same strength). */
export function buyersOf(insights: Insight[]): Insight[] {
  return insights.filter(i => i.group === "buyers")
    .map((insight, index) => ({ insight, index }))
    .sort((a, b) => (b.insight.strength ?? 0) - (a.insight.strength ?? 0) || a.index - b.index)
    .map(x => x.insight);
}

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

/** How a finding was read, in plain words (never the internal code). */
function methodLabel(method: string, t: Translate): string {
  switch (method) {
    case "LEXICON": return t("Términos de su propia web", "Terms on its own website");
    case "SCHEMA_ORG_TYPE": return t("Tipo que declara en sus datos estructurados", "Type it declares in its structured data");
    case "SEMANTIC_JUDGMENT": return t("Lectura semántica de su web (no autoritativa)", "Semantic reading of its website (non-authoritative)");
    case "OFFICIAL_REGISTER": return t("Registro oficial", "Official register");
    case "STATED_INDUSTRY": return t("Sector que indica Wikidata", "Industry stated in Wikidata");
    case "SITE_SIGNALS": return t("Varias señales de su web", "Several signals on its website");
    default: return /^[A-Z][A-Z0-9_]+$/.test(method) ? t("Método registrado", "Recorded method") : method;
  }
}

function discoveryInsight(d: Discovery, index: number, t: Translate, locale: string): Insight {
  const copy = discoveryCopy(d, t, locale);
  const buyer = d.kind === "DEMAND" && d.code === "POTENTIAL_BUYER";
  const lane: Lane = d.kind === "SIGNIFICANT_UNKNOWN" ? "unknown"
    : d.kind === "DEMAND" ? "matters"
    : "understood";
  const nature: Nature = d.kind === "REPRESENTATION_GAP" ? "CLARIFY" : epistemicNature(d.epistemicState);
  const detail = d.detail;
  const proof: Proof[] = [];
  if (typeof detail.method === "string") proof.push({ label: t("Método", "Method"), value: methodLabel(String(detail.method), t) });
  if (typeof detail.model === "string") proof.push({ label: t("Evaluador", "Evaluator"), value: `${detail.model} · ${t("juicio no autoritativo, no es una probabilidad de verdad", "non-authoritative judgment, not a probability of truth")}` });
  if (typeof detail.source === "string") proof.push({ label: t("Fuente", "Source"), value: String(detail.source) });
  if (typeof detail.buyer === "string") proof.push({ label: t("Comprador", "Buyer"), value: String(detail.buyer) });
  if (typeof detail.deadline === "string") proof.push({ label: t("Plazo", "Deadline"), value: String(detail.deadline) });
  if (detail.classifiedAs === "MAIN" || detail.classifiedAs === "ADDITIONAL") proof.push({ label: t("Clasificación del comprador", "Buyer's classification"),
    value: detail.classifiedAs === "MAIN"
      ? t("Objeto principal de la licitación", "Main object of the call")
      : t("Código adicional; el objeto principal es otro", "Additional code; the main object is something else") });
  if (typeof detail.instrument === "string") proof.push({ label: t("Instrumento y versión", "Instrument and version"), value: String(detail.instrument) });
  if (typeof detail.conditions === "string") proof.push({ label: t("Condiciones de observación", "Observation conditions"), value: String(detail.conditions) });
  if (typeof detail.sample === "string") proof.push({ label: t("Muestra", "Sample"), value: String(detail.sample) });
  if (typeof detail.coverage === "string") proof.push({ label: t("Cobertura", "Coverage"), value: String(detail.coverage) });
  // A change is only stated against a comparable earlier observation; otherwise the proof says why not.
  const comparable = detail.comparison === "COMPARABLE" && typeof detail.previous === "string";
  if (detail.comparison === "FIRST_OBSERVATION") proof.push({ label: t("Comparación", "Comparison"), value: t("Primera observación: todavía no hay una anterior con la que compararla.", "First observation: there is no earlier one to compare it with.") });
  if (detail.comparison === "NOT_COMPARABLE") proof.push({ label: t("Comparación", "Comparison"), value: t("Condiciones distintas a las de la observación anterior: no se declara ningún cambio.", "Conditions differ from the earlier observation: no change is declared.") });
  if (typeof detail.limitation === "string") proof.push({ label: t("Límite", "Limitation"), value: String(detail.limitation) });
  if (typeof detail.impact === "string") proof.push({ label: t("Impacto", "Impact"), value: auditImpact(detail.impact, t) });
  for (const [label, value] of auditRows(detail.audit, t)) proof.push({ label, value });
  return {
    id: `${d.kind}:${d.code}:${index}`, lane, nature,
    headline: copy.finding, why: copy.why, observedAt: d.observedAt,
    meaning: [copy.why],
    reasoning: buyer
      ? [t("Cada señal es pública y se muestra con su fuente y fecha. No se suman en una puntuación: el orden solo refleja cuántas señales independientes coinciden.", "Each signal is public and shown with its source and date. They are not added into a score: the order only reflects how many independent signals agree."),
        t("Es una posibilidad, no un cliente, un lead ni una probabilidad.", "A possibility, not a customer, a lead nor a probability.")]
      : d.kind === "REPRESENTATION_GAP"
      ? [t("Es una brecha posible en lo que leen las máquinas, no una causa demostrada de ningún resultado.", "It is a possible gap in what machines read, not a demonstrated cause of any result.")]
      : d.kind === "SIGNIFICANT_UNKNOWN"
        ? [t("AXIGNAL lo declara abierto en lugar de suponerlo.", "AXIGNAL declares it open instead of assuming it.")]
        : [],
    proposal: d.kind === "REPRESENTATION_GAP" && d.code.startsWith("AUDIT:") ? auditCopy(d.code.slice(6), t, d.detail.value).action
      : d.kind === "REPRESENTATION_GAP" && d.code !== "HOMEPAGE_NOINDEX"
      ? t("Si quieres que las máquinas relacionen tu oferta, decláralo también en datos estructurados (schema.org). Vuelve a observar después para comprobarlo.",
        "If you want machines to connect your offer, also declare it as structured data (schema.org). Observe again afterwards to check.")
      : null,
    sources: buyer ? buyerSources(d, t)
      : d.sourceUrl || d.excerpt ? [{ url: d.sourceUrl, label: d.sourceUrl ? hostOf(d.sourceUrl) : t("Fuente", "Source"), observedAt: d.observedAt, quote: d.excerpt }] : [],
    proof: buyer ? [...buyerProof(d, t), ...proof] : proof, dimensions: [],
    previous: comparable ? String(detail.previous) : null,
    changeKey: keyOf(`${d.kind}:${d.code}`, d.statement, d.excerpt, d.epistemicState),
    ...facetOfDiscovery(d),
    limits: typeof detail.limitation === "string" ? [String(detail.limitation)] : [],
    ...(buyer ? { group: "buyers" as const, strength: Number(d.detail.independentSignals ?? 1) } : {}),
  };
}

/** The organization's own description of itself, quoted as it publishes it: declared, never verified. */
function presenceInsight(d: Discovery, t: Translate): Insight[] {
  const quote = (d.excerpt ?? "").trim();
  if (d.kind !== "PUBLIC_PRESENCE" || !quote) return [];
  const why = t("Es lo que la organización dice de sí misma en su web. AXIGNAL no lo ha verificado ni lo convierte en una capacidad.",
    "It is what the organization says about itself on its website. AXIGNAL has not verified it nor turned it into a capability.");
  return [{
    id: `${d.kind}:${d.code}:self`, lane: "understood", nature: "DECLARED",
    headline: fill(t("Así se presenta: «{quote}»", "How it presents itself: “{quote}”"), { quote: clip(quote, 220) }),
    why, observedAt: d.observedAt, meaning: [why], reasoning: [],
    proposal: null,
    sources: [{ url: d.sourceUrl, label: d.sourceUrl ? hostOf(d.sourceUrl) : t("Su web", "Its website"), observedAt: d.observedAt, quote }],
    proof: [], dimensions: [], previous: null,
    changeKey: keyOf(`${d.kind}:${d.code}:self`, quote),
    ...facetOfDiscovery(d),
  }];
}

/**
 * The measured checks of its own website, one finding each: what is in place, and every check that is not.
 * Each keeps the instrument, conditions and limitation. A check is not a ranking, a score or a cause.
 */
function representationInsights(d: Discovery, offerGapShown: boolean, t: Translate): Insight[] {
  const checks = d.detail.checks;
  if (d.kind !== "WEB_REPRESENTATION" || typeof checks !== "object" || checks === null) return [];
  const c = checks as Record<string, unknown>;
  const proof: Proof[] = [
    ...(typeof d.detail.instrument === "string" ? [{ label: t("Instrumento y versión", "Instrument and version"), value: d.detail.instrument }] : []),
    ...(typeof d.detail.conditions === "string" ? [{ label: t("Condiciones de observación", "Observation conditions"), value: d.detail.conditions }] : []),
    ...(typeof d.detail.limitation === "string" ? [{ label: t("Límite", "Limitation"), value: d.detail.limitation }] : []),
  ];
  const sitemaps = typeof c.sitemapsDeclared === "number" ? c.sitemapsDeclared : 0;
  // With the full audit, each item to review is its own gap card; here only what is in place.
  const audit = d.detail.audit as { checks?: Array<{ id: string; status: string }> } | undefined;
  if (audit && Array.isArray(audit.checks)) {
    const passed = audit.checks.filter(x => x.status === "PASS");
    if (!passed.length) return [];
    for (const [label, value] of auditRows(d.detail.audit, t)) proof.push({ label, value });
    return [{
      id: `${d.kind}:IN_PLACE`, lane: "understood", nature: "STRENGTH",
      headline: fill(t("{n} de {total} comprobaciones de su web están en orden para buscadores y asistentes.", "{n} of {total} checks of its website are in order for search engines and assistants."), { n: passed.length, total: audit.checks.length }),
      why: t("Auditoría de su propia web: encontrabilidad, preparación para respuestas de IA y compartir.", "Audit of its own website: findability, AI answer readiness and sharing."),
      observedAt: d.observedAt, meaning: [], reasoning: [t("Es una comprobación de su propia web, no una posición en buscadores ni la causa de ningún resultado.", "It is a check of its own website, not a search position nor the cause of any result.")], proposal: null,
      sources: d.sourceUrl ? [{ url: d.sourceUrl, label: hostOf(d.sourceUrl), observedAt: d.observedAt, quote: null }] : [],
      proof, dimensions: [], previous: null,
      changeKey: keyOf(`${d.kind}:IN_PLACE`, String(passed.length)),
      ...facetOfDiscovery(d),
    }];
  }
  const reasoning = [t("Es una comprobación de su propia web, no una posición en buscadores ni la causa de ningún resultado.",
    "It is a check of its own website, not a search position nor the cause of any result.")];
  const make = (code: string, nature: Nature, headline: string, why: string, proposal: string | null): Insight => ({
    id: `${d.kind}:${code}`, lane: "understood", nature, headline, why, observedAt: d.observedAt,
    meaning: [why], reasoning, proposal,
    sources: d.sourceUrl ? [{ url: d.sourceUrl, label: hostOf(d.sourceUrl), observedAt: d.observedAt, quote: null }] : [],
    proof, dimensions: [], previous: null,
    changeKey: keyOf(`${d.kind}:${code}`, headline),
    ...facetOfDiscovery(d),
  });
  const present = [
    c.titlePresent === true ? t("título", "title") : null,
    c.descriptionPresent === true ? t("descripción", "description") : null,
    c.robotsTxtPublished === true ? "robots.txt" : null,
    sitemaps > 0 ? fill(sitemaps === 1 ? t("{n} sitemap", "{n} sitemap") : t("{n} sitemaps", "{n} sitemaps"), { n: sitemaps }) : null,
    typeof c.canonical === "string" && c.canonical ? t("URL canónica", "canonical URL") : null,
    c.organizationDeclared === true ? t("quién es, en datos estructurados", "who it is, as structured data") : null,
  ].filter((x): x is string => Boolean(x));
  const out: Insight[] = [];
  if (present.length) out.push(make("IN_PLACE", "STRENGTH",
    fill(t("Lo que su web ya pone a disposición de buscadores y asistentes: {list}.", "What its website already offers search engines and assistants: {list}."), { list: present.join(", ") }),
    t("Observado en su página principal y robots.txt.", "Observed on its homepage and robots.txt."), null));
  if (c.titlePresent === false) out.push(make("NO_TITLE", "CLARIFY",
    t("Su página principal no tiene título.", "Its homepage has no title."),
    t("Es lo primero que muestran buscadores y asistentes al citarla.", "It is the first thing search engines and assistants show when citing it."),
    t("Añade un título que diga quién es y qué ofrece. Vuelve a observar después para comprobarlo.", "Add a title that says who it is and what it offers. Observe again afterwards to check.")));
  if (c.descriptionPresent === false) out.push(make("NO_DESCRIPTION", "CLARIFY",
    t("Su página principal no tiene meta descripción.", "Its homepage has no meta description."),
    t("Sin ella, buscadores y asistentes la resumen con texto que no ha elegido.", "Without it, search engines and assistants summarize it with text it did not choose."),
    t("Escribe una frase que diga qué ofrece y a quién. Vuelve a observar después para comprobarlo.", "Write one sentence that says what it offers and to whom. Observe again afterwards to check.")));
  if (c.organizationDeclared === false) out.push(make("NO_ORGANIZATION_DATA", "CLARIFY",
    t("No declara quién es en datos estructurados.", "It does not declare who it is as structured data."),
    t("Las máquinas que leen schema.org no encuentran su nombre, logotipo ni datos de contacto declarados.", "Machines that read schema.org find no declared name, logo or contact details."),
    t("Declara la organización con schema.org (Organization). Vuelve a observar después para comprobarlo.", "Declare the organization with schema.org (Organization). Observe again afterwards to check.")));
  if (c.offerDeclared === false && !offerGapShown) out.push(make("NO_OFFER_DATA", "CLARIFY",
    t("En las páginas leídas no declara servicios ni productos como datos estructurados.", "On the pages read it declares no services or products as structured data."),
    t("Las superficies que leen datos estructurados podrían no relacionarla con lo que ofrece.", "Surfaces that read structured data may not connect it with what it offers."),
    t("Declara su oferta con schema.org (Service o Product). Vuelve a observar después para comprobarlo.", "Declare its offer with schema.org (Service or Product). Observe again afterwards to check.")));
  if (c.robotsTxtPublished === true && sitemaps === 0) out.push(make("NO_SITEMAP", "CLARIFY",
    t("Su robots.txt no declara ningún sitemap.", "Its robots.txt declares no sitemap."),
    t("Un sitemap ayuda a que se descubran todas sus páginas.", "A sitemap helps all its pages get discovered."),
    t("Declara su sitemap en robots.txt. Vuelve a observar después para comprobarlo.", "Declare its sitemap in robots.txt. Observe again afterwards to check.")));
  return out;
}

/** A quote shortened for a sentence; its own closing stop is dropped so the sentence keeps one. */
function clip(text: string, max: number): string {
  const bare = text.trim().replace(/[.。]+$/u, "");
  return bare.length <= max ? bare : `${bare.slice(0, max - 1).trimEnd()}…`;
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

type RuntimeNode = RuntimeProjection["nodes"][number];

/**
 * A reading with no first observation is read from the governed projection's own signals. Each keeps the
 * runtime's wording, state and limits as they came: the epistemic state is the runtime's, never raised, and
 * what the signal does not cover is listed as not verified.
 */
function nodeInsight(node: RuntimeNode, familyId: FamilyId | null, t: Translate, locale: string): Insight {
  const say = (text: string) => runtimeText(text, locale);
  const officialWeb = node.evidenceNarrative.steps.some(step => step.kind === "SOURCE" && step.label === "OFFICIAL_WEB");
  const host = (url: string) => { try { return new URL(url).hostname; } catch { return url; } };
  return {
    id: node.id, lane: node.epistemicState === "OBSERVED" ? "understood" : "unknown",
    nature: node.epistemicState === "OBSERVED" ? "OBSERVED" : node.epistemicState === "POTENTIAL" ? "POTENTIAL" : "UNKNOWN",
    headline: say(node.title),
    why: say(node.whyAttention),
    observedAt: node.observedAt,
    meaning: [say(node.interpretation)],
    reasoning: [say(node.uncertainty)],
    proposal: null,
    sources: node.sourceRefs.map(url => ({ url, label: host(url), observedAt: node.observedAt, quote: null })),
    proof: [
      { label: t("Vigencia", "Currentness"), value: currentnessLabel(node.currentness, t) },
      ...(node.unknowns.length ? [{ label: t("Sin verificar", "Not verified"), value: node.unknowns.map(say).join(" · ") }] : []),
    ],
    dimensions: [],
    previous: null,
    // Each re-observation mints a new signal id and time; only a change in what is stated, its currentness or its
    // sources is news. Keyed on content, the same homepage observed again is not shown as new.
    changeKey: keyOf(
      `node:${node.nodeKind}:${node.title}`,
      node.epistemicState, node.whyAttention, node.interpretation, node.uncertainty,
      node.evidenceAccess, node.currentness,
      [...node.unknowns].sort().join(","), [...node.sourceRefs].sort().join(","),
    ),
    family: familyId,
    channel: familyId === "presence" && officialWeb ? "WEB" : null,
  };
}

export function insightsFor(reading: Reading, t: Translate, locale: string): Insight[] {
  const opportunities = reading.projection?.cognition?.opportunities ?? [];
  const titles = new Set(opportunities.map(o => o.title));
  const discoveries = reading.firstObservation?.discoveries ?? [];
  const report = reading.firstObservation?.publicUnderstanding ?? null;
  const families = new Map((reading.projection?.cognition?.signals ?? []).map(signal => [signal.id, signal.familyId as FamilyId]));
  const nodes = reading.firstObservation ? [] : (reading.projection?.nodes ?? []);
  const out: Insight[] = [
    ...nodes.map(node => nodeInsight(node, families.get(node.id) ?? null, t, locale)),
    ...opportunities.map(o => opportunityInsight(o, t, locale)),
    ...discoveries.flatMap((d, i) => CONTEXT_ONLY.has(d.kind) || (d.kind === "DEMAND" && titles.has(String(d.detail.title ?? d.statement)))
      ? [] : [discoveryInsight(d, i, t, locale)]),
    // Context kinds still say what they observed: its own description and the checks of its website.
    ...discoveries.flatMap(d => presenceInsight(d, t)),
    ...discoveries.flatMap(d => representationInsights(d, discoveries.some(g => g.code === "OFFER_NOT_MACHINE_READABLE"), t)),
    ...(report ? understandingInsights(report, t) : []),
  ];
  // Within a lane: what to clarify first, then what is understood well, then context.
  const order: Record<Nature, number> = { CLARIFY: 0, UNRESOLVED: 1, STRENGTH: 2, POTENTIAL: 3, OBSERVED: 4, DECLARED: 5, UNKNOWN: 6 };
  return out.sort((a, b) => order[a.nature] - order[b.nature]);
}

export function byLane(insights: Insight[]): Record<Lane, Insight[]> {
  return {
    matters: insights.filter(i => i.lane === "matters" && i.group !== "buyers"),
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
  const selfDescription = reading.firstObservation?.discoveries.find(d => d.kind === "PUBLIC_PRESENCE" && d.excerpt?.trim())?.excerpt?.trim() ?? null;
  const where = place ? (place.code === "LOCATION_STATED_IN_TEXT" || place.code === "COUNTRY_FROM_SITE_SIGNALS" ? placeLabel(place.statement, locale) : placeLabel(place.statement.length <= 6 ? place.statement : "", locale) || place.statement) : null;
  const lead = activity
    ? fill(t("Por lo que publica, {name} probablemente se dedica a {activity}.", "From what it publishes, {name} most likely works in {activity}."),
      { name, activity: `${activityLabel(activity.code, activity.statement, t).toLocaleLowerCase(locale)}${where ? ` (${where})` : ""}` })
    : selfDescription
      ? fill(t("{name} se presenta así: «{quote}». AXIGNAL todavía no ha establecido su actividad con evidencia suficiente.", "{name} presents itself as: “{quote}”. AXIGNAL has not yet established its activity with enough evidence."),
        { name, quote: clip(selfDescription, 180) })
      : fill(t("AXIGNAL todavía no ha establecido a qué se dedica {name}.", "AXIGNAL has not yet established what {name} does."), { name });
  const lanes = byLane(insights);
  const buyers = buyersOf(insights);
  const multi = buyers.filter(b => (b.strength ?? 0) >= 2).length;
  const potential = lanes.matters.filter(i => i.nature === "POTENTIAL").length;
  const clarify = insights.filter(i => i.nature === "CLARIFY").length;
  const strength = insights.filter(i => i.nature === "STRENGTH").length;
  const unknown = lanes.unknown.length;
  const demand = reading.firstObservation?.demand;
  const tally = [
    demand?.live && demand.total ? count(demand.total, t("{n} licitación abierta que encaja", "{n} open tender that fits"), t("{n} licitaciones abiertas que encajan", "{n} open tenders that fit")) : null,
    demand?.live && demand.new ? count(demand.new, t("{n} nueva esta semana", "{n} new tender this week"), t("{n} nuevas esta semana", "{n} new tenders this week")) : null,
    potential && !(demand?.live && demand.total) ? count(potential, t("{n} oportunidad potencial", "{n} potential opportunity"), t("{n} oportunidades potenciales", "{n} potential opportunities")) : null,
    buyers.length ? count(buyers.length, t("{n} posible comprador", "{n} potential buyer"), t("{n} posibles compradores", "{n} potential buyers"))
      + (multi ? ` (${fill(t("{n} con varias señales", "{n} with several signals"), { n: multi })})` : "") : null,
    strength ? count(strength, t("{n} aspecto que se entiende bien", "{n} aspect understood well"), t("{n} aspectos que se entienden bien", "{n} aspects understood well")) : null,
    clarify ? count(clarify, t("{n} aspecto que conviene aclarar", "{n} aspect worth clarifying"), t("{n} aspectos que conviene aclarar", "{n} aspects worth clarifying")) : null,
    unknown ? count(unknown, t("{n} incógnita abierta", "{n} open unknown"), t("{n} incógnitas abiertas", "{n} open unknowns")) : null,
  ].filter((x): x is string => Boolean(x));
  return { lead, tally };
}
