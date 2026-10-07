import commercialSeed from "@/content/acquisition/seed/commercial.json";
import commercialExpansionSeed from "@/content/acquisition/seed/commercial-expansion.json";
import commercialExpansionLocalesA from "@/content/acquisition/seed/commercial-expansion-locales-a.json";
import commercialExpansionLocalesB from "@/content/acquisition/seed/commercial-expansion-locales-b.json";
import commercialLocales from "@/content/acquisition/seed/commercial-locales.json";
import evidenceSeed from "@/content/acquisition/seed/evidence.json";
import knowledgeExpansionAiSeed from "@/content/acquisition/seed/knowledge-expansion-ai.json";
import knowledgeExpansionAiLocales from "@/content/acquisition/seed/knowledge-expansion-ai-locales.json";
import knowledgeExpansionAi2Seed from "@/content/acquisition/seed/knowledge-expansion-ai-2.json";
import knowledgeExpansionAi2LocalesA from "@/content/acquisition/seed/knowledge-expansion-ai-2-locales.json";
import knowledgeExpansionAi2LocalesB from "@/content/acquisition/seed/knowledge-expansion-ai-2-locales-b.json";
import knowledgeExpansionAi3Seed from "@/content/acquisition/seed/knowledge-expansion-ai-3.json";
import knowledgeExpansionAi3Locales from "@/content/acquisition/seed/knowledge-expansion-ai-3-locales.json";
import evidenceLocales from "@/content/acquisition/seed/evidence-locales.json";
import aiMemorySeed from "@/content/acquisition/seed/ai-memory.json";
import aiMemoryLocales from "@/content/acquisition/seed/ai-memory-locales.json";
import audienceSeed from "@/content/acquisition/seed/audience.json";
import audienceLocales from "@/content/acquisition/seed/audience-locales.json";
import jtbdSeed from "@/content/acquisition/seed/jtbd.json";
import jtbdLocales from "@/content/acquisition/seed/jtbd-locales.json";
import comparisonsSeed from "@/content/acquisition/seed/comparisons.json";
import comparisonsExpansionSeed from "@/content/acquisition/seed/comparisons-expansion.json";
import comparisonLocales from "@/content/acquisition/seed/comparison-locales.json";
import comparisonExpansionLocales from "@/content/acquisition/seed/comparisons-expansion-locales.json";
import { isLocale, locales, type Locale } from "./languages";

export type AcquisitionType = "commercial" | "knowledge" | "jtbd" | "comparison";

export type LocalizedAcquisitionPage = {
  slug: string;
  title: string;
  description: string;
  lead: string;
  answer: string;
  sections: { heading: string; body: string }[];
  example: string;
  limits: string;
  cta: { label: string; href: string };
  related: string[];
};

export type AcquisitionPage = {
  id: string;
  cluster: string;
  intent: string;
  type: AcquisitionType;
  locales: Partial<Record<Locale, LocalizedAcquisitionPage>>;
};

export const acquisitionClusterLabels: Record<string, Record<Locale, string>> = {
  "commercial-use": { es: "Casos de observación económica", en: "Economic observation use cases", fr: "Cas d’usage de l’observation économique", de: "Anwendungsfälle der Wirtschaftsbeobachtung", it: "Casi d’uso dell’osservazione economica", pt: "Casos de observação económica" },
  "commercial-expansion": { es: "Casos avanzados de observación económica", en: "Advanced economic observation use cases", fr: "Cas avancés d’observation économique", de: "Erweiterte Anwendungsfälle der Wirtschaftsbeobachtung", it: "Casi avanzati d’uso dell’osservazione economica", pt: "Casos avançados de observação económica" },
  "evidence-and-trust": { es: "Evidencia y límites de conocimiento", en: "Evidence and knowledge boundaries", fr: "Preuves et limites de la connaissance", de: "Belege und Grenzen des Wissens", it: "Prove e limiti della conoscenza", pt: "Evidência e limites do conhecimento" },
  "ai-memory-context": { es: "Memoria y contexto para la IA", en: "Memory and context for AI", fr: "Mémoire et contexte pour l’IA", de: "Gedächtnis und Kontext für KI", it: "Memoria e contesto per l’IA", pt: "Memória e contexto para IA" },
  "audience-jtbd": { es: "Equipos y necesidades", en: "Teams and needs", fr: "Équipes et besoins", de: "Teams und Aufgaben", it: "Team e necessità", pt: "Equipas e necessidades" },
  "decision-workflows": { es: "Contexto para decidir", en: "Context for decisions", fr: "Contexte pour décider", de: "Entscheidungskontext", it: "Contesto per decidere", pt: "Contexto para decidir" },
  "comparison-methods": { es: "Métodos de investigación comparados", en: "Research methods compared", fr: "Méthodes de recherche comparées", de: "Vergleich von Recherchemethoden", it: "Metodi di ricerca a confronto", pt: "Métodos de investigação comparados" },
};

