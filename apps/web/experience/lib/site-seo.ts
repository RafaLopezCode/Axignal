/**
 * What AXIGNAL's own public site declares to search engines and assistants: who it is, the
 * site, the published offer (from the governed price book) and its language versions. The
 * same checks AXIGNAL runs on a subscriber's website, applied to itself.
 */
import { EUR_REFERENCE } from "./commercial-prices";
import { locales, type Locale } from "./languages";
import { absolutePublicUrl } from "./acquisition-seo";
import { HOME_METADATA } from "./public-home-metadata";

/** Every home language version, plus x-default on the language-neutral root. */
export function homeLanguages(): Record<string, string> {
  return {
    ...Object.fromEntries(locales.map(({ id }) => [id, absolutePublicUrl(`/${id}`)])),
    "x-default": absolutePublicUrl("/"),
  };
}

export function siteStructuredData(locale: Locale | null, pagePath?: string): Record<string, unknown> {
  const url = absolutePublicUrl(pagePath ?? (locale ? `/${locale}` : "/"));
  const meta = HOME_METADATA[locale ?? "en"];
  const euros = (minor: number) => (minor / 100).toFixed(2);
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": absolutePublicUrl("/#organization"),
        name: "AXIGNAL",
        url: absolutePublicUrl("/"),
        logo: absolutePublicUrl("/brand/apple-touch-icon.png"),
        description: HOME_METADATA.en.description,
        // The official profiles the footer links, declared for machines too.
        sameAs: ["https://www.linkedin.com/company/axignal/"],
        contactPoint: {
          "@type": "ContactPoint",
          contactType: "customer support",
          url: absolutePublicUrl("/contact"),
          availableLanguage: locales.map(({ id }) => id),
        },
      },
      {
        "@type": "WebSite",
        "@id": absolutePublicUrl("/#website"),
        url: absolutePublicUrl("/"),
        name: "AXIGNAL",
        inLanguage: locales.map(({ id }) => id),
        publisher: { "@id": absolutePublicUrl("/#organization") },
      },
      {
        "@type": "WebPage",
        "@id": `${url}#webpage`,
        url,
        name: meta.title,
        description: meta.description,
        inLanguage: locale ?? "en",
        isPartOf: { "@id": absolutePublicUrl("/#website") },
      },
      {
        "@type": "Service",
        "@id": absolutePublicUrl("/#service"),
        name: "AXIGNAL",
        serviceType: "Economic observation of organizations from public sources",
        provider: { "@id": absolutePublicUrl("/#organization") },
        areaServed: "Worldwide",
        offers: [
          {
            "@type": "Offer",
            name: "First observed organization",
            price: euros(EUR_REFERENCE.baseMinor),
            priceCurrency: EUR_REFERENCE.currency,
            url: absolutePublicUrl("/pricing"),
            priceSpecification: {
              "@type": "UnitPriceSpecification",
              price: euros(EUR_REFERENCE.baseMinor),
              priceCurrency: EUR_REFERENCE.currency,
              unitText: "MONTH",
              valueAddedTaxIncluded: false,
            },
          },
          {
            "@type": "Offer",
            name: "Each additional observed organization",
            price: euros(EUR_REFERENCE.additionalMinor),
            priceCurrency: EUR_REFERENCE.currency,
            url: absolutePublicUrl("/pricing"),
            priceSpecification: {
              "@type": "UnitPriceSpecification",
              price: euros(EUR_REFERENCE.additionalMinor),
              priceCurrency: EUR_REFERENCE.currency,
              unitText: "MONTH",
              valueAddedTaxIncluded: false,
            },
          },
        ],
      },
    ],
  };
}

/** Serialized for a <script type="application/ld+json">; "<" is escaped so it cannot close the tag. */
export function jsonLd(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}
