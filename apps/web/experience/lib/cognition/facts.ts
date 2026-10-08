/**
 * Family-shaped knowledge for the illustrative Panorama (FIXTURE_ONLY).
 *
 * Each knowledge shape has its own typed structure so the interface can explain
 * it in its own terms. Epistemic state, currentness and provenance are data here;
 * the presentation layer only reads them. UNKNOWN values are explicit, never 0.
 */
import type { Copy } from "../locale";
import type { Epistemic, FamilyId } from "../projection";
import type { Garden, GardenExposure, GardenPlace } from "../garden";

const c = (es: string, en: string): Copy => ({ es, en });

export type KnowledgeShape =
  | "TREND"
  | "ANSWER_SPACE"
  | "DEMAND_MATCH"
  | "NETWORK"
  | "TERRITORY"
  | "DISCOURSE"
  | "CHANGE"
  | "PROVENANCE";

/** A family can carry several shapes: presence is both search trend and answer space. */
export const familyShapes: Record<FamilyId, KnowledgeShape[]> = {
  presence: ["TREND", "ANSWER_SPACE"],
  reputation: ["DISCOURSE"],
  value: ["DEMAND_MATCH"],
  markets: ["TERRITORY"],
  relationships: ["NETWORK"],
  demand: ["DEMAND_MATCH"],
  activity: ["CHANGE"],
  economics: ["CHANGE"],
  organization: ["PROVENANCE"],
  context: ["CHANGE"],
};

export type Currentness = "CURRENT" | "STALE" | "HISTORICAL" | "UNKNOWN";

export type FactSource = {
  id: string;
  title: Copy;
  observedAt: string;
  currentness?: Currentness;
  instrument: Copy;
  limitation: Copy;
};

export type TrendPoint = { date: string; value: number | null; note?: Copy };
export type TrendFacts = {
  measure: Copy;
  unit: "PERCENT";
  instrument: Copy;
  sample: Copy;
  points: TrendPoint[];
  topics: { label: Copy; delta: number | null }[];
  pages: { path: string; change: "GAINED" | "LOST" | "STABLE" | "UNKNOWN" }[];
  sourceIds: string[];
};

export type AnswerCell = "CITED" | "MENTIONED" | "ABSENT" | "NOT_OBSERVED";
export type AnswerSpaceFacts = {
  surfaces: { id: string; label: Copy; observedAt: string | null; sample: number | null }[];
  questions: { text: Copy; cells: Record<string, AnswerCell> }[];
  claims: {
    text: Copy;
    support: "SUPPORTED" | "UNSUPPORTED" | "CONTRADICTED" | "UNKNOWN";
    sourceId?: string;
  }[];
  coOccurring: { name: string; questions: number }[];
  sourceIds: string[];
};

export type OpportunityFacts = {
  id: string;
  title: Copy;
  buyer: Copy;
  market: Copy;
  form: Copy;
  deadline: string | null;
  epistemic: Extract<Epistemic, "POTENTIAL" | "UNKNOWN">;
  capability: { label: Copy; excerpt: Copy; sourceId: string };
  demand: { label: Copy; code: string | null; sourceId: string };
  known: { label: Copy; value: Copy }[];
  unknown: Copy[];
  whyPotential: Copy;
  observedAt: string;
};

export type NetworkFacts = {
  nodes: { id: string; label: string; role: Copy }[];
  edges: {
    from: string;
    to: string;
    kind: Copy;
    state: Exclude<Epistemic, "UNKNOWN">;
    since: string | null;
    sourceId: string | null;
    reason: Copy;
  }[];
};

export type TerritoryFacts = {
  markets: {
    code: string;
    label: Copy;
    state: Epistemic;
    currentness: Currentness;
    signal: Copy | null;
    sourceId: string | null;
  }[];
};

export type DiscourseFacts = {
  statements: {
    id: string;
    text: Copy;
    where: Copy;
    date: string;
    materiality: "LOW" | "MEDIUM" | "HIGH";
    contradicts?: string;
    sample: Copy;
  }[];
  absences: Copy[];
};

export type ChangeFacts = {
  events: {
    date: string;
    kind: "EVIDENCE_ARRIVED" | "MATERIAL_CHANGE" | "BECAME_STALE" | "HYPOTHESIS_UPDATED";
    label: Copy;
    sourceId: string | null;
  }[];
};

