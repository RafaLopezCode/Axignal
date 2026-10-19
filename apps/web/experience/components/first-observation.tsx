"use client";

import { industryName } from "@/lib/industries";
import { contractScaleRows } from "@/lib/contract-scale";
import { ExternalLink } from "lucide-react";
import { PublicUnderstandingView } from "./public-understanding";
import { useLocale } from "@/lib/locale";
import { useEvidenceLink } from "./evidence-link-context";
import { type Discovery, type FirstObservation } from "@/lib/subscriber-contracts";
import { auditCopy, auditImpact, auditSection, auditStatus } from "@/lib/representation-audit";

type Translate = (es: string, en: string) => string;

/** Subscriber-facing state of a First Observation: derived from what actually ran. */
export function observationStateCopy(state: string, t: Translate): string {
  switch (state) {
    case "QUEUED": return t("Observación en cola. Se hace por turnos con un límite diario; puedes seguir navegando.", "Observation queued. It runs in turns within a daily limit; you can keep browsing.");
    case "OBSERVING_PUBLIC_PRESENCE": return t("Observando su presencia pública…", "Observing its public presence…");
    case "FIRST_PROOF_READY": return t("Primera observación lista, con sus evidencias.", "First observation ready, with its evidence.");
    case "NOT_ENOUGH_CAPABILITY_EVIDENCE": return t("AXIGNAL todavía no ha podido clasificar su actividad con evidencia suficiente. No la suponemos.", "AXIGNAL has not yet been able to classify its activity with enough evidence. We do not assume it.");
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
    case "legal-services": return t("Servicios jurídicos", "Legal services");
    case "accounting-tax": return t("Contabilidad, auditoría y asesoría fiscal", "Accounting, audit and tax advisory");
    case "management-consulting": return t("Consultoría de gestión y negocio", "Management and business consulting");
    case "market-research": return t("Estudios de mercado e inteligencia económica", "Market research and economic intelligence");
    case "software-development": return t("Desarrollo de software", "Software development");
    case "business-software": return t("Software de gestión empresarial", "Business management software");
    case "it-services": return t("Servicios y soporte informático", "IT services and support");
    case "cybersecurity": return t("Ciberseguridad", "Cybersecurity");
    case "telecommunications": return t("Telecomunicaciones y conectividad", "Telecommunications and connectivity");
    case "engineering-services": return t("Servicios de ingeniería", "Engineering services");
    case "architecture": return t("Servicios de arquitectura", "Architectural services");
    case "building-construction": return t("Construcción de edificios y obra civil", "Building and civil construction");
    case "formwork-scaffolding": return t("Encofrados y andamios", "Formwork and scaffolding");
    case "ventilation-systems": return t("Sistemas de ventilación", "Ventilation systems");
    case "automotive-components": return t("Fabricación de componentes de automoción", "Automotive components manufacturing");
    case "metal-fabrication": return t("Estructuras metálicas y mecanizado", "Metal fabrication and machining");
    case "food-retail": return t("Distribución alimentaria (supermercados)", "Food retail (supermarkets)");
    case "food-manufacturing": return t("Fabricación de alimentos y bebidas", "Food and beverage manufacturing");
    case "catering": return t("Catering y restauración colectiva", "Catering and contract food services");
    case "hospitality": return t("Alojamiento hotelero", "Hotel accommodation");
    case "cleaning-services": return t("Servicios de limpieza", "Cleaning services");
    case "security-guarding": return t("Seguridad privada y vigilancia", "Private security and guarding");
    case "security-systems": return t("Sistemas de seguridad y videovigilancia", "Security and surveillance systems");
    case "facility-maintenance": return t("Gestión y mantenimiento de instalaciones", "Facility management and maintenance");
    case "waste-management": return t("Gestión de residuos y reciclaje", "Waste management and recycling");
    case "water-treatment": return t("Tratamiento de aguas y depuración", "Water and wastewater treatment");
    case "freight-logistics": return t("Transporte de mercancías y logística", "Freight transport and logistics");
    case "courier-parcel": return t("Mensajería y paquetería", "Courier and parcel delivery");
    case "energy-supply": return t("Suministro de electricidad y gas", "Electricity and gas supply");
    case "medical-devices": return t("Productos y equipos sanitarios", "Medical devices and equipment");
    case "pharmaceuticals": return t("Productos farmacéuticos", "Pharmaceutical products");
    case "healthcare-services": return t("Servicios sanitarios", "Healthcare services");
    case "training": return t("Formación para empresas", "Training and education for companies");
    case "marketing-advertising": return t("Marketing y publicidad", "Marketing and advertising");
    case "web-design": return t("Diseño y desarrollo web", "Web design and development");
    case "translation": return t("Traducción e interpretación", "Translation and interpreting");
    case "recruitment-staffing": return t("Selección de personal y trabajo temporal", "Recruitment and staffing");
    case "insurance": return t("Seguros", "Insurance");
    case "real-estate": return t("Servicios inmobiliarios", "Real estate services");
    case "printing": return t("Servicios de impresión", "Printing services");
    case "events": return t("Organización de eventos", "Event organisation");
    case "furniture": return t("Fabricación y suministro de mobiliario", "Furniture manufacturing and supply");
    case "workwear": return t("Ropa laboral y uniformes", "Workwear and uniforms");
    case "laboratory-testing": return t("Ensayos de laboratorio e inspección", "Laboratory testing and inspection");
    case "agriculture": return t("Producción agrícola", "Agricultural production");
    default: return fallback;
  }
}

