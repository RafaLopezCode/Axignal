"use client";
import Link from "next/link";
import { ArrowRight, Plus } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { marketingPath } from "@/lib/marketing-content";
import {
  publicCopy as p,
  methodSteps,
  audiences,
  trustItems,
  marketingFaq,
} from "@/lib/marketing-ui";
import { WeeklyBriefChannel } from "./weekly-brief-channel";
import { funnelCta, track } from "@/lib/funnel-events";
import {
  IndustryArt,
  IndustryList,
  MarketingClosing,
  MarketingPricing,
} from "./marketing-shared";

export function MarketingHomeBody() {
  const { locale } = useLocale();
  return (
    <>
      <section
        className="marketing-method marketing-section"
        id="how"
        aria-labelledby="method-title"
      >
        <div className="marketing-section-intro">
          <h2 id="method-title">{p.methodTitle[locale]}</h2>
          <p>{p.methodLead[locale]}</p>
        </div>
        <ol className="marketing-method-steps">
          {methodSteps.map((step, index) => (
            <li key={step.image}>
              <div className="marketing-method-art">
                <img
                  src={`/marketing/${step.image}.webp`}
                  width={640}
                  height={640}
                  alt=""
                  loading="lazy"
                />
              </div>
              <span className="marketing-method-step">{index + 1}</span>
              <h3>{step.title[locale]}</h3>
              <p>{step.body[locale]}</p>
            </li>
          ))}
        </ol>
      </section>
      <section
        className="marketing-proof marketing-section"
        id="proof"
        aria-labelledby="proof-title"
      >
        <div>
          <h2 id="proof-title">{p.proofTitle[locale]}</h2>
          <p className="marketing-proof-lead">{p.proofLead[locale]}</p>
          <Link prefetch={false}
            className="marketing-text-link"
            href="/demo"
            onClick={() =>
              track({
                kind: "CTA_ACTIVATED",
                surface: "landing",
                cta: funnelCta.proofExample,
              })
            }
          >
            {p.example[locale]}
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </div>
        <div className="marketing-principles">
          {trustItems.map((item) => (
            <article key={item.title.en}>
              <h3>{item.title[locale]}</h3>
              <p>{item.body[locale]}</p>
            </article>
          ))}
        </div>
      </section>
      <section
        className="marketing-audiences marketing-section"
        id="audience"
        aria-labelledby="audience-title"
      >
        <h2 id="audience-title">{p.audienceTitle[locale]}</h2>
        <div>
          {audiences.map((a) => (
            <article key={a.slug}>
              <h3>{a.title[locale]}</h3>
              <p>{a.body[locale]}</p>
              <Link prefetch={false}
                className="marketing-text-link"
                href={marketingPath(`/industries/${a.slug}`, locale)}
              >
                {p.sectorLink[locale]}
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
            </article>
          ))}
        </div>
      </section>
      <section
        className="marketing-sectors marketing-section"
        aria-labelledby="sectors-title"
      >
        <div className="marketing-section-intro">
          <h2 id="sectors-title">{p.industryTitle[locale]}</h2>
          <p>{p.industryLead[locale]}</p>
        </div>
        <IndustryArt />
        <IndustryList />
        <p className="marketing-small">{p.editorial[locale]}</p>
      </section>
      <section className="marketing-trust marketing-section" id="trust">
        <h2>{p.proofTitle[locale]}</h2>
        <p>{p.proofLead[locale]}</p>
        <div>
          <Link prefetch={false} className="marketing-text-link" href="/policies">
            {p.trust[locale]}
            <ArrowRight size={17} aria-hidden="true" />
          </Link>
          <Link prefetch={false}
            className="marketing-text-link"
            href="/knowledge/basis/product-model"
          >
            Knowledge
            <ArrowRight size={17} aria-hidden="true" />
          </Link>
        </div>
      </section>
      <MarketingPricing />
      <section
        className="marketing-faq marketing-section"
        aria-labelledby="faq-title"
      >
        <h2 id="faq-title">{p.faqTitle[locale]}</h2>
        <div>
          {marketingFaq.map((f) => (
            <details key={f.question.en}>
              <summary>
                {f.question[locale]}
                <Plus size={21} strokeWidth={1.5} aria-hidden="true" />
              </summary>
              <p>{f.answer[locale]}</p>
            </details>
          ))}
        </div>
      </section>
      <WeeklyBriefChannel variant="marketing" />
      <MarketingClosing />
    </>
  );
}