export type FamilyFacts = {
  sources: FactSource[];
  trend?: TrendFacts;
  answerSpace?: AnswerSpaceFacts;
  opportunities?: OpportunityFacts[];
  network?: NetworkFacts;
  territory?: TerritoryFacts;
  discourse?: DiscourseFacts;
  change?: ChangeFacts;
};

const SOURCES: FactSource[] = [
  {
    id: "src-search-sample",
    title: c("Muestra de búsquedas web", "Web search sample"),
    observedAt: "2026-10-02",
    instrument: c("40 consultas fijas, primera página, España", "40 fixed queries, first page, Spain"),
    limitation: c("Muestra pequeña; no representa todo el tráfico.", "Small sample; not all traffic."),
  },
  {
    id: "src-generative-sample",
    title: c("Muestra de respuestas generativas", "Generative answer sample"),
    observedAt: "2026-10-02",
    instrument: c("12 preguntas, un asistente, una ejecución", "12 questions, one assistant, one run"),
    limitation: c(
      "Una mención no es una cita ni un respaldo.",
      "A mention is neither a citation nor an endorsement.",
    ),
  },
  {
    id: "src-capabilities",
    title: c("Ficha técnica pública de la empresa", "Company public technical sheet"),
    observedAt: "2026-07-01",
    instrument: c("Documento público, lectura determinista", "Public document, deterministic reading"),
    limitation: c("Una declaración no demuestra ejecución.", "A declaration does not prove execution."),
  },
  {
    id: "src-programme",
    title: c("Programa nacional de eficiencia en edificios", "National building efficiency programme"),
    observedAt: "2026-09-01",
    instrument: c("Boletín oficial, lectura determinista", "Official gazette, deterministic reading"),
    limitation: c("No establece presupuesto por actuación.", "Does not set a budget per action."),
  },
  {
    id: "src-tender",
    title: c("Anuncio de licitación pública", "Public tender notice"),
    observedAt: "2026-10-01",
    instrument: c("Portal de contratación, búsqueda por CPV", "Procurement portal, CPV search"),
    limitation: c("Requisitos técnicos en pliegos no leídos.", "Technical requirements in unread tender documents."),
  },
  {
    id: "src-project-case",
    title: c("Caso de proyecto publicado por la empresa", "Project case published by the company"),
    observedAt: "2026-07-01",
    instrument: c("Documento público, lectura determinista", "Public document, deterministic reading"),
    limitation: c("Autodeclarado; sin confirmación del cliente.", "Self-declared; not confirmed by the client."),
  },
  {
    id: "src-hiring",
    title: c("Oferta de empleo publicada por la empresa", "Job posting published by the company"),
    observedAt: "2026-09-20",
    instrument: c("Portal de empleo público, lectura determinista", "Public job board, deterministic reading"),
    limitation: c(
      "Una oferta indica preparación, no actividad ya iniciada.",
      "A posting signals preparation, not activity already under way.",
    ),
  },
  {
    id: "src-reviews",
    title: c("Reseñas en un directorio profesional", "Reviews on a professional directory"),
    observedAt: "2026-09-10",
    instrument: c("6 reseñas públicas leídas", "6 public reviews read"),
    limitation: c("Muestra mínima; no mide satisfacción general.", "Minimal sample; does not measure overall satisfaction."),
  },
];

