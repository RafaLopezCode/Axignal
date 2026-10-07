import Link from "next/link";
import { ArrowLeft, ArrowUpRight, BookOpen, Compass, MoveRight } from "lucide-react";
import { locales, type Locale } from "@/lib/languages";
import {
  acquisitionPages,
  acquisitionClusterLabels,
  localizedPagePath,
  type AcquisitionPage,
  type LocalizedAcquisitionPage,
} from "@/lib/acquisition";
import { articleStructuredData, hubStructuredData } from "@/lib/acquisition-seo";
import { PublicShell } from "./public-shell";

const labels: Record<Locale, { back: string; cluster: string; answer: string; limits: string; example: string; related: string; home: string; explore: string }> = {
  es: { back: "Volver al cuaderno", cluster: "Tema", answer: "Respuesta breve", limits: "Alcance y límites", example: "Ejemplo conceptual", related: "Sigue el hilo", home: "Cuaderno de AXIGNAL", explore: "Explorar AXIGNAL" },
  en: { back: "Back to Knowledge", cluster: "Topic", answer: "In brief", limits: "Scope and limits", example: "Conceptual example", related: "Continue exploring", home: "AXIGNAL Knowledge", explore: "Explore AXIGNAL" },
  fr: { back: "Retour aux connaissances", cluster: "Thème", answer: "En bref", limits: "Portée et limites", example: "Exemple conceptuel", related: "Pour poursuivre", home: "Connaissances AXIGNAL", explore: "Découvrir AXIGNAL" },
  de: { back: "Zurück zum Wissen", cluster: "Thema", answer: "Kurz erklärt", limits: "Umfang und Grenzen", example: "Konzeptionelles Beispiel", related: "Weiterlesen", home: "AXIGNAL Wissen", explore: "AXIGNAL entdecken" },
  it: { back: "Torna alla Knowledge", cluster: "Tema", answer: "In breve", limits: "Ambito e limiti", example: "Esempio concettuale", related: "Continua il percorso", home: "Knowledge di AXIGNAL", explore: "Scopri AXIGNAL" },
  pt: { back: "Voltar ao Knowledge", cluster: "Tema", answer: "Em resumo", limits: "Âmbito e limites", example: "Exemplo conceptual", related: "Continue a leitura", home: "Knowledge da AXIGNAL", explore: "Conheça a AXIGNAL" },
};

const typeLabels: Record<Locale, Record<AcquisitionPage["type"], string>> = {
  es: { commercial: "Casos de uso", knowledge: "Conocimiento", jtbd: "Tareas", comparison: "Métodos" },
  en: { commercial: "Use cases", knowledge: "Knowledge", jtbd: "Jobs to be done", comparison: "Methods" },
  fr: { commercial: "Cas d’usage", knowledge: "Connaissances", jtbd: "Besoins", comparison: "Méthodes" },
  de: { commercial: "Anwendungsfälle", knowledge: "Wissen", jtbd: "Aufgaben", comparison: "Methoden" },
  it: { commercial: "Casi d’uso", knowledge: "Conoscenze", jtbd: "Attività", comparison: "Metodi" },
  pt: { commercial: "Casos de uso", knowledge: "Conhecimento", jtbd: "Tarefas", comparison: "Métodos" },
};

