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
const content = {
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
export type LandingLabContent = typeof content;
/** Called by server pages. Localized routes deliver only their chosen wording,
 * retaining the localized-record interface used by presentation. Repeated aliases
 * compress locally; source catalogs never enter client JS. The unprefixed route
 * retains all locales for saved/browser preference resolution.
 */
export function getLandingLabContent(locale: Locale | null): LandingLabContent {
  if (locale === null) return content;
  const chosen = locale;
  function select(value: unknown): unknown {
    if (Array.isArray(value)) return value.map(select);
    if (value && typeof value === "object") {
      const record = value as Record<string, unknown>;
      if (locales.every(({ id }) => typeof record[id] === "string")) {
        return Object.fromEntries(
          Object.keys(record).map((id) => [id, record[chosen]]),
        );
      }
      return Object.fromEntries(
        Object.entries(record).map(([key, item]) => [key, select(item)]),
      );
    }
    return value;
  }
  return select(content) as LandingLabContent;
}