type SupplementalLocales = { id: string } & Partial<Record<Locale, LocalizedAcquisitionPage>>;
const initialSeeds = [commercialSeed, commercialExpansionSeed, evidenceSeed, knowledgeExpansionAiSeed, knowledgeExpansionAi2Seed, knowledgeExpansionAi3Seed, aiMemorySeed, audienceSeed, jtbdSeed, comparisonsSeed, comparisonsExpansionSeed] as unknown as AcquisitionPage[][];
const normalizedJtbdLocales = (jtbdLocales as unknown as { id: string; locales: Partial<Record<Locale, LocalizedAcquisitionPage>> }[]).map(({ id, locales: localized }) => ({ id, ...localized }));
const supplementalLocales = [commercialLocales, commercialExpansionLocalesA, commercialExpansionLocalesB, evidenceLocales, knowledgeExpansionAiLocales, knowledgeExpansionAi2LocalesA, knowledgeExpansionAi2LocalesB, knowledgeExpansionAi3Locales, aiMemoryLocales, audienceLocales, normalizedJtbdLocales, comparisonLocales, comparisonExpansionLocales] as unknown as SupplementalLocales[][];
const supplementalById = supplementalLocales.flat();
export const acquisitionPages: AcquisitionPage[] = initialSeeds.flat().map((page) => {
  const supplemental = supplementalById.find((item) => item.id === page.id);
  const { id: _id, ...localized } = supplemental ?? { id: page.id };
  return { ...page, locales: { ...page.locales, ...localized } };
});

export function pageForLocale(
  page: AcquisitionPage,
  locale: Locale,
): LocalizedAcquisitionPage | undefined {
  return page.locales[locale];
}

export function pageByLocalizedSlug(locale: Locale, slug: string) {
  const page = acquisitionPages.find((candidate) => candidate.locales[locale]?.slug === slug);
  return page ? { page, content: page.locales[locale]! } : undefined;
}

export function localizedPagePath(page: AcquisitionPage, locale: Locale): string {
  const content = pageForLocale(page, locale);
  if (!content) throw new Error(`Missing ${locale} copy for ${page.id}`);
  return `/${locale}/knowledge/${content.slug}`;
}

export const acquisitionHubs = locales.map((locale) => ({
  locale: locale.id,
  path: `/${locale.id}/knowledge`,
}));