/** FINDING and WHY IT MATTERS for one discovery. Fixed copy per code: never generated. */
export function discoveryCopy(d: Discovery, t: Translate, locale = "en"): { finding: string; why: string } {
  const title = String(d.detail.title ?? d.statement);
  if (d.kind === "IDENTITY_HINT" && d.code === "IDENTITY_CORROBORATED") {
    const anchors = Array.isArray(d.detail.anchors) ? d.detail.anchors.length : 0;
    return { finding: t("Identidad corroborada por {n} fuentes independientes: {name}", "Identity corroborated by {n} independent sources: {name}").replace("{n}", String(anchors)).replace("{name}", d.statement),
      why: t("Wikidata (por su web oficial), el registro oficial y su LEI apuntan a la misma entidad legal. Es una coincidencia de fuentes: un registro aún no ha admitido la identidad.", "Wikidata (through its official website), the official register and its LEI point to the same legal entity. An agreement of sources: a registry has not admitted the identity yet.") };
  }
  if (d.kind === "ACTIVITY" && d.code === "STATED_INDUSTRY") return { finding: `${t("Sector declarado", "Stated industry")}: ${d.statement}`,
    why: t("Según Wikidata, para el elemento identificado por su web oficial. Orienta la demanda y el contexto; no es una capacidad verificada.", "According to Wikidata, for the item identified through its official website. It directs demand and context; it is not a verified capability.") };
  if (d.kind === "ACTIVITY" && d.code === "REGISTERED_ACTIVITY") return { finding: `${t("Actividad registrada", "Registered activity")}: ${d.statement}`,
    why: t("Según {register}: es la clasificación con la que se registró; puede no reflejar todo lo que ofrece hoy.", "According to {register}: the classification it registered under; it may not reflect everything it offers today.").replace("{register}", String(d.detail.source ?? "")) };
  if (d.kind === "ACTIVITY") return { finding: `${t("Actividad probable", "Likely activity")}: ${activityLabel(d.code, d.statement, t)}`, why: t("Orienta dónde buscar demanda. Es una hipótesis con su cita, no una capacidad verificada.", "It directs where to look for demand. It is a hypothesis with its quote, not a verified capability.") };
  if (d.kind === "MENTION" && d.code === "WIKIPEDIA_NOTORIETY") {
    const views = typeof d.detail.views === "number" ? d.detail.views.toLocaleString(locale) : d.statement;
    const langs = Array.isArray(d.detail.languages) ? d.detail.languages.length : 0;
    const trend = typeof d.detail.trend === "number" ? d.detail.trend : null;
    const moved = trend === null ? "" : " " + (trend >= 0
      ? t("Últimos 3 meses: +{p} % frente a los 3 anteriores.", "Last 3 months: +{p}% against the 3 before.")
      : t("Últimos 3 meses: {p} % frente a los 3 anteriores.", "Last 3 months: {p}% against the 3 before.")).replace("{p}", String(Math.round(trend * 100)));
    return { finding: t("Notoriedad pública: {v} visitas a su artículo de Wikipedia en {m} ({n} idiomas)", "Public notoriety: {v} views of its Wikipedia article in {m} ({n} languages)")
        .replace("{v}", views).replace("{m}", String(d.detail.month ?? "")).replace("{n}", String(langs)),
      why: t("Mide atención pública real, no opinión. Identificado por su web oficial en Wikidata.", "It measures real public attention, not opinion. Identified through its official website in Wikidata.") + moved };
  }
  if (d.kind === "MENTION") {
    const outlet = typeof d.detail.outlet === "string" ? d.detail.outlet : "";
    const dated = typeof d.detail.publishedAt === "string" ? ` (${d.detail.publishedAt.slice(0, 10)})` : "";
    const linked = d.detail.linksToItsWebsite === true
      ? " " + t("La página enlaza a su web.", "The page links to its website.") : "";
    if (d.code === "REVIEW_PAGE") return { finding: `${t("Página de opiniones", "Reviews page")} · ${outlet}: ${d.statement}${dated}`,
      why: t("AXIGNAL ha leído la página y nombra a la organización. Que trate de ella no está verificado del todo; las opiniones son de terceros y no se puntúan.", "AXIGNAL read the page and it names the organization. That it is about it is not fully verified; the reviews are third-party and are not scored.") + linked };
    if (d.code === "WEB_MENTION") return { finding: `${t("La nombran en la web", "Named on the web")} · ${outlet}: ${d.statement}${dated}`,
      why: t("Un buscador propuso la página y AXIGNAL la ha leído: su texto nombra a la organización. Mencionar no es recomendar.", "A search index proposed the page and AXIGNAL read it: its text names the organization. A mention is not an endorsement.") + linked };
    if (d.code === "PRESS_RELEASE") return { finding: `${t("Nota de prensa distribuida", "Distributed press release")} · ${outlet}: ${d.statement}`, why: t("Una nota que una organización distribuye sobre sí misma: es su voz, no cobertura independiente.", "A release an organization distributes about itself: its own voice, not independent coverage.") };
    return d.code === "OWN_PUBLICATION"
      ? { finding: `${t("Publicado por la propia organización", "Published by the organization itself")}: ${d.statement}`, why: t("Es su propia voz, no una mención de terceros.", "It is its own voice, not a third-party mention.") }
      : { finding: `${t("Mención en prensa", "Press mention")} · ${outlet}: ${d.statement}`, why: t("El titular nombra a la organización. Que trate de ella no está verificado, y mencionar no es recomendar.", "The headline names the organization. That it is about it is not verified, and a mention is not an endorsement.") };
  }
  if (d.kind === "RELATIONSHIP" && d.code === "TECHNOLOGY_SUPPLIER_OBSERVED") return {
    finding: `${t("Proveedor tecnológico", "Technology supplier")}: ${d.statement} (${techCategory(String(d.detail.category ?? ""), t)})`,
    why: t("Su web carga tecnología de este proveedor: es un proveedor observado. El contrato, el plan o el gasto no están establecidos.", "Its website loads this vendor's technology: an observed supplier. The contract, plan or spend is not established.") };
  if (d.kind === "RELATIONSHIP" && (d.code === "CLIENT_DECLARED" || d.code === "PARTNER_DECLARED")) return {
    finding: `${d.code === "CLIENT_DECLARED" ? t("Cliente que muestra", "Client it shows") : t("Partner que muestra", "Partner it shows")}: ${d.statement}`,
    why: t("Lo muestra su propia web bajo «{heading}». Es su declaración: la otra parte no lo ha confirmado.", "Its own website shows it under “{heading}”. Its own claim: the other party has not confirmed it.").replace("{heading}", String(d.detail.heading ?? "")) };
  // Spec 097: what it sells, in its own catalog's words.
  if (d.kind === "OFFER") return {
    finding: `${t("Lo que vende, según su catálogo", "What it sells, according to its catalog")}: ${Array.isArray(d.detail.categories) ? d.detail.categories.slice(0, 8).map(String).join(", ") : d.statement}`,
    why: d.detail.basis === "PRODUCT_TYPES"
      ? t("Son los tipos de producto de su catálogo público, ordenados por número de productos. Lo declara su tienda: es lo que ofrece, no lo que más vende.", "These are the product types in its public catalog, ordered by number of products. Its shop declares them: what it offers, not what it sells most.")
      : t("Son las categorías que enlaza su propia web en su catálogo. Lo declara ella: es lo que ofrece, no lo que más vende.", "These are the categories its own website links in its catalog. It declares them: what it offers, not what it sells most.") };
  if (d.kind === "CREDENTIAL") return {
    finding: `${t("Certificación que declara", "Certification it claims")}: ${d.statement}`,
    why: t("Lo afirma en su web; no se ha comprobado en el registro del emisor.", "Claimed on its website; the issuer's register has not been checked.") };
  // Spec 096: what it publishes on its own channel, and how often.
  if (d.kind === "OPERATING_SIGNAL" && d.code === "WEBSITE_HISTORY") {
    const first = String(d.detail.firstCapture ?? "").slice(0, 4);
    const recent = typeof d.detail.homeVersionsLast12Months === "number" ? d.detail.homeVersionsLast12Months : null;
    const total = Number(d.detail.homeVersions ?? 0);
    const changes = recent === null
      ? t("sin capturas válidas recientes de su inicio (puede redirigir), sus cambios del último año no se conocen", "with no recent valid captures of its home page (it may redirect), its changes over the last year are unknown")
      : t("su página de inicio cambió {n} veces en los últimos 12 meses", "its home page changed {n} times in the last 12 months").replace("{n}", String(recent));
    return { finding: t("Su dominio tiene capturas en el Internet Archive desde {y}: {changes} ({t} versiones en total)", "Its domain has Internet Archive captures since {y}: {changes} ({t} versions in all)")
        .replace("{y}", first).replace("{changes}", changes).replace("{t}", String(total)),
      why: t("Según las capturas mensuales del Internet Archive. La primera captura fecha el dominio, que pudo tener otro dueño antes; no es la fecha de fundación. Un cambio puede ser una edición pequeña.", "From the Internet Archive's monthly captures. The first capture dates the domain, which may have had an earlier owner; it is not the founding date. A change may be a small edit.") };
  }
  if (d.kind === "OPERATING_SIGNAL" && d.code === "WEBSITE_NOT_ARCHIVED") return {
    finding: t("El Internet Archive no tiene capturas de su web", "The Internet Archive holds no captures of its website"),
    why: t("Suele indicar una web reciente o poco enlazada. No significa que no exista: el archivo muestrea la web.", "It usually means a recent or little-linked website. It does not mean it does not exist: the archive samples the web.") };
  if (d.kind === "OPERATING_SIGNAL" && d.code === "PUBLISHING_CADENCE") {
    const n90 = Number(d.detail.last90Days ?? 0), n365 = Number(d.detail.last365Days ?? 0);
    const last = typeof d.detail.lastPublishedAt === "string" ? d.detail.lastPublishedAt.slice(0, 10) : null;
    return { finding: n365 === 0
        ? t("Su canal de noticias está parado: última publicación {date}", "Its news channel is quiet: last post {date}").replace("{date}", last ?? "—")
        : t("Publica en su propio canal: {n} publicaciones en 90 días (la última, {date})", "It publishes on its own channel: {n} posts in 90 days (latest {date})").replace("{n}", String(n90)).replace("{date}", last ?? "—"),
      why: t("Leído del canal de noticias que declara su web: qué cuenta y con qué ritmo. Un canal parado no significa que la organización esté parada.", "Read from the news feed its website declares: what it says and at what pace. A quiet channel does not mean the organization is idle.") };
  }
  if (d.kind === "OPERATING_SIGNAL" && d.code === "OPEN_POSITIONS") {
    const fns = d.detail.functions && typeof d.detail.functions === "object" ? Object.entries(d.detail.functions as Record<string, number>).filter(([f]) => f !== "OTHER").slice(0, 4).map(([f, n]) => `${f} (${n})`) : [];
    const where = d.detail.countries && typeof d.detail.countries === "object" ? Object.keys(d.detail.countries as Record<string, number>).slice(0, 6).map(c => placeLabel(c, locale)) : [];
    return { finding: t("Contratando: {n} vacantes abiertas", "Hiring: {n} open positions").replace("{n}", d.statement)
        + (fns.length ? ` · ${fns.join(", ")}` : "") + (where.length ? ` · ${where.join(", ")}` : ""),
      why: t("Leídas en su portal público de empleo ({v}). Una vacante es intención de contratar, no una contratación; muestra dónde y en qué está creciendo.", "Read from its public job board ({v}). A posting is an intention to hire, not a hire; it shows where and in what it is growing.").replace("{v}", String(d.detail.vendor ?? "")) };
  }
  if (d.kind === "DECLARED_LOCATION" && d.code === "HIRING_IN_COUNTRIES") return {
    finding: `${t("Contrata en", "Hiring in")}: ${Object.keys((d.detail.countries ?? {}) as Record<string, number>).map(c => placeLabel(c, locale)).join(", ")}`,
    why: t("Países de sus vacantes abiertas: presencia operativa o intención de tenerla allí.", "Countries of its open positions: an operating presence, or an intention to have one there.") };
  if (d.kind === "OPERATING_SIGNAL" && d.code === "JOB_POSTINGS_PUBLISHED") return {
    finding: t("Publica {n} ofertas de empleo", "It publishes {n} job posting(s)").replace("{n}", d.statement) + (Array.isArray(d.detail.titles) && d.detail.titles.length ? `: ${d.detail.titles.slice(0, 3).map(String).join(", ")}` : ""),
    why: t("Contratar es actividad: indica dónde está creciendo. Son ofertas que publica ella misma.", "Hiring is activity: it shows where it is growing. These are postings it publishes itself.") };
  if (d.kind === "OPERATING_SIGNAL") return {
    finding: Array.isArray(d.detail.hiringVendors) && d.detail.hiringVendors.length
      ? `${t("Canal de empleo", "Hiring channel")}: ${d.detail.hiringVendors.map(String).join(", ")}`
      : t("Publica una página de empleo", "It publishes a careers page"),
    why: t("Muestra que existe un proceso de selección; no establece vacantes abiertas salvo que las publique.", "It shows a hiring process exists; open positions are not established unless it publishes them.") };
  if (d.kind === "RATING" && d.code === "RATING_SELF_PUBLISHED") return {
    finding: `${t("Valoración que publica sobre sí misma", "Rating it publishes about itself")}: ${d.statement}${typeof d.detail.count === "number" && d.detail.count ? ` (${d.detail.count.toLocaleString(locale)} ${t("opiniones", "reviews")})` : ""}`,
    why: t("Es su propia afirmación en datos estructurados, no una reseña independiente.", "Its own claim in structured data, not an independent review.") };
  if (d.kind === "RATING") return {
    finding: `${t("Perfil de opiniones enlazado", "Linked review profile")}: ${d.statement}`,
    why: t("Remite a sus clientes a esta plataforma para opinar. AXIGNAL no ha leído todavía la valoración allí.", "It sends customers to this platform to review it. AXIGNAL has not read the rating there yet.") };
  if (d.kind === "RELATIONSHIP" && d.code === "GROUP_PARENT") return {
    finding: `${d.detail.role === "ULTIMATE_PARENT" ? t("Matriz última del grupo", "Group's ultimate parent") : t("Matriz directa", "Direct parent")}: ${d.statement}`,
    why: t("Según el registro mundial de entidades (GLEIF). Es estructura societaria registrada, no una opinión.", "According to the global entity registry (GLEIF). It is registered corporate structure, not an opinion.") };
  if (d.kind === "RELATIONSHIP" && d.code === "GROUP_SUBSIDIARIES") {
    const countries = d.detail.countries && typeof d.detail.countries === "object" ? Object.keys(d.detail.countries as Record<string, number>) : [];
    return { finding: t("{n} filiales registradas en {c} países", "{n} subsidiaries registered in {c} countries").replace("{n}", d.statement).replace("{c}", String(countries.length)),
      why: d.epistemicState === "OBSERVED"
        ? t("Del registro mundial de entidades (GLEIF), con su identificador verificado.", "From the global entity registry (GLEIF), with its verified identifier.")
        : t("Del registro mundial de entidades (GLEIF), a partir del identificador que declara su web; la atribución sigue siendo potencial.", "From the global entity registry (GLEIF), using the identifier its website declares; the attribution stays potential.") };
  }
  if (d.kind === "RELATIONSHIP" && d.code === "PUBLIC_CONTRACT_PARTNER") return {
    finding: t("Socio en contratos públicos: {name}", "Partner in public contracts: {name}").replace("{name}", d.statement),
    why: d.detail.how === "SAME_LOT_JOINT_AWARD"
      ? t("Adjudicatario del mismo lote que esta organización. Es una colaboración pasada documentada, no una alianza actual.", "Awarded the same lot as this organization. A documented past collaboration, not a current alliance.")
      : t("Aparece con esta organización en el nombre de una unión temporal de empresas (UTE). Leído del nombre: la colaboración sigue siendo potencial.", "Appears with this organization in the name of a joint venture (UTE). Read from the name: the collaboration stays potential.") };
  if (d.kind === "RELATIONSHIP") {
    const n = Number(d.detail.contracts ?? 0);
    return { finding: t("Cliente público: {buyer} · {n} contratos ganados", "Public client: {buyer} · {n} contracts won").replace("{buyer}", d.statement).replace("{n}", String(n)),
      why: d.epistemicState === "OBSERVED"
        ? t("Adjudicaciones oficiales a su NIF. Es una relación pasada documentada, no una garantía de negocio futuro.", "Official awards to its tax ID. A documented past relationship, not a guarantee of future business.")
        : t("Adjudicaciones a una empresa con su mismo nombre legal; sin NIF confirmado, la atribución sigue siendo potencial.", "Awards to a company with the same legal name; without a confirmed tax ID, the attribution stays potential.") };
  }
  if (d.kind === "COMPETITION") return {
    finding: t("Competidor posible: {name} · {n} contratos en sus mismos códigos", "Possible competitor: {name} · {n} contracts under the same codes").replace("{name}", d.statement).replace("{n}", String(d.detail.contracts ?? 0)),
    why: t("Gana contratos públicos con los mismos códigos de actividad. Que compita con ella es una inferencia, no una clasificación de calidad.", "It wins public contracts under the same activity codes. That it competes with this organization is an inference, not a quality ranking.") };
  if (d.kind === "CONTEXT_SIGNAL" && d.code === "REGULATION") {
    const journal = ({ BOE: "BOE", EUR_LEX: "EUR-Lex", FEDERAL_REGISTER: "Federal Register", LEGISLATION_GOV_UK: "legislation.gov.uk" } as Record<string, string>)[String(d.detail.journal ?? "")] ?? String(d.detail.journal ?? "");
    const published = typeof d.detail.published === "string" ? d.detail.published.slice(0, 10) : "";
    const issuer = typeof d.detail.issuer === "string" && d.detail.issuer ? ` · ${d.detail.issuer}` : "";
    return { finding: `${t("Norma nueva", "New rule")} · ${journal} ${published}: ${d.statement}`,
      why: t("Publicada en el boletín oficial{issuer}. Que concierna a su sector lo ha juzgado un asistente; si le aplica y cómo no está evaluado. No es asesoramiento jurídico.", "Published in the official journal{issuer}. That it concerns its sector was judged by an assistant; whether and how it applies is not assessed. Not legal advice.").replace("{issuer}", issuer) };
  }
  if (d.kind === "CONTEXT_SIGNAL" && d.code === "WEB_SECTOR_SOURCE") {
    const outlet = typeof d.detail.outlet === "string" ? d.detail.outlet : "";
    const dated = typeof d.detail.publishedAt === "string" ? ` (${d.detail.publishedAt.slice(0, 10)})` : "";
    return { finding: `${t("Marco de su actividad", "Framework of its activity")} · ${outlet}: ${d.statement}${dated}`,
      why: t("Página sobre su actividad y las normas que la enmarcan, leída por AXIGNAL. Trata del sector, no de la organización; si le aplica y cómo no está evaluado. No es asesoramiento jurídico.", "A page about its activity and the rules that frame it, read by AXIGNAL. It is about the sector, not the organization; whether and how it applies is not assessed. Not legal advice.") };
  }
  if (d.kind === "CONTEXT_SIGNAL") {
    const outlet = typeof d.detail.outlet === "string" ? d.detail.outlet : "";
    return { finding: `${t("En su sector", "In its sector")} · ${outlet}: ${d.statement}`,
      why: t("Titular reciente sobre su actividad en su país, no sobre la organización. Su relevancia la ha juzgado un asistente: no es un hecho.", "A recent headline about its activity in its country, not about the organization. Its relevance was judged by an assistant: it is not a fact.") };
  }
  if (d.kind === "ECONOMIC_FACT" && d.detail.fact === "sectorMarket") {
    const country = placeLabel(String(d.detail.country ?? ""), locale);
    const money = (meur: unknown) => typeof meur === "number" ? (meur * 1_000_000).toLocaleString(locale, { notation: "compact", style: "currency", currency: "EUR", maximumFractionDigits: 1 }) : "—";
    const count = (n: unknown) => typeof n === "number" ? n.toLocaleString(locale, { maximumFractionDigits: 0 }) : "—";
    const growth = typeof d.detail.employmentGrowthPc === "number" ? d.detail.employmentGrowthPc : null;
    return {
      finding: t("Su sector en {country}: {n} empresas facturan {turnover} y emplean a {persons} personas ({year})", "Its sector in {country}: {n} enterprises turn over {turnover} and employ {persons} people ({year})")
        .replace("{country}", country).replace("{n}", count(d.detail.enterprises)).replace("{turnover}", money(d.detail.turnoverMeur))
        .replace("{persons}", count(d.detail.personsEmployed)).replace("{year}", String(d.detail.year ?? "")),
      why: (growth === null ? "" : t("El empleo del sector varió un {g} % en el último año. ", "Employment in the sector changed by {g}% over the last year. ").replace("{g}", `${growth > 0 ? "+" : ""}${growth.toLocaleString(locale)}`))
        + t("Son datos oficiales del sector, no de la organización: dan escala a sus cifras, o a su ausencia.", "These are official figures for the sector, not for the organization: they give its own figures, or their absence, a scale.") };
  }
  if (d.kind === "ECONOMIC_FACT") {
    const fact = String(d.detail.fact ?? "");
    const labels: Record<string, string> = {
      revenue: t("Ingresos", "Revenue"), netProfit: t("Beneficio neto", "Net profit"), assets: t("Activos totales", "Total assets"),
      employees: t("Empleados", "Employees"), employeesBand: t("Empleados (tramo)", "Employees (band)"),
      sizeCategory: t("Tamaño de empresa", "Company size"), accountsType: t("Tipo de cuentas depositadas", "Type of accounts filed"),
      marketCapitalization: t("Capitalización bursátil", "Market capitalization"), inception: t("Año de fundación", "Founded"),
      stockExchange: t("Cotiza en", "Listed on"), establishments: t("Establecimientos abiertos", "Open establishments"),
      activity: t("Actividad registrada", "Registered activity"), status: t("Estado en el registro", "Register status"),
    };
    const label = labels[fact] ?? t("Sector", "Industry");
    const coded: Record<string, string> = {
      PME: t("Pyme", "SME"), ETI: t("Empresa mediana (ETI)", "Mid-sized company (ETI)"), GE: t("Gran empresa", "Large company"),
      ACTIVE: t("Activa", "Active"), CLOSED: t("Cerrada", "Closed"),
    };
    const raw = d.detail.value;
    const value = typeof raw === "number"
      ? `${raw.toLocaleString(locale, { maximumFractionDigits: 0 })}${typeof d.detail.unit === "string" ? " " + d.detail.unit : ""}`
      : typeof raw === "string" && coded[raw] ? coded[raw]
      : typeof d.detail.label === "string" && d.detail.label ? `${d.detail.label} (${String(raw)})` : d.statement;
    const period = typeof d.detail.period === "string" ? d.detail.period.slice(0, 10) : null;
    const year = fact === "inception" ? "" : period ? ` (${t("ejercicio cerrado el", "year ended")} ${period})` : typeof d.detail.year === "string" ? ` (${d.detail.year})` : "";
    if (d.detail.sourceKind === "OFFICIAL_REGISTER") return { finding: `${label}: ${value}${year}`,
      why: (d.epistemicState === "OBSERVED"
        ? t("Según {register}, registro oficial, para {identifier}, el identificador que la propia organización publica.", "According to {register}, the official register, for {identifier}, the identifier the organization itself publishes.")
        : t("Según {register}, registro oficial, para {identifier}. El nombre registrado no confirma todavía que sea esta organización.", "According to {register}, the official register, for {identifier}. The registered name does not yet confirm it is this organization."))
        .replace("{register}", String(d.detail.source ?? "")).replace("{identifier}", String(d.detail.identifier ?? "")) };
    return { finding: `${label}: ${value}${year}`,
      why: t("Según Wikidata, una fuente comunitaria: no es una cuenta oficial y puede estar desactualizada.", "According to Wikidata, a community source: it is not an official account and may be outdated.") };
  }
  if (d.kind === "CHANGE") {
    const v = (d.detail.values && typeof d.detail.values === "object" ? d.detail.values : {}) as Record<string, unknown>;
    const metric = String(v.metric ?? "");
    const shown = (x: unknown) => Array.isArray(x) ? (x.length ? x.map(String).join(", ") : t("ninguno", "none"))
      : metric === "presence.ai_named_share" || metric === "presence.search_ranked_share" ? `${Math.round(Number(x ?? 0) * 100)} %`
      : metric === "presence.ai_knows_brand" || metric === "activity.hiring_channel" ? (Number(x) ? t("sí", "yes") : t("no", "no"))
      : typeof x === "number" ? x.toLocaleString(locale) : String(x ?? "");
    const added = Array.isArray(v.added) ? v.added.map(String) : [];
    const removed = Array.isArray(v.removed) ? v.removed.map(String) : [];
    const what = added.length || removed.length
      ? [added.length ? `${t("nuevo", "new")}: ${added.join(", ")}` : "", removed.length ? `${t("ya no", "no longer")}: ${removed.join(", ")}` : ""].filter(Boolean).join(" · ")
      : `${shown(v.before)} → ${shown(v.after)}`;
    const direction = String(v.direction ?? "");
    const since = t("Entre el {a} y el {b}.", "Between {a} and {b}.").replace("{a}", String(v.beforeDay ?? "")).replace("{b}", String(v.afterDay ?? ""));
    const reading = direction === "EVOLUTION" ? t("Evoluciona a mejor.", "It is improving.")
      : direction === "REGRESSION" ? t("Retrocede.", "It is regressing.")
      : t("Un cambio observado, sin juicio de mejor o peor.", "An observed change, with no judgement of better or worse.");
    return { finding: `${changeLabel(metric, t)}: ${what}`,
      why: `${reading} ${since} ${t("Compara dos lecturas del mismo instrumento: dice qué cambió, no por qué.", "It compares two readings by the same instrument: it says what changed, not why.")}` };
  }
  if (d.kind === "INXIGHT") {
    const v = (d.detail.values && typeof d.detail.values === "object" ? d.detail.values : {}) as Record<string, unknown>;
    const list = (x: unknown) => Array.isArray(x) ? x.map(String).join(", ") : String(x ?? "");
    const pct = (x: unknown) => String(Math.round(Number(x ?? 0) * 100));
    const rule = String(d.detail.rule ?? "");
    const copy: Record<string, [string, string]> = {
      LOCAL_BUYERS_NEVER_AWARDED: [
        (v.where === "AREA" ? t("{n} organismos públicos de su zona contratan lo que hace ({c} contratos en el periodo observado) y ninguno le ha adjudicado nada.", "{n} public bodies in its area award what it does ({c} contracts in the period held) and none has awarded it a contract.")
          : t("{n} organismos públicos de su país contratan lo que hace ({c} contratos en el periodo observado) y ninguno le ha adjudicado nada.", "{n} public bodies in its country award what it does ({c} contracts in the period held) and none has awarded it a contract."))
          .replace("{n}", String(v.buyers ?? "")).replace("{c}", String(v.contracts ?? "")),
        t("Demanda recurrente cercana que no está captando.", "Recurring demand close by that it is not capturing.")],
      COMPETITORS_WIN_WITH_ITS_BUYERS: [
        (Array.isArray(v.buyers) && v.buyers.length === 1
          ? t("{competitors} ya ganan contratos con {buyers}, que compra su actividad y no le ha adjudicado nada.", "{competitors} already win contracts with {buyers}, a buyer of its activity that has not awarded it.")
          : t("{competitors} ya ganan contratos con {buyers}, que compran su actividad y no le han adjudicado nada.", "{competitors} already win contracts with {buyers}: buyers of its activity that have not awarded it."))
          .replace("{competitors}", list(v.competitors)).replace("{buyers}", list(v.buyers)),
        t("Donde sus competidores ya trabajan, el comprador ya compra esta actividad: la puerta está abierta y se sabe quién la ocupa.", "Where competitors are established, the buyer already buys this activity: the door is open, and who holds it is known.")],
      OPEN_DEMAND_OFFER_NOT_DECLARED: [
        t("{n} licitaciones abiertas encajan con lo que hace, pero su web no declara esa oferta como datos estructurados.", "{n} open public call(s) match what it does, while its website does not declare that offer as structured data.").replace("{n}", String(v.openCalls ?? "")),
        t("Los compradores y buscadores que se apoyan en datos estructurados pueden no conectarla con una demanda que existe ahora.", "Buyers and search surfaces that rely on structured data may not connect it to demand that exists now.")],
      AI_NAMES_COMPETITORS_NOT_IT: [
        t("Al preguntar por su categoría, los asistentes de IA nombran a {competitors} —que ganan contratos en sus códigos— y no a esta organización.", "Asked about its category, AI assistants name {competitors} — companies that win contracts in its codes — and not this organization.").replace("{competitors}", list(v.competitors)),
        t("Se recomienda a sus competidores donde los compradores preguntan hoy; a ella no.", "Competitors are being recommended where buyers now ask; this organization is not.")],
      PUBLIC_CONTRACTS_WEIGHT: [
        Number(v.share ?? 0) >= 1
          ? t("Los contratos públicos adjudicados en el periodo observado superan su última facturación anual declarada (los contratos suelen durar varios años).", "Public contracts awarded to it in the period held exceed its latest reported annual revenue (contracts often span several years).")
          : t("Los contratos públicos adjudicados en el periodo observado suman cerca del {p}% de su última facturación anual declarada.", "Public contracts awarded to it in the period held add up to about {p}% of its latest reported annual revenue.").replace("{p}", pct(v.share)),
        t("Mucho peso de lo público implica exposición a presupuestos y licitaciones. Los contratos pueden durar años: es un orden de magnitud, no una ratio de ventas.", "A high weight of public contracts means exposure to public budgets and tenders. Contract amounts may span several years: an order of magnitude, not a ratio of sales.")],
      PUBLIC_CLIENT_CONCENTRATION: [
        t("{client} concentra el {p}% del valor de los contratos públicos que se le han adjudicado en el periodo observado.", "{client} accounts for {p}% of the public contract value awarded to it in the period held.").replace("{client}", String(v.client ?? "")).replace("{p}", pct(v.share)),
        t("Dependencia de un solo cliente público: una renovación o un cambio de presupuesto ahí pesa mucho.", "Dependence on one public client: a renewal or a budget change there weighs a lot.")],
      SECTOR_IN_NEWS_NOT_IT: [
        t("Su sector está en las noticias ({n} titulares recientes en su país) y la prensa indexada no nombra a esta organización.", "Its sector is in the news ({n} recent headlines in its country) and the indexed press does not name this organization.").replace("{n}", String(v.headlines ?? "")),
        t("Se está hablando de su mercado sin su voz.", "A conversation about its market is happening without its voice.")],
      GROUP_COUNTRIES_DEMAND_UNWATCHED: [
        t("Su grupo tiene sociedades registradas en {countries}, donde no se está vigilando su demanda.", "Its group has registered entities in {countries}, where its demand is not being watched.").replace("{countries}", Array.isArray(v.countries) ? v.countries.map(c => placeLabel(String(c), locale) || String(c)).join(", ") : ""),
        t("Los países donde ya tiene presencia legal son los mercados más baratos de vigilar: dirige allí la demanda para verla.", "Countries where it already has a legal presence are the cheapest markets to watch; direct demand there to see it.")],
      SIZE_IN_SECTOR: [sizeInSectorCopy(v, t, locale),
        t("Da escala a sus cifras: la misma facturación es grande en un sector y pequeña en otro. La media la elevan unas pocas grandes; su tramo de tamaño es la comparación más justa.", "It gives its figures a scale: the same revenue is large in one sector and small in another. A few large firms pull the average up; its size class is the fairer comparison.")],
      FOUNDING_YEAR_SOURCES_DISAGREE: [
        t("El registro oficial la data en {a}; Wikidata, en {b}.", "The official register dates it to {a}; Wikidata to {b}.").replace("{a}", String(v.register ?? "")).replace("{b}", String(v.wikidata ?? "")),
        t("Suele ser una sociedad predecesora o un nuevo registro: conviene saber qué entidad lleva su historia.", "Often a predecessor company or a re-registration; worth knowing which entity carries its history.")],
    };
    const [finding, why] = copy[rule] ?? [d.statement, String(d.detail.why ?? "")];
    const count = Number(d.detail.evidenceCount ?? 0);
    const crossed = count === 1 ? t("Se apoya en 1 evidencia; es una inferencia, no un hecho.", "It rests on 1 piece of evidence; an inference, not a fact.") : t("Cruza {n} evidencias; es una inferencia, no un hecho.", "It crosses {n} pieces of evidence; an inference, not a fact.").replace("{n}", String(count));
    return { finding, why: `${why} ${crossed}` };
  }
  if (d.code === "VALUE_CHAIN_BUYERS" || d.code === "VALUE_CHAIN_SUPPLIERS") {
    const sectors = Array.isArray(d.detail.sectors) ? d.detail.sectors as { code: string; share: number }[] : [];
    const list = sectors.map(x => `${industryName(x.code, locale)} ${Math.round(x.share * 1000) / 10}%`).join(" · ");
    const own = industryName(String(d.detail.industry ?? ""), locale);
    const buyers = d.code === "VALUE_CHAIN_BUYERS";
    return { finding: (buyers ? t("Quién compra a su sector", "Who buys from its sector") : t("A quién compra su sector", "Who its sector buys from")) + `: ${list}`,
      why: t("Estructura de la economía de la UE-27 para «{sector}» (Eurostat, tabla input-output {year}). Es el sector, no la cartera de clientes o proveedores de esta organización.", "Structure of the EU-27 economy for “{sector}” (Eurostat input-output table {year}). It is the sector, not this organization's own clients or suppliers.")
        .replace("{sector}", own).replace("{year}", String(d.detail.year ?? "")) };
  }
  if (d.code === "POTENTIAL_PRIVATE_CUSTOMER" || d.code === "POTENTIAL_SUPPLIER") {
    const sector = industryName(String(d.detail.sector ?? ""), locale);
    const n = String(d.detail.contracts ?? 0);
    return d.code === "POTENTIAL_PRIVATE_CUSTOMER"
      ? { finding: t("Posible cliente: {name} · {sector}", "Possible customer: {name} · {sector}").replace("{name}", d.statement).replace("{sector}", sector),
          why: t("Activa en su zona en un sector que suele comprar al suyo ({n} contratos públicos lo muestran). Es una posibilidad, no una relación.", "Active in its area in a sector that usually buys from its own ({n} public contracts show it). A possibility, not a relationship.").replace("{n}", n) }
      : { finding: t("Posible proveedor: {name} · {sector}", "Possible supplier: {name} · {sector}").replace("{name}", d.statement).replace("{sector}", sector),
          why: t("Activa en su zona en un sector al que el suyo suele comprar ({n} contratos públicos lo muestran). Es una posibilidad, no una relación.", "Active in its area in a sector its own usually buys from ({n} public contracts show it). A possibility, not a relationship.").replace("{n}", n) };
  }
  if (d.kind === "DEMAND" && d.code === "POTENTIAL_BUYER") {
    const signals = Array.isArray(d.detail.signals) ? d.detail.signals as { type: string; via?: string | null }[] : [];
    const kinds = Array.isArray(d.detail.signalTypes) ? d.detail.signalTypes.length : 0;
    const routes = signals.map(s => buyerSignalLabel(s.type, t) + (s.via ? ` (${s.via})` : "")).join(" · ");
    const count = kinds === 1 ? t("1 tipo de señal", "1 kind of signal") : t("{n} tipos de señal independientes", "{n} independent kinds of signal").replace("{n}", String(kinds));
    return { finding: t("Posible comprador: {name}", "Possible buyer: {name}").replace("{name}", d.statement) + ` · ${count}`,
      why: (routes ? `${routes}. ` : "") + t("Cada señal es pública y tiene su fuente y fecha. Es una posibilidad, no un cliente, un lead ni una probabilidad.", "Each signal is public, with its source and date. A possibility, not a customer, a lead nor a probability.") };
  }
  if (d.kind === "DEMAND" && d.code === "RECURRING_PUBLIC_BUYER") {
    const n = Number(d.detail.contracts ?? 0);
    const amount = typeof d.detail.amount === "number" && d.detail.amount > 0
      ? ` · ${d.detail.amount.toLocaleString(locale, { maximumFractionDigits: 0 })} ${typeof d.detail.currency === "string" ? d.detail.currency : ""}` : "";
    const offers = typeof d.detail.medianOffers === "number" ? t("suele recibir {n} ofertas", "usually receives {n} offers").replace("{n}", String(d.detail.medianOffers)) : null;
    const winners = typeof d.detail.distinctWinners === "number" ? t("{n} adjudicatarios distintos", "{n} different winners").replace("{n}", String(d.detail.distinctWinners)) : null;
    return { finding: t("Comprador público recurrente: {buyer} · {n} contratos en su actividad", "Recurrent public buyer: {buyer} · {n} contracts in its activity").replace("{buyer}", d.statement).replace("{n}", String(n)) + amount,
      why: [offers, winners].filter(Boolean).join(" · ") + (offers || winners ? ". " : "")
        + t("Compra lo que esta organización hace y aún no le ha adjudicado nada. Es una oportunidad potencial, no un cliente ni una probabilidad de ganar.", "It buys what this organization does and has not awarded it anything yet. A potential opportunity, not a client nor a probability of winning.") };
  }
  if (d.kind === "DEMAND") {
    const deadline = typeof d.detail.deadline === "string" ? d.detail.deadline.slice(0, 10) : null;
    const buyer = typeof d.detail.buyer === "string" ? d.detail.buyer : null;
    const facts = [deadline ? t("Plazo {date}", "Deadline {date}").replace("{date}", deadline) : null, buyer].filter(Boolean).join(" · ");
    // The buyer classified the call mainly as something else: the activity is only one of its additional codes.
    const additional = d.detail.classifiedAs === "ADDITIONAL";
    // An evaluator's judgment of how closely the work is the activity's (spec 075); never shown as a fact.
    const fit = d.detail.fit === "PARTIAL" ? t("Encaje parcial", "Partial fit") : d.detail.fit === "ADJACENT" ? t("Afín, otro trabajo principal", "Adjacent, other main work") : d.detail.fit === "UNCERTAIN" ? t("Encaje dudoso", "Unclear fit") : null;
    return { finding: `${d.detail.isNew === true ? `${t("Nueva", "New")} · ` : ""}${fit ? `${fit} · ` : ""}${additional ? `${t("Parte secundaria", "Secondary part")} · ` : ""}${t("Demanda pública potencial", "Potential public demand")}: ${title}`,
      why: `${facts ? `${facts}. ` : ""}${additional
        ? t("Su actividad figura solo como código adicional: el objeto principal de esta licitación es otro. No es un cliente, una invitación ni una relación.", "Its activity appears only as an additional code: the main object of this call is something else. It is not a customer, an invitation or a relationship.")
        : t("Coincide por clasificación y lugar. No es un cliente, una invitación ni una relación.", "It matches by classification and place. It is not a customer, an invitation or a relationship.")}` };
  }
  if (d.kind === "DECLARED_LOCATION" && d.code === "GROUP_ENTITIES_IN_COUNTRIES") return {
    finding: `${t("Países con sociedades del grupo", "Countries with group entities")}: ${d.statement.split(", ").map(code => placeLabel(code, locale) || code).join(", ")}`,
    why: t("Donde el grupo tiene entidades registradas. No es todo su mercado ni dónde vende.", "Where the group has registered entities. It is not its whole market nor where it sells.") };
  if (d.kind === "DECLARED_LOCATION" && d.code === "PREMISES_PINNED_ON_MAP") return {
    finding: `${t("Sede que señala en el mapa de su web", "Premises pinned on its website's map")}: ${d.statement}`,
    why: t("La propia organización publica este punto. Indica dónde está, no todo su mercado ni dónde opera.", "The organization itself publishes this point. It shows where it is, not its whole market or where it operates.") };
  if (d.kind === "DECLARED_LOCATION" && d.code === "COUNTRY_FROM_SITE_SIGNALS") return {
    finding: `${t("País deducido de señales de su web", "Country inferred from its website's signals")}: ${placeLabel(d.statement, locale)}`,
    why: t("Dos o más señales independientes de su propia web apuntan a este país. Indica dónde empezar a buscar demanda; no define su mercado ni dónde opera.", "Two or more independent signals on its own website point to this country. It shows where to start looking for demand; it does not define its market or where it operates.") };
  if (d.kind === "DECLARED_LOCATION") return d.code === "LOCATION_STATED_IN_TEXT"
    ? { finding: `${t("Ubicación mencionada en su web", "Location mentioned on its website")}: ${placeLabel(d.statement, locale)}`, why: t("Indica dónde mirar primero. No define dónde opera ni todo su mercado.", "It shows where to look first. It does not define where it operates or its whole market.") }
    : { finding: `${t("Dirección que declara", "Address it declares")}: ${d.statement}`, why: t("Indica dónde mirar primero. No define dónde opera ni todo su mercado.", "It shows where to look first. It does not define where it operates or its whole market.") };
  if (d.kind === "DECLARED_SERVICE_AREA" && d.code === "SITE_VERSIONS_FOR_COUNTRIES") return {
    finding: `${t("Su web tiene versiones para", "Its website has versions for")}: ${Object.keys((d.detail.countries ?? {}) as Record<string, unknown>).map(c => placeLabel(c, locale)).join(", ")}`,
    why: t("Es lo que declara su propia web con sus versiones por país: dónde dice vender o atender, no una prueba de ventas allí.", "Its own website declares it through its country versions: where it says it sells or serves, not proof of sales there.") };
  if (d.kind === "DECLARED_SERVICE_AREA") return { finding: `${t("Zona de servicio que declara", "Service area it declares")}: ${d.statement}`, why: t("Es lo que la organización dice de sí misma; no se ha verificado.", "It is what the organization says about itself; it has not been verified.") };
  if (d.kind === "LANGUAGES") return { finding: `${t("Idiomas publicados", "Published languages")}: ${d.statement}`, why: t("Muestra en qué idiomas se presenta; no prueba en qué mercados vende.", "It shows the languages it presents itself in; it does not prove where it sells.") };
  if (d.kind === "IDENTITY_HINT" && d.code === "IDENTIFIER_IN_DIRECTORY") {
    const scheme = String(d.detail.scheme ?? "");
    const outlet = typeof d.detail.outlet === "string" ? d.detail.outlet : "";
    return { finding: `${t("Identificador en un directorio público", "Identifier in a public directory")} · ${outlet}: ${identifierLabel(`IDENTIFIER_DECLARED:${scheme}`, d.statement, t)}`,
      why: t("Una web de terceros muestra este identificador en una página que nombra a la organización; su dígito de control es válido. Solo un registro oficial admite una identidad.", "A third-party website shows this identifier on a page that names the organization; its check digit is valid. Only an official register admits an identity.") };
  }
  if (d.kind === "IDENTITY_HINT") return { finding: `${t("Su web declara", "Its website declares")}: ${identifierLabel(d.code, d.statement, t)}`, why: t("Es una pista de identidad. Solo un registro puede verificarla.", "It is an identity hint. Only a registry can verify it.") };
  if (d.kind === "PUBLIC_PRESENCE") return { finding: `${t("Web pública observada", "Public website observed")}: ${d.statement}`, why: t("Es la fuente de lo que la organización declara sobre sí misma.", "It is the source of what the organization declares about itself.") };
  // Spec 091: the searches of its activity, in its own words, read through a permitted API.
  if (d.kind === "SEARCH_VISIBILITY" && (d.code === "SEARCH_RANKS_MEASURED" || d.code === "SEARCH_NOT_RANKED")) {
    const [ranked, measured] = d.statement.split("/");
    return d.code === "SEARCH_RANKS_MEASURED" ? {
      finding: t("Aparece en {ranked} de {measured} búsquedas de su actividad", "It appears in {ranked} of {measured} searches for its activity").replace("{ranked}", ranked ?? "").replace("{measured}", measured ?? ""),
      why: t("Búsquedas formadas con las palabras de su propia web y su país, leídas en un buscador independiente. Puedes comprobar cada una en Google: allí los resultados cambian según la persona y el lugar.", "Searches built from its own website's words and its country, read on an independent search engine. You can check each one on Google, where results change by person and place.") } : {
      finding: t("No aparece entre los primeros resultados de {measured} búsquedas de su actividad", "It does not appear among the top results of {measured} searches for its activity").replace("{measured}", measured ?? ""),
      why: t("Quien busca lo que hace encuentra antes a otros. Es una medición con fecha y condiciones, no un juicio sobre el negocio.", "Whoever searches for what it does finds others first. It is a dated measurement with its conditions, not a judgment of the business.") };
  }
  if (d.kind === "SEARCH_VISIBILITY") return { finding: `${t("Visibilidad en buscadores medida", "Search visibility measured")}: ${d.statement}`, why: t("Es lo observado para una consulta y unas condiciones concretas. No es una posición general ni explica el motivo.", "It is what was observed for a given query and conditions. It is not a general ranking and does not explain why.") };
  if (d.kind === "GENERATIVE_VISIBILITY" && d.code === "AI_NAMED_FOR_CATEGORY") return {
    finding: t("Un asistente de IA la nombra al preguntar por su actividad ({n} de las preguntas)", "An AI assistant names it when asked about its activity ({n} of the questions)").replace("{n}", d.statement),
    why: t("Medido con preguntas fijas, sin búsqueda web. Nombrar no es recomendar; las respuestas varían entre ejecuciones.", "Measured with fixed questions, without web search. Naming is not recommending; answers vary between runs.") };
  if (d.kind === "GENERATIVE_VISIBILITY" && d.code === "AI_NOT_NAMED_FOR_CATEGORY") return {
    finding: t("Un asistente de IA no la nombra al preguntar por su actividad", "An AI assistant does not name it when asked about its activity"),
    why: t("Quien pregunta a un asistente por proveedores de su actividad no la encuentra en esa respuesta. Es una muestra con sus condiciones, no todo lo que sabe el asistente.", "Someone asking an assistant for providers of its activity does not find it in that answer. It is a sample with its conditions, not all the assistant knows.") };
  if (d.kind === "GENERATIVE_VISIBILITY" && d.code === "AI_CITED_SOURCES") return {
    finding: t("Webs que cita un asistente de IA al preguntar por su actividad: {sites}", "Websites an AI assistant cites when asked about its activity: {sites}").replace("{sites}", d.statement),
    why: t("Son las fuentes de las que bebe la respuesta: donde conviene estar presente para que la IA la encuentre. Citar no es recomendar.", "They are the sources the answer draws on: where it pays to be present for the AI to find it. Citing is not endorsing.") };
  if (d.kind === "GENERATIVE_VISIBILITY" && d.code === "AI_KNOWS_BRAND") return {
    finding: t("Un asistente de IA reconoce la organización por su nombre", "An AI assistant recognizes the organization by name"),
    why: t("Al preguntarle directamente, afirma tener conocimiento específico de ella. No verifica que lo que diga sea correcto.", "Asked directly, it states specific knowledge of it. This does not verify that what it says is correct.") };
  if (d.kind === "GENERATIVE_VISIBILITY" && d.code === "AI_DOES_NOT_KNOW_BRAND") return {
    finding: t("Un asistente de IA no reconoce la organización por su nombre", "An AI assistant does not recognize the organization by name"),
    why: t("Al preguntarle directamente, no tiene conocimiento específico de ella: su presencia en fuentes públicas citables puede ser escasa.", "Asked directly, it has no specific knowledge of it: its presence in citable public sources may be thin.") };
  if (d.kind === "GENERATIVE_VISIBILITY" && (d.code === "OPEN_CORPUS_CAPTURED" || d.code === "OPEN_CORPUS_NOT_CAPTURED")) {
    const conditions = (d.detail.conditions ?? {}) as Record<string, unknown>;
    const crawl = String(conditions.crawl ?? "");
    const pages = Number(d.detail.okCaptures ?? 0).toLocaleString(locale) + (d.detail.capped === true ? "+" : "");
    const before = Number(d.detail.capturedInPrevious ?? 0);
    const history = t("En los {m} rastreos anteriores aparece en {n}.", "It appears in {n} of the {m} previous crawls.")
      .replace("{n}", String(before)).replace("{m}", String(Array.isArray(d.detail.previousCrawls) ? d.detail.previousCrawls.length : 0));
    return d.code === "OPEN_CORPUS_CAPTURED"
      ? { finding: t("Su web está en el corpus abierto con el que se entrenan modelos de IA: {n} páginas en {crawl}", "Its website is in the open corpus AI models are trained on: {n} pages in {crawl}").replace("{n}", pages).replace("{crawl}", crawl),
          why: history + " " + t("Common Crawl es un rastreo abierto de la web que usan muchos modelos de lenguaje. Estar no garantiza que un modelo concreto la conozca o la cite.", "Common Crawl is an open crawl of the web that many language models use. Being in it does not guarantee that a given model knows or cites it.") }
      : { finding: t("Su web no aparece en el último rastreo abierto con el que se entrenan modelos de IA ({crawl})", "Its website does not appear in the latest open crawl AI models are trained on ({crawl})").replace("{crawl}", crawl),
          why: history + " " + t("Puede deberse al muestreo del rastreo, a una regla de robots.txt para CCBot o al tamaño del sitio. Es una señal GEO que se puede revisar.", "It may be the crawl's sampling, a robots.txt rule for CCBot or the site's size. It is a GEO signal worth reviewing.") };
  }
  if (d.kind === "GENERATIVE_VISIBILITY") return { finding: `${t("Aparición en respuestas de IA medida", "AI answer appearance measured")}: ${d.statement}`, why: t("Mencionar no es citar, y citar no es recomendar. Es una medición con sus condiciones, no una conclusión sobre el negocio.", "A mention is not a citation, and a citation is not an endorsement. It is a measurement with its conditions, not a conclusion about the business.") };
  if (d.kind === "WEB_REPRESENTATION" && d.code === "LIGHTHOUSE_AUDIT") {
    const scores = (d.detail.scores ?? {}) as Record<string, number | null>;
    const names: Record<string, string> = { SEO: "SEO", PERFORMANCE: t("Rendimiento", "Performance"),
      ACCESSIBILITY: t("Accesibilidad", "Accessibility"), BEST_PRACTICES: t("Buenas prácticas", "Best practices") };
    const conditions = (d.detail.conditions ?? {}) as Record<string, unknown>;
    const device = conditions.strategy === "DESKTOP" ? t("escritorio", "desktop") : t("móvil", "mobile");
    const parts = Object.entries(scores).filter(([, v]) => typeof v === "number").map(([k, v]) => `${names[k] ?? k} ${v}`);
    const failing = ((d.detail.failing ?? {}) as Record<string, { title?: string }[]>).SEO ?? [];
    const instrument = (d.detail.instrument ?? {}) as Record<string, unknown>;
    const seo = failing.length
      ? t("{n} comprobaciones de SEO no pasan: {list}. ", "{n} SEO checks do not pass: {list}. ").replace("{n}", String(failing.length))
          .replace("{list}", failing.slice(0, 4).map(f => f.title ?? "").filter(Boolean).join("; "))
      : t("Pasa todas las comprobaciones de SEO de Lighthouse. ", "It passes every Lighthouse SEO check. ");
    return { finding: `${t("Lighthouse de su web", "Lighthouse of its website")} (${device}): ${parts.join(" · ")}`,
      why: seo + t("Medido por Google PageSpeed Insights en laboratorio (Lighthouse {v}): varía unos puntos entre mediciones, no es la experiencia de sus visitantes ni su posición en buscadores.", "Measured by Google PageSpeed Insights in a lab (Lighthouse {v}): it varies a few points between runs, and it is neither its visitors' experience nor its search position.").replace("{v}", String(instrument.lighthouseVersion ?? "")) };
  }
  if (d.kind === "WEB_REPRESENTATION") return { finding: t("Representación web medida", "Web representation measured"), why: t("Comprobaciones de su propia web, con instrumento y condiciones. No es una posición en buscadores.", "Checks of its own website, with instrument and conditions. It is not a search ranking.") };
  if (d.kind === "REPRESENTATION_GAP" && d.code.startsWith("AUDIT:")) {
    const copy = auditCopy(d.code.slice(6), t, d.detail.value);
    return { finding: copy.title, why: copy.why };
  }
  if (d.kind === "REPRESENTATION_GAP" && d.code === "OFFER_NATURE_UNCLEAR") return {
    finding: t("Su web no deja claro si vende productos, presta servicios o hace obras.", "Its website does not make clear whether it sells products, performs services or carries out works."),
    why: t("Visitantes, buscadores y asistentes de IA podrían leerla como otro tipo de negocio y relacionarla con demanda que no es suya. Es una lectura de su propio texto, no un hecho.", "Visitors, search engines and AI assistants may read it as another kind of business and connect it with demand that is not its own. It is a reading of its own text, not a fact."),
  };
  if (d.kind === "REPRESENTATION_GAP") return d.code === "HOMEPAGE_NOINDEX"
    ? { finding: t("Su página principal pide no aparecer en buscadores.", "Its homepage asks search engines not to index it."), why: t("Los buscadores podrían no representar la web mientras siga así. No mide posiciones.", "Search engines may not represent the site while it stays so. It does not measure rankings.") }
    : { finding: t("En las páginas leídas, su oferta aparece en el texto pero no en datos estructurados.", "On the pages read, its offer appears in the text but not as structured data."), why: t("Las superficies que leen datos estructurados podrían no relacionarla con lo que ofrece. Es una brecha posible, no una causa medida.", "Surfaces that read structured data may not connect it with what it offers. It is a possible gap, not a measured cause.") };
  if (d.code.startsWith("NO_GOVERNED_DEMAND_SOURCE:")) {
    const place = placeLabel(String(d.detail.jurisdiction ?? ""), locale);
    const asked = Array.isArray(d.detail.questions) ? d.detail.questions.map(q => demandQuestionLabel(String(q), t)).filter((x): x is string => Boolean(x)) : [];
    return asked.length
      ? { finding: t("En {place} aún no hay fuente gobernada para: {list}.", "In {place} there is no governed source yet for: {list}.").replace("{place}", place).replace("{list}", asked.join(", ")), why: t("Falta de fuente no es falta de mercado ni de demanda.", "No source is not no market and not no demand.") }
      : { finding: `${t("Aún no hay una fuente de demanda gobernada para", "No governed demand source yet for")} ${place}`, why: t("Falta de fuente no es falta de mercado ni de demanda.", "No source is not no market and not no demand.") };
  }
  switch (d.code) {
    case "IDENTITY_NOT_VERIFIED": return { finding: t("Identidad legal todavía no verificada.", "Legal identity not verified yet."), why: t("Lo que ves describe su web y su presencia pública, que se observan igual. Verificar la identidad es opcional: con un registro (por ejemplo, su código LEI) se añaden razón social, registros, cuentas y contratos adjudicados.", "What you see describes its website and public presence, which are observed all the same. Verifying identity is optional: with a registry (for example its LEI code) legal name, registrations, accounts and awarded contracts are added.") };
    case "WEBSITE_LINK_NOT_REGISTRY_VERIFIED": return { finding: t("Ningún registro vincula esta web a la organización.", "No registry links this website to the organization."), why: t("La web la indicaste tú; la tratamos como atención, no como hecho.", "You indicated this website; we treat it as attention, not as fact.") };
    case "ACTIVITY_NOT_ESTABLISHED": return { finding: t("Qué ofrece no está establecido todavía.", "What it offers is not established yet."), why: t("No buscamos demanda sobre una suposición.", "We do not search for demand on an assumption.") };
    case "LOCATION_NOT_DECLARED": return { finding: t("No hemos establecido su ubicación ni su ámbito geográfico de servicio.", "Its location and geographic service scope have not been established."), why: t("No elegimos un mercado por defecto.", "We do not pick a default market.") };
    case "DEMAND_NOT_ROUTABLE": case "NO_ROUTABLE_DEMAND_QUESTION": return { finding: t("Ninguna fuente de demanda gobernada aplica todavía a esta actividad y lugar.", "No governed demand source applies yet to this activity and place."), why: t("No es una ausencia de oportunidades.", "It is not an absence of opportunities.") };
    case "NO_PRESS_MENTION_FOUND": return { finding: t("Ningún titular de los medios indexados la nombra.", "No headline in the indexed media names it."), why: t("Solo cubre los medios y fechas indicados; no significa que no tenga cobertura en otros.", "It only covers the stated media and dates; it does not mean it has no coverage elsewhere.") };
    case "NO_BUYER_SIGNALS": return { finding: t("Todavía no se pueden derivar posibles compradores.", "No potential buyer can be derived yet."), why: t("Se derivan de quién ya compra: clientes que muestra su web, adjudicaciones públicas, clientes de competidores y sectores compradores. No es una ausencia de demanda.", "They are derived from who already buys: clients its website shows, public awards, competitors' clients and buying sectors. It is not an absence of demand.") };
    case "NO_PUBLIC_AWARDS_FOUND": return { finding: t("No hay adjudicaciones públicas a su nombre en el periodo cubierto.", "No public contract awards in its name in the period covered."), why: t("Solo cubre adjudicaciones publicadas desde la fecha indicada; no significa que no tenga contratos.", "It only covers awards published since the stated date; it does not mean it has no contracts.") };
    case "NO_RELEVANT_DEMAND_FOUND": return { finding: t("Las fuentes consultadas no tienen ahora demanda que coincida.", "The sources searched have no matching demand right now."), why: t("Sin resultado no es sin oportunidad; volveremos a observar.", "No result is not no opportunity; we will observe again.") };
    case "NOT_AN_OPERATING_BUSINESS_SITE": return { finding: t("La página no parece la web de una actividad en marcha.", "The page does not read as an operating business website."), why: t("Es un juicio no autoritativo sobre la página, no sobre la organización.", "It is a non-authoritative judgment about the page, not about the organization.") };
    case "NO_PUBLIC_WEBSITE": return { finding: t("No hay una web pública que observar.", "There is no public website to observe."), why: t("Añade su web para empezar la observación.", "Add its website to start observing.") };
    case "WEBSITE_OF_ANOTHER_ORGANIZATION": return { finding: t("Un registro asocia esta web a otra organización.", "A registry links this website to another organization."), why: t("No la observamos como si fuera de esta organización.", "We do not observe it as if it belonged to this organization.") };
    case "ROBOTS_DISALLOWED": return { finding: t("Su robots.txt no permite que la observemos.", "Its robots.txt does not allow us to observe it."), why: t("Lo respetamos y no leemos sus páginas. No concluimos nada de ello.", "We respect it and do not read its pages. We conclude nothing from it.") };
    case "REDIRECTS_TO_ANOTHER_SITE": return { finding: t("Esta web redirige a otro dominio.", "This website redirects to another domain."), why: t("No la seguimos porque podría ser otra organización. Indica el dominio al que lleva para observarla.", "We do not follow it because it could be another organization. Give the domain it leads to in order to observe it.") };
    case "HOMEPAGE_UNAVAILABLE": return { finding: t("Su página principal no respondió a una lectura automática.", "Its homepage did not answer an automated reading."), why: t("Puede limitar los accesos automáticos; no lo eludimos. No concluimos nada de ello.", "It may limit automated access; we do not bypass it. We conclude nothing from it.") };
    case "TLS_CERTIFICATE_NOT_VERIFIED": return { finding: t("No pudimos verificar el certificado de seguridad de su web.", "We could not verify its website's security certificate."), why: t("Su servidor no presenta una cadena de certificados completa. No desactivamos la verificación; no concluimos nada sobre la organización.", "Its server does not present a complete certificate chain. We do not switch verification off; we conclude nothing about the organization.") };
    case "ROBOTS_UNAVAILABLE": return { finding: t("Su web no respondió a una lectura automática.", "Its website did not answer an automated reading."), why: t("Lo intentamos también con www. Puede ser temporal; no concluimos nada de ello.", "We also tried with www. It may be temporary; we conclude nothing from it.") };
    default: return { finding: t("La web no se pudo observar con sus reglas de acceso.", "The website could not be observed under its access rules."), why: t("Respetamos robots.txt y nuestros límites; no concluimos nada de ello.", "We respect robots.txt and our limits; we conclude nothing from that.") };
  }
}