const NORTE: FamilyFacts = {
  sources: SOURCES,
  trend: {
    measure: c("Consultas de la muestra con la web en primera página", "Sample queries with the site on page one"),
    unit: "PERCENT",
    instrument: c("40 consultas fijas, primera página, España", "40 fixed queries, first page, Spain"),
    sample: c("40 consultas", "40 queries"),
    points: [
      { date: "2026-07-01", value: 18 },
      { date: "2026-08-01", value: null, note: c("Sin medición", "Not measured") },
      { date: "2026-09-01", value: 22 },
      { date: "2026-10-02", value: 31 },
    ],
    topics: [
      { label: c("eficiencia energética de edificios", "building energy efficiency"), delta: 12 },
      { label: c("aislamiento térmico", "thermal insulation"), delta: 3 },
      { label: c("ayudas a la eficiencia energética", "energy efficiency grants"), delta: -4 },
      { label: c("aerotermia", "heat pumps"), delta: null },
    ],
    pages: [
      { path: "/servicios/eficiencia-energetica", change: "GAINED" },
      { path: "/proyectos", change: "STABLE" },
      { path: "/blog/ayudas-2025", change: "LOST" },
      { path: "/contacto", change: "UNKNOWN" },
    ],
    sourceIds: ["src-search-sample"],
  },
  answerSpace: {
    surfaces: [
      { id: "assistant-a", label: c("Asistente A", "Assistant A"), observedAt: "2026-10-02", sample: 12 },
      { id: "assistant-b", label: c("Asistente B", "Assistant B"), observedAt: null, sample: null },
    ],
    questions: [
      {
        text: c("¿Quién aísla edificios en España?", "Who insulates buildings in Spain?"),
        cells: { "assistant-a": "MENTIONED", "assistant-b": "NOT_OBSERVED" },
      },
      {
        text: c("Empresas de aislamiento térmico cerca de Pamplona", "Thermal insulation firms near Pamplona"),
        cells: { "assistant-a": "ABSENT", "assistant-b": "NOT_OBSERVED" },
      },
      {
        text: c("¿Cómo reducir el consumo energético de un edificio?", "How to cut a building's energy use?"),
        cells: { "assistant-a": "CITED", "assistant-b": "NOT_OBSERVED" },
      },
    ],
    claims: [
      { text: c("Reforma edificios residenciales", "Retrofits residential buildings"), support: "SUPPORTED", sourceId: "src-capabilities" },
      { text: c("Instala aerotermia", "Installs heat pumps"), support: "UNSUPPORTED" },
      { text: c("Trabaja en Portugal", "Works in Portugal"), support: "UNKNOWN" },
    ],
    coOccurring: [
      { name: "Rehabita Norte", questions: 2 },
      { name: "Envolvente Pirineo", questions: 1 },
    ],
    sourceIds: ["src-generative-sample"],
  },
  opportunities: [
    {
      id: "opp-programme",
      title: c("Mejora energética de vivienda social", "Energy upgrade of social housing"),
      buyer: c("Agencia pública de vivienda", "Public housing agency"),
      market: c("España", "Spain"),
      form: c("Programa público", "Public programme"),
      deadline: null,
      epistemic: "POTENTIAL",
      capability: {
        label: c("Aislamiento térmico de edificios", "Thermal insulation of buildings"),
        excerpt: c(
          "«aislamiento térmico y reformas energéticas de edificios»",
          "“thermal insulation and energy retrofits of buildings”",
        ),
        sourceId: "src-capabilities",
      },
      demand: {
        label: c("Actuaciones sobre la envolvente térmica", "Thermal envelope works"),
        code: null,
        sourceId: "src-programme",
      },
      known: [
        { label: c("Ámbito", "Scope"), value: c("Vivienda social", "Social housing") },
        { label: c("Horizonte", "Horizon"), value: c("Hasta 2027", "Until 2027") },
      ],
      unknown: [
        c("Presupuesto por actuación", "Budget per action"),
        c("Solvencia exigida", "Required solvency"),
        c("Capacidad disponible de la empresa", "Company's available capacity"),
      ],
      whyPotential: c(
        "Hay demanda publicada y una capacidad declarada que encajan; ninguna fuente confirma que la empresa pueda o quiera optar.",
        "Published demand and a declared capability fit; no source confirms the company can or wants to bid.",
      ),
      observedAt: "2026-09-01",
    },
    {
      id: "opp-tender",
      title: c("Aislamiento de cubiertas en colegios públicos", "Roof insulation in public schools"),
      buyer: c("Ayuntamiento de Pamplona", "Pamplona City Council"),
      market: c("España", "Spain"),
      form: c("Licitación abierta", "Open tender"),
      deadline: "2026-10-28",
      epistemic: "POTENTIAL",
      capability: {
        label: c("Aislamiento térmico de edificios", "Thermal insulation of buildings"),
        excerpt: c(
          "«aislamiento térmico y reformas energéticas de edificios»",
          "“thermal insulation and energy retrofits of buildings”",
        ),
        sourceId: "src-capabilities",
      },
      demand: {
        label: c("Trabajos de aislamiento térmico", "Thermal insulation work"),
        code: "CPV 45321000",
        sourceId: "src-tender",
      },
      known: [
        { label: c("Plazo de oferta", "Bid deadline"), value: c("28 oct 2026", "28 Oct 2026") },
        { label: c("Procedimiento", "Procedure"), value: c("Abierto", "Open") },
      ],
      unknown: [
        c("Requisitos técnicos de los pliegos", "Technical requirements in tender documents"),
        c("Clasificación empresarial exigida", "Required contractor classification"),
        c("Proveedor actual", "Incumbent supplier"),
      ],
      whyPotential: c(
        "El comprador pide una categoría que la empresa declara ofrecer; los pliegos y su elegibilidad no se han leído.",
        "The buyer asks for a category the company declares; tender documents and eligibility are unread.",
      ),
      observedAt: "2026-10-01",
    },
  ],
  network: {
    nodes: [
      { id: "norte", label: "Norte Renovable", role: c("Empresa observada", "Observed company") },
      { id: "ribera", label: "Cooperativa Ribera", role: c("Cliente", "Client") },
      { id: "aislantes", label: "Aislantes del Ebro", role: c("Proveedor", "Supplier") },
      { id: "agencia", label: "Agencia de vivienda", role: c("Comprador público", "Public buyer") },
      { id: "ingenieria", label: "Ingeniería Arga", role: c("Socio técnico", "Technical partner") },
    ],
    edges: [
      {
        from: "norte",
        to: "ribera",
        kind: c("ejecutó una obra para", "carried out works for"),
        state: "OBSERVED",
        since: "2025-05-01",
        sourceId: "src-project-case",
        reason: c("Caso de proyecto publicado", "Published project case"),
      },
      {
        from: "aislantes",
        to: "norte",
        kind: c("suministró material a", "supplied material to"),
        state: "OBSERVED",
        since: "2025-05-01",
        sourceId: "src-project-case",
        reason: c("Nombrado en el mismo caso", "Named in the same case"),
      },
      {
        from: "norte",
        to: "agencia",
        kind: c("podría optar a programas de", "could bid for programmes of"),
        state: "POTENTIAL",
        since: null,
        sourceId: "src-programme",
        reason: c("Programa compatible con su capacidad", "Programme compatible with its capability"),
      },
      {
        from: "norte",
        to: "ingenieria",
        kind: c("podría colaborar con", "could partner with"),
        state: "POTENTIAL",
        since: null,
        sourceId: null,
        reason: c("Capacidades complementarias en la misma zona", "Complementary capabilities in the same area"),
      },
    ],
  },
  territory: {
    markets: [
      {
        code: "ES",
        label: c("España", "Spain"),
        state: "OBSERVED",
        currentness: "CURRENT",
        signal: c("Obras propias publicadas en el país", "Own works published in the country"),
        sourceId: "src-project-case",
      },
      {
        code: "PT",
        label: c("Portugal", "Portugal"),
        state: "POTENTIAL",
        currentness: "CURRENT",
        // Expansion needs the organization's own preparatory act (ADR-0089); demand
        // somewhere (the national programme) is never expansion evidence.
        signal: c("Busca jefe de obra en Lisboa", "Hiring a site manager in Lisbon"),
        sourceId: "src-hiring",
      },
      {
        code: "FR",
        label: c("Francia", "France"),
        state: "UNKNOWN",
        currentness: "UNKNOWN",
        signal: null,
        sourceId: null,
      },
      {
        code: "DE",
        label: c("Alemania", "Germany"),
        state: "UNKNOWN",
        currentness: "UNKNOWN",
        signal: null,
        sourceId: null,
      },
    ],
  },
  discourse: {
    statements: [
      {
        id: "st-punctual",
        text: c("Destacan la puntualidad de las obras", "Praise the punctuality of works"),
        where: c("Directorio profesional", "Professional directory"),
        date: "2026-09-10",
        materiality: "LOW",
        sample: c("4 de 6 reseñas", "4 of 6 reviews"),
      },
      {
        id: "st-delay",
        text: c("Una reseña menciona un retraso", "One review mentions a delay"),
        where: c("Directorio profesional", "Professional directory"),
        date: "2026-08-22",
        materiality: "LOW",
        contradicts: "st-punctual",
        sample: c("1 de 6 reseñas", "1 of 6 reviews"),
      },
    ],
    absences: [
      c("Sin cobertura observada en prensa sectorial", "No observed coverage in trade press"),
      c("Sin reseñas observadas en otras plataformas", "No observed reviews on other platforms"),
    ],
  },
  change: {
    events: [
      { date: "2026-07-01", kind: "EVIDENCE_ARRIVED", label: c("Ficha técnica observada", "Technical sheet observed"), sourceId: "src-capabilities" },
      { date: "2026-09-01", kind: "EVIDENCE_ARRIVED", label: c("Programa nacional publicado", "National programme published"), sourceId: "src-programme" },
      { date: "2026-09-01", kind: "HYPOTHESIS_UPDATED", label: c("Oportunidad potencial en vivienda social", "Potential opportunity in social housing"), sourceId: "src-programme" },
      { date: "2026-10-01", kind: "MATERIAL_CHANGE", label: c("Nueva licitación compatible", "New compatible tender"), sourceId: "src-tender" },
      { date: "2026-10-03", kind: "BECAME_STALE", label: c("La ficha técnica supera los 90 días", "The technical sheet passes 90 days"), sourceId: "src-capabilities" },
    ],
  },
};

