import { translate } from "./copy-catalog";
import { locales, type Copy, type Locale } from "./languages";
import type { FamilyId } from "./projection";

const c = (es: string, en: string): Copy => ({ es, en });

/**
 * The single authority that connects everyday words to the ten canonical families.
 *
 * `terms` are what a person already calls things (shown wherever a family is
 * named); `aliases` are extra words people type. Matching folds case and
 * accents and accepts every product language, so "SEO", "reseñas", "tenders"
 * or "Kunden" reach the same family from any surface. Families never change:
 * the vocabulary only helps people recognise them.
 */
export const familyVocabulary: Record<FamilyId, { terms: readonly Copy[]; aliases: readonly string[] }> = {
  presence: {
    terms: [c("SEO", "SEO"), c("GEO", "GEO"), c("Visibilidad digital", "Online visibility")],
    aliases: ["seo", "geo", "posicionamiento", "buscador", "google", "chatgpt", "ia generativa", "generative", "web", "sitio", "website", "visibil", "sichtbar", "referencement", "indexa"],
  },
  reputation: {
    terms: [c("Opiniones", "Reviews"), c("Comentarios", "Comments"), c("Menciones", "Mentions")],
    aliases: ["reseña", "resena", "opinion", "review", "comentari", "comment", "mencion", "mention", "dicen de", "say about", "reputa", "bewertung", "avis", "recension", "avalia"],
  },
  value: {
    terms: [c("Oferta", "Offer"), c("Servicios", "Services"), c("Capacidades", "Capabilities")],
    aliases: ["oferta", "offer", "servicio", "service", "producto", "product", "capacidad", "capabilit", "que ofrece", "what we offer", "leistung", "angebot", "offre", "serviz", "servic"],
  },
  markets: {
    terms: [c("Geografías", "Geographies"), c("Sectores", "Sectors"), c("Expansión", "Expansion")],
    aliases: ["mercado", "market", "pais", "country", "region", "geograf", "sector", "expansion", "internacional", "markt", "marche", "mercat"],
  },
  relationships: {
    terms: [c("Clientes", "Customers"), c("Partners", "Partners"), c("Proveedores", "Suppliers"), c("Competidores", "Competitors")],
    aliases: ["cliente", "client", "customer", "partner", "socio", "alianza", "proveedor", "supplier", "competid", "competitor", "competencia", "kunde", "lieferant", "fournisseur", "fornitor", "fornecedor", "concurren", "wettbewerb"],
  },
  demand: {
    terms: [c("Oportunidades", "Opportunities"), c("Compradores", "Buyers"), c("Licitaciones", "Tenders")],
    aliases: ["oportunidad", "opportunit", "comprador", "buyer", "licitac", "tender", "concurso", "contrato publico", "demanda", "demand", "ausschreib", "appel d", "gara", "oportunidade", "chance"],
  },
  activity: {
    terms: [c("Cambios", "Changes"), c("Proyectos", "Projects"), c("Novedades", "News")],
    aliases: ["cambio", "change", "proyecto", "project", "novedad", "news", "que ha pasado", "what happened", "lanzamiento", "launch", "contratac", "hiring", "projet", "progett", "projekt"],
  },
  economics: {
    terms: [c("Facturación", "Revenue"), c("Empleo", "Headcount"), c("Cifras", "Figures")],
    aliases: ["factura", "fatura", "revenue", "ingreso", "beneficio", "profit", "empleado", "employee", "tamaño", "size", "economi", "financ", "umsatz", "chiffre d", "fatturat", "receita"],
  },
  organization: {
    terms: [c("Quién es", "Who it is"), c("Qué hace", "What it does"), c("Identidad", "Identity")],
    aliases: ["quien es", "quienes son", "who is", "who are", "que hace", "what does", "empresa", "company", "perfil", "profile", "identidad", "identity", "unternehmen", "entreprise", "aziend"],
  },
  context: {
    terms: [c("Regulación", "Regulation"), c("Tendencias", "Trends"), c("Factores externos", "External factors")],
    // Not "context": in "explain this context" it is talk about the conversation, not a topic.
    aliases: ["regula", "normativ", "ley", "law", "tendencia", "trend", "vorschrift", "reglement", "legisla", "macroecon"],
  },
};

/** Lowercase without accents: "Reseñas" and "resenas" match the same alias. */
export function fold(text: string): string {
  return text.normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase();
}

/** The visible discovery terms of a family, in the reader's language. */
export function familyTerms(id: FamilyId, locale: Locale): string[] {
  return familyVocabulary[id].terms.map((term) => translate(term.es, term.en, locale));
}

const stems: [FamilyId, string][] = (Object.keys(familyVocabulary) as FamilyId[]).flatMap((id) => [
  ...familyVocabulary[id].aliases.map((alias): [FamilyId, string] => [id, fold(alias)]),
  ...locales.flatMap(({ id: locale }) =>
    familyVocabulary[id].terms.map((term): [FamilyId, string] => [id, fold(translate(term.es, term.en, locale))]),
  ),
]);

function contains(text: string, stem: string): boolean {
  // A short word must stand alone ("geo" is not "geografía"); longer stems may start a word.
  const pattern = stem.length <= 3 ? `(^|[^\\p{L}])${stem}([^\\p{L}]|$)` : `(^|[^\\p{L}])${stem}`;
  return new RegExp(pattern, "u").test(text);
}

/**
 * Which families a person's words point to, best first. Deterministic, no model:
 * the family whose terms or aliases appear most (longest wins ties) comes first.
 */
export function familiesForText(text: string): FamilyId[] {
  const folded = fold(text);
  const score = new Map<FamilyId, number>();
  for (const [id, stem] of stems)
    if (stem && contains(folded, stem)) score.set(id, (score.get(id) ?? 0) + stem.length);
  return [...score.entries()].sort((a, b) => b[1] - a[1]).map(([id]) => id);
}
