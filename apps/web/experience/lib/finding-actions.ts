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
  if (d.kind === "MENTION" && (d.code === "REVIEW_PAGE" || d.code === "WEB_MENTION")) return {
    act: [
      t("Lee la página en su fuente: si es una reseña o una reclamación, valora responder allí mismo; si contiene un dato erróneo, pide que se corrija.", "Read the page at its source: if it is a review or a complaint, consider answering there; if it contains a wrong fact, ask for a correction."),
      t("Una mención no es una recomendación: cuenta qué se dice y dónde, no solo cuántas veces.", "A mention is not an endorsement: weigh what is said and where, not just how often."),
    ],
    research: [t("Si hay más reseñas o reclamaciones parecidas en otras plataformas y si se repite el mismo motivo.", "Whether there are similar reviews or complaints on other platforms and whether the same reason recurs.")],
  };
  return null;
}