export function AcquisitionHub({ locale }: { locale: Locale }) {
  const copy = labels[locale];
  const pages = acquisitionPages.filter((page) => page.locales[locale]);
  const groups = [...new Set(pages.map((page) => page.cluster))];
  const schema = JSON.stringify(hubStructuredData(locale)).replace(/</g, "\\u003c");
  return (
    <PublicShell className="acquisition-page" localeRoutes={locales.map((item) => ({ locale: item.id, href: `/${item.id}/knowledge` }))}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: schema }} />
      <div lang={locale}>
        <header className="article-intro acquisition-intro">
          <span className="eyebrow">AXIGNAL · {copy.home}</span>
          <h1>{locale === "es" ? "Comprender una organización exige memoria y evidencia." : locale === "en" ? "Understanding an organization takes memory and evidence." : locale === "fr" ? "Comprendre une organisation demande mémoire et preuves." : locale === "de" ? "Eine Organisation zu verstehen braucht Gedächtnis und Belege." : locale === "it" ? "Capire un’organizzazione richiede memoria e prove." : "Compreender uma organização exige memória e evidência."}</h1>
          <p>{locale === "es" ? "Un cuaderno para explorar cómo AXIGNAL observa la economía, conserva contexto en el tiempo y distingue lo que sabe de lo que todavía no puede concluir." : locale === "en" ? "A notebook for exploring how AXIGNAL observes the economy, preserves context over time and distinguishes what it knows from what it cannot yet conclude." : locale === "fr" ? "Un carnet pour découvrir comment AXIGNAL observe l’économie, conserve le contexte dans le temps et distingue ce qu’il sait de ce qu’il ne peut pas encore conclure." : locale === "de" ? "Ein Notizbuch darüber, wie AXIGNAL die Wirtschaft beobachtet, Kontext über die Zeit bewahrt und zwischen Wissen und offenen Fragen unterscheidet." : locale === "it" ? "Un quaderno per scoprire come AXIGNAL osserva l’economia, conserva il contesto nel tempo e distingue ciò che sa da ciò che non può ancora concludere." : "Um caderno para explorar como a AXIGNAL observa a economia, preserva contexto ao longo do tempo e distingue o que sabe do que ainda não pode concluir."}</p>
          <div className="acquisition-definition">
            <BookOpen size={19} aria-hidden="true" />
            <p>{locale === "es" ? "AXIGNAL es Observation-as-a-Service: una capacidad de observación económica independiente y persistente, vinculada a fuentes, tiempo y límites visibles." : locale === "en" ? "AXIGNAL is Observation-as-a-Service: an independent, persistent economic observation capability tied to sources, time and visible limits." : locale === "fr" ? "AXIGNAL est un service d’observation économique indépendant et persistant, lié à ses sources, à sa temporalité et à des limites visibles." : locale === "de" ? "AXIGNAL bietet unabhängige, fortlaufende Wirtschaftsbeobachtung mit nachvollziehbaren Quellen, Zeitbezug und Grenzen." : locale === "it" ? "AXIGNAL offre un’osservazione economica indipendente e persistente, collegata a fonti, tempo e limiti espliciti." : "A AXIGNAL oferece observação económica independente e persistente, ligada a fontes, tempo e limites visíveis."}</p>
          </div>
        </header>
        <div className="acquisition-hub-content">
          <div className="acquisition-hub-heading"><span className="eyebrow">{pages.length} {locale === "es" ? "lecturas" : locale === "en" ? "readings" : locale === "fr" ? "lectures" : locale === "de" ? "Beiträge" : locale === "it" ? "letture" : "leituras"}</span><span className="acquisition-locale-list" aria-label="Languages">{locales.map((item) => <Link href={`/${item.id}/knowledge`} key={item.id} lang={item.id} hrefLang={item.id} aria-current={item.id === locale ? "page" : undefined}>{item.id.toUpperCase()}</Link>)}</span></div>
          {groups.map((group) => (
            <section className="acquisition-cluster" key={group}>
              <h2>{acquisitionClusterLabels[group]?.[locale] ?? group}</h2>
              <div className="acquisition-card-grid">
                {pages.filter((page) => page.cluster === group).map((page) => {
                  const content = page.locales[locale]!;
                  return <Link className="acquisition-card" href={localizedPagePath(page, locale)} key={page.id} lang={locale}>
                    <span className="eyebrow">{typeLabels[locale][page.type]}</span>
                    <h3>{content.title}</h3>
                    <p>{content.description}</p>
                    <span className="text-link">{locale === "es" ? "Leer explicación" : locale === "en" ? "Read the explanation" : locale === "fr" ? "Lire l’explication" : locale === "de" ? "Erklärung lesen" : locale === "it" ? "Leggi la spiegazione" : "Ler a explicação"}<ArrowUpRight size={15} /></span>
                  </Link>;
                })}
              </div>
            </section>
          ))}
          <aside className="acquisition-cta">
            <Compass size={21} aria-hidden="true" />
            <p>{locale === "es" ? "AXIGNAL observa lo que puede sostener con evidencia. Una brecha visible no demuestra por sí sola su causa." : locale === "en" ? "AXIGNAL observes what its evidence can support. A visible gap does not, by itself, establish its cause." : locale === "fr" ? "AXIGNAL observe ce que les preuves permettent d’étayer. Une lacune visible n’en établit pas à elle seule la cause." : locale === "de" ? "AXIGNAL beobachtet, was durch Belege gestützt werden kann. Eine sichtbare Lücke belegt für sich genommen nicht ihre Ursache." : locale === "it" ? "AXIGNAL osserva ciò che le prove sostengono. Una lacuna visibile, da sola, non ne dimostra la causa." : "A AXIGNAL observa o que as evidências sustentam. Uma lacuna visível, por si só, não demonstra a sua causa."}</p>
            <Link href="/signup">{copy.explore}<MoveRight size={17} /></Link>
          </aside>
        </div>
      </div>
    </PublicShell>
  );
}

