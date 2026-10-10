"use client";

import { ExternalLink } from "lucide-react";
import { PublicUnderstandingView } from "./public-understanding";
import { useLocale } from "@/lib/locale";
import { useEvidenceLink } from "./evidence-link-context";
import { type Discovery, type FirstObservation } from "@/lib/subscriber-contracts";

type Translate = (es: string, en: string) => string;

/** Subscriber-facing state of a First Observation: derived from what actually ran. */
export function observationStateCopy(state: string, t: Translate): string {
  switch (state) {
    case "QUEUED": return t("Observación preparada. Empieza en segundo plano; puedes seguir navegando.", "Observation prepared. It starts in the background; you can keep browsing.");
    case "OBSERVING_PUBLIC_PRESENCE": return t("Observando su presencia pública…", "Observing its public presence…");
    case "FIRST_PROOF_READY": return t("Primera observación lista, con sus evidencias.", "First observation ready, with its evidence.");
    case "NOT_ENOUGH_CAPABILITY_EVIDENCE": return t("Su web pública todavía no deja claro qué ofrece. No lo suponemos.", "Its public website does not yet make clear what it offers. We do not assume it.");
    case "NO_PUBLIC_WEBSITE": return t("No hay una web pública que observar. Añade su web para empezar.", "There is no public website to observe. Add its website to begin.");
    case "SOURCE_UNAVAILABLE": return t("Su web no se pudo observar con sus reglas de acceso. No concluimos nada de ello.", "Its website could not be observed under its access rules. We conclude nothing from that.");
    case "BUDGET_EXHAUSTED": return t("La observación se detuvo en sus límites. Seguirá en el próximo ciclo.", "Observation stopped at its limits. It will continue in the next cycle.");
    case "CAPACITY_REQUIRED": return t("Tu capacidad actual ya está en uso. Amplíala para observar esta organización.", "Your current capacity is already in use. Expand it to observe this organization.");
    case "OBSERVATION_FAILED": return t("No pudimos completar la observación. Pide que se vuelva a comprobar; no concluimos nada de ello.", "We could not complete the observation. Ask to check again; we conclude nothing from that.");
    default: return t("Observación no disponible todavía.", "Observation not available yet.");
  }
}