const BY_ORGANIZATION: Record<string, FamilyFacts> = { norte: NORTE };

/** Facts visible at ``asOf``: nothing observed later leaks into an earlier cut. */
export function factsAt(organizationId: string, asOf: string): FamilyFacts {
  const all = BY_ORGANIZATION[organizationId];
  if (!all) return { sources: [] };
  const seen = (date: string | null) => date !== null && date <= asOf;
  const sources = all.sources.filter((s) => s.observedAt <= asOf);
  const known = new Set(sources.map((s) => s.id));
  return {
    sources,
    trend: all.trend && {
      ...all.trend,
      points: all.trend.points.filter((p) => p.date <= asOf),
      topics: known.has("src-search-sample") ? all.trend.topics : [],
      pages: known.has("src-search-sample") ? all.trend.pages : [],
    },
    answerSpace: all.answerSpace && known.has("src-generative-sample") ? all.answerSpace : undefined,
    opportunities: all.opportunities?.filter((o) => o.observedAt <= asOf),
    network: all.network && {
      nodes: all.network.nodes,
      edges: all.network.edges.filter((e) => e.sourceId === null || known.has(e.sourceId)),
    },
    territory: all.territory && {
      markets: all.territory.markets.map((m) =>
        m.sourceId && !known.has(m.sourceId)
          ? { ...m, state: "UNKNOWN", currentness: "UNKNOWN", signal: null, sourceId: null }
          : m,
      ),
    },
    discourse: all.discourse && {
      statements: all.discourse.statements.filter((s) => s.date <= asOf),
      absences: all.discourse.absences,
    },
    change: all.change && { events: all.change.events.filter((e) => seen(e.date)) },
  };
}

