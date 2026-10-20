import type { Metadata } from "next";
import { LandingLab } from "@/components/landing-lab";
import { getLandingLabContent } from "@/lib/landing-lab-content";
import { LandingLabCriticalType } from "@/components/landing-lab-critical-type";
import { absolutePublicUrl } from "@/lib/acquisition-seo";
import { homeLanguages, jsonLd, siteStructuredData } from "@/lib/site-seo";

export const metadata: Metadata = {
  alternates: { canonical: absolutePublicUrl("/"), languages: homeLanguages() },
};

export default function Page() {
  return <>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(siteStructuredData(null)) }}/>
    <LandingLabCriticalType />
    <LandingLab content={getLandingLabContent(null)} />
  </>;
}
