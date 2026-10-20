import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LandingLab } from "@/components/landing-lab";
import { getLandingLabContent } from "@/lib/landing-lab-content";
import { LandingLabCriticalType } from "@/components/landing-lab-critical-type";
import { absolutePublicUrl } from "@/lib/acquisition-seo";
import { isLocale, locales, type Locale } from "@/lib/languages";
import { HOME_METADATA } from "@/lib/public-home-metadata";
import { homeLanguages, jsonLd, siteStructuredData } from "@/lib/site-seo";

/** The home page in one language: its own URL, so each language version can be found and declared. */
export const dynamicParams = false;
export function generateStaticParams() { return locales.map(({ id }) => ({ locale: id })); }

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const home = HOME_METADATA[locale as Locale];
  return {
    title: { absolute: home.title },
    description: home.description,
    alternates: { canonical: absolutePublicUrl(`/${locale}`), languages: homeLanguages() },
    openGraph: { title: home.title, description: home.description, url: absolutePublicUrl(`/${locale}`), locale },
  };
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(siteStructuredData(locale)) }}/>
    <LandingLabCriticalType />
    <LandingLab content={getLandingLabContent(locale)} />
  </>;
}