const US_STATES: Record<string, string> = { AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California", CO: "Colorado", CT: "Connecticut", DE: "Delaware", DC: "District of Columbia", FL: "Florida", GA: "Georgia", HI: "Hawaii", ID: "Idaho", IL: "Illinois", IN: "Indiana", IA: "Iowa", KS: "Kansas", KY: "Kentucky", LA: "Louisiana", ME: "Maine", MD: "Maryland", MA: "Massachusetts", MI: "Michigan", MN: "Minnesota", MS: "Mississippi", MO: "Missouri", MT: "Montana", NE: "Nebraska", NV: "Nevada", NH: "New Hampshire", NJ: "New Jersey", NM: "New Mexico", NY: "New York", NC: "North Carolina", ND: "North Dakota", OH: "Ohio", OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania", RI: "Rhode Island", SC: "South Carolina", SD: "South Dakota", TN: "Tennessee", TX: "Texas", UT: "Utah", VT: "Vermont", VA: "Virginia", WA: "Washington", WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming" };

/** A jurisdiction path (EU/ES, US/US-AR, JP) as a place a person reads, in their language. */
export function placeLabel(code: string, locale: string): string {
  const region = (cc: string) => {
    try { return new Intl.DisplayNames([locale], { type: "region" }).of(cc === "EL" ? "GR" : cc) ?? cc; } catch { return cc; }
  };
  const parts = code.split("/");
  if (parts[0] === "US") return parts[1]?.startsWith("US-") ? `${US_STATES[parts[1].slice(3)] ?? parts[1].slice(3)}, ${region("US")}` : region("US");
  if (parts[0] === "EU" && parts[1]) return parts.length > 2 ? `${parts[parts.length - 1]} · ${region(parts[1])}` : region(parts[1]);
  return /^[A-Z]{2}$/.test(parts[0]) && parts.length === 1 ? region(parts[0]) : code;
}

/** Activity labels by stable code; the backend label stays the fallback. */
export function activityLabel(code: string, fallback: string, t: Translate): string {
  switch (code) {
    case "isic-A": return t("Agricultura, silvicultura y pesca", "Agriculture, forestry and fishing");
    case "isic-B": return t("Minería y extracción", "Mining and quarrying");
    case "isic-C": return t("Industria manufacturera", "Manufacturing");
    case "isic-D": return t("Electricidad, gas y climatización", "Electricity, gas, steam and air conditioning");
    case "isic-E": return t("Agua, saneamiento y residuos", "Water supply, sewerage and waste management");
    case "isic-F": return t("Construcción", "Construction");
    case "isic-G": return t("Comercio y reparación de vehículos", "Wholesale and retail trade; vehicle repair");
    case "isic-H": return t("Transporte y almacenamiento", "Transportation and storage");
    case "isic-I": return t("Hostelería y restauración", "Accommodation and food service");
    case "isic-J": return t("Información y comunicaciones", "Information and communication");
    case "isic-K": return t("Finanzas y seguros", "Financial and insurance activities");
    case "isic-L": return t("Actividades inmobiliarias", "Real estate activities");
    case "isic-M": return t("Actividades profesionales, científicas y técnicas", "Professional, scientific and technical activities");
    case "isic-N": return t("Servicios administrativos y de apoyo", "Administrative and support services");
    case "isic-O": return t("Administración pública y defensa", "Public administration and defence");
    case "isic-P": return t("Educación", "Education");
    case "isic-Q": return t("Sanidad y servicios sociales", "Human health and social work");
    case "isic-R": return t("Artes, ocio y entretenimiento", "Arts, entertainment and recreation");
    case "isic-S": return t("Otros servicios", "Other service activities");
    case "solar-pv-installation": return t("Instalación solar fotovoltaica", "Solar photovoltaic installation");
    case "electrical-installation": return t("Instalaciones eléctricas", "Electrical installation work");
    case "industrial-hvac": return t("Climatización industrial", "Industrial HVAC installation and maintenance");
    case "industrial-refrigeration": return t("Refrigeración industrial", "Industrial refrigeration installation and maintenance");
    case "consumer-mobile-app": return t("App móvil para consumidores", "Consumer mobile ordering app");
    default: return fallback;
  }
}

/** FINDING and WHY IT MATTERS for one discovery. Fixed copy per code: never generated. */
export function discoveryCopy(d: Discovery, t: Translate, locale = "en"): { finding: string; why: string } {
  const title = String(d.detail.title ?? d.statement);
  if (d.kind === "ACTIVITY") return { finding: `${t("Actividad probable", "Likely activity")}: ${activityLabel(d.code, d.statement, t)}`, why: t("Orienta dónde buscar demanda. Es una hipótesis con su cita, no una capacidad verificada.", "It directs where to look for demand. It is a hypothesis with its quote, not a verified capability.") };
  if (d.kind === "DEMAND") return { finding: `${t("Demanda pública potencial", "Potential public demand")}: ${title}`, why: t("Coincide por clasificación y lugar. No es un cliente, una invitación ni una relación.", "It matches by classification and place. It is not a customer, an invitation or a relationship.") };
  if (d.kind === "DECLARED_LOCATION") return d.code === "LOCATION_STATED_IN_TEXT"
    ? { finding: `${t("Ubicación mencionada en su web", "Location mentioned on its website")}: ${placeLabel(d.statement, locale)}`, why: t("Indica dónde mirar primero. No define dónde opera ni todo su mercado.", "It shows where to look first. It does not define where it operates or its whole market.") }
    : { finding: `${t("Dirección que declara", "Address it declares")}: ${d.statement}`, why: t("Indica dónde mirar primero. No define dónde opera ni todo su mercado.", "It shows where to look first. It does not define where it operates or its whole market.") };
  if (d.kind === "DECLARED_SERVICE_AREA") return { finding: `${t("Zona de servicio que declara", "Service area it declares")}: ${d.statement}`, why: t("Es lo que la organización dice de sí misma; no se ha verificado.", "It is what the organization says about itself; it has not been verified.") };
  if (d.kind === "LANGUAGES") return { finding: `${t("Idiomas publicados", "Published languages")}: ${d.statement}`, why: t("Muestra en qué idiomas se presenta; no prueba en qué mercados vende.", "It shows the languages it presents itself in; it does not prove where it sells.") };
  if (d.kind === "IDENTITY_HINT") return { finding: `${t("Su web declara", "Its website declares")}: ${d.statement}`, why: t("Es una pista de identidad. Solo un registro puede verificarla.", "It is an identity hint. Only a registry can verify it.") };
  if (d.kind === "PUBLIC_PRESENCE") return { finding: `${t("Web pública observada", "Public website observed")}: ${d.statement}`, why: t("Es la fuente de lo que la organización declara sobre sí misma.", "It is the source of what the organization declares about itself.") };
  if (d.kind === "SEARCH_VISIBILITY") return { finding: `${t("Visibilidad en buscadores medida", "Search visibility measured")}: ${d.statement}`, why: t("Es lo observado para una consulta y unas condiciones concretas. No es una posición general ni explica el motivo.", "It is what was observed for a given query and conditions. It is not a general ranking and does not explain why.") };
  if (d.kind === "GENERATIVE_VISIBILITY") return { finding: `${t("Aparición en respuestas de IA medida", "AI answer appearance measured")}: ${d.statement}`, why: t("Mencionar no es citar, y citar no es recomendar. Es una medición con sus condiciones, no una conclusión sobre el negocio.", "A mention is not a citation, and a citation is not an endorsement. It is a measurement with its conditions, not a conclusion about the business.") };
  if (d.kind === "WEB_REPRESENTATION") return { finding: t("Representación web medida", "Web representation measured"), why: t("Comprobaciones de su propia web, con instrumento y condiciones. No es una posición en buscadores.", "Checks of its own website, with instrument and conditions. It is not a search ranking.") };
  if (d.kind === "REPRESENTATION_GAP") return d.code === "HOMEPAGE_NOINDEX"
    ? { finding: t("Su página principal pide no aparecer en buscadores.", "Its homepage asks search engines not to index it."), why: t("Los buscadores podrían no representar la web mientras siga así. No mide posiciones.", "Search engines may not represent the site while it stays so. It does not measure rankings.") }
    : { finding: t("En las páginas leídas, su oferta aparece en el texto pero no en datos estructurados.", "On the pages read, its offer appears in the text but not as structured data."), why: t("Las superficies que leen datos estructurados podrían no relacionarla con lo que ofrece. Es una brecha posible, no una causa medida.", "Surfaces that read structured data may not connect it with what it offers. It is a possible gap, not a measured cause.") };
  if (d.code.startsWith("NO_GOVERNED_DEMAND_SOURCE:")) return { finding: `${t("Aún no hay una fuente de demanda gobernada para", "No governed demand source yet for")} ${placeLabel(String(d.detail.jurisdiction ?? ""), locale)}`, why: t("Falta de fuente no es falta de mercado ni de demanda.", "No source is not no market and not no demand.") };
  switch (d.code) {
    case "IDENTITY_NOT_VERIFIED": return { finding: t("Identidad legal todavía no verificada.", "Legal identity not verified yet."), why: t("Lo que ves describe la web pública, no una organización verificada por un registro.", "What you see describes the public website, not an organization verified by a registry.") };
    case "WEBSITE_LINK_NOT_REGISTRY_VERIFIED": return { finding: t("Ningún registro vincula esta web a la organización.", "No registry links this website to the organization."), why: t("La web la indicaste tú; la tratamos como atención, no como hecho.", "You indicated this website; we treat it as attention, not as fact.") };
    case "ACTIVITY_NOT_ESTABLISHED": return { finding: t("Qué ofrece no está establecido todavía.", "What it offers is not established yet."), why: t("No buscamos demanda sobre una suposición.", "We do not search for demand on an assumption.") };
    case "LOCATION_NOT_DECLARED": return { finding: t("No hemos establecido su ubicación ni su ámbito geográfico de servicio.", "Its location and geographic service scope have not been established."), why: t("No elegimos un mercado por defecto.", "We do not pick a default market.") };
    case "DEMAND_NOT_ROUTABLE": case "NO_ROUTABLE_DEMAND_QUESTION": return { finding: t("Ninguna fuente de demanda gobernada aplica todavía a esta actividad y lugar.", "No governed demand source applies yet to this activity and place."), why: t("No es una ausencia de oportunidades.", "It is not an absence of opportunities.") };
    case "NO_RELEVANT_DEMAND_FOUND": return { finding: t("Las fuentes consultadas no tienen ahora demanda que coincida.", "The sources searched have no matching demand right now."), why: t("Sin resultado no es sin oportunidad; volveremos a observar.", "No result is not no opportunity; we will observe again.") };
    case "NOT_AN_OPERATING_BUSINESS_SITE": return { finding: t("La página no parece la web de una actividad en marcha.", "The page does not read as an operating business website."), why: t("Es un juicio no autoritativo sobre la página, no sobre la organización.", "It is a non-authoritative judgment about the page, not about the organization.") };
    case "NO_PUBLIC_WEBSITE": return { finding: t("No hay una web pública que observar.", "There is no public website to observe."), why: t("Añade su web para empezar la observación.", "Add its website to start observing.") };
    case "WEBSITE_OF_ANOTHER_ORGANIZATION": return { finding: t("Un registro asocia esta web a otra organización.", "A registry links this website to another organization."), why: t("No la observamos como si fuera de esta organización.", "We do not observe it as if it belonged to this organization.") };
    default: return { finding: t("La web no se pudo observar con sus reglas de acceso.", "The website could not be observed under its access rules."), why: t("Respetamos robots.txt y nuestros límites; no concluimos nada de ello.", "We respect robots.txt and our limits; we conclude nothing from that.") };
  }
}

function epistemicCopy(state: Discovery["epistemicState"], t: Translate): string {
  if (state === "OBSERVED") return t("Observado", "Observed");
  if (state === "DECLARED") return t("Declarado por la organización", "Declared by the organization");
  if (state === "POTENTIAL") return t("Potencial", "Potential");
  return t("Desconocido", "Unknown");
}

function checkLabel(key: string, t: Translate): string {
  switch (key) {
    case "robotsTxtPublished": return t("robots.txt publicado", "robots.txt published");
    case "sitemapsDeclared": return t("Sitemaps declarados", "Sitemaps declared");
    case "canonical": return t("URL canónica", "Canonical URL");
    case "homepageNoindex": return t("Portada con noindex", "Homepage noindex");
    case "titlePresent": return t("Título presente", "Title present");
    case "descriptionPresent": return t("Descripción presente", "Description present");
    case "schemaTypes": return t("Tipos schema.org", "schema.org types");
    case "organizationDeclared": return t("Organización declarada en datos estructurados", "Organization declared in structured data");
    case "offerDeclared": return t("Oferta declarada en datos estructurados", "Offer declared in structured data");
    case "alternateLanguages": return t("Versiones en otros idiomas", "Alternate language versions");
    default: return key;
  }
}

function sourceName(url: string): string {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; }
}