export function validateAcquisitionPages(): string[] {
  const issues: string[] = [];
  const ids = new Set<string>();
  const localeSlugs = new Set<string>();

  for (const page of acquisitionPages) {
    if (!acquisitionClusterLabels[page.cluster]) issues.push(`${page.id}: missing localized cluster label`);
    if (ids.has(page.id)) issues.push(`duplicate id: ${page.id}`);
    ids.add(page.id);
    for (const locale of locales) {
      const content = page.locales[locale.id];
      if (!content) {
        issues.push(`${page.id}: missing locale ${locale.id}`);
        continue;
      }
      const key = `${locale.id}/${content.slug}`;
      if (localeSlugs.has(key)) issues.push(`duplicate locale slug: ${key}`);
      localeSlugs.add(key);
      if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(content.slug))
        issues.push(`${key}: invalid slug`);
      if (content.title.trim().length < 24 || content.title.length > 70)
        issues.push(`${key}: title length must be 24–70 characters`);
      if (content.description.trim().length < 70 || content.description.length > 170)
        issues.push(`${key}: description length must be 70–170 characters`);
      const body = [content.lead, content.answer, ...content.sections.map((section) => section.body), content.example, content.limits].join(" ");
      const words = body.trim().split(/\s+/).filter(Boolean).length;
      if (content.sections.length < 4 || words < 350)
        issues.push(`${key}: thin page (${words} words, ${content.sections.length} sections)`);
      if (content.related.length < 3) issues.push(`${key}: fewer than three contextual links`);
      if (new Set(content.related).size !== content.related.length)
        issues.push(`${key}: duplicate contextual link`);
      if (content.related.includes(page.id)) issues.push(`${key}: self-referencing contextual link`);
      if (!content.cta?.label?.trim() || !isValidCtaHref(content.cta.href))
        issues.push(`${key}: invalid contextual CTA`);
    }
  }

  for (const page of acquisitionPages) {
    for (const [localeId, content] of Object.entries(page.locales)) {
      if (!isLocale(localeId)) continue;
      for (const relatedId of content.related) {
        if (!ids.has(relatedId)) issues.push(`${page.id}/${localeId}: broken related id ${relatedId}`);
      }
    }
  }

  const pagesById = new Map(acquisitionPages.map((page) => [page.id, page]));
  for (const page of acquisitionPages) {
    for (const locale of locales) {
      const content = page.locales[locale.id];
      if (!content) continue;
      for (const relatedId of content.related) {
        const target = pagesById.get(relatedId);
        if (target && !target.locales[locale.id])
          issues.push(`${page.id}/${locale.id}: related page ${relatedId} lacks locale`);
      }
    }
  }

  const normalizedDescriptions = new Set<string>();
  const normalizedTitles = new Set<string>();
  const pageBodies: { id: string; locale: string; text: string; shingles: Set<string> }[] = [];
  for (const page of acquisitionPages) {
    for (const [locale, content] of Object.entries(page.locales)) {
      if (!content) continue;
      const title = content.title.toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
      const description = content.description.toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
      const titleKey = `${locale}:${title}`;
      const descriptionKey = `${locale}:${description}`;
      if (normalizedTitles.has(titleKey)) issues.push(`${page.id}/${locale}: duplicate title`);
      if (normalizedDescriptions.has(descriptionKey)) issues.push(`${page.id}/${locale}: duplicate description`);
      normalizedTitles.add(titleKey);
      normalizedDescriptions.add(descriptionKey);
      const body = [content.lead, content.answer, ...content.sections.map((section) => section.body), content.example, content.limits].join(" ");
      const tokens = body.toLocaleLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];
      const shingles = new Set(tokens.slice(0, -2).map((_, index) => tokens.slice(index, index + 3).join(" ")));
      pageBodies.push({ id: page.id, locale, text: body, shingles });
    }
  }

  for (let index = 0; index < pageBodies.length; index += 1) {
    const current = pageBodies[index]!;
    for (let otherIndex = index + 1; otherIndex < pageBodies.length; otherIndex += 1) {
      const other = pageBodies[otherIndex]!;
      if (current.locale !== other.locale) continue;
      const intersection = [...current.shingles].filter((shingle) => other.shingles.has(shingle)).length;
      const union = current.shingles.size + other.shingles.size - intersection;
      if (union > 0 && intersection / union > 0.72)
        issues.push(`${current.id}/${current.locale}: body too similar to ${other.id} (${(intersection / union).toFixed(2)})`);
    }
  }

  const inbound = new Map(acquisitionPages.map((page) => [page.id, 0]));
  for (const page of acquisitionPages) {
    for (const locale of locales) {
      for (const relatedId of page.locales[locale.id]?.related ?? [])
        inbound.set(relatedId, (inbound.get(relatedId) ?? 0) + 1);
    }
  }
  for (const page of acquisitionPages) {
    if ((inbound.get(page.id) ?? 0) === 0)
      issues.push(`${page.id}: no inbound contextual link (orphan)`);
  }

  return issues;
}

export function isValidCtaHref(href: string): boolean {
  return href === "/signup" || href === "/knowledge" || /^\/(?:es|en|fr|de|it|pt)\/knowledge$/.test(href);
}
