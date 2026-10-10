import snapshot from "./synthetic-observatory.json";
import { portfolioSchema, type SubscriberPortfolio } from "@/lib/subscriber-contracts";
import type { Locale } from "@/lib/languages";
import type { ObservatorySource } from "@/lib/observatory-source";
import { SYNTHETIC_PHRASES } from "./synthetic-phrases";

/**
 * The public demo reads a fixed, fictional snapshot instead of the account's API.
 * Nothing here is private data: every organization is fictional, and its demo domain is only a name.
 * The demo renders the same Observatory as the subscriber; only this data source differs.
 */
export const SYNTHETIC_PROVENANCE: string = snapshot.provenance;

const outputs = snapshot.outputs as Record<string, unknown>;

type Words = Record<Locale, string>;
const same = (word: string): Words => ({ es: word, en: word, de: word, pt: word, fr: word, it: word });

/**
 * The translatable word of each demo domain (www.demo-<word>.com), in portfolio order.
 * `es` is the snapshot's own word; the other locales translate it, so the domain stays valid ASCII.
 */
const SITES: { es: string; words: Words }[] = [
  { es: "energia", words: { es: "energia", en: "energy", de: "energie", pt: "energia", fr: "energie", it: "energia" } },
  { es: "seo-geo", words: same("seo-geo") },
  { es: "consultor", words: { es: "consultor", en: "consultant", de: "berater", pt: "consultor", fr: "consultant", it: "consulente" } },
  { es: "constructor", words: { es: "constructor", en: "builder", de: "bauunternehmer", pt: "construtor", fr: "constructeur", it: "costruttore" } },
  { es: "marketing", words: same("marketing") },
  { es: "fabrica", words: { es: "fabrica", en: "factory", de: "fabrik", pt: "fabrica", fr: "usine", it: "fabbrica" } },
  { es: "distribuidor", words: { es: "distribuidor", en: "distributor", de: "distributor", pt: "distribuidor", fr: "distributeur", it: "distributore" } },
];

const capitalize = (word: string) => word.charAt(0).toUpperCase() + word.slice(1);

/** Every demo domain, demo panel name and measurement phrase, rewritten into the reader's locale wherever it appears. */
function localize<T>(value: T, locale: Locale): T {
  // The snapshot's words are Spanish (names, domains) and English (measurement phrases).
  const pairs = locale === "es" ? [] : SITES.flatMap(({ es, words }) => {
    // An unexpected locale reads the Spanish word rather than breaking the whole demo.
    const word = words[locale] ?? es;
    return [
      [`demo-${es}.com`, `demo-${word}.com`],
      [`Demo ${capitalize(es)}`, `Demo ${capitalize(word)}`],
    ];
  });
  const replace = (text: string) => pairs.reduce((out, [from, to]) => out.split(from).join(to), text);
  const walk = (node: unknown): unknown => {
    if (typeof node === "string") return (locale !== "en" && SYNTHETIC_PHRASES[node]?.[locale]) || replace(node);
    if (Array.isArray(node)) return node.map(walk);
    if (node && typeof node === "object") return Object.fromEntries(Object.entries(node).map(([key, child]) => [key, walk(child)]));
    return node;
  };
  return walk(value) as T;
}

export function syntheticPortfolio(locale: Locale): SubscriberPortfolio {
  return portfolioSchema.parse({
    state: "success",
    capacity: 10,
    capacityCurrentness: "CURRENT",
    entitlementSource: "UNKNOWN",
    canPurchase: false,
    contractingEnabled: false,
    organizations: localize(snapshot.portfolio, locale),
  });
}

export function syntheticOutput(focusId: string, locale: Locale): unknown {
  if (!Object.prototype.hasOwnProperty.call(outputs, focusId)) throw new Error("READ_FAILED");
  return localize(outputs[focusId], locale);
}

/** The demonstration context of the Observatory: this snapshot, read only, with no account and no operations. */
export const demoSource: ObservatorySource = {
  mode: "demo",
  canAct: false,
  localized: true,
  // The demo shows every control, disabled, so the reader sees the whole product.
  capabilities: { account: true, manage: true, recheck: true, axent: "subscriber" },
  async readPortfolio(_signal, locale) { return syntheticPortfolio(locale); },
  async readOutput(focusId, _signal, locale) { return syntheticOutput(focusId, locale); },
  // The rail names an organization by its demo domain, derived from the panel name it already carries.
  menuName: item => "www." + item.label.toLowerCase().replace(" ", "-") + ".com",
};