const EXPOSURE: Record<string, GardenExposure[]> = {
  // Derived from how the example delivers its work (at the customer's site), the same
  // rule spec 059 applies: the channel is known, the shock that travels it is not.
  norte: [
    {
      id: "fuel-and-travel",
      channel: c("Combustible y desplazamientos", "Fuel and travel"),
      path: c(
        "Trabaja en casa del cliente: una subida del combustible le llega aunque ocurra lejos.",
        "It works at the customer's site: a fuel price rise reaches it even when it starts far away.",
      ),
    },
    {
      id: "local-regulation",
      channel: c("Normativa donde trabaja", "Rules where it works"),
      path: c(
        "Un cambio normativo en España le afecta; uno en otro país, no.",
        "A rule change in Spain affects it; one in another country does not.",
      ),
    },
  ],
};

/** The example's garden at ``asOf``: the territory lens read as reach, never widened. */
export function gardenAt(organizationId: string, asOf: string): Garden | null {
  const facts = factsAt(organizationId, asOf);
  if (!facts.territory) return null;
  const sources = new Map(facts.sources.map((source) => [source.id, source]));
  const places: GardenPlace[] = facts.territory.markets.map((market) => ({
    code: market.code,
    label: market.label,
    state: market.state,
    currentness: market.currentness,
    basis: market.signal,
    source: market.sourceId ? sources.get(market.sourceId) : undefined,
  }));
  return {
    operating: places.filter((place) => place.state === "OBSERVED"),
    expansion: places.filter((place) => place.state === "POTENTIAL"),
    unknown: places.filter((place) => place.state === "UNKNOWN"),
    exposure: EXPOSURE[organizationId] ?? [],
  };
}
