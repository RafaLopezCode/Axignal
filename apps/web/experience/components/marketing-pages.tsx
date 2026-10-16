"use client";
import Link from "next/link";
import { INDUSTRY_SRC_SET, INDUSTRY_SIZES } from "@/lib/marketing-media";
import { ArrowRight } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { FAMILY_ORDER } from "@/lib/observation-families";
import {
  familyNames,
  familyQuestions,
  marketingPath,
  marketingCopy,
} from "@/lib/marketing-content";
import { familyDetails } from "@/lib/marketing-families";
import { industryBySlug } from "@/lib/marketing-industries";
import { publicCopy as p, marketingFaq } from "@/lib/marketing-ui";
import {
  FamilyIcon,
  IndustryArt,
  IndustryList,
  MarketingClosing,
  MarketingPricing,
  MarketingShell,
} from "./marketing-shared";

export function DataPage() {
  const { locale } = useLocale();
  return (
    <MarketingShell path="/data">
      <header className="marketing-page-intro">
        <h1>{p.dataTitle[locale]}</h1>
        <p>{p.dataLead[locale]}</p>
        <Link prefetch={false} className="marketing-text-link" href="/demo">
          {p.example[locale]}
          <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </header>
      <div className="marketing-data-layout">
        <nav
          className="marketing-family-index"
          aria-label={p.familyLink[locale]}
        >
          {FAMILY_ORDER.map((f) => (
            <a key={f} href={`#${f}`}>
              <FamilyIcon family={f} size={18} />
              {familyNames[f][locale]}
            </a>
          ))}
        </nav>
        <div className="marketing-family-articles">
          {FAMILY_ORDER.map((f) => (
            <article className="marketing-family-article" key={f} id={f}>
              <div className="marketing-family-title">
                <FamilyIcon family={f} size={32} />
                <h2>{familyNames[f][locale]}</h2>
              </div>
              <p className="marketing-family-question">
                {familyQuestions[f][locale]}
              </p>
              <p>{familyDetails[f].description[locale]}</p>
              <div className="marketing-family-evidence">
                <h3>{p.evidence[locale]}</h3>
                <p>{familyDetails[f].evidence[locale]}</p>
                <h3>{p.limit[locale]}</h3>
                <p>{familyDetails[f].limit[locale]}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
      <section className="marketing-trust marketing-section">
        <h2>{marketingCopy.sectors[locale]}</h2>
        <p>{p.industryLead[locale]}</p>
        <Link prefetch={false}
          className="marketing-text-link"
          href={marketingPath("/industries", locale)}
        >
          {p.allSectors[locale]}
          <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </section>
      <MarketingClosing />
    </MarketingShell>
  );
}

export function IndustriesPage() {
  const { locale } = useLocale();
  return (
    <MarketingShell path="/industries">
      <header className="marketing-page-intro">
        <h1>{p.industryTitle[locale]}</h1>
        <p>{p.industryLead[locale]}</p>
      </header>
      <div className="marketing-hub-content">
        <IndustryArt />
        <IndustryList />
        <p className="marketing-small">{p.editorial[locale]}</p>
      </div>
      <MarketingClosing />
    </MarketingShell>
  );
}

export function IndustryPage({ slug }: { slug: string }) {
  const { locale } = useLocale();
  const industry = industryBySlug(slug);
  // Server route validates the allowlist before rendering; this guard also avoids a client crash.
  if (!industry) return null;
  return (
    <MarketingShell path={`/industries/${industry.slug}`}>
      <header className="marketing-page-intro marketing-sector-intro">
        <Link prefetch={false}
          className="marketing-breadcrumb"
          href={marketingPath("/industries", locale)}
        >
          {p.allSectors[locale]}
        </Link>
        <h1>{industry.title[locale]}</h1>
        <p>{industry.intro[locale]}</p>
      </header>
      <figure className="marketing-sector-art">
        <img
          src="/marketing/industries.webp"
        srcSet={INDUSTRY_SRC_SET}
        sizes={INDUSTRY_SIZES}
        decoding="async"
          width={2007}
          height={784}
          alt=""
          style={{ objectPosition: industry.position }}
          fetchPriority="high"
        />
        <figcaption>{p.artNote[locale]}</figcaption>
      </figure>
      <section className="marketing-use-case marketing-section">
        <h2>{p.questions[locale]}</h2>
        <ol>
          {industry.questions.map((q) => (
            <li key={q.en}>{q[locale]}</li>
          ))}
        </ol>
      </section>
      <section className="marketing-related marketing-section">
        <h2>{p.relevant[locale]}</h2>
        <div>
          {industry.families.map((f) => (
            <Link prefetch={false} key={f} href={`${marketingPath("/data", locale)}#${f}`}>
              <FamilyIcon family={f} />
              <span>
                <strong>{familyNames[f][locale]}</strong>
                <span>{familyQuestions[f][locale]}</span>
              </span>
              <ArrowRight size={20} aria-hidden="true" />
            </Link>
          ))}
        </div>
      </section>
      <aside className="marketing-sector-limit marketing-section">
        <h2>{p.limit[locale]}</h2>
        <p>{industry.limit[locale]}</p>
        <small>{p.editorial[locale]}</small>
      </aside>
      <section className="marketing-case-next marketing-section">
        <h2>{p.proofTitle[locale]}</h2>
        <p>{marketingFaq[0].answer[locale]}</p>
        <Link prefetch={false} className="marketing-button" href="/demo">
          {p.example[locale]}
          <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </section>
      <MarketingClosing />
    </MarketingShell>
  );
}

export function MarketingPricingPage() {
  return (
    <MarketingShell path="/pricing">
      <MarketingPricing heading="h1" />
      <MarketingClosing />
    </MarketingShell>
  );
}