/** The persisted basis of one discovery, as rows. Never a regenerated narrative. A
 * provider's confidence is not shown: it is not a probability of truth (ADR-0047) and a
 * percentage would be false precision (MASTER); it stays in authorized traces. */
export function basisRows(d: Discovery, t: Translate, locale: string): Array<[string, string]> {
  const rows: Array<[string, string]> = [];
  const detail = d.detail;
  if (d.excerpt) rows.push([detail.method === "SEMANTIC_JUDGMENT" ? t("Extracto de la fuente", "Source excerpt") : t("Cita exacta", "Exact quote"), `“${d.excerpt}”`]);
  if (typeof detail.method === "string") rows.push([t("Método", "Method"), detail.method]);
  if (typeof detail.instrument === "string") rows.push([t("Instrumento", "Instrument"), detail.instrument]);
  if (typeof detail.model === "string") rows.push([t("Evaluador", "Evaluator"), `${detail.model} · ${t("juicio no autoritativo, no es una probabilidad de verdad", "non-authoritative judgment, not a probability of truth")}`]);
  if (Array.isArray(detail.routingCodes) && detail.routingCodes.length) rows.push([t("Códigos de búsqueda", "Search codes"), detail.routingCodes.join(", ")]);
  if (Array.isArray(detail.codes) && detail.codes.length) rows.push([t("Códigos que coinciden", "Matching codes"), detail.codes.join(", ")]);
  if (typeof detail.market === "string") rows.push([t("Lugar buscado", "Place searched"), placeLabel(detail.market, locale)]);
  if (typeof detail.source === "string") rows.push([t("Fuente", "Source"), detail.source]);
  if (typeof detail.buyer === "string") rows.push([t("Comprador", "Buyer"), detail.buyer]);
  if (typeof detail.deadline === "string") rows.push([t("Plazo", "Deadline"), detail.deadline]);
  if (detail.checks && typeof detail.checks === "object") for (const [key, value] of Object.entries(detail.checks as Record<string, unknown>)) rows.push([checkLabel(key, t), Array.isArray(value) ? value.join(", ") || "—" : value === true ? t("Sí", "Yes") : value === false ? t("No", "No") : String(value ?? "—")]);
  if (typeof detail.limitation === "string") rows.push([t("Límite", "Limitation"), detail.limitation]);
  if (d.observedAt) rows.push([t("Observado el", "Observed on"), d.observedAt.slice(0, 10)]);
  return rows;
}

