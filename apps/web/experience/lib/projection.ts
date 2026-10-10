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
      "Cómo aparece la organización y si se la encuentra: buscadores, respuestas de IA y su web.",
      "How the organization appears and whether it can be found: search engines, AI answers and its website.",
    ),
  },
  {
    id: "reputation",
    name: c("Reputación", "Reputation"),
    color: "lavender",
    intro: c(
      "Qué se dice públicamente de la organización, dónde y con qué evidencia.",
      "What is said publicly about the organization, where, and with what evidence.",
    ),
  },
  {
    id: "value",
    name: c("Valor", "Value"),
    color: "sage",
    intro: c(
      "Qué sabe hacer y qué ofrece, según lo observado.",
      "What it can do and what it offers, according to what has been observed.",
    ),
  },
  {
    id: "markets",
    name: c("Mercados", "Markets"),
    color: "sand",
    intro: c(
      "Dónde tiene actividad observada y dónde solo hay potencial.",
      "Where activity is observed and where there is only potential.",
    ),
  },
  {
    id: "relationships",
    name: c("Relaciones", "Relationships"),
    color: "blue",
    intro: c(
      "Clientes, partners y proveedores con evidencia, y vínculos que merece la pena investigar.",
      "Customers, partners and suppliers backed by evidence, and links worth investigating.",
    ),
  },
  {
    id: "demand",
    name: c("Demanda", "Demand"),
    color: "sage",
    intro: c(
      "Dónde puede haber demanda para lo que hace. Una oportunidad es potencial, no un cliente.",
      "Where there may be demand for what it does. An opportunity is potential, not a customer.",
    ),
  },
  {
    id: "activity",
    name: c("Actividad", "Activity"),
    color: "lavender",
    intro: c(
      "Qué ocurre y qué ha cambiado con el tiempo.",
      "What happens and what has changed over time.",
    ),
  },
  {
    id: "economics",
    name: c("Economía", "Economics"),
    color: "sand",
    intro: c(
      "Qué cifras económicas se pueden observar y cuáles siguen siendo desconocidas.",
      "Which economic figures can be observed and which remain unknown.",
    ),
  },
  {
    id: "organization",
    name: c("Organización", "Organization"),
    color: "blue",
    intro: c(
      "Quién es: su identidad económica observable.",
      "Who it is: its observable economic identity.",
    ),
  },
  {
    id: "context",
    name: c("Contexto", "Context"),
    color: "sage",
    intro: c(
      "Regulación, tendencias y factores externos necesarios para interpretar las señales.",
      "Regulation, trends and external factors needed to interpret signals.",
    ),
  },
] as const;
export type FamilyId = (typeof families)[number]["id"];
export const demoOrganizationName = c("Organización Demo", "Demo Organization");
export const organizations = [
  {
    id: "norte",
    name: "Organización Demo",
    sector: c(
      "Eficiencia energética de edificios · ejemplo ficticio",
      "Building energy efficiency · fictional example",
    ),
    does: c(
      "Reforma edificios para que gasten menos energía: aislamiento, ventanas y climatización. Trabaja en España.",
      "Retrofits buildings so they use less energy: insulation, windows and heating. It works in Spain.",
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
    does: c(
      "Recupera materiales de construcción y los devuelve al mercado.",
      "Recovers construction materials and returns them to the market.",
    ),
    focusId: "focus-atlas",
    focusSince: "2026-09-01",
  },
  {
    id: "empty",
    name: "Nueva observación",
    sector: c("Sin organización seleccionada", "No organization selected"),
    does: c("Sin organización seleccionada.", "No organization selected."),
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
      "Ficha técnica de Organización Demo",
      "Demo Organization's technical sheet",
    ),
    source: c(
      "Ficha técnica pública · fuente ilustrativa",
      "Public technical sheet · illustrative source",
    ),
    publishedAt: "2026-06-24",
    observedAt: "2026-07-01",
    body: c(
      "La ficha de ejemplo describe aislamiento térmico y reformas energéticas de edificios. No acredita contratos, solvencia ni capacidad disponible.",
      "The example sheet describes thermal insulation and energy retrofits of buildings. It does not establish contracts, solvency or available capacity.",
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
      "Programa público de ayudas para que los edificios gasten menos energía",
      "Public grant programme to cut energy use in buildings",
    ),
    source: c(
      "Anuncio de programa · fuente ilustrativa",
      "Programme announcement · illustrative source",
    ),
    publishedAt: "2026-08-28",
    observedAt: "2026-09-01",
    body: c(
      "El anuncio (ficticio) financia obras para mejorar el aislamiento y la eficiencia energética de edificios. Es una posible demanda para Organización Demo, no un encargo ni un contrato.",
      "The (fictional) announcement funds works that improve the insulation and energy efficiency of buildings. It is possible demand for Demo Organization, not an order or a contract.",
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
      "Dos respuestas de asistentes de IA que la nombran",
      "Two AI assistant answers that name it",
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
  {
    id: "customer-case",
    title: c(
      "Caso de cliente publicado en la web de Organización Demo",
      "Customer case published on Demo Organization's website",
    ),
    source: c(
      "Página de casos · fuente ilustrativa",
      "Case study page · illustrative source",
    ),
    publishedAt: "2026-06-30",
    observedAt: "2026-07-01",
    body: c(
      "La página de casos menciona a Cooperativa Ribera como cliente de una rehabilitación. Es una declaración de la propia empresa.",
      "The case page names Cooperativa Ribera as a client of a renovation. It is the company's own statement.",
    ),
    basis: c(
      "Declaración pública del propio proveedor; no hay contrato ni factura visible.",
      "Public statement by the provider itself; no contract or invoice is visible.",
    ),
    limitation: c(
      "No confirma el contrato, su importe ni si la obra se completó.",
      "It does not confirm the contract, its value or whether the work was completed.",
    ),
  },
  {
    id: "tender",
    title: c(
      "Licitación municipal de rehabilitación de colegios",
      "Municipal tender for school building renovation",
    ),
    source: c(
      "Plataforma de contratación · fuente ilustrativa",
      "Procurement platform · illustrative source",
    ),
    publishedAt: "2026-09-14",
    observedAt: "2026-09-15",
    body: c(
      "Un ayuntamiento publica una licitación para mejorar el aislamiento y la eficiencia energética de varios colegios.",
      "A town council publishes a tender to improve insulation and energy efficiency in several schools.",
    ),
    basis: c(
      "Anuncio oficial de licitación; el alcance está en el pliego publicado.",
      "Official tender notice; the scope is in the published specification.",
    ),
    limitation: c(
      "Una licitación no es una adjudicación ni un cliente: falta conocer requisitos, plazos y solvencia exigida.",
      "A tender is not an award or a customer: requirements, deadlines and required solvency are still unknown.",
    ),
  },
  {
    id: "energy-rule",
    title: c(
      "Nueva exigencia de eficiencia energética para edificios existentes",
      "New energy-efficiency requirement for existing buildings",
    ),
    source: c(
      "Boletín oficial · fuente ilustrativa",
      "Official bulletin · illustrative source",
    ),
    publishedAt: "2026-06-20",
    observedAt: "2026-07-01",
    body: c(
      "Una norma publicada fija objetivos de mejora para edificios antiguos en un plazo de años.",
      "A published rule sets improvement targets for older buildings within a number of years.",
    ),
    basis: c(
      "Texto normativo publicado; el efecto práctico depende de cada edificio.",
      "Published regulatory text; the practical effect depends on each building.",
    ),
    limitation: c(
      "La norma no crea demanda concreta por sí sola ni indica quién la comprará.",
      "The rule does not create concrete demand by itself, nor say who will buy.",
    ),
  },
  {
    id: "public-works",
    title: c(
      "Obras publicadas en la web de la empresa este trimestre",
      "Works published on the company's website this quarter",
    ),
    source: c(
      "Noticias de la empresa · fuente ilustrativa",
      "Company news · illustrative source",
    ),
    publishedAt: "2026-09-28",
    observedAt: "2026-10-03",
    body: c(
      "La web publica tres actuaciones recientes con fotografías y descripción de la obra.",
      "The website publishes three recent works with photographs and a description of each.",
    ),
    basis: c(
      "Publicaciones propias de la empresa, con fechas visibles.",
      "The company's own posts, with visible dates.",
    ),
    limitation: c(
      "Son anuncios de la propia empresa: no muestran el volumen de negocio ni los resultados.",
      "They are the company's own announcements: they do not show business volume or results.",
    ),
  },
  {
    id: "audit-offer",
    title: c(
      "Oferta de auditoría energética previa a la obra",
      "Pre-works energy audit offer",
    ),
    source: c(
      "Página de servicios · fuente ilustrativa",
      "Services page · illustrative source",
    ),
    publishedAt: "2026-06-24",
    observedAt: "2026-07-01",
    body: c(
      "La página de servicios describe una auditoría energética antes de cada reforma.",
      "The services page describes an energy audit before each renovation.",
    ),
    basis: c(
      "Descripción de servicio publicada por la empresa.",
      "Service description published by the company.",
    ),
    limitation: c(
      "Describe la oferta; no demuestra su precio, su calidad ni que se ofrezca hoy.",
      "It describes the offer; it does not establish its price, quality or current availability.",
    ),
  },
];
export const signals: Signal[] = [
  {
    id: "renovation",
    organizationId: "norte",
    family: "markets",
    title: c(
      "Un programa público de ayudas encaja con lo que hace.",
      "A public grant programme fits what it does.",
    ),
    summary: c(
      "España ha publicado un programa que paga obras para que los edificios gasten menos energía. Encaja con lo que la empresa dice hacer; la elegibilidad y el encaje comercial siguen abiertos.",
      "Spain has published a programme that pays for works that cut buildings' energy use. It fits what the company says it does; eligibility and commercial fit remain open.",
    ),
    epistemic: "POTENTIAL",
    eventAt: "2026-08-28",
    detectedAt: "2026-09-01",
    availableFrom: "2026-09-01",
    evidenceIds: ["capabilities", "program"],
    why: c(
      "El programa paga el tipo de obra que Organización Demo dice hacer, en el país donde trabaja. Por eso merece una mirada más atenta.",
      "The programme pays for the kind of work Demo Organization says it does, in the country where it works. That is why it deserves a closer look.",
    ),
    derivation: c(
      "Lo que la empresa dice hacer + lo que el programa financia + dónde y cuándo → una posibilidad. No se ha visto adjudicación, cliente ni contrato.",
      "What the company says it does + what the programme funds + where and when → a possibility. No award, customer or contract has been seen.",
    ),
    limitation: c(
      "Falta saber si cumple los requisitos, si tiene capacidad libre y cuánto dinero hay por obra.",
      "Still unknown: whether it meets the requirements, whether it has free capacity and how much money there is per project.",
    ),
    next: c(
      "Leer los requisitos del programa antes de decidir si merece la pena presentarse.",
      "Read the programme's requirements before deciding whether it is worth applying.",
    ),
    dimensions: [
      {
        label: c("Capacidad", "Capability"),
        value: c("Encaja con lo que hace", "Fits what it does"),
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
      "Aparece mencionada en respuestas de asistentes de IA.",
      "It is mentioned in AI assistant answers.",
    ),
    summary: c(
      "En dos de las respuestas revisadas, un asistente de IA nombra a la empresa. Que la nombre no significa que la recomiende.",
      "In two of the answers reviewed, an AI assistant names the company. Naming it does not mean recommending it.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-09-30",
    detectedAt: "2026-10-03",
    availableFrom: "2026-10-03",
    evidenceIds: ["surface"],
    why: c(
      "Cada vez más clientes preguntan a asistentes de IA. Saber si la nombran, y cómo, importa.",
      "More and more customers ask AI assistants. Knowing whether they name it, and how, matters.",
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
      "Su ficha pública dice que aísla edificios para que gasten menos energía.",
      "Its public sheet says it insulates buildings so they use less energy.",
    ),
    summary: c(
      "Su ficha técnica dice que mejora el aislamiento térmico de edificios. Es lo que la empresa declara de sí misma.",
      "Its technical sheet says it improves the thermal insulation of buildings. It is what the company declares about itself.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-06-24",
    detectedAt: "2026-07-01",
    availableFrom: "2026-07-01",
    evidenceIds: ["capabilities"],
    why: c(
      "Saber qué hace permite reconocer qué demanda le encaja, sin inventarle un perfil.",
      "Knowing what it does makes it possible to recognise which demand fits it, without inventing a profile.",
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
      "Todavía no se puede valorar su reputación.",
      "Its reputation cannot be assessed yet.",
    ),
    summary: c(
      "Hay muy pocas opiniones públicas para sacar una conclusión. No saber no es una mala valoración.",
      "There are too few public opinions to draw a conclusion. Not knowing is not a bad rating.",
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
      "Comprobación de suficiencia: no existe una base adecuada en este ejemplo.",
      "Sufficiency check: no adequate basis exists in this example.",
    ),
    limitation: c(
      "Sin base suficiente para comparar o valorar.",
      "Insufficient basis to compare or assess.",
    ),
    next: c("Buscar más opiniones en fuentes públicas antes de valorar.", "Look for more opinions in public sources before assessing."),
    dimensions: [],
  },
  {
    id: "circular-pilot",
    organizationId: "atlas",
    family: "activity",
    title: c(
      "Publica un proyecto piloto con materiales recuperados.",
      "It publishes a pilot project with recovered materials.",
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
  {
    id: "audit-service",
    organizationId: "norte",
    family: "value",
    title: c(
      "Ofrece una auditoría energética antes de cada obra.",
      "It offers an energy audit before each works project.",
    ),
    summary: c(
      "Su web describe una auditoría previa a la reforma. Es una oferta declarada, no un resultado medido.",
      "Its website describes an audit before each renovation. It is a declared offer, not a measured result.",
    ),
    epistemic: "OBSERVED",
    eventAt: null,
    detectedAt: "2026-07-01",
    availableFrom: "2026-07-01",
    evidenceIds: ["audit-offer"],
    why: c(
      "Explica qué ofrece antes de vender una obra, lo que ayuda a entender su forma de trabajar.",
      "It shows what the company offers before a works contract, which helps understand how it works.",
    ),
    derivation: c(
      "Descripción publicada del servicio → oferta declarada. No se ha visto precio ni volumen.",
      "Published service description → declared offer. No price or volume has been seen.",
    ),
    limitation: c(
      "No se sabe si la auditoría se cobra, cuánto tarda ni qué resultados produce.",
      "It is unknown whether the audit is charged, how long it takes or what results it produces.",
    ),
    next: c(
      "Comparar con otras empresas que ofrezcan auditorías similares.",
      "Compare with other companies that offer similar audits.",
    ),
    dimensions: [
      { label: c("Tipo", "Type"), value: c("Servicio declarado", "Declared service") },
      { label: c("Precio", "Price"), value: c("Desconocido", "Unknown") },
    ],
  },
  {
    id: "client-reference",
    organizationId: "norte",
    family: "relationships",
    title: c(
      "Su web menciona a Cooperativa Ribera como cliente.",
      "Its website names Cooperativa Ribera as a client.",
    ),
    summary: c(
      "Hay una declaración pública de la empresa sobre un caso con esa cooperativa. Es lo que dice la empresa, no un contrato verificado.",
      "There is a public statement by the company about a case with that cooperative. It is what the company says, not a verified contract.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-06-30",
    detectedAt: "2026-07-01",
    availableFrom: "2026-07-01",
    evidenceIds: ["customer-case"],
    why: c(
      "Una relación declarada con un cliente conocido es una pista útil para entender su mercado.",
      "A declared relationship with a known client is a useful lead for understanding its market.",
    ),
    derivation: c(
      "Caso publicado por la empresa → relación declarada. No se ha verificado con la cooperativa.",
      "Case published by the company → declared relationship. It has not been verified with the cooperative.",
    ),
    limitation: c(
      "No se sabe si el contrato sigue vigente, su importe ni si la obra se completó.",
      "It is unknown whether the contract is still active, its value or whether the work was completed.",
    ),
    next: c(
      "Confirmar la relación solo si hay una fuente independiente.",
      "Confirm the relationship only with an independent source.",
    ),
    dimensions: [
      { label: c("Origen", "Origin"), value: c("Declaración de la empresa", "Company statement") },
      { label: c("Verificado", "Verified"), value: c("No", "No") },
    ],
  },
  {
    id: "school-tender",
    organizationId: "norte",
    family: "demand",
    title: c(
      "Hay una licitación de colegios que encaja con lo que hace.",
      "A school tender fits what it does.",
    ),
    summary: c(
      "Un ayuntamiento busca mejorar el aislamiento de varios colegios. La demanda es plausible; no es un cliente.",
      "A town council wants to improve insulation in several schools. The demand is plausible; it is not a customer.",
    ),
    epistemic: "POTENTIAL",
    eventAt: "2026-09-14",
    detectedAt: "2026-09-15",
    availableFrom: "2026-09-15",
    evidenceIds: ["tender"],
    why: c(
      "Es demanda pública y visible para un trabajo que la empresa describe. Merece una lectura de requisitos.",
      "It is visible public demand for work the company describes. It deserves a reading of the requirements.",
    ),
    derivation: c(
      "Licitación publicada + lo que la empresa dice hacer → una posibilidad. No hay adjudicación.",
      "Published tender + what the company says it does → a possibility. There is no award.",
    ),
    limitation: c(
      "Faltan requisitos, plazos, solvencia exigida y si la empresa concurre.",
      "Requirements, deadlines, required solvency and whether the company bids are still unknown.",
    ),
    next: c(
      "Leer el pliego antes de decidir si presentarse.",
      "Read the specification before deciding whether to bid.",
    ),
    dimensions: [
      { label: c("Tipo", "Type"), value: c("Licitación pública", "Public tender") },
      { label: c("Encaje", "Fit"), value: c("Plausible, por verificar", "Plausible, to verify") },
    ],
  },
  {
    id: "rule-context",
    organizationId: "norte",
    family: "context",
    title: c(
      "Una nueva norma sube las exigencias a edificios antiguos.",
      "A new rule raises the requirements for older buildings.",
    ),
    summary: c(
      "La norma publicada fija objetivos de mejora. Explica el entorno, no crea por sí sola una oportunidad.",
      "The published rule sets improvement targets. It explains the environment; on its own it creates no opportunity.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-06-20",
    detectedAt: "2026-07-01",
    availableFrom: "2026-07-01",
    evidenceIds: ["energy-rule"],
    why: c(
      "Cambia lo que los propietarios tendrán que hacer, y eso da contexto a cualquier oferta de reforma.",
      "It changes what owners will have to do, which gives context to any renovation offer.",
    ),
    derivation: c(
      "Texto normativo publicado → contexto regulatorio. No implica demanda concreta.",
      "Published regulatory text → regulatory context. It does not imply concrete demand.",
    ),
    limitation: c(
      "No se sabe cuántos edificios afectará en la práctica ni en qué plazo.",
      "It is unknown how many buildings it will affect in practice or on what timetable.",
    ),
    next: c(
      "Vigilar los reglamentos de aplicación.",
      "Watch the implementing regulations.",
    ),
    dimensions: [
      { label: c("Tipo", "Type"), value: c("Norma publicada", "Published rule") },
      { label: c("Alcance", "Reach"), value: c("Por verificar", "To verify") },
    ],
  },
  {
    id: "works-activity",
    organizationId: "norte",
    family: "activity",
    title: c(
      "Ha publicado tres obras recientes en su web.",
      "It has published three recent works on its website.",
    ),
    summary: c(
      "Son anuncios propios con fecha. Muestran actividad visible, no volumen de negocio.",
      "They are dated company announcements. They show visible activity, not business volume.",
    ),
    epistemic: "OBSERVED",
    eventAt: "2026-09-28",
    detectedAt: "2026-10-03",
    availableFrom: "2026-10-03",
    evidenceIds: ["public-works"],
    why: c(
      "Un ritmo de obras visible sugiere que la empresa está activa en este trimestre.",
      "A visible pace of works suggests the company is active this quarter.",
    ),
    derivation: c(
      "Publicaciones fechadas de la empresa → actividad declarada. No se ha visto facturación.",
      "Dated company posts → declared activity. No invoicing has been seen.",
    ),
    limitation: c(
      "No dice cuánto ingresa, cuántas obras acaba ni si las obras son típicas de su oferta.",
      "It does not say how much it earns, how many works it completes or whether they are typical of its offer.",
    ),
    next: c(
      "Seguir la publicación de obras los próximos meses.",
      "Follow published works over the coming months.",
    ),
    dimensions: [
      { label: c("Obras visibles", "Visible works"), value: c("3 en el trimestre", "3 this quarter") },
      { label: c("Facturación", "Revenue"), value: c("Desconocida", "Unknown") },
    ],
  },
  {
    id: "economics-unknown",
    organizationId: "norte",
    family: "economics",
    title: c(
      "Su tamaño y facturación no están publicados.",
      "Its size and revenue are not published.",
    ),
    summary: c(
      "No hay cuentas públicas visibles para esta organización de ejemplo. Lo que no se sabe se declara como desconocido.",
      "No public accounts are visible for this example organization. What is not known is declared as unknown.",
    ),
    epistemic: "UNKNOWN",
    eventAt: null,
    detectedAt: "2026-07-01",
    availableFrom: "2026-07-01",
    evidenceIds: ["capabilities"],
    why: c(
      "Sin datos económicos no se puede saber si la empresa puede asumir una licitación grande.",
      "Without economic data it is not possible to know whether the company can take on a large tender.",
    ),
    derivation: c(
      "No se ha encontrado un registro público de cuentas para esta organización de ejemplo.",
      "No public accounts record has been found for this example organization.",
    ),
    limitation: c(
      "Desconocido no significa negativo: solo significa que no se ha observado.",
      "Unknown does not mean negative: it only means it has not been observed.",
    ),
    next: c(
      "Buscar cuentas depositadas o pedirlas en una conversación real.",
      "Look for filed accounts or ask for them in a real conversation.",
    ),
    dimensions: [
      { label: c("Facturación", "Revenue"), value: c("Desconocida", "Unknown") },
      { label: c("Plantilla", "Staff"), value: c("Desconocida", "Unknown") },
    ],
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
  const instant = date ? new Date(/^\d{4}-\d{2}-\d{2}$/.test(date) ? date + "T12:00:00Z" : date) : null;
  return instant && Number.isFinite(instant.getTime())
    ? new Intl.DateTimeFormat(locale === "en" ? "en-GB" : locale, {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }).format(instant)
    : translate("Sin fecha acreditada", "No supported date", locale);
}
