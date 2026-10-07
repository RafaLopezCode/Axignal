import { acquisitionClusterLabels, type AcquisitionPage, type LocalizedAcquisitionPage } from "./acquisition";
import type { Locale } from "./languages";

export const publicOrigin = (process.env.NEXT_PUBLIC_SITE_URL ?? "https://axignal.com").replace(/\/$/, "");
export const absolutePublicUrl = (path: string, origin = publicOrigin) => new URL(path, `${origin}/`).toString();

export function hreflangMap(paths: Partial<Record<Locale, string>>, origin = publicOrigin): Record<string, string> {
  const languages = Object.fromEntries(Object.entries(paths).flatMap(([locale, path]) => path ? [[locale, absolutePublicUrl(path, origin)]] : []));
  if (paths.es) languages["x-default"] = absolutePublicUrl(paths.es, origin);
  return languages;
}

export function hubStructuredData(locale: Locale, origin = publicOrigin) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "AXIGNAL Knowledge",
    url: absolutePublicUrl(`/${locale}/knowledge`, origin),
    inLanguage: locale,
    isPartOf: { "@type": "WebSite", name: "AXIGNAL", url: `${origin}/` },
  };
}

export function articleStructuredData(page: AcquisitionPage, content: LocalizedAcquisitionPage, locale: Locale, origin = publicOrigin) {
  const homeLabel: Record<Locale, string> = { es: "Cuaderno de AXIGNAL", en: "AXIGNAL Knowledge", fr: "Connaissances AXIGNAL", de: "AXIGNAL Wissen", it: "Knowledge di AXIGNAL", pt: "Knowledge da AXIGNAL" };
  const url = absolutePublicUrl(`/${locale}/knowledge/${content.slug}`, origin);
  const image = absolutePublicUrl("/brand/og-image-1200x630.png", origin);
  const logo = absolutePublicUrl("/brand/organization-logo-512.png", origin);
  const organization = { "@type": "Organization", name: "AXIGNAL", url: `${origin}/`, logo: { "@type": "ImageObject", url: logo } };
  return [
    { "@context": "https://schema.org", "@type": "Article", headline: content.title, description: content.description, inLanguage: locale, articleSection: acquisitionClusterLabels[page.cluster]?.[locale], image: { "@type": "ImageObject", url: image, width: 1200, height: 630 }, datePublished: "2026-10-07", dateModified: "2026-10-07", author: organization, publisher: organization, mainEntityOfPage: url, isPartOf: absolutePublicUrl(`/${locale}/knowledge`, origin), about: ["AXIGNAL", acquisitionClusterLabels[page.cluster]?.[locale] ?? page.cluster] },
    { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [
      { "@type": "ListItem", position: 1, name: "AXIGNAL", item: `${origin}/` },
      { "@type": "ListItem", position: 2, name: homeLabel[locale], item: absolutePublicUrl(`/${locale}/knowledge`, origin) },
      { "@type": "ListItem", position: 3, name: content.title, item: url },
    ] },
  ];
}
