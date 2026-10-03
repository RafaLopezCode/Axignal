"use client";
import Link from "next/link";
import { ArrowLeft, BookOpen } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { PublicShell } from "./public-shell";
import { basisSources, type BasisSource } from "@/lib/doctrine-basis";
export function DoctrineBasis({ source }: { source: BasisSource }) {
  const { t, copy } = useLocale();
  const basis = basisSources[source];
  return (
    <PublicShell className="article-page">
      <header className="article-intro">
        <Link href="/knowledge" className="text-link">
          <ArrowLeft size={16} />
          {t("Volver al cuaderno", "Back to the notebook")}
        </Link>
        <div className="article-title-spread">
          <div>
            <span className="eyebrow">
              {t("La base de nuestras ideas", "The basis of our ideas")}
            </span>
            <h1>{copy(basis.title)}</h1>
            <p>
              {t(
                "Extractos seleccionados de la doctrina de AXIGNAL. Conservamos el idioma y el significado del original; no son una publicación de investigación ni evidencia de resultados económicos.",
                "Selected excerpts from AXIGNAL doctrine. We retain the original language and meaning; these are neither a research publication nor evidence of economic outcomes.",
              )}
            </p>
          </div>
          <div className="basis-document">
            <BookOpen size={34} />
            <span className="mono">{basis.document}</span>
            <p>
              {t(
                "Fuente de producto · copia de referencia del 3 de octubre de 2026",
                "Product source · reference copy from 3 October 2026",
              )}
            </p>
          </div>
        </div>
      </header>
      <div className="article-reading">
        <nav
          className="reading-rail"
          aria-label={t("En esta fuente", "In this source")}
        >
          <span className="eyebrow">
            {t("Extractos del original", "Original excerpts")}
          </span>
          {basis.excerpts.map((e, i) => (
            <a key={i} href={"#excerpt-" + i}>
              {e.section}
            </a>
          ))}
        </nav>
        <article className="article-prose">
          {basis.excerpts.map((e, i) => (
            <section id={"excerpt-" + i} key={i}>
              <h2>{e.section}</h2>
              <blockquote lang={"language" in e ? e.language : basis.language}>
                {e.quote}
              </blockquote>
            </section>
          ))}
          <aside className="article-basis">
            <h3>
              {t(
                "Una referencia con límites claros.",
                "A reference with clear limits.",
              )}
            </h3>
            <p>
              {t(
                "Esta selección explica la base de las lecturas del cuaderno. No reemplaza el documento completo ni acredita que todas las capacidades descritas estén disponibles en esta demo.",
                "This selection explains the basis of the notebook readings. It does not replace the complete document or establish that every described capability is available in this demo.",
              )}
            </p>
            <Link href="/knowledge" className="text-link">
              {t("Seguir leyendo", "Keep reading")}
              <ArrowLeft size={16} />
            </Link>
          </aside>
        </article>
      </div>
    </PublicShell>
  );
}