/** The demand question a missing source leaves open, in the reader's words. */
export function buyerSignalLabel(type: string, t: Translate): string {
  switch (type) {
    case "CUSTOMER_OF_COMPETITOR": return t("Compra a un competidor", "Buys from a competitor");
    case "PUBLIC_BUYER_OF_CATEGORY": return t("Comprador público de su actividad", "Public buyer of its activity");
    case "GROUP_OF_CUSTOMER": return t("Del grupo de un cliente", "In a customer's group");
    case "SIMILAR_TO_CUSTOMERS": return t("Parecida a sus clientes", "Similar to its customers");
    case "SECTOR_BUYS_FROM_ITS_SECTOR": return t("Su sector compra al suyo", "Its sector buys from its own");
    default: return type;
  }
}

function techCategory(category: string, t: Translate): string {
  const labels: Record<string, string> = {
    ANALYTICS: t("analítica", "analytics"), ADVERTISING: t("publicidad", "advertising"),
    CRM_MARKETING: t("CRM y marketing", "CRM and marketing"), EMAIL_MARKETING: t("email marketing", "email marketing"),
    ECOMMERCE: t("comercio electrónico", "e-commerce"), PAYMENTS: t("pagos", "payments"), CMS: t("gestor de contenidos", "content management"),
    SUPPORT_CHAT: t("atención al cliente", "customer support"), CONSENT: t("consentimiento de cookies", "cookie consent"),
    HOSTING_CDN: t("alojamiento y CDN", "hosting and CDN"), SCHEDULING: t("agenda de citas", "scheduling"), FORMS: t("formularios", "forms"),
    VIDEO: t("vídeo", "video"), MAPS: t("mapas", "maps"), SEARCH: t("búsqueda", "search"), SECURITY: t("seguridad", "security"),
  };
  return labels[category] ?? category.toLowerCase();
}

