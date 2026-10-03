"use client";
import Link from "next/link";
import { useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  ArrowLeft,
  Search,
  BookOpen,
  Clock3,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  articles,
  topics,
  filterArticles,
  readingMinutes,
  type Article,
} from "@/lib/editorial";
import { Observer, Badge } from "./ui";
import { PublicShell, PublicationNote } from "./public-shell";

export function EditorialArt({
  kind,
  compact = false,
}: {
  kind: Article["art"];
  compact?: boolean;
}) {
  const { t } = useLocale();
  return (
    <div
      className={"editorial-art art-" + kind + (compact ? " art-compact" : "")}
      aria-hidden="true"
    >
      <div className="art-orbit orbit-a" />
      <div className="art-orbit orbit-b" />
      {kind === "certainty" ? (
        <>
          <div className="art-slip slip-known">
            <span className="mono">{t("Lo que sabemos", "What we know")}</span>
            <Badge state="OBSERVED" />
            <i className="art-line" />
            <i className="art-line short" />
          </div>
          <div className="art-slip slip-potential">
            <Badge state="POTENTIAL" />
            <span className="art-question">{t("¿Y si…?", "What if…?")}</span>
          </div>
          <span className="hand-note art-note">
            {t("primero, la evidencia", "evidence comes first")}
          </span>
        </>
      ) : kind === "time" ? (
        <>
          <div className="art-time-line">
            <span>{t("Publicado", "Published")}</span>
            <span>{t("Observado", "Observed")}</span>
            <span>{t("Vigencia", "Currentness")}</span>
          </div>
          <div className="art-time-focus" />
          <span className="hand-note art-note">
            {t("cada momento cuenta", "every moment matters")}
          </span>
        </>
      ) : kind === "layers" ? (
        <>
          <div className="art-layer layer-back">
            {t("Un mundo", "One world")}
          </div>
          <div className="art-layer layer-mid">
            {t("Tu foco", "Your focus")}
          </div>
          <div className="art-layer layer-front">Panorama</div>
        </>
      ) : kind === "unknown" ? (
        <>
          <div className="unknown-disc">
            <span>?</span>
            <Badge state="UNKNOWN" />
          </div>
          <span className="hand-note art-note">
            {t("la pregunta sigue abierta", "the question stays open")}
          </span>
        </>
      ) : kind === "conversation" ? (
        <>
          <div className="art-slip conversation-slip">
            <span className="axent-wordmark">Axent</span>
            <p>
              {t("¿Qué sostiene esta lectura?", "What supports this reading?")}
            </p>
            <BookOpen size={22} />
          </div>
          <span className="hand-note art-note">
            {t("con contexto, siempre", "always with context")}
          </span>
        </>
      ) : (
        <>
          <div className="memory-sheets">
            <i />
            <i />
            <i />
            <span>
              {t("Contexto que se acumula", "Context that compounds")}
            </span>
          </div>
          <span className="hand-note art-note">
            {t("volver a mirar", "look again")}
          </span>
        </>
      )}
      <Observer
        className="art-observer"
        pose={
          kind === "time"
            ? "pointing"
            : kind === "layers"
              ? "connecting"
              : kind === "conversation"
                ? "accompanying"
                : kind === "unknown"
                  ? "thinking"
                  : kind === "memory"
                    ? "connecting"
                    : "analyzing"
        }
      />
    </div>
  );
}
export function Knowledge() {
  const { t, copy, locale } = useLocale();
  const [query, setQuery] = useState("");
  const [topic, setTopic] = useState("all");
  const filtered = filterArticles(query, topic, locale);
  const featured = articles[0];
  const pristine = !query.trim() && topic === "all";
  return (
    <PublicShell className="knowledge-page">
      <section className="public-intro notebook-intro">
        <div>
          <span className="eyebrow">
            Knowledge /{" "}
            {t("El cuaderno del Observador", "The Observer's notebook")}
          </span>
          <h1>
            {t("El mundo cambia.", "The world changes.")}
            <br />
            <em>{t("Aprende a mirarlo.", "Learn to look.")}</em>
          </h1>
        </div>
        <div className="intro-side">
          <p>
            {t(
              "Ideas para leer señales, hacer mejores preguntas y entender qué sostiene una conclusión.",
              "Ideas for reading signals, asking better questions and understanding what supports a conclusion.",
            )}
          </p>
          <span className="hand-note">
            {t("la curiosidad tiene método", "curiosity has a method")}
          </span>
          <PublicationNote editorial />
        </div>
      </section>
      {pristine && (
        <section className="notebook-feature">
          <Link className="feature-copy" href={"/knowledge/" + featured.slug}>
            <span className="eyebrow">
              {t("Empieza por aquí", "Start here")}
            </span>
            <h2>{copy(featured.title)}</h2>
            <p>{copy(featured.deck)}</p>
            <span className="text-link">
              {t("Abrir el cuaderno", "Open the notebook")}
              <ArrowUpRight size={19} />
            </span>
            <span className="article-meta">
              <Clock3 size={13} />
              {readingMinutes(featured, locale)} min {t("de lectura", "read")}
            </span>
          </Link>
          <Link
            href={"/knowledge/" + featured.slug}
            tabIndex={-1}
            aria-hidden="true"
          >
            <EditorialArt kind="certainty" />
          </Link>
        </section>
      )}
      <section
        className="notebook-index"
        aria-labelledby="notebook-index-title"
      >
        <div className="index-heading">
          <h2 id="notebook-index-title">
            {t("Una idea abre otra.", "One idea opens another.")}
          </h2>
          <label className="notebook-search">
            <Search size={17} />
            <span className="sr-only">
              {t("Buscar en Knowledge", "Search Knowledge")}
            </span>
            <input
              type="search"
              value={query}
              maxLength={120}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t(
                "¿Qué quieres comprender?",
                "What would you like to understand?",
              )}
            />
          </label>
        </div>
        <div
          className="notebook-topics"
          role="group"
          aria-label={t("Temas del cuaderno", "Notebook topics")}
        >
          {topics.map((item) => (
            <button
              key={item.id}
              onClick={() => setTopic(item.id)}
              aria-pressed={topic === item.id}
            >
              {copy(item.name)}
            </button>
          ))}
        </div>
        <p className="result-count" role="status">
          {filtered.length} {t("lecturas", "readings")}
        </p>
        <div className="article-list">
          {filtered.map((article, i) => (
            <Link
              className="article-row"
              href={"/knowledge/" + article.slug}
              key={article.slug}
            >
              <span className="mono row-index">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="row-art">
                <EditorialArt kind={article.art} compact />
              </div>
              <div className="row-copy">
                <span className="eyebrow">
                  {copy(topics.find((item) => item.id === article.topic)!.name)}
                </span>
                <h3>{copy(article.title)}</h3>
                <p>{copy(article.deck)}</p>
              </div>
              <div className="row-end">
                <span className="mono">
                  {readingMinutes(article, locale)} min
                </span>
                <ArrowUpRight size={22} />
              </div>
            </Link>
          ))}
        </div>
        {!filtered.length && (
          <div className="notebook-empty">
            <BookOpen size={30} />
            <h3>
              {t(
                "Esta página del cuaderno sigue abierta.",
                "This notebook page is still open.",
              )}
            </h3>
            <p>
              {t(
                "No hay lecturas que coincidan con esta búsqueda. Prueba otra palabra o vuelve a todos los temas.",
                "No readings match this search. Try another word or return to all topics.",
              )}
            </p>
            <button
              className="button secondary"
              onClick={() => {
                setQuery("");
                setTopic("all");
              }}
            >
              {t("Ver todo el cuaderno", "See the whole notebook")}
              <ArrowRight size={16} />
            </button>
          </div>
        )}
      </section>
      <aside className="notebook-invitation">
        <BookOpen size={26} />
        <div>
          <h3>{t("De la idea a la mirada.", "From idea to perspective.")}</h3>
          <p>
            {t(
              "Explora cómo se relacionan contexto, señales y evidencia en una demo ilustrativa.",
              "Explore how context, signals and evidence relate in an illustrative demo.",
            )}
          </p>
        </div>
        <Link className="button secondary" href="/panorama">
          {t("Abrir Panorama", "Open Panorama")}
          <ArrowUpRight size={16} />
        </Link>
      </aside>
    </PublicShell>
  );
}
export function KnowledgeArticle({ slug }: { slug: string }) {
  const { t, copy, locale } = useLocale();
  const article = articles.find((a) => a.slug === slug)!;
  const related = articles.filter((a) => a.slug !== slug).slice(0, 2);
  return (
    <PublicShell className="article-page">
      <header className="article-intro">
        <Link className="text-link" href="/knowledge">
          <ArrowLeft size={16} />
          {t("Volver al cuaderno", "Back to the notebook")}
        </Link>
        <div className="article-title-spread">
          <div>
            <span className="eyebrow">
              {copy(topics.find((item) => item.id === article.topic)!.name)}
            </span>
            <h1>{copy(article.title)}</h1>
            <p>{copy(article.deck)}</p>
            <div className="article-meta">
              <Clock3 size={14} />
              {readingMinutes(article, locale)} min
              <PublicationNote editorial />
            </div>
          </div>
          <EditorialArt kind={article.art} />
        </div>
      </header>
      <div className="article-reading">
        <nav
          className="reading-rail"
          aria-label={t("En esta lectura", "In this reading")}
        >
          <span className="eyebrow">
            {t("En esta lectura", "In this reading")}
          </span>
          {article.sections.map((s, i) => (
            <a key={i} href={"#section-" + i}>
              {copy(s.title)}
            </a>
          ))}
          <a href="#basis">
            {t("La base de esta idea", "The basis of this idea")}
          </a>
        </nav>
        <article className="article-prose">
          {article.sections.map((s, i) => (
            <section id={"section-" + i} key={i}>
              <h2>{copy(s.title)}</h2>
              <p>{copy(s.body)}</p>
              {i === 0 && <blockquote>{copy(article.takeaway)}</blockquote>}
            </section>
          ))}
          <section id="basis" className="article-basis">
            <BookOpen size={21} />
            <h3>{t("La base de esta idea", "The basis of this idea")}</h3>
            <p>
              {t(
                "Explicación editorial basada en la doctrina de producto. Los ejemplos son conceptuales y no acreditan hechos económicos.",
                "An editorial explanation based on product doctrine. Examples are conceptual and do not establish economic facts.",
              )}
            </p>
            <Link href={article.source.href} className="text-link">
              {article.source.title}
              <ArrowUpRight size={15} />
            </Link>
          </section>
        </article>
      </div>
      <section className="related-readings">
        <h2>{t("Sigue el hilo.", "Follow the thread.")}</h2>
        <div>
          {related.map((a) => (
            <Link href={"/knowledge/" + a.slug} key={a.slug}>
              <span className="eyebrow">
                {copy(topics.find((item) => item.id === a.topic)!.name)}
              </span>
              <h3>{copy(a.title)}</h3>
              <ArrowUpRight size={21} />
            </Link>
          ))}
        </div>
      </section>
    </PublicShell>
  );
}
