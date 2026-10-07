import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { AcquisitionArticle } from "@/components/acquisition";
import { acquisitionPages, localizedPagePath, pageByLocalizedSlug } from "@/lib/acquisition";
import { isLocale, locales, type Locale } from "@/lib/languages";
import { absolutePublicUrl, hreflangMap } from "@/lib/acquisition-seo";

export const dynamicParams = false;
export function generateStaticParams() {
  return locales.flatMap(({ id }) => acquisitionPages.flatMap((page) => page.locales[id] ? [{ locale: id, slug: page.locales[id]!.slug }] : []));
}
export async function generateMetadata({ params }: { params: Promise<{ locale: string; slug: string }> }): Promise<Metadata> {
  const { locale: rawLocale, slug } = await params;
  if (!isLocale(rawLocale)) return {};
  const match = pageByLocalizedSlug(rawLocale, slug);
  if (!match) return { robots: { index: false, follow: false } };
  const languages = Object.fromEntries(locales.flatMap(({ id }) => {
    const localized = match.page.locales[id];
    return localized ? [[id, localizedPagePath(match.page, id)]] : [];
  }));
  const languageAlternates = hreflangMap(languages);
  const url = absolutePublicUrl(localizedPagePath(match.page, rawLocale));
  const region: Record<Locale, string> = { es: "ES", en: "US", fr: "FR", de: "DE", it: "IT", pt: "PT" };
  return {
    title: match.content.title,
    description: match.content.description,
    alternates: { canonical: url, languages: languageAlternates },
    openGraph: { type: "article", locale: `${rawLocale}_${region[rawLocale]}`, url, title: match.content.title, description: match.content.description, siteName: "AXIGNAL", images: ["/brand/og-image-1200x630.png"] },
    twitter: { card: "summary_large_image", title: match.content.title, description: match.content.description, images: ["/brand/og-image-1200x630.png"] },
    robots: { index: true, follow: true },
  };
}
export default async function Page({ params }: { params: Promise<{ locale: string; slug: string }> }) {
  const { locale: rawLocale, slug } = await params;
  if (!isLocale(rawLocale)) notFound();
  const match = pageByLocalizedSlug(rawLocale, slug);
  if (!match) notFound();
  return <AcquisitionArticle page={match.page} content={match.content} locale={rawLocale as Locale} />;
}
