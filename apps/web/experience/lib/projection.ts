import { translate } from "./copy-catalog";
import type { Locale } from "./languages";
import type { Copy } from "./locale";
const c = (es: string, en: string): Copy => ({ es, en });
export type Epistemic = "OBSERVED" | "POTENTIAL" | "UNKNOWN";
export const families = [
  {
    id: "presence",
    name: c("Presencia", "Presence"),
    color: "blue",
    intro: c(
      "Cómo se hace visible una organización.",
      "How an organization becomes visible.",
    ),
  },
  {
    id: "reputation",
    name: c("Reputación", "Reputation"),
    color: "lavender",
    intro: c(
      "Qué se expresa públicamente y con qué límites.",
      "What is expressed publicly, and its limits.",
    ),
  },
  {
    id: "value",
    name: c("Valor", "Value"),
    color: "sage",
    intro: c(
      "Qué capacidades pueden aportar valor y bajo qué condiciones.",
      "What capabilities could add value, and under what conditions.",
    ),
  },
  {
    id: "markets",
    name: c("Mercados", "Markets"),
    color: "sand",
    intro: c(
      "Dónde cambia el contexto para las capacidades observadas.",
      "Where context changes for observed capabilities.",
    ),
  },
  {
    id: "relationships",
    name: c("Relaciones", "Relationships"),
    color: "blue",
    intro: c(
      "Vínculos sostenidos por evidencia; caminos que merecen investigación.",
      "Evidence-backed relationships; paths worth investigating.",
    ),
  },
  {
    id: "demand",
    name: c("Demanda", "Demand"),
    color: "sage",
    intro: c(
      "Necesidades económicas, sin convertirlas en clientes.",
      "Economic needs, without turning them into customers.",
    ),
  },
  {
    id: "activity",
    name: c("Actividad", "Activity"),
    color: "lavender",
    intro: c(
      "Qué ocurre y cuándo podemos sostener que ocurrió.",
      "What happens, and when we can support that it happened.",
    ),
  },
  {
    id: "economics",
    name: c("Economía", "Economics"),
    color: "sand",
    intro: c(
      "Condiciones económicas y límites de lo que sabemos.",
      "Economic conditions and the limits of our knowledge.",
    ),
  },
  {
    id: "organization",
    name: c("Organización", "Organization"),
    color: "blue",
    intro: c(
      "El sujeto económico y sus capacidades observadas.",
      "The economic subject and its observed capabilities.",
    ),
  },
  {
    id: "context",
    name: c("Contexto", "Context"),
    color: "sage",
    intro: c(
      "Entender el entorno antes de interpretar una señal.",
      "Understand the surroundings before interpreting a signal.",
    ),
  },
] as const;
export type FamilyId = (typeof families)[number]["id"];
export const organizations = [
  {
    id: "norte",
    name: "Norte Renovable",
    sector: c(
      "Rehabilitación energética · ejemplo ficticio",
      "Energy renovation · fictional example",
    ),
    focusId: "focus-norte",
    focusSince: "2026-07-01",
  },
  {
    id: "atlas",
    name: "Atlas Circular",
    sector: c(
      "Materiales recuperados · ejemplo ficticio",
      "Recovered materials · fictional example",
    ),
    focusId: "focus-atlas",
    focusSince: "2026-09-01",
  },
  {
    id: "empty",
    name: "Nueva observación",
    sector: c("Sin organización seleccionada", "No organization selected"),
    focusId: null,
    focusSince: null,
  },
] as const;
export const snapshots = [
  { date: "2026-07-01", label: c("Julio", "July") },
  { date: "2026-09-01", label: c("Septiembre", "September") },
  { date: "2026-10-03", label: c("Ahora", "Now") },
] as const;
export type Signal = {
  id: string;
  organizationId: string;
  family: FamilyId;
  title: Copy;
  summary: Copy;
  epistemic: Epistemic;
  eventAt: string | null;
  detectedAt: string;
  availableFrom: string;
  evidenceIds: string[];
  why: Copy;
  derivation: Copy;
  limitation: Copy;
  next: Copy;
  dimensions: { label: Copy; value: Copy }[];
};
export type Evidence = {
  id: string;
  title: Copy;
  source: Copy;
  publishedAt: string;
  observedAt: string;
  body: Copy;
  basis: Copy;
  limitation: Copy;
  instrument?: Copy;
};
export const evidence: Evidence[] = [
  {
    id: "capabilities",
    title: c(
      "Una capacidad declarada y documentada",
      "A declared, documented capability",
    ),
    source: c(
      "Ficha técnica pública · fuente ilustrativa",
      "Public technical sheet · illustrative source",
    ),
    publishedAt: "2026-06-24",
    observedAt: "2026-07-01",
    body: c(
      "La ficha de ejemplo describe rehabilitación térmica y coordinación técnica de edificios. No acredita contratos, solvencia ni capacidad disponible.",
      "The example sheet describes thermal renovation and technical building coordination. It does not establish contracts, solvency or available capacity.",
    ),
    basis: c(
      "Declaración explícita del documento; alcance limitado a la capacidad descrita.",
      "Explicit statement in the document; scope limited to the capability described.",
    ),
    limitation: c(
      "La declaración no demuestra ejecución ni disponibilidad actual.",
      "The declaration does not establish execution or current availability.",
    ),
  },
  {
    id: "program",
    title: c(
      "Un programa abre un contexto de demanda",
      "A programme opens a demand context",
    ),
    source: c(
      "Anuncio de programa · fuente ilustrativa",
      "Programme announcement · illustrative source",
    ),
    publishedAt: "2026-08-28",
    observedAt: "2026-09-01",
    body: c(
      "El anuncio ficticio contempla actuaciones de rehabilitación energética en edificios. Su calendario y requisitos crean un contexto de investigación; no una relación comercial.",
      "The fictional announcement concerns energy renovation of buildings. Its schedule and requirements create research context, not a commercial relationship.",
    ),
    basis: c(
      "Ámbito publicado en el anuncio y fecha del programa.",
      "Scope published in the announcement and programme date.",
    ),
    limitation: c(
      "Desconocemos presupuesto adjudicado, elegibilidad concreta y encaje comercial.",
      "Awarded budget, specific eligibility and commercial fit are unknown.",
    ),
  },
  {
    id: "pilot",
    title: c(
      "Se publica un piloto de materiales recuperados",
      "A recovered-materials pilot is published",
    ),
    source: c(
      "Memoria del proyecto · fuente ilustrativa",
      "Project report · illustrative source",
    ),
    publishedAt: "2026-09-25",
    observedAt: "2026-10-03",
    body: c(
      "La memoria ficticia describe un piloto local y sus materiales. Es evidencia del anuncio del piloto, sin demostrar una relación contractual entre actores.",
      "The fictional report describes a local pilot and its materials. It supports the pilot announcement, without establishing a contractual relationship between actors.",
    ),
    basis: c(
      "Publicación explícita del piloto; no inferir clientes a partir de coapariciones.",
      "Explicit publication of the pilot; do not infer customers from co-occurrence.",
    ),
    limitation: c(
      "Resultados, escalado y relaciones comerciales no verificados.",
      "Results, scaling and commercial relationships are unverified.",
    ),
  },
  {
    id: "surface",
    title: c(
      "Una mención cambia en una muestra pública",
      "A mention changes in a public sample",
    ),
    source: c(
      "Muestra de respuesta generativa · ilustrativa",
      "Generative response sample · illustrative",
    ),
    publishedAt: "2026-09-30",
    observedAt: "2026-10-03",
    body: c(
      "En dos respuestas de ejemplo aparece el nombre de la organización. La mención observada no implica cita, recomendación, cuota de mercado ni realidad del negocio.",
      "The organization name appears in two example responses. The observed mention does not imply citation, endorsement, market share or business reality.",
    ),
    basis: c(
      "Respuesta de superficie preservada bajo condiciones concretas.",
      "Preserved surface response under specific conditions.",
    ),
    instrument: c(
      "Instrumento DEMO-DRI v1 · consulta ilustrativa · español · 2 muestras · 30 sep 2026. Sin estimación poblacional.",
      "DEMO-DRI v1 instrument · illustrative prompt · Spanish · 2 samples · 30 Sep 2026. No population estimate.",
    ),
    limitation: c(
      "Muestra pequeña; incertidumbre no cuantificada. No representa estabilidad ni rendimiento.",
      "Small sample; uncertainty not quantified. Does not represent stability or performance.",
    ),
  },
];
export const signals: Signal[] = [
  {
    id: "renovation",
    organizationId: "norte",
    family: "markets",
    title: c(
      "La rehabilitación abre una nueva conversación.",
      "Renovation opens a new conversation.",
    ),
    summary: c(
      "Una capacidad conocida encuentra un contexto de demanda. Hay una posibilidad que investigar; el encaje comercial sigue abierto.",
      "A known capability meets a demand context. There is a possibility to investigate; commercial fit remains open.",
    ),
    epistemic: "POTENTIAL",
    eventAt: "2026-08-28",
    detectedAt: "2026-09-01",
    availableFrom: "2026-09-01",
    evidenceIds: ["capabilities", "program"],
    why: c(
      "El programa contempla actuaciones relacionadas con la capacidad descrita por Norte Renovable. La coincidencia es una razón para mirar más de cerca.",
      "The programme covers work related to Norte Renovable's described capability. That overlap is a reason to look closer.",
    ),
    derivation: c(
      "Capacidad declarada + ámbito del programa + contexto temporal → posibilidad derivada. No se ha observado adjudicación, cliente ni contrato.",
      "Declared capability + programme scope + temporal context → derived possibility. No award, customer or contract has been observed.",
    ),
    limitation: c(
      "Elegibilidad, alcance geográfico por capacidad, recursos disponibles y condiciones económicas pendientes.",
      "Eligibility, geographic reach per capability, available resources and economic conditions remain unresolved.",
    ),
    next: c(
      "Investigar requisitos y alcance antes de evaluar el encaje.",
      "Investigate requirements and reach before assessing fit.",
    ),
    dimensions: [
      {
        label: c("Capacidad", "Capability"),
        value: c("Coincidencia temática", "Thematic overlap"),
      },
      { label: c("Alcance", "Reach"), value: c("Por verificar", "To verify") },
      {
        label: c("Condiciones", "Conditions"),
        value: c("Desconocidas", "Unknown"),
      },
    ],
  },
  {
    id: "representation",
    organizationId: "norte",
    family: "presence",
    title: c(
      "Una mención aparece. Su significado tiene límites.",
      "A mention appears. Its meaning has limits.",
    ),
    summary: c(
      "La organización aparece en una muestra generativa. Observamos la superficie, sin confundirla con una recomendación o con el negocio.",
      "The organization appears in a generative sample. We observe the surface without equating it with endorsement or business reality.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-09-30",
    detectedAt: "2026-10-03",
    availableFrom: "2026-10-03",
    evidenceIds: ["surface"],
    why: c(
      "Conviene entender cómo se representa públicamente la organización y qué información acompaña a la mención.",
      "It is useful to understand how the organization is publicly represented and what information accompanies the mention.",
    ),
    derivation: c(
      "Observación de una respuesta bajo condiciones documentadas. Alcance exclusivo de esa muestra.",
      "Observation of a response under documented conditions. Scope restricted to this sample.",
    ),
    limitation: c(
      "No acredita cita, endorsement, reputación general ni conocimiento del negocio.",
      "Does not establish citation, endorsement, general reputation or business knowledge.",
    ),
    next: c(
      "Ampliar la muestra con investigación autorizada.",
      "Expand the sample through authorized research.",
    ),
    dimensions: [
      {
        label: c("Muestra", "Sample"),
        value: c("2 respuestas", "2 responses"),
      },
      {
        label: c("Instrumento", "Instrument"),
        value: c("DEMO-DRI v1", "DEMO-DRI v1"),
      },
    ],
  },
  {
    id: "capability",
    organizationId: "norte",
    family: "organization",
    title: c(
      "Una capacidad ayuda a situar el panorama.",
      "A capability helps frame the panorama.",
    ),
    summary: c(
      "Una ficha pública describe rehabilitación térmica. Es contexto documentado, con un alcance concreto.",
      "A public sheet describes thermal renovation. It is documented context with a specific scope.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-06-24",
    detectedAt: "2026-07-01",
    availableFrom: "2026-07-01",
    evidenceIds: ["capabilities"],
    why: c(
      "Entender la capacidad descrita permite orientar atención sin inventar un perfil comercial.",
      "Understanding the described capability helps direct attention without inventing a commercial profile.",
    ),
    derivation: c(
      "Declaración explícita en una ficha de ejemplo; observación limitada a esa declaración.",
      "Explicit declaration in an example sheet; observation limited to that declaration.",
    ),
    limitation: c(
      "Experiencia ejecutada y recursos disponibles no verificados.",
      "Executed experience and available resources are unverified.",
    ),
    next: c(
      "Contrastar la declaración con evidencia adicional.",
      "Compare the declaration with additional evidence.",
    ),
    dimensions: [],
  },
  {
    id: "reputation-gap",
    organizationId: "norte",
    family: "reputation",
    title: c(
      "Aún no podemos sostener una lectura de reputación.",
      "We cannot yet support a reputation reading.",
    ),
    summary: c(
      "Falta una muestra suficiente y contextualizada. La ausencia de conocimiento no es una valoración negativa.",
      "A sufficient, contextualized sample is missing. Absence of knowledge is not a negative assessment.",
    ),
    epistemic: "UNKNOWN",
    eventAt: null,
    detectedAt: "2026-07-01",
    availableFrom: "2026-07-01",
    evidenceIds: [],
    why: c(
      "Una conclusión sería prematura.",
      "A conclusion would be premature.",
    ),
    derivation: c(
      "Comprobación de suficiencia: no existe una base adecuada en esta demostración.",
      "Sufficiency check: no adequate basis exists in this demonstration.",
    ),
    limitation: c(
      "Sin base suficiente para comparar o valorar.",
      "Insufficient basis to compare or assess.",
    ),
    next: c("Definir una investigación acotada.", "Define bounded research."),
    dimensions: [],
  },
  {
    id: "circular-pilot",
    organizationId: "atlas",
    family: "activity",
    title: c(
      "Un piloto pone el contexto en movimiento.",
      "A pilot puts context in motion.",
    ),
    summary: c(
      "Se publica una experiencia de materiales recuperados. El anuncio amplía el contexto, sin establecer vínculos comerciales.",
      "A recovered-materials experience is published. The announcement expands context without establishing commercial relationships.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-09-25",
    detectedAt: "2026-10-03",
    availableFrom: "2026-10-03",
    evidenceIds: ["pilot"],
    why: c(
      "El piloto permite investigar capacidades y condiciones de escalado.",
      "The pilot allows research into capabilities and conditions for scaling.",
    ),
    derivation: c(
      "Publicación explícita del piloto en una memoria ilustrativa.",
      "Explicit publication of the pilot in an illustrative report.",
    ),
    limitation: c(
      "Resultados y continuidad todavía no verificados.",
      "Results and continuity are not yet verified.",
    ),
    next: c(
      "Examinar los resultados publicados cuando exista evidencia.",
      "Examine published results when evidence exists.",
    ),
    dimensions: [],
  },
];
export type ProjectionContext = {
  organizationId: string;
  family: FamilyId;
  signalId: string | null;
  asOf: string;
  revision: string;
};
export const makeContext = (
  organizationId = "norte",
  family: FamilyId = "markets",
  asOf = "2026-10-03",
  signalId: string | null = null,
): ProjectionContext => ({
  organizationId,
  family,
  asOf,
  signalId,
  revision: [organizationId, family, asOf, signalId ?? "overview"].join(":"),
});
export function project(context: ProjectionContext) {
  const visible = signals.filter(
    (s) =>
      s.organizationId === context.organizationId &&
      s.availableFrom <= context.asOf,
  );
  const sourceIds = new Set(visible.flatMap((s) => s.evidenceIds));
  return {
    mode: "FIXTURE_ONLY" as const,
    context,
    organization: organizations.find((o) => o.id === context.organizationId)!,
    signals: visible,
    evidence: evidence.filter(
      (e) => sourceIds.has(e.id) && e.observedAt <= context.asOf,
    ),
    families,
  };
}
export function dateLabel(date: string | null, locale: Locale) {
  return date
    ? new Intl.DateTimeFormat(locale === "en" ? "en-GB" : locale, {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }).format(new Date(date + "T12:00:00Z"))
    : translate("Sin fecha acreditada", "No supported date", locale);
}
