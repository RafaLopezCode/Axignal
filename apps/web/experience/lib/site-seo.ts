/**
 * What AXIGNAL's own public site declares to search engines and assistants: who it is, the
 * site, the published offer (from the governed price book) and its language versions. The
 * same checks AXIGNAL runs on a subscriber's website, applied to itself.
 */
import type { Metadata } from "next";
import { EUR_REFERENCE } from "./commercial-prices";
import { locales, type Locale } from "./languages";
import { absolutePublicUrl } from "./acquisition-seo";
import { HOME_METADATA } from "./public-home-metadata";

const socialLocales: Record<Locale, string> = {
  es: "es_ES", en: "en_US", de: "de_DE", pt: "pt_PT", fr: "fr_FR", it: "it_IT",
};
export const PUBLIC_SOCIAL_IMAGE = "/brand/og-image-1200x630.png";

/** Next replaces nested OpenGraph metadata: every route must declare its image. */
export function publicSocialMetadata({ title, description, path, locale }: {
  title: string; description: string; path: string; locale: Locale;
}): Pick<Metadata, "openGraph" | "twitter"> {
  const images = [{ url: PUBLIC_SOCIAL_IMAGE, width: 1200, height: 630, alt: title }];
  return {
    openGraph: {
      type: "website", siteName: "AXIGNAL", title, description,
      url: absolutePublicUrl(path), locale: socialLocales[locale],
      alternateLocale: locales.filter(({ id }) => id !== locale).map(({ id }) => socialLocales[id]),
      images,
    },
    twitter: { card: "summary_large_image", title, description, images },
  };
}

export function localizedHomeMetadata(locale: Locale): Metadata {
  const home = HOME_METADATA[locale];
  return {
    title: { absolute: home.title },
    description: home.description,
    alternates: { canonical: absolutePublicUrl(`/${locale}`), languages: homeLanguages() },
    ...publicSocialMetadata({ ...home, path: `/${locale}`, locale }),
  };
}

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
        logo: { "@type": "ImageObject", url: absolutePublicUrl("/brand/organization-logo-512.png"), width: 512, height: 512 },
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
        about: { "@id": absolutePublicUrl("/#service") },
      },
      {
        "@type": "WebPage",
        "@id": `${url}#webpage`,
        url,
        name: meta.title,
        description: meta.description,
        inLanguage: locale ?? "en",
        isPartOf: { "@id": absolutePublicUrl("/#website") },
        mainEntity: { "@id": absolutePublicUrl("/#service") },
        primaryImageOfPage: { "@type": "ImageObject", url: absolutePublicUrl(PUBLIC_SOCIAL_IMAGE), width: 1200, height: 630 },
      },
      {
        "@type": "Service",
        "@id": absolutePublicUrl("/#service"),
        name: "AXIGNAL",
        url: absolutePublicUrl("/"),
        description: HOME_METADATA.en.description,
        serviceType: "Economic observation of organizations from public sources",
        provider: { "@id": absolutePublicUrl("/#organization") },
        offers: [
          {
            "@type": "Offer",
            name: "First observed organization",
            description: "Monthly reference price excluding tax. Access is by Design Partner invitation, without payment during the programme; see the pricing page for terms.",
            price: euros(EUR_REFERENCE.baseMinor),
            priceCurrency: EUR_REFERENCE.currency,
            url: absolutePublicUrl("/pricing"),
            priceSpecification: {
              "@type": "UnitPriceSpecification",
              price: euros(EUR_REFERENCE.baseMinor),
              priceCurrency: EUR_REFERENCE.currency,
              unitText: "MONTH",
              billingDuration: "P1M",
              valueAddedTaxIncluded: false,
            },
          },
          {
            "@type": "Offer",
            name: "Each additional observed organization",
            description: "Monthly reference price per additional organization, excluding tax. Signals are not charged individually. Access is currently by invitation.",
            price: euros(EUR_REFERENCE.additionalMinor),
            priceCurrency: EUR_REFERENCE.currency,
            url: absolutePublicUrl("/pricing"),
            priceSpecification: {
              "@type": "UnitPriceSpecification",
              price: euros(EUR_REFERENCE.additionalMinor),
              priceCurrency: EUR_REFERENCE.currency,
              unitText: "MONTH",
              billingDuration: "P1M",
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
