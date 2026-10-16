import type { Metadata } from "next";
import { locales, type Locale } from "./languages";
import { absolutePublicUrl } from "./acquisition-seo";
import { marketingPath } from "./marketing-content";
import { publicCopy } from "./marketing-ui";
import { industries, industryBySlug } from "./marketing-industries";

export const marketingPaths = [
  "/data",
  "/industries",
  "/pricing",
  ...industries.map((i) => `/industries/${i.slug}`),
] as const;
export function marketingLanguages(path: string): Record<string, string> {
  return Object.fromEntries([
    ...locales.map(({ id }) => [
      id,
      absolutePublicUrl(marketingPath(path, id)),
    ]),
    ["x-default", absolutePublicUrl(marketingPath(path, "en"))],
  ]);
}
export function marketingMetadata(path: string, locale: Locale): Metadata {
  const industry = path.startsWith("/industries/")
    ? industryBySlug(path.slice("/industries/".length))
    : undefined;
  if (!marketingPaths.includes(path))
    throw new Error(`Unpublished marketing page: ${path}`);
  const title =
    industry?.title[locale] ??
    (path === "/data"
      ? publicCopy.dataTitle[locale]
      : path === "/pricing"
        ? publicCopy.pricingTitle[locale]
        : publicCopy.industryTitle[locale]);
  const description =
    industry?.intro[locale] ??
    (path === "/data"
      ? publicCopy.dataLead[locale]
      : path === "/pricing"
        ? publicCopy.pricingLead[locale]
        : publicCopy.industryLead[locale]);
  const url = absolutePublicUrl(marketingPath(path, locale));
  return {
    title,
    description,
    alternates: { canonical: url, languages: marketingLanguages(path) },
    openGraph: {
      title: `${title} · AXIGNAL`,
      description,
      url,
      locale,
      type: "website",
    },
  };
}