export function changeLabel(metric: string, t: Translate): string {
  const labels: Record<string, string> = {
    "presence.ai_named_share": t("Respuestas de IA que la nombran en su categoría", "AI answers naming it in its category"),
    "presence.search_ranked_share": t("Búsquedas de su actividad en las que aparece", "Searches for its activity where it appears"),
    "presence.ai_knows_brand": t("La IA conoce la marca", "AI knows the brand"),
    "presence.audit_attention": t("Puntos de su web que piden atención", "Website checks needing attention"),
    "presence.lcp_ms": t("Carga real de su web (ms)", "Real-user page load (ms)"),
    "presence.inp_ms": t("Respuesta real de su web (ms)", "Real-user responsiveness (ms)"),
    "presence.languages": t("Idiomas de su web", "Website languages"),
    "reputation.press_mentions": t("Titulares que la nombran", "Headlines naming it"),
    "activity.own_publications": t("Publicaciones propias", "Own publications"),
    "activity.publications_90d": t("Publicaciones en 90 días (canal propio)", "Posts in 90 days (own channel)"),
    "value.activities": t("Actividades probables", "Likely activities"),
    "markets.premises": t("Sedes declaradas", "Declared premises"),
    "markets.group_countries": t("Países de su grupo", "Group countries"),
    "relationships.public_clients": t("Clientes públicos", "Public clients"),
    "relationships.partners": t("Socios en contratos públicos", "Public contract partners"),
    "relationships.competitors": t("Competidores observados", "Observed competitors"),
    "demand.open_public_calls": t("Licitaciones abiertas que encajan", "Matching open public calls"),
    "demand.recurrent_buyers": t("Compradores recurrentes de su actividad", "Recurring buyers of its activity"),
    "economics.revenue": t("Ingresos", "Revenue"),
    "economics.employees": t("Empleados", "Employees"),
    "relationships.technology": t("Proveedores tecnológicos de su web", "Website technology suppliers"),
    "relationships.declared_clients": t("Clientes que muestra", "Clients it shows"),
    "relationships.declared_partners": t("Partners que muestra", "Partners it shows"),
    "value.credentials": t("Certificaciones que declara", "Certifications it claims"),
    "activity.job_postings": t("Ofertas de empleo publicadas", "Job postings published"),
    "activity.hiring_channel": t("Canal de empleo publicado", "Hiring channel published"),
    "reputation.review_profiles": t("Perfiles de opiniones enlazados", "Linked review profiles"),
    "activity.open_positions": t("Vacantes abiertas", "Open positions"),
    "markets.hiring_countries": t("Países donde contrata", "Countries it hires in"),
    "reputation.wikipedia_views": t("Visitas a su artículo de Wikipedia (mes)", "Wikipedia article views (month)"),
    "reputation.wikipedia_languages": t("Idiomas con artículo en Wikipedia", "Languages with a Wikipedia article"),
    "reputation.self_rating": t("Valoración que publica sobre sí misma", "Rating it publishes about itself"),
    "organization.identifiers": t("Identificadores publicados", "Published identifiers"),
    "context.sector_headlines": t("Titulares de su sector", "Sector headlines"),
    "context.regulation": t("Normas nuevas sobre su actividad", "New rules about its activity"),
  };
  return labels[metric] ?? metric;
}

