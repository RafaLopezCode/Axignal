import type { Metadata } from "next";
import { LandingLab } from "@/components/landing-lab";
import { getLandingLabContent } from "@/lib/landing-lab-content";
import { LandingLabCriticalType } from "@/components/landing-lab-critical-type";
import { jsonLd, siteStructuredData } from "@/lib/site-seo";
import { HOME_METADATA } from "@/lib/public-home-metadata";
export const metadata: Metadata = {
  title: { absolute: HOME_METADATA.en.title },
  description: HOME_METADATA.en.description,
  robots: { index: false, follow: true },
  openGraph: {
    title: HOME_METADATA.en.title,
    description: HOME_METADATA.en.description,
    url: "https://axignal.com/landing-lab",
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
    title: HOME_METADATA.en.title,
    description: HOME_METADATA.en.description,
    images: ["/brand/og-image-1200x630.png"],
  },
  alternates: { canonical: "https://axignal.com/landing-lab" },
};
export default function Page() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: jsonLd(siteStructuredData(null, "/landing-lab")),
        }}
      />
      <LandingLabCriticalType />
      <LandingLab content={getLandingLabContent(null)} />
    </>
  );
}
