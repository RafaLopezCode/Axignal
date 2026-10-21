import type { Locale } from "./languages";

/**
 * The neutral root initially renders English and can follow reader preferences.
 * Each explicit language URL renders its own stable metadata and content on the
 * server. Keep the category, evidence and potential-opportunity meaning aligned.
 */
export const HOME_METADATA: Record<Locale, { title: string; description: string }> = {
  es: { title: "AXIGNAL — Inteligencia económica con evidencia y memoria", description: "AXIGNAL observa empresas y su entorno, conecta cambios y oportunidades potenciales y explica por qué importan. Con fuentes, fechas y memoria." },
  en: { title: "AXIGNAL — Economic intelligence with evidence and memory", description: "AXIGNAL observes companies and their environment, connects changes and potential opportunities, and explains why they matter. With sources, dates and memory." },
  de: { title: "AXIGNAL — Wirtschaftliche Intelligenz mit Quellen und Gedächtnis", description: "AXIGNAL beobachtet Unternehmen und ihr Umfeld, verbindet Veränderungen und potenzielle Chancen und erklärt sie mit Quellen, Datum und Gedächtnis." },
  fr: { title: "AXIGNAL — Intelligence économique, sources et mémoire", description: "AXIGNAL observe les entreprises et leur environnement, relie changements et opportunités potentielles et les explique avec sources, dates et mémoire." },
  it: { title: "AXIGNAL — Intelligence economica con fonti e memoria", description: "AXIGNAL osserva le imprese e il loro contesto, collega cambiamenti e opportunità potenziali e li spiega con fonti, date e memoria." },
  pt: { title: "AXIGNAL — Inteligência económica com fontes e memória", description: "A AXIGNAL observa empresas e o seu contexto, liga mudanças e oportunidades potenciais e explica por que importam. Com fontes, datas e memória." },
};
