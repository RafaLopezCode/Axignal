import { translate } from "./copy-catalog";
import type { Locale } from "./languages";
export type EditorialCopy = { es: string; en: string };
const c = (es: string, en: string): EditorialCopy => ({ es, en });
export const topics = [
  { id: "all", name: c("Todo el cuaderno", "The whole notebook") },
  { id: "perspective", name: c("Perspectiva", "Perspective") },
  { id: "evidence", name: c("Evidencia", "Evidence") },
  { id: "product", name: c("Dentro de AXIGNAL", "Inside AXIGNAL") },
] as const;
export type Article = {
  slug: string;
  topic: string;
  art: "certainty" | "layers" | "time" | "unknown" | "conversation" | "memory";
  title: EditorialCopy;
  deck: EditorialCopy;
  takeaway: EditorialCopy;
  sections: { title: EditorialCopy; body: EditorialCopy }[];
  source: { title: string; href: string };
};
const master = {
  title: "AXIGNAL · Modelo de producto",
  href: "/knowledge/basis/product-model",
};
const hfx = {
  title: "AXIGNAL · Human First Cognitive UX",
  href: "/knowledge/basis/human-first",
};
export const articles: Article[] = [
  {
    slug: "una-senal-no-es-una-certeza",
    topic: "evidence",
    art: "certainty",
    title: c("Una señal no es una certeza.", "A signal is not a certainty."),
    deck: c(
      "La diferencia entre algo que merece atención y algo que podemos afirmar.",
      "The difference between something worth noticing and something we can establish.",
    ),
    takeaway: c(
      "Una posibilidad abre una pregunta. La evidencia delimita la respuesta.",
      "A possibility opens a question. Evidence defines the limits of the answer.",
    ),
    sections: [
      {
        title: c("Primero, qué sabemos", "First, what we know"),
        body: c(
          "AXIGNAL distingue lo observado de lo potencial. Lo observado requiere evidencia admitida que sostenga una afirmación concreta. Incluso entonces, conviene preguntar qué se observó: una declaración de capacidad no acredita por sí sola una operación realizada. El alcance de la fuente importa tanto como su existencia. Una señal concentra atención sobre un cambio o una conexión relevante; su aparición no transforma automáticamente esa interpretación en un hecho.",
          "AXIGNAL distinguishes observed from potential. An observation requires admitted evidence supporting a specific claim. Even then, ask what was observed: a statement of capability does not, by itself, establish a completed operation. The scope of the source matters as much as its existence. A signal focuses attention on a relevant change or connection; its appearance does not automatically turn that interpretation into a fact.",
        ),
      },
      {
        title: c(
          "Una coincidencia abre investigación",
          "A match opens an investigation",
        ),
        body: c(
          "Imagina un ejemplo conceptual: una organización declara una capacidad y un programa publica una necesidad relacionada. La coincidencia puede merecer investigación. No demuestra que la organización sea cliente, proveedora, adjudicataria o una oportunidad comercial confirmada. Falta comprender alcance, condiciones, temporalidad y adecuación. AXIGNAL conserva esa posibilidad como potencial y hace inspeccionable el razonamiento que la conecta con sus fuentes.",
          "Consider a conceptual example: an organization declares a capability and a programme publishes a related need. The match may deserve investigation. It does not establish a customer, supplier, award recipient or confirmed commercial opportunity. Scope, conditions, timing and suitability still need to be understood. AXIGNAL keeps that possibility potential and makes the reasoning connecting it to its sources inspectable.",
        ),
      },
      {
        title: c("Acércate hasta la base", "Look closer at the basis"),
        body: c(
          "Lee primero qué merece tu atención. Después, si lo necesitas, abre la explicación, revisa el razonamiento y llega a la evidencia. Esas profundidades están disponibles directamente; no son pasos obligatorios. Comprueba las fechas y los límites antes de actuar. Una conclusión útil también puede ser que todavía no sabemos suficiente. Esa claridad protege la decisión y permite orientar mejor la siguiente pregunta.",
          "Read what deserves your attention first. Then, if needed, open the explanation, inspect the reasoning and reach the evidence. These depths are directly available, rather than mandatory steps. Check dates and limitations before acting. A useful conclusion may be that we still do not know enough. That clarity protects the decision and helps direct the next question.",
        ),
      },
    ],
    source: master,
  },
  {
    slug: "una-organizacion-una-mirada-un-mundo",
    topic: "perspective",
    art: "layers",
    title: c(
      "Una organización. Una mirada. Un mundo.",
      "An organization. A focus. A world.",
    ),
    deck: c(
      "Tres cosas conectadas que conviene mantener distintas.",
      "Three connected things that need to remain distinct.",
    ),
    takeaway: c(
      "Tú eliges dónde mirar. El mundo observado conserva su independencia.",
      "You choose where to look. The observed world keeps its independence.",
    ),
    sections: [
      {
        title: c(
          "La organización existe fuera de tu vista",
          "The organization exists beyond your view",
        ),
        body: c(
          "Una organización es un sujeto económico. Puede tener capacidades, actividades y relaciones sostenidas por evidencia. Elegirla en una interfaz no crea esa organización ni la convierte en propiedad de quien la observa. AXIGNAL mantiene un único mundo económico canónico, AXIGLAND, con memoria temporal y gobernada. La atención de distintas personas puede coincidir sobre una misma entidad sin crear versiones privadas de su verdad.",
          "An organization is an economic subject. It may have capabilities, activities and relationships supported by evidence. Selecting it in an interface neither creates it nor makes it the observer's property. AXIGNAL maintains one canonical economic world, AXIGLAND, with governed temporal memory. Different people's attention may meet around the same entity without creating private versions of its truth.",
        ),
      },
      {
        title: c(
          "El foco mantiene la atención",
          "The focus sustains attention",
        ),
        body: c(
          "El foco de observación, históricamente Xeed, es la asignación persistente de atención alrededor de ese sujeto. Organización y foco se relacionan, pero no son sinónimos. La primera responde a quién estamos observando; el segundo, a la continuidad de nuestra atención. El contexto privado y sus permisos pertenecen a su propia frontera. Ninguna preferencia de la persona puede editar directamente hechos económicos canónicos.",
          "The observation focus, historically Xeed, is a persistent allocation of attention around that subject. Organization and focus are related, but are not synonyms. The first answers who we observe; the second concerns the continuity of our attention. Private context and its permissions have their own boundary. No personal preference can directly edit canonical economic facts.",
        ),
      },
      {
        title: c(
          "Panorama te ayuda a comprender",
          "Panorama helps you understand",
        ),
        body: c(
          "Panorama es la proyección humana de ese mundo: una composición que selecciona contexto, cambios y señales para hacerlos comprensibles. No es AXIGLAND mismo. Dos vistas pueden destacar aspectos distintos y seguir siendo fieles a la misma base. Humanizar el lenguaje hace más fácil la experiencia sin sustituir la arquitectura que preserva sus distinciones.",
          "Panorama is the human projection of that world: a composition selecting context, changes and signals to make them understandable. It is not AXIGLAND itself. Two views can emphasize different aspects while remaining faithful to the same basis. Human language makes the experience easier without replacing the architecture that preserves its distinctions.",
        ),
      },
    ],
    source: master,
  },
  {
    slug: "el-contexto-tambien-tiene-fecha",
    topic: "evidence",
    art: "time",
    title: c("El contexto también tiene fecha.", "Context has a date, too."),
    deck: c(
      "Una fuente de ayer puede explicar el pasado sin describir el presente.",
      "Yesterday's source can explain the past without describing the present.",
    ),
    takeaway: c(
      "Publicado, observado y vigente responden a preguntas diferentes.",
      "Published, observed and current answer different questions.",
    ),
    sections: [
      {
        title: c(
          "Una fecha no cuenta toda la historia",
          "One date cannot tell the whole story",
        ),
        body: c(
          "La fecha de publicación indica cuándo apareció una fuente. La fecha de observación indica cuándo se obtuvo una observación. La vigencia pregunta si esa base sigue siendo aplicable al contexto que estamos leyendo. Confundirlas puede hacer que una señal parezca más reciente o más sólida de lo que realmente es. Por eso la temporalidad forma parte del significado, no solo de un pie de página.",
          "A publication date tells us when a source appeared. An observation date tells us when an observation was obtained. Currentness asks whether that basis still applies to the context we are reading. Confusing them can make a signal appear newer or stronger than it is. Time is therefore part of meaning, rather than a footnote.",
        ),
      },
      {
        title: c(
          "Cambiar de momento cambia la pregunta",
          "Changing the moment changes the question",
        ),
        body: c(
          "Cuando exploras una instantánea anterior, preguntas qué estaba disponible en ese momento. No debemos introducir evidencia futura en esa lectura. La línea de tiempo permite reconstruir el contexto sin tratar la historia como una lista de novedades. Los hechos posteriores pueden justificar una reevaluación actual, pero no reescriben silenciosamente lo que una persona podía conocer antes.",
          "When you explore an earlier snapshot, you ask what was available at that time. Future evidence must not enter that reading. A timeline reconstructs context without treating history as a news feed. Later facts may justify a current reevaluation, but do not silently rewrite what a person could know before.",
        ),
      },
      {
        title: c(
          "La memoria no es confianza eterna",
          "Memory is not permanent trust",
        ),
        body: c(
          "Reutilizar conocimiento evita empezar de cero. Sin embargo, reutilizar exige conservar procedencia, estado epistémico y actualidad. Si cambia una fuente relevante, las conclusiones dependientes deben poder revisarse. El contexto se acumula precisamente porque sus límites permanecen visibles: podemos reconocer qué se mantiene, qué cambió y qué necesita otra mirada.",
          "Reusing knowledge avoids starting from scratch. Yet reuse must preserve provenance, epistemic state and currentness. When a relevant source changes, dependent conclusions must be open to review. Context compounds precisely because its limits stay visible: we can recognize what holds, what changed and what needs another look.",
        ),
      },
    ],
    source: master,
  },
  {
    slug: "no-saber-es-un-estado-util",
    topic: "perspective",
    art: "unknown",
    title: c("No saber es un estado útil.", "Not knowing is a useful state."),
    deck: c(
      "Cómo una ausencia de evidencia puede orientar la siguiente pregunta.",
      "How an absence of evidence can guide the next question.",
    ),
    takeaway: c(
      "Desconocido no significa falso. Significa que la pregunta sigue abierta.",
      "Unknown does not mean false. It means the question remains open.",
    ),
    sections: [
      {
        title: c("El hueco tiene significado", "The gap has meaning"),
        body: c(
          "No encontrar una relación no demuestra que esa relación no exista. Puede faltar cobertura, una fuente adecuada o un contexto suficiente para responder. AXIGNAL conserva UNKNOWN como un estado distinto de FALSE. Convertir cada hueco en una respuesta negativa produciría una imagen del mundo más sencilla, pero también menos fiel. La interfaz debe ayudarte a reconocer ese límite sin obligarte a descifrar lenguaje técnico.",
          "Not finding a relationship does not prove that it does not exist. Coverage, a suitable source or enough context to answer may be missing. AXIGNAL keeps UNKNOWN distinct from FALSE. Turning every gap into a negative answer would create a simpler but less faithful picture of the world. The interface should help you recognize that limit without requiring technical vocabulary.",
        ),
      },
      {
        title: c(
          "Pregunta si es posible responder",
          "Ask whether it can be answered",
        ),
        body: c(
          "Antes de formular un juicio, conviene comprobar qué pregunta estamos haciendo y qué base necesitamos. Una evaluación estructurada no crea esa base. El modelo puede ayudar a interpretar dentro de una frontera definida, pero su respuesta no se convierte por sí sola en verdad canónica. Si falta contexto, la salida útil es investigar de manera gobernada o abstenerse de concluir.",
          "Before making a judgment, check which question we are asking and which basis it requires. A structured evaluation does not create that basis. A model can help interpret within a defined boundary, but its answer does not become canonical truth by itself. When context is missing, the useful outcome is governed research or abstaining from a conclusion.",
        ),
      },
      {
        title: c("Una recuperación con dirección", "Recovery with direction"),
        body: c(
          "Una vista vacía, una respuesta desconocida y un error de carga necesitan mensajes diferentes. La primera invita a orientar la atención. La segunda explica qué falta para concluir. El tercero permite recuperar la vista sin perder el contexto. Distinguir estos estados evita que una pantalla silenciosa parezca una afirmación sobre la economía.",
          "An empty view, an unknown answer and a loading error need different messages. The first invites you to direct attention. The second explains what is missing for a conclusion. The third lets you recover the view without losing context. Distinguishing these states prevents a silent screen from looking like a statement about the economy.",
        ),
      },
    ],
    source: hfx,
  },
  {
    slug: "axent-una-conversacion-con-contexto",
    topic: "product",
    art: "conversation",
    title: c(
      "AXENT: una conversación con contexto.",
      "AXENT: a conversation with context.",
    ),
    deck: c(
      "Investigar y explicar desde lo que estás mirando, con una base que puedes inspeccionar.",
      "Research and explanation rooted in what you are viewing, with an inspectable basis.",
    ),
    takeaway: c(
      "AXENT puede orientar tu mirada. La autoridad de la evidencia permanece separada.",
      "AXENT can guide your attention. Evidence authority remains separate.",
    ),
    sections: [
      {
        title: c(
          "La pregunta empieza en tu contexto",
          "A question starts in your context",
        ),
        body: c(
          "Una conversación útil no necesita que repitas cada organización, señal y fecha que ya estás mirando. AXENT conserva el contexto de lectura para investigar, explicar y ayudar a navegar. Ese contexto no equivale al historial de acciones de la interfaz. Cambiar una pestaña no debe convertirse en una respuesta; una conversación debe aportar comprensión a la pregunta que haces.",
          "A useful conversation should not require you to repeat every organization, signal and date already in view. AXENT retains reading context to research, explain and help navigate. That context is not the interface's action history. Changing a tab should not become an answer; a conversation should add understanding to your question.",
        ),
      },
      {
        title: c(
          "Explicar conserva las fronteras",
          "Explanation keeps the boundaries",
        ),
        body: c(
          "AXENT no tiene autoridad para inventar o admitir verdad económica. Cuando presenta una lectura material, debe mantener un camino hacia su evidencia, derivación y límites temporales. Las capacidades reales del entorno también importan: una demo sin modelo en vivo debe decirlo. Una tarea de investigación no puede darse por realizada solo porque la interfaz muestre una animación o una frase convincente.",
          "AXENT has no authority to invent or admit economic truth. A material interpretation must retain a path to evidence, derivation and temporal limits. The environment's actual capabilities matter too: a demo without a live model must say so. Research cannot be treated as completed merely because an interface shows an animation or a convincing sentence.",
        ),
      },
      {
        title: c(
          "La composición también es gobernada",
          "Composition is governed, too",
        ),
        body: c(
          "La IA puede sugerir dónde poner la atención y qué referencias autorizadas conviene mostrar. Un registro controlado de componentes transforma esa propuesta en una composición legible. El plan no contiene hechos nuevos ni código arbitrario. La aplicación comprueba alcance y actualidad antes de renderizar. Así, una experiencia generativa puede ser expresiva sin convertir la presentación en una nueva autoridad.",
          "AI may suggest where attention belongs and which authorized references to display. A controlled component registry turns that proposal into a readable composition. The plan contains neither new facts nor arbitrary code. The application checks scope and currentness before rendering. A generative experience can then be expressive without turning presentation into a new authority.",
        ),
      },
    ],
    source: hfx,
  },
  {
    slug: "comprender-sin-empezar-de-cero",
    topic: "product",
    art: "memory",
    title: c(
      "Comprender sin empezar de cero.",
      "Understand without starting from scratch.",
    ),
    deck: c(
      "La memoria económica importa cuando conserva también cómo llegó a saber.",
      "Economic memory matters when it also preserves how it came to know.",
    ),
    takeaway: c(
      "El conocimiento se acumula. Sus condiciones también deben acompañarlo.",
      "Knowledge compounds. Its conditions must travel with it.",
    ),
    sections: [
      {
        title: c(
          "La continuidad permite mejores preguntas",
          "Continuity supports better questions",
        ),
        body: c(
          "Una observación aislada puede ser útil. Una memoria que conecta observaciones, contexto y cambio permite preguntar de manera diferente. AXIGNAL busca inteligencia económica que se acumula: las próximas lecturas aprovechan lo aprendido sin confundir cantidad de información con comprensión. La cartografía es el sustrato de ese razonamiento, no un índice cuyo único propósito sea enumerar entidades.",
          "An isolated observation can be useful. Memory connecting observations, context and change makes different questions possible. AXIGNAL seeks compounding economic intelligence: future readings use what was learned without confusing information volume with understanding. Cartography supports that reasoning; it is not an index whose only purpose is to list entities.",
        ),
      },
      {
        title: c(
          "Compartir no borra los límites",
          "Sharing does not erase boundaries",
        ),
        body: c(
          "Una observación pública autorizada puede reutilizarse en contextos pertinentes, conservando derechos, procedencia, estado y actualidad. Esa posibilidad no permite mezclar información privada entre personas o ámbitos. La misma base puede alimentar preguntas distintas, pero el significado específico del foco necesita recalcularse para cada contexto. No contamos dos veces una observación para que una conclusión parezca más fuerte.",
          "An authorized public observation may be reused in relevant contexts while retaining rights, provenance, state and currentness. That does not permit private information to be mixed across people or scopes. The same basis can inform different questions, but focus-specific meaning must be recomputed for each context. We do not count an observation twice to make a conclusion appear stronger.",
        ),
      },
      {
        title: c(
          "Recordar incluye reevaluar",
          "Remembering includes reevaluation",
        ),
        body: c(
          "La memoria no debe inmovilizar el mundo. Fuentes y circunstancias cambian; una conclusión puede necesitar revisión. Conservar la trazabilidad ayuda a entender qué depende de qué. La experiencia humana empieza con una lectura simple y permite profundizar cuando una decisión lo merece. Esa combinación de claridad y rigor hace que el contexto sea algo que podemos usar, no solo almacenar.",
          "Memory must not freeze the world. Sources and circumstances change; a conclusion may need review. Preserving traceability helps explain what depends on what. The human experience begins with a simple reading and lets you go deeper when a decision warrants it. Clarity and rigor together make context something we can use, not merely store.",
        ),
      },
    ],
    source: master,
  },
];
export function readingMinutes(article: Article, locale: Locale) {
  const words = [
    translate(article.deck.es, article.deck.en, locale),
    ...article.sections.map(
      (s) =>
        translate(s.title.es, s.title.en, locale) +
        " " +
        translate(s.body.es, s.body.en, locale),
    ),
    translate(article.takeaway.es, article.takeaway.en, locale),
  ]
    .join(" ")
    .trim()
    .split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 180));
}
export function filterArticles(query: string, topic: string, locale: Locale) {
  const normalize = (value: string) =>
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase(locale);
  const needle = normalize(query.trim());
  return articles.filter(
    (a) =>
      (topic === "all" || a.topic === topic) &&
      normalize(
        translate(a.title.es, a.title.en, locale) +
          " " +
          translate(a.deck.es, a.deck.en, locale),
      ).includes(needle),
  );
}
