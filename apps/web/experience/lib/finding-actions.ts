/**
 * What a reader can do about one finding, and what AXENT would look into next, built from
 * that finding's own data (the sites an assistant cites, who it names instead, the checks
 * that fail). Deterministic and specific: never a generic paragraph, never a promise that a
 * step will change a result. Advice, not execution: AXIGNAL observes and measures again.
 */
import type { Discovery } from "./subscriber-contracts";

type Translate = (es: string, en: string) => string;
export type FindingActions = { act: string[]; research: string[] };

const list = (values: string[], max = 4) => values.filter(Boolean).slice(0, max).join(", ");

/** Names from a detail list of names, [name, count] pairs or {name} objects. */
function names(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map(v => Array.isArray(v) ? String(v[0] ?? "") : v && typeof v === "object" ? String((v as Record<string, unknown>).name ?? (v as Record<string, unknown>).host ?? "") : String(v ?? "")).filter(Boolean);
}

function failingTitles(detail: Record<string, unknown>, category: string): string[] {
  const failing = detail.failing && typeof detail.failing === "object" ? (detail.failing as Record<string, unknown>)[category] : null;
  return Array.isArray(failing) ? failing.map(f => String((f as Record<string, unknown>).title ?? "")).filter(Boolean) : [];
}

export function findingActions(d: Discovery, t: Translate): FindingActions | null {
  const detail = d.detail as Record<string, unknown>;
  const again = t("Vuelve a medir dentro de unas semanas: estos resultados cambian despacio y una sola medición no es una tendencia.", "Measure again in a few weeks: these results change slowly and a single measurement is not a trend.");
  if (d.kind === "GENERATIVE_VISIBILITY") {
    const competitors = names(detail.competitorsNamed);
    const sites = names(detail.sitesCited);
    switch (d.code) {
      case "AI_NOT_NAMED_FOR_CATEGORY":
      case "AI_NAMED_FOR_CATEGORY":
      case "GENERATIVE_VISIBILITY_MEASURED": return {
        act: [
          t("Que su web diga en frases claras qué hace, para quién y dónde, con una página por actividad: es lo que leen los asistentes para responder.", "Make its website say in plain sentences what it does, for whom and where, with one page per activity: that is what assistants read to answer."),
          ...(competitors.length ? [t("Mira qué publican las organizaciones que sí nombra ({names}): páginas de servicio claras, comparativas y presencia en webs de terceros.", "Look at what the organizations it does name publish ({names}): clear service pages, comparisons and presence on third-party sites.").replace("{names}", list(competitors))] : []),
          t("Consigue estar en las webs que el asistente cita para esa pregunta (directorios, comparativas, medios del sector): ver el hallazgo «Webs que cita».", "Get onto the sites the assistant cites for that question (directories, comparisons, trade media): see the “Sites it cites” finding."),
          again,
        ],
        research: [
          t("Si el resultado se repite con otras formulaciones de la pregunta y en otros idiomas de sus mercados.", "Whether the result holds with other wordings of the question and in the languages of its markets."),
          t("Qué tienen en común las organizaciones que el asistente nombra y ella no: tipo de web, fuentes que las mencionan.", "What the organizations the assistant names have in common that it lacks: kind of website, sources that mention them."),
        ],
      };
      case "AI_CITED_SOURCES": return {
        act: [
          t("Estas webs alimentan la respuesta del asistente: {sites}. Revisa si la organización aparece en ellas.", "These sites feed the assistant's answer: {sites}. Check whether the organization appears on them.").replace("{sites}", list(sites, 6)),
          t("Si no aparece, busca cómo entrar en cada una: ficha en un directorio, artículo o comparativa, nota de prensa o reseña. Empieza por las que más se citan.", "If it does not, find how to get onto each: a directory listing, an article or comparison, a press release or a review. Start with the most cited."),
          again,
        ],
        research: [
          t("Qué páginas de {sites} tratan de su sector y si alguna la nombra.", "Which pages of {sites} cover its sector and whether any names it.").replace("{sites}", list(sites, 3)),
          t("Qué organizaciones aparecen en esas webs y si son las mismas que el asistente nombra.", "Which organizations appear on those sites and whether they are the ones the assistant names."),
        ],
      };
      case "AI_DOES_NOT_KNOW_BRAND": return {
        act: [
          t("Haz que su nombre sea una entidad reconocible: datos estructurados Organization con enlaces sameAs a sus perfiles oficiales.", "Make its name a recognizable entity: Organization structured data with sameAs links to its official profiles."),
          t("Consigue menciones en fuentes que los asistentes citan: prensa, directorios del sector, Wikidata si es notable.", "Earn mentions in sources assistants cite: press, trade directories, Wikidata if it is notable."),
          again,
        ],
        research: [t("Qué fuentes públicas citables la nombran hoy (prensa, directorios, registros) y cuáles faltan.", "Which citable public sources name it today (press, directories, registers) and which are missing.")],
      };
      case "AI_KNOWS_BRAND": return {
        act: [t("Comprueba que lo que el asistente dice de ella es correcto y actual; si no, corrige la fuente pública de la que lo toma.", "Check that what the assistant says about it is correct and current; if not, fix the public source it takes it from.")],
        research: [t("Qué dice exactamente de ella y de qué fuentes lo saca.", "What exactly it says about it and from which sources.")],
      };
      case "OPEN_CORPUS_NOT_CAPTURED": return {
        act: [
          t("Revisa que su robots.txt no bloquee a CCBot y que la web tenga sitemap y enlaces internos a sus páginas importantes.", "Check that its robots.txt does not block CCBot and that the website has a sitemap and internal links to its key pages."),
          t("Consigue enlaces desde otras webs: un rastreo abierto llega a una web siguiendo enlaces.", "Earn links from other websites: an open crawl reaches a site by following links."),
          again,
        ],
        research: [t("Si aparece en el siguiente rastreo de Common Crawl.", "Whether it appears in the next Common Crawl crawl.")],
      };
    }
  }
  if (d.kind === "SEARCH_VISIBILITY") {
    const instead = names(detail.rankingInstead);
    return {
      act: [
        ...(instead.length ? [t("Mira qué página de quienes aparecen antes ({names}) responde a esa búsqueda y qué ofrece que la suya no.", "Look at which page of those ranking first ({names}) answers that search and what it offers that its own does not.").replace("{names}", list(instead))] : []),
        t("Que cada búsqueda clave tenga en su web una página que la responda, con esas palabras en el título y el texto.", "Make sure each key search has a page on its website that answers it, with those words in the title and text."),
        again,
      ],
      research: [t("Su posición en otras búsquedas de su actividad y en otros países donde opera.", "Its position in other searches for its activity and in other countries where it operates.")],
    };
  }
  if (d.kind === "WEB_REPRESENTATION" && d.code === "SECURITY_HEADERS_GRADE") return {
    act: [
      t("Abre el informe de Mozilla Observatory (su fuente) para ver qué comprobaciones fallan.", "Open the Mozilla Observatory report (its source) to see which checks fail."),
      t("Lo habitual: forzar HTTPS con HSTS, añadir una política de seguridad de contenidos (CSP) y las cabeceras X-Content-Type-Options y Referrer-Policy en el servidor.", "The usual: enforce HTTPS with HSTS, add a content security policy (CSP) and the X-Content-Type-Options and Referrer-Policy headers on the server."),
      t("Vuelve a medir después: la nota cambia en cuanto el servidor envía las cabeceras.", "Measure again afterwards: the grade changes as soon as the server sends the headers."),
    ],
    research: [t("Qué nota tienen las webs de sus competidores con la misma medición.", "What grade its competitors' websites get with the same measurement.")],
  };
  if (d.kind === "WEB_REPRESENTATION" && d.code === "LIGHTHOUSE_AUDIT") {
    const seo = failingTitles(detail, "SEO");
    const performance = failingTitles(detail, "PERFORMANCE");
    const accessibility = failingTitles(detail, "ACCESSIBILITY");
    const act = [
      ...(seo.length ? [t("Corrige lo que no pasa en SEO: {list}.", "Fix what fails in SEO: {list}.").replace("{list}", list(seo, 5))] : []),
      ...(performance.length ? [t("Mejora la velocidad en lo que señala Lighthouse: {list}.", "Improve speed where Lighthouse points: {list}.").replace("{list}", list(performance, 4))] : []),
      ...(accessibility.length ? [t("Corrige la accesibilidad: {list}.", "Fix accessibility: {list}.").replace("{list}", list(accessibility, 3))] : []),
    ];
    return {
      act: act.length ? [...act, t("Vuelve a medir después: una medición de laboratorio varía unos puntos entre ejecuciones.", "Measure again afterwards: a lab measurement varies a few points between runs.")]
        : [t("Pasa las comprobaciones de Lighthouse; mantén el control tras cada cambio de su web.", "It passes Lighthouse's checks; keep checking after each change to its website.")],
      research: [t("Si sus visitantes reales viven lo mismo (datos de campo de Chrome, CrUX) y cómo están sus páginas de servicio, no solo la de inicio.", "Whether its real visitors experience the same (Chrome field data, CrUX) and how its service pages do, not just the home page.")],
    };
  }
  const what = d.statement;
  // Value: what it offers and can prove.
  if (d.kind === "ACTIVITY" || d.kind === "OFFER") return {
    act: [
      t("Comprueba que su web presenta «{what}» con una página propia: qué es, para quién y con qué resultados.", "Check that its website presents “{what}” on its own page: what it is, for whom and with what results.").replace("{what}", what),
      t("Si es una actividad principal, nómbrala igual en el título, el texto y los datos estructurados para que buscadores e IA la entiendan.", "If it is a main activity, name it the same way in the title, text and structured data so search engines and AI understand it."),
    ],
    research: [t("Qué demanda pública y qué competidores hay para «{what}» en sus mercados.", "What public demand and which competitors exist for “{what}” in its markets.").replace("{what}", what)],
  };
  if (d.kind === "CREDENTIAL") return {
    act: [t("Muestra la certificación «{what}» con su número y su organismo, enlazando al registro que la acredita.", "Show the “{what}” credential with its number and issuer, linking to the register that proves it.").replace("{what}", what)],
    research: [t("Si la certificación sigue vigente en el registro oficial del organismo emisor.", "Whether the credential is still valid in the issuer's official register.")],
  };
  // Markets: where it acts.
  if (d.kind === "DECLARED_LOCATION" || d.kind === "DECLARED_SERVICE_AREA") return {
    act: [
      t("Si atiende esos mercados, que cada uno tenga su versión de la web (idioma, país, contacto local) y lo declare en hreflang.", "If it serves those markets, give each its own version of the website (language, country, local contact) declared in hreflang."),
      t("Indica en «Dónde buscar demanda» los mercados que te interesan para observarlos de forma directa.", "Set the markets you care about under “Where to look for demand” so they are observed directly."),
    ],
    research: [t("Si hay demanda pública y competidores observados en esos mercados.", "Whether there is public demand and observed competitors in those markets.")],
  };
  // Relationships: who it works with or competes against.
  if (d.kind === "RELATIONSHIP") return {
    act: [
      t("Abre la fuente y comprueba si la relación con {who} sigue vigente: una relación declarada no es una confirmada.", "Open the source and check whether the relationship with {who} still holds: a declared relationship is not a confirmed one.").replace("{who}", what),
      t("Si es un cliente o socio relevante, un caso publicado con su permiso la hace verificable para terceros.", "If it is a relevant client or partner, a case study published with its permission makes it verifiable by others."),
    ],
    research: [t("Si {who} aparece en otras fuentes (adjudicaciones, prensa, su propia web) junto a esta organización.", "Whether {who} appears in other sources (awards, press, its own website) together with this organization.").replace("{who}", what)],
  };
  if (d.kind === "COMPETITION") return {
    act: [t("Revisa qué contratos gana {who} con los mismos códigos y a qué compradores: indica dónde compite y con qué precio.", "Review which contracts {who} wins under the same codes and from which buyers: it shows where it competes and at what price.").replace("{who}", what)],
    research: [t("Si {who} compite en los mismos mercados y si gana más de lo que pierde frente a ella.", "Whether {who} competes in the same markets and whether it wins more than it loses against it.").replace("{who}", what)],
  };
  // Demand: potential, never a customer.
  if (d.kind === "DEMAND") {
    const deadline = typeof detail.deadline === "string" ? detail.deadline.slice(0, 10) : null;
    return {
      act: [
        t("Abre la fuente y valora si encaja con lo que hace: es una oportunidad potencial, no un cliente.", "Open the source and judge whether it fits what it does: it is a potential opportunity, not a customer."),
        ...(deadline ? [t("Si encaja, el plazo es el {date}: revisa antes los requisitos (solvencia, certificaciones, lotes).", "If it fits, the deadline is {date}: check the requirements (solvency, credentials, lots) first.").replace("{date}", deadline)] : []),
      ],
      research: [t("Quién ganó antes contratos parecidos de ese comprador y por qué importe.", "Who won similar contracts from that buyer before, and for what amount.")],
    };
  }
  // Activity: what it does and how often.
  if (d.kind === "OPERATING_SIGNAL") return {
    act: [t("Sigue esta señal en «Evolución»: una sola lectura no muestra una tendencia.", "Follow this signal in “Evolution”: a single reading does not show a trend.")],
    research: [t("Si la señal se mantiene, crece o cae en las próximas observaciones.", "Whether the signal holds, grows or falls over the next observations.")],
  };
  // Economics: figures with source and date.
  if (d.kind === "ECONOMIC_FACT") return {
    act: [t("Contrasta la cifra con su fuente y su fecha; si es antigua, búscala en el registro oficial más reciente.", "Check the figure against its source and date; if it is old, look for it in the latest official register.")],
    research: [t("Su evolución en años anteriores y cómo se compara con su sector en su país.", "Its trend over previous years and how it compares with its sector in its country.")],
  };
  // Organization: who it is.
  if (d.kind === "IDENTITY_HINT" && d.code === "IDENTIFIER_IN_DIRECTORY") return {
    act: [t("Comprueba en el registro oficial que el identificador {id} corresponde a la organización y, si es así, publícalo en su web.", "Check in the official register that identifier {id} belongs to the organization and, if so, publish it on its website.").replace("{id}", what)],
    research: [t("Si el registro oficial confirma ese identificador, su nombre legal y su domicilio.", "Whether the official register confirms that identifier, its legal name and address.")],
  };
  if (d.kind === "IDENTITY_HINT") return {
    act: [t("Que su web muestre su nombre legal y su número de registro o NIF, y que coincidan con el registro oficial.", "Make its website show its legal name and registration or tax number, matching the official register.")],
    research: [t("Si el registro oficial confirma ese nombre, su domicilio y su actividad.", "Whether the official register confirms that name, its address and its activity.")],
  };
  // Context: the frame it operates in.
  if (d.kind === "CONTEXT_SIGNAL") return {
    act: [t("Lee la norma o la noticia en su fuente y valora si afecta a esta organización y desde cuándo. No es asesoramiento jurídico.", "Read the rule or news at its source and judge whether it affects this organization and from when. Not legal advice.")],
    research: [t("Qué otras organizaciones de su sector se ven afectadas y cómo han reaccionado.", "Which other organizations in its sector are affected and how they have reacted.")],
  };
  if (d.kind === "MENTION" && (d.code === "OWN_PUBLICATION" || d.code === "PRESS_RELEASE")) return {
    act: [t("Es su propia voz: comprueba que lo que publica llega a medios y webs de terceros, que es lo que leen buscadores e IA.", "It is its own voice: check that what it publishes reaches third-party media and sites, which is what search engines and AI read.")],
    research: [t("Si algún medio o web de terceros recogió esa publicación.", "Whether any third-party media or site picked up that publication.")],
  };
  if (d.kind === "MENTION" || d.kind === "RATING") return {
    act: [
      t("Lee la página en su fuente: si es una reseña o una reclamación, valora responder allí mismo; si contiene un dato erróneo, pide que se corrija.", "Read the page at its source: if it is a review or a complaint, consider answering there; if it contains a wrong fact, ask for a correction."),
      t("Una mención no es una recomendación: cuenta qué se dice y dónde, no solo cuántas veces.", "A mention is not an endorsement: weigh what is said and where, not just how often."),
    ],
    research: [t("Si hay más reseñas o reclamaciones parecidas en otras plataformas y si se repite el mismo motivo.", "Whether there are similar reviews or complaints on other platforms and whether the same reason recurs.")],
  };
  return null;
}
