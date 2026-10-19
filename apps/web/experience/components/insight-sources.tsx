"use client";
import { ExternalLink } from "lucide-react";
import { useLocale } from "@/lib/locale";
import type { Proof, Source } from "@/lib/observatory";
import { useEvidenceLink } from "./evidence-link-context";

/** Shared product proof, without importing a workspace, account or provider. */
export function InsightSources({
  sources,
  proof,
}: {
  sources: readonly Source[];
  proof: readonly Proof[];
}) {
  const { t, locale } = useLocale();
  const evidenceLink = useEvidenceLink();
  const date = (value: string) => {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime())
      ? ""
      : new Intl.DateTimeFormat(locale, {
          day: "numeric",
          month: "short",
          year: "numeric",
        }).format(parsed);
  };
  return (
    <>
      {sources.map((source, index) => {
        const link = evidenceLink.href(source.url);
        return (
          <figure key={index} className="obs-source">
            {source.quote && <blockquote>“{source.quote}”</blockquote>}
            <figcaption>
              {link ? (
                <a href={link} target="_blank" rel="noopener noreferrer">
                  {source.label}
                  <ExternalLink size={13} aria-hidden="true" />
                  <span className="sr-only">
                    {t("(se abre en otra pestaña)", "(opens in a new tab)")}
                  </span>
                </a>
              ) : (
                <span>{source.label}</span>
              )}
              {evidenceLink.synthetic && (
                <small>
                  {t(
                    "Fuente ficticia, ejemplo no navegable",
                    "Fictional source, non-navigable example",
                  )}
                </small>
              )}
              {source.observedAt && (
                <time dateTime={source.observedAt}>
                  {date(source.observedAt)}
                </time>
              )}
            </figcaption>
          </figure>
        );
      })}
      {proof.length > 0 && (
        <dl className="obs-proof">
          {proof.map((item) => (
            <div key={item.label + item.value}>
              <dt>{item.label}</dt>
              <dd>{item.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </>
  );
}
