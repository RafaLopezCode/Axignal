import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { AcquisitionHub } from "@/components/acquisition";
import { acquisitionHubs } from "@/lib/acquisition";
import { absolutePublicUrl, hreflangMap } from "@/lib/acquisition-seo";
import { isLocale, locales, type Locale } from "@/lib/languages";

export const dynamicParams = false;
export function generateStaticParams() { return locales.map(({ id }) => ({ locale: id })); }
function openGraphRegion(locale: Locale) {
  switch (locale) {
    case "es": return "ES";
    case "en": return "US";
    case "fr": return "FR";
    case "de": return "DE";
    case "it": return "IT";
    case "pt": return "PT";
  }
}
export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) return {};
  const locale = rawLocale as Locale;
  const title: Record<Locale, string> = { es: "Knowledge: memoria económica y evidencia", en: "Knowledge: economic memory and evidence", fr: "Knowledge : mémoire économique et preuves", de: "Knowledge: Wirtschaftsgedächtnis und Belege", it: "Knowledge: memoria economica e prove", pt: "Knowledge: memória económica e evidências" };
  const description: Record<Locale, string> = { es: "Explora cómo AXIGNAL observa organizaciones, conserva el contexto económico en el tiempo y explica qué sostienen sus evidencias.", en: "Explore how AXIGNAL observes organizations, preserves economic context over time and explains what its evidence supports.", fr: "Découvrez comment AXIGNAL observe les organisations, conserve le contexte économique dans le temps et explique ce que ses preuves permettent d’étayer.", de: "Erfahren Sie, wie AXIGNAL Organisationen beobachtet, wirtschaftlichen Kontext bewahrt und nachvollziehbar macht, was Belege stützen.", it: "Scopri come AXIGNAL osserva le organizzazioni, conserva il contesto economico nel tempo e spiega ciò che le prove sostengono.", pt: "Explore como a AXIGNAL observa organizações, preserva contexto económico ao longo do tempo e explica o que as evidências sustentam." };
  const languagePaths = Object.fromEntries(acquisitionHubs.map((hub) => [hub.locale, hub.path]));
  return { title: title[locale], description: description[locale], alternates: { canonical: absolutePublicUrl(`/${locale}/knowledge`), languages: hreflangMap(languagePaths) }, openGraph: { type: "website", locale: `${locale}_${openGraphRegion(locale)}`, url: absolutePublicUrl(`/${locale}/knowledge`), title: title[locale], description: description[locale], siteName: "AXIGNAL", images: ["/brand/og-image-1200x630.png"] }, twitter: { card: "summary_large_image", title: title[locale], description: description[locale], images: ["/brand/og-image-1200x630.png"] }, robots: { index: true, follow: true } };
}
export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  return <AcquisitionHub locale={rawLocale} />;
}