function Basis({ d }: { d: Discovery }) {
  const { t, locale } = useLocale();
  const rows = basisRows(d, t, locale);
  return <details className="fo-basis"><summary>{t("Cómo lo sabe AXIGNAL", "Show me how AXIGNAL knows")}</summary>
    {rows.length ? <dl>{rows.map(([label, value]) => <div key={label + value}><dt>{label}</dt><dd>{value}</dd></div>)}</dl> : <p>{t("Esta afirmación no tiene más base que su estado.", "This statement has no basis beyond its state.")}</p>}
  </details>;
}

function Finding({ d }: { d: Discovery }) {
  const { t, locale } = useLocale();
  const copy = discoveryCopy(d, t, locale);
  const link = useEvidenceLink().href(d.sourceUrl);
  return <article className={`fo-finding fo-${d.epistemicState.toLowerCase()}`}>
    <h4>{copy.finding}</h4>
    <p className="fo-why">{copy.why}</p>
    <p className="fo-meta"><span className="fo-state">{epistemicCopy(d.epistemicState, t)}</span>
      {link && <a href={link} target="_blank" rel="noopener noreferrer">{sourceName(link)}<ExternalLink size={14} aria-hidden="true"/><span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a>}
      {d.observedAt && <span>{t("observado", "observed")} {d.observedAt.slice(0, 10)}</span>}</p>
    <Basis d={d}/>
  </article>;
}

