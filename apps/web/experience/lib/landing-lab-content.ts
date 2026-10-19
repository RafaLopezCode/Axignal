import type { Locale } from "./languages";
import { locales } from "./languages";
import { labCopy, labQuestions, labPersonas, labFaq } from "./landing-lab-copy";
import { labExperienceCopy } from "./landing-lab-experience-copy";
import {
  publicCopy,
  marketingFaq,
  trustItems,
  methodSteps,
} from "./marketing-ui";
import { newsletterCopy } from "./marketing-newsletter";
import { industries } from "./marketing-industries";
import { labInsight } from "./landing-lab-model";
import {
  exampleInsights,
  EXAMPLE_MOMENTS,
  type ExampleMoment,
} from "./landing-observatory";
import { evidence, demoOrganizationName } from "./projection";
import { translate } from "./copy-catalog";

const content = {
  heroEvidence: evidence.filter((item) => item.id === "capabilities"),
  demoOrganizationName,
  c: labCopy,
  x: labExperienceCopy,
  p: {
    access: publicCopy.access,
    contact: publicCopy.contact,
    extra: publicCopy.extra,
    first: publicCopy.first,
    month: publicCopy.month,
    pricingTitle: publicCopy.pricingTitle,
    request: publicCopy.request,
    rights: publicCopy.rights,
    taxes: publicCopy.taxes,
    trust: publicCopy.trust,
  },
  newsletterCopy: {
    title: newsletterCopy.title,
    lead: newsletterCopy.lead,
    boundary: newsletterCopy.boundary,
    checking: newsletterCopy.checking,
  },
  labQuestions,
  labPersonas,
  labFaq,
  marketingFaq,
  trustItems,
  methodSteps,
  industries: industries.map(({ slug, title }) => ({ slug, title })),
};

type Scenario = (typeof labQuestions)[number]["id"];
type Views = Record<
  ExampleMoment,
  Record<Scenario, ReturnType<typeof labInsight>>
>;
function readingFor(locale: Locale) {
  const copy = (value: { es: string; en: string }) =>
    translate(value.es, value.en, locale);
  const hero = exampleInsights("2026-10-03", copy).find(
    (item) => item.id === "renovation",
  );
  if (!hero) throw new Error("Missing canonical landing fixture");
  const views = Object.fromEntries(
    EXAMPLE_MOMENTS.map((moment) => [
      moment,
      Object.fromEntries(
        labQuestions.map((question) => [
          question.id,
          labInsight(moment, question.id, copy),
        ]),
      ),
    ]),
  ) as Views;
  return { hero, views };
}
export type LandingLabContent = typeof content & {
  runtime: {
    moments: typeof EXAMPLE_MOMENTS;
    byLocale: Record<Locale, ReturnType<typeof readingFor>>;
  };
};

/** Server pages select wording and compute the same existing synthetic projections.
 * Localized routes share one selected-language reading by reference; the unprefixed
 * route retains every locale for saved/browser preferences. No evidence is changed.
 */
export function getLandingLabContent(locale: Locale | null): LandingLabContent {
  let presentation = content;
  if (locale !== null) {
    const chosen = locale;
    function select(value: unknown): unknown {
      if (Array.isArray(value)) return value.map(select);
      if (value && typeof value === "object") {
        const record = value as Record<string, unknown>;
        if (locales.every(({ id }) => typeof record[id] === "string"))
          return Object.fromEntries(
            Object.keys(record).map((id) => [id, record[chosen]]),
          );
        return Object.fromEntries(
          Object.entries(record).map(([key, item]) => [key, select(item)]),
        );
      }
      return value;
    }
    presentation = select(content) as typeof content;
  }
  const selected = locale === null ? null : readingFor(locale);
  const byLocale = Object.fromEntries(
    locales.map(({ id }) => [id, selected ?? readingFor(id)]),
  ) as LandingLabContent["runtime"]["byLocale"];
  return { ...presentation, runtime: { moments: EXAMPLE_MOMENTS, byLocale } };
}
