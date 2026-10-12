import type { Metadata } from "next";
import { Landing } from "@/components/landing";
import { absolutePublicUrl } from "@/lib/acquisition-seo";
import { homeLanguages, jsonLd, siteStructuredData } from "@/lib/site-seo";
import "@/components/observatory.css";
import "@/components/landing-observatory.css";

export const metadata: Metadata = {
  alternates: { canonical: absolutePublicUrl("/"), languages: homeLanguages() },
};

export default function Page() {
  return <>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(siteStructuredData(null)) }}/>
    <Landing />
  </>;
}