const ORDER: Discovery["kind"][] = ["ACTIVITY", "DEMAND", "DECLARED_LOCATION", "DECLARED_SERVICE_AREA", "LANGUAGES", "IDENTITY_HINT", "PUBLIC_PRESENCE", "WEB_REPRESENTATION"];

export function FirstObservationView({ observation }: { observation: FirstObservation }) {
  const { t } = useLocale();
  const findings = ORDER.flatMap(kind => observation.discoveries.filter(d => d.kind === kind));
  const gaps = observation.discoveries.filter(d => d.kind === "REPRESENTATION_GAP");
  const unknowns = observation.discoveries.filter(d => d.kind === "SIGNIFICANT_UNKNOWN");
  return <section className="fo-view" aria-labelledby="first-observation-title">
    <span className="eyebrow">{t("Primera observación", "First observation")}</span>
    <h3 id="first-observation-title">{observationStateCopy(observation.state, t)}</h3>
    <p className="fo-authority">{t("Lectura operativa con sus fuentes. No es verdad canónica: lo potencial sigue siendo potencial.", "Operational reading with its sources. It is not canonical truth: what is potential stays potential.")}</p>
    {observation.publicUnderstanding && <PublicUnderstandingView report={observation.publicUnderstanding}/>}
    {findings.length > 0 && <div className="fo-group"><h4 className="fo-group-title">{t("Lo que AXIGNAL ha encontrado", "What AXIGNAL found")}</h4>{findings.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
    {gaps.length > 0 && <div className="fo-group"><h4 className="fo-group-title">{t("Brechas posibles", "Possible gaps")}</h4>{gaps.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
    {unknowns.length > 0 && <div className="fo-group"><h4 className="fo-group-title">{t("Lo que todavía no sabemos", "What we do not know yet")}</h4>{unknowns.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
  </section>;
}