function demandQuestionLabel(id: string, t: Translate): string | null {
  switch (id) {
    case "compatible-public-tenders": return t("licitaciones abiertas", "open tenders");
    case "revealed-public-demand": return t("adjudicaciones recientes", "recent awards");
    case "public-investment-pipeline": return t("inversión pública planificada", "planned public investment");
    case "funding-driven-demand": return t("subvenciones y ayudas", "grants and subsidies");
    case "projects-needing-capability": return t("permisos y proyectos", "permits and projects");
    case "private-project-announcements": return t("proyectos privados anunciados", "announced private projects");
    case "regulation-driven-demand": return t("cambios regulatorios", "regulatory changes");
    case "buyer-expansion": return t("compradores en expansión", "expanding buyers");
    case "consumer-representation": return t("presencia ante consumidores", "consumer presence");
    default: return null;
  }
}

function epistemicCopy(state: Discovery["epistemicState"], t: Translate): string {
  if (state === "OBSERVED") return t("Observado", "Observed");
  if (state === "DECLARED") return t("Declarado por la organización", "Declared by the organization");
  if (state === "POTENTIAL") return t("Potencial", "Potential");
  return t("Desconocido", "Unknown");
}

function signalLabel(kind: string, t: Translate): string {
  switch (kind) {
    case "DOMAIN": return t("Dominio de país", "Country domain");
    case "LANGUAGE_REGION": return t("Idioma y región declarados", "Declared language and region");
    case "PHONE_PREFIX": return t("Prefijo telefónico", "Telephone prefix");
    case "TAX_IDENTIFIER": return t("Identificador fiscal", "Tax identifier");
    case "POSTAL_AND_NAME": return t("Código postal y país", "Postal code and country");
    default: return kind;
  }
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

const SIZE_CLASS_LABEL: Record<string, [string, string]> = {
  "0-9": ["0–9", "0–9"], "10-19": ["10–19", "10–19"], "20-49": ["20–49", "20–49"],
  "50-249": ["50–249", "50–249"], GE250: ["250 o más", "250 or more"],
};

/** Its size against its sector (spec 095), from the crossing's values only. */
export function sizeInSectorCopy(v: Record<string, unknown>, t: Translate, locale: string): string {
  const country = placeLabel(String(v.country ?? ""), locale);
  const size = typeof v.sizeClass === "string" && SIZE_CLASS_LABEL[v.sizeClass] ? t(...SIZE_CLASS_LABEL[v.sizeClass]) : null;
  const times = (x: unknown) => typeof x === "number" ? x.toLocaleString(locale, { maximumFractionDigits: 1 }) : "";
  const parts: string[] = [];
  if (typeof v.revenue === "number") {
    const revenue = `${v.revenue.toLocaleString(locale, { notation: "compact", style: "currency", currency: "EUR", maximumFractionDigits: 1 })}${v.revenueYear ? ` (${String(v.revenueYear)})` : ""}`;
    parts.push(typeof v.timesSizeClassAverage === "number" && size
      ? t("Su facturación, {revenue}, es {x} veces la media de las empresas de su tamaño ({size} personas) en su sector en {country}, y {y} veces la de la empresa media del sector.", "Its revenue, {revenue}, is {x} times the average of enterprises of its size ({size} people) in its sector in {country}, and {y} times the sector's average enterprise.")
        .replace("{revenue}", revenue).replace("{x}", times(v.timesSizeClassAverage)).replace("{size}", size).replace("{country}", country).replace("{y}", times(v.timesSectorAverage))
      : t("Su facturación, {revenue}, es {y} veces la de la empresa media de su sector en {country}.", "Its revenue, {revenue}, is {y} times the sector's average enterprise in {country}.")
        .replace("{revenue}", revenue).replace("{y}", times(v.timesSectorAverage)).replace("{country}", country));
  }
  if (typeof v.shareAtLeastItsSize === "number" && size) {
    const share = (v.shareAtLeastItsSize * 100).toLocaleString(locale, { maximumFractionDigits: v.shareAtLeastItsSize < 0.1 ? 1 : 0 });
    parts.push(t("Solo el {p} % de las empresas de su sector en {country} tienen su tamaño ({size} personas) o más.", "Only {p}% of enterprises in its sector in {country} are its size ({size} people) or larger.")
      .replace("{p}", share).replace("{country}", country).replace("{size}", size));
  }
  return parts.join(" ");
}

/** A declared register identifier in the reader's words: "CIF B54941729", not the scheme code
 * "ES_CIF B54941729" (spec 094). Other identity hints keep their statement. */
export function identifierLabel(code: string, statement: string, t: Translate): string {
  if (!code.startsWith("IDENTIFIER_DECLARED:")) return statement;
  const scheme = code.slice("IDENTIFIER_DECLARED:".length);
  const value = statement.startsWith(`${scheme} `) ? statement.slice(scheme.length + 1) : statement;
  const label: Record<string, string> = {
    ES_CIF: t("CIF", "Spanish tax ID (CIF)"),
    SIREN: "SIREN",
    COMPANIES_HOUSE: t("número de Companies House", "Companies House number"),
    ORGNR: t("número de organización (Noruega)", "Norwegian organisation number"),
    DE_HR: t("inscripción en el Registro Mercantil alemán", "German commercial register entry"),
    LEI: "LEI",
  };
  return label[scheme] ? `${label[scheme]} ${value}` : statement;
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
  rows.push(...contractScaleRows(detail.scale, t, locale));
  if (detail.checks && typeof detail.checks === "object" && !detail.audit) for (const [key, value] of Object.entries(detail.checks as Record<string, unknown>)) rows.push([checkLabel(key, t), Array.isArray(value) ? value.join(", ") || "—" : value === true ? t("Sí", "Yes") : value === false ? t("No", "No") : String(value ?? "—")]);
  if (detail.instrument && typeof detail.instrument === "object" && typeof (detail.instrument as Record<string, unknown>).model === "string") rows.push([t("Asistente medido", "Assistant measured"), String((detail.instrument as Record<string, unknown>).model)]);
  if (detail.conditions && typeof detail.conditions === "object" && Array.isArray((detail.conditions as Record<string, unknown>).questions)) for (const q of (detail.conditions as { questions: unknown[] }).questions) rows.push([t("Pregunta", "Question"), String(q)]);
  if (typeof detail.measuredAt === "string") rows.push([t("Medido el", "Measured on"), detail.measuredAt.slice(0, 10)]);
  // Spec 090: share of voice, position, who it names instead and which sites it cites.
  if (typeof detail.shareOfVoice === "number") rows.push([t("Cuota de voz en las respuestas", "Share of voice in the answers"), `${Math.round(detail.shareOfVoice * 100)} % ${t("de las organizaciones nombradas", "of the organizations named")}`]);
  if (typeof detail.averagePosition === "number" && d.kind === "SEARCH_VISIBILITY") rows.push([t("Posición media donde aparece", "Average position where it appears"), String(detail.averagePosition)]);
  else if (typeof detail.averagePosition === "number") rows.push([t("Posición media cuando la nombra", "Average position when named"), String(detail.averagePosition)]);
  if (Array.isArray(detail.rankingInstead) && detail.rankingInstead.length) rows.push([t("Webs que aparecen en su lugar", "Websites that appear instead"), (detail.rankingInstead as unknown[][]).slice(0, 8).map(r => `${String(r[0])} (${String(r[1])})`).join(" · ")]);
  if (Array.isArray(detail.competitorFrequency) && detail.competitorFrequency.length) rows.push([t("A quién nombra en su lugar", "Who it names instead"), (detail.competitorFrequency as unknown[][]).map(r => `${String(r[0])} (${String(r[1])})`).join(" · ")]);
  else if (Array.isArray(detail.competitorsNamed) && detail.competitorsNamed.length) rows.push([t("Otras organizaciones que nombra", "Other organizations it names"), detail.competitorsNamed.join(" · ")]);
  if (Array.isArray(detail.sitesCited) && detail.sitesCited.length) rows.push([t("Webs que cita", "Websites it cites"), (detail.sitesCited as unknown[][]).map(r => `${String(r[0])} (${String(r[1])})`).join(" · ")]);
  if (detail.fact === "sectorMarket") {
    if (Array.isArray(detail.divisions)) rows.push([t("Actividades (NACE Rev.2)", "Activities (NACE Rev.2)"), detail.divisions.join(", ")]);
    if (typeof detail.turnoverPerPersonTeur === "number") rows.push([t("Facturación por persona ocupada", "Turnover per person employed"), `${(detail.turnoverPerPersonTeur * 1000).toLocaleString(locale, { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}`]);
    if (typeof detail.industryReadFrom === "string") rows.push([t("Sector leído de", "Sector read from"), detail.industryReadFrom === "REGISTER_ACTIVITY_CODE" ? t("su código de actividad en el registro", "its register activity code") : t("su actividad observada (lectura potencial)", "its observed activity (a potential reading)")]);
  }
  if (typeof detail.uncertainty === "string") rows.push([t("Incertidumbre", "Uncertainty"), detail.uncertainty]);
  if (typeof detail.outlet === "string") rows.push([t("Medio", "Outlet"), detail.outlet]);
  if (typeof detail.publishedAt === "string") rows.push([t("Publicado", "Published"), detail.publishedAt.slice(0, 10)]);
  if (typeof detail.feeds === "number") rows.push([t("Medios indexados", "Indexed media"), String(detail.feeds)]);
  if (typeof detail.contracts === "number") rows.push([t("Contratos", "Contracts"), String(detail.contracts)]);
  if (typeof detail.amount === "number" && detail.amount > 0) rows.push([t("Importe adjudicado (sin IVA)", "Awarded amount (excl. VAT)"), `${detail.amount.toLocaleString(locale, { maximumFractionDigits: 0 })} ${typeof detail.currency === "string" ? detail.currency : ""}`]);
  if (typeof detail.matchedBy === "string") rows.push([t("Atribuida por", "Attributed by"), detail.matchedBy === "TAX_ID" ? t("NIF", "Tax ID") : t("nombre legal", "legal name")]);
  if (typeof detail.medianOffers === "number") rows.push([t("Ofertas recibidas (mediana)", "Offers received (median)"), String(detail.medianOffers)]);
  if (Array.isArray(detail.subsidiaries)) for (const s of (detail.subsidiaries as Array<Record<string, unknown>>).slice(0, 12)) rows.push([t("Filial", "Subsidiary"), [s.name, s.city, s.country].filter(Boolean).join(" · ")]);
  if (typeof detail.lei === "string") rows.push(["LEI", detail.lei]);
  if (Array.isArray(detail.buyers) && detail.buyers.length) rows.push([t("Compradores", "Buyers"), detail.buyers.join(" · ")]);
  if (Array.isArray(detail.awards)) for (const a of (detail.awards as Array<Record<string, unknown>>).slice(0, 5)) rows.push([t("Adjudicación", "Award"), [a.title, a.buyer, a.awardedOn, typeof a.amount === "number" ? `${a.amount.toLocaleString(locale, { maximumFractionDigits: 0 })} ${a.currency ?? ""}` : null].filter(Boolean).join(" · ")]);
  if (typeof detail.coverageSince === "string") rows.push([t("Cobertura desde", "Coverage since"), detail.coverageSince]);
  if (typeof detail.latitude === "number" && typeof detail.longitude === "number") rows.push([t("Coordenadas", "Coordinates"), `${detail.latitude}, ${detail.longitude}`]);
  if (typeof detail.attribution === "string") rows.push([t("Lugar según", "Place according to"), detail.attribution]);
  if (Array.isArray(detail.signals)) for (const s of detail.signals as Array<{ kind?: unknown; value?: unknown }>) rows.push([signalLabel(String(s.kind ?? ""), t), String(s.value ?? "")]);
  if (typeof detail.limitation === "string") rows.push([t("Límite", "Limitation"), detail.limitation]);
  if (typeof detail.impact === "string") rows.push([t("Impacto", "Impact"), auditImpact(detail.impact, t)]);
  if (d.code.startsWith("AUDIT:")) rows.push([t("Qué puedes hacer", "What you can do"), auditCopy(d.code.slice(6), t, d.detail.value).action]);
  for (const [label, value] of auditRows(detail.audit, t)) rows.push([label, value]);
  if (d.observedAt) rows.push([t("Observado el", "Observed on"), d.observedAt.slice(0, 10)]);
  return rows;
}

/** The representation audit as rows: per section, its counts, then what to review. */
export function auditRows(audit: unknown, t: Translate): Array<[string, string]> {
  if (!audit || typeof audit !== "object") return [];
  const a = audit as { instrument?: unknown; pagesRead?: unknown; checks?: unknown };
  const checks = Array.isArray(a.checks) ? a.checks as Array<{ id: string; section: string; status: string; impact: string; value?: unknown }> : [];
  const rows: Array<[string, string]> = [];
  if (typeof a.instrument === "string") rows.push([t("Auditoría", "Audit"), `${a.instrument} · ${t("páginas leídas", "pages read")}: ${String(a.pagesRead ?? "—")}`]);
  for (const section of ["SEARCH_FINDABILITY", "AI_ANSWER_READINESS", "SHARING_AND_MOBILE", "REAL_USER_EXPERIENCE"]) {
    const inSection = checks.filter(c => c.section === section);
    if (!inSection.length) continue;
    const counts = ["PASS", "ATTENTION", "UNKNOWN"].map(s => `${auditStatus(s, t)}: ${inSection.filter(c => c.status === s).length}`).join(" · ");
    rows.push([auditSection(section, t), counts]);
    for (const c of inSection.filter(c => c.status === "ATTENTION")) rows.push([`${auditImpact(c.impact, t)}`, auditCopy(c.id, t, c.value).title]);
  }
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
    {d.kind === "SEARCH_VISIBILITY" && <SearchRows d={d}/>}
    <Basis d={d}/>
  </article>;
}

type SearchRow = { keyword?: unknown; position?: unknown; ranksInstead?: unknown; googleUrl?: unknown };

/** Spec 091: each search with its position and a link to see the same search on Google. */
export function searchRows(d: Discovery): Array<{ keyword: string; position: number | null; instead: string[]; googleUrl: string | null }> {
  const rows = Array.isArray(d.detail.rows) ? d.detail.rows as SearchRow[] : [];
  return rows.filter(r => typeof r.keyword === "string").map(r => ({
    keyword: String(r.keyword),
    position: typeof r.position === "number" ? r.position : null,
    instead: Array.isArray(r.ranksInstead) ? (r.ranksInstead as unknown[]).slice(0, 3).map(String) : [],
    googleUrl: typeof r.googleUrl === "string" && r.googleUrl.startsWith("https://www.google.com/search?") ? r.googleUrl : null,
  }));
}

function SearchRows({ d }: { d: Discovery }) {
  const { t } = useLocale();
  const rows = searchRows(d);
  if (!rows.length) return null;
  return <ul className="fo-search-rows">{rows.map(r => <li key={r.keyword}>
    <strong>«{r.keyword}»</strong>{" "}
    <span>{r.position === null ? t("no aparece en los 20 primeros", "not in the top 20") : t("posición {n}", "position {n}").replace("{n}", String(r.position))}</span>
    {r.instead.length > 0 && <span className="fo-search-instead"> · {t("antes aparecen", "ahead of it")}: {r.instead.join(", ")}</span>}
    {r.googleUrl && <> · <a href={r.googleUrl} target="_blank" rel="noopener noreferrer">{t("Ver esta búsqueda en Google", "See this search on Google")}<ExternalLink size={14} aria-hidden="true"/><span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a></>}
  </li>)}</ul>;
}

const ORDER: Discovery["kind"][] = ["ACTIVITY", "DEMAND", "DECLARED_LOCATION", "DECLARED_SERVICE_AREA", "LANGUAGES", "IDENTITY_HINT", "PUBLIC_PRESENCE", "WEB_REPRESENTATION"];

export function FirstObservationView({ observation }: { observation: FirstObservation }) {
  const { t } = useLocale();
  const findings = ORDER.flatMap(kind => observation.discoveries.filter(d => d.kind === kind));
  const gaps = observation.discoveries.filter(d => d.kind === "REPRESENTATION_GAP");
  const crossings = observation.discoveries.filter(d => d.kind === "INXIGHT");
  const changes = observation.discoveries.filter(d => d.kind === "CHANGE");
  const unknowns = observation.discoveries.filter(d => d.kind === "SIGNIFICANT_UNKNOWN");
  return <section className="fo-view" aria-labelledby="first-observation-title">
    <span className="eyebrow">{t("Primera observación", "First observation")}</span>
    <h3 id="first-observation-title">{observationStateCopy(observation.state, t)}</h3>
    <p className="fo-authority">{t("Lectura operativa con sus fuentes. No es verdad canónica: lo potencial sigue siendo potencial.", "Operational reading with its sources. It is not canonical truth: what is potential stays potential.")}</p>
    {observation.publicUnderstanding && <PublicUnderstandingView report={observation.publicUnderstanding}/>}
    {crossings.length > 0 && <div className="fo-group fo-crossings"><h4 className="fo-group-title">{t("Lo que revela el cruce", "What crossing the findings reveals")}</h4>{crossings.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
    {changes.length > 0 && <div className="fo-group fo-changes"><h4 className="fo-group-title">{t("Cómo ha cambiado", "How it has changed")}</h4>{changes.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
    {findings.length > 0 && <div className="fo-group"><h4 className="fo-group-title">{t("Lo que AXIGNAL ha encontrado", "What AXIGNAL found")}</h4>{findings.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
    {gaps.length > 0 && <div className="fo-group"><h4 className="fo-group-title">{t("Brechas posibles", "Possible gaps")}</h4>{gaps.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
    {unknowns.length > 0 && <div className="fo-group"><h4 className="fo-group-title">{t("Lo que todavía no sabemos", "What we do not know yet")}</h4>{unknowns.map((d, i) => <Finding key={`${d.code}-${i}`} d={d}/>)}</div>}
  </section>;
}
