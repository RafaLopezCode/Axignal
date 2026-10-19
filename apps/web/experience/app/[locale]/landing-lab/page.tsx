import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LandingLab } from "@/components/landing-lab";
import { locales, isLocale } from "@/lib/languages";
import { jsonLd, siteStructuredData } from "@/lib/site-seo";
import { HOME_METADATA } from "@/lib/public-home-metadata";
export const dynamicParams = false;
export function generateStaticParams() {
  return locales.map(({ id }) => ({ locale: id }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const copy = HOME_METADATA[locale];
  return {
    title: { absolute: copy.title },
    description: copy.description,
    robots: { index: false, follow: true },
    alternates: {
      canonical: `https://axignal.com/${locale}/landing-lab`,
      languages: Object.fromEntries([
        ...locales.map(({ id }) => [
          id,
          `https://axignal.com/${id}/landing-lab`,
        ]),
        ["x-default", "https://axignal.com/landing-lab"],
      ]),
    },
    openGraph: {
      title: copy.title,
      description: copy.description,
      url: `https://axignal.com/${locale}/landing-lab`,
      locale,
      type: "website",
      images: [
        {
          url: "/brand/og-image-1200x630.png",
          width: 1200,
          height: 630,
          alt: "AXIGNAL",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: copy.title,
      description: copy.description,
      images: ["/brand/og-image-1200x630.png"],
    },
  };
}
export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: jsonLd(siteStructuredData(locale, `/${locale}/landing-lab`)),
        }}
      />
      <LandingLab />
    </>
  );
}