export function AcquisitionArticle({ page, content, locale }: { page: AcquisitionPage; content: LocalizedAcquisitionPage; locale: Locale }) {
  const copy = labels[locale];
  const related = content.related.map((id) => acquisitionPages.find((candidate) => candidate.id === id)).filter((candidate): candidate is AcquisitionPage => Boolean(candidate));
  const schemas = articleStructuredData(page, content, locale).map((schema) => JSON.stringify(schema).replace(/</g, "\\u003c"));
  return <PublicShell className="article-page acquisition-page" localeRoutes={locales.flatMap(({ id }) => page.locales[id] ? [{ locale: id, href: localizedPagePath(page, id) }] : [])}>
    <div lang={locale}>
      <header className="article-intro acquisition-article-intro">
        <nav aria-label={locale === "es" ? "Ruta de navegación" : "Breadcrumb"} className="acquisition-breadcrumb"><Link href={`/${locale}/knowledge`}><ArrowLeft size={15} />{copy.back}</Link><span aria-hidden="true">/</span><span>{typeLabels[locale][page.type]}</span></nav>
        <span className="eyebrow">{copy.cluster} · {acquisitionClusterLabels[page.cluster]?.[locale] ?? page.cluster}</span>
        <h1>{content.title}</h1>
        <p className="acquisition-lead">{content.lead}</p>
        <section className="acquisition-answer" aria-labelledby="acquisition-answer-title"><span className="eyebrow" id="acquisition-answer-title">{copy.answer}</span><p>{content.answer}</p></section>
      </header>
      <div className="article-reading acquisition-reading">
        <nav className="reading-rail" aria-label={locale === "es" ? "En esta lectura" : locale === "en" ? "On this page" : locale === "fr" ? "Dans cette lecture" : locale === "de" ? "In diesem Beitrag" : locale === "it" ? "In questa lettura" : "Nesta leitura"}>
          <span className="eyebrow">{locale === "es" ? "En esta lectura" : locale === "en" ? "On this page" : locale === "fr" ? "Dans cette lecture" : locale === "de" ? "In diesem Beitrag" : locale === "it" ? "In questa lettura" : "Nesta leitura"}</span>
          {content.sections.map((section, index) => <a href={`#section-${index}`} key={section.heading}>{section.heading}</a>)}
          <a href="#example">{copy.example}</a><a href="#limits">{copy.limits}</a>
        </nav>
        <article className="article-prose">
          {content.sections.map((section, index) => <section id={`section-${index}`} key={section.heading}><h2>{section.heading}</h2><p>{section.body}</p></section>)}
          <section id="example"><h2>{copy.example}</h2><p>{content.example}</p></section>
          <section id="limits" className="article-basis"><h2>{copy.limits}</h2><p>{content.limits}</p></section>
          <section className="article-basis acquisition-basis"><h2>{locale === "es" ? "Base editorial" : locale === "en" ? "Editorial basis" : locale === "fr" ? "Base éditoriale" : locale === "de" ? "Redaktionelle Grundlage" : locale === "it" ? "Base editoriale" : "Base editorial"}</h2><p>{locale === "es" ? "Esta página explica doctrina y límites de producto. No demuestra cobertura de fuentes ni resultados observados." : locale === "en" ? "This page explains product doctrine and boundaries. It does not demonstrate source coverage or observed outcomes." : locale === "fr" ? "Cette page explique la doctrine et les limites du produit. Elle ne démontre ni couverture des sources ni résultats observés." : locale === "de" ? "Diese Seite erläutert Produktgrundsätze und Grenzen. Sie belegt weder Quellenabdeckung noch beobachtete Ergebnisse." : locale === "it" ? "Questa pagina spiega la dottrina e i limiti del prodotto. Non dimostra copertura delle fonti o risultati osservati." : "Esta página explica a doutrina e os limites do produto. Não demonstra cobertura de fontes nem resultados observados."}</p><Link className="text-link" href="/knowledge/basis/product-model">{locale === "es" ? "Consultar el modelo de producto" : locale === "en" ? "Read the product model" : locale === "fr" ? "Consulter le modèle produit" : locale === "de" ? "Das Produktmodell lesen" : locale === "it" ? "Leggi il modello di prodotto" : "Consultar o modelo de produto"}<ArrowUpRight size={15} /></Link></section>
          <section className="acquisition-page-cta"><p>{content.cta.label}</p><Link className="text-link" href={content.cta.href}>{copy.explore}<ArrowUpRight size={16} /></Link></section>
        </article>
      </div>
      <section className="related-readings acquisition-related"><h2>{copy.related}</h2><div>{related.map((target) => { const targetCopy = target.locales[locale]; return targetCopy ? <Link href={localizedPagePath(target, locale)} key={target.id}><span className="eyebrow">{typeLabels[locale][target.type]}</span><h3>{targetCopy.title}</h3><ArrowUpRight size={21} /></Link> : null; })}</div></section>
      <div className="acquisition-jsonld" aria-hidden="true">{schemas.map((schema) => <script key={schema} type="application/ld+json" dangerouslySetInnerHTML={{ __html: schema }} />)}</div>
    </div>
  </PublicShell>;
}
