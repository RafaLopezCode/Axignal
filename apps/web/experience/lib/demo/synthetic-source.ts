import snapshot from "./synthetic-observatory.json";
import { portfolioSchema, type SubscriberPortfolio } from "@/lib/subscriber-contracts";
import type { Locale } from "@/lib/languages";

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
  { es: "seo", words: same("seo") },
  { es: "geo", words: same("geo") },
  { es: "consultor", words: { es: "consultor", en: "consultant", de: "berater", pt: "consultor", fr: "consultant", it: "consulente" } },
  { es: "constructor", words: { es: "constructor", en: "builder", de: "bauunternehmer", pt: "construtor", fr: "constructeur", it: "costruttore" } },
  { es: "marketing", words: same("marketing") },
  { es: "fabrica", words: { es: "fabrica", en: "factory", de: "fabrik", pt: "fabrica", fr: "usine", it: "fabbrica" } },
  { es: "distribuidor", words: { es: "distribuidor", en: "distributor", de: "distributor", pt: "distribuidor", fr: "distributeur", it: "distributore" } },
];

const capitalize = (word: string) => word.charAt(0).toUpperCase() + word.slice(1);

/** Every demo domain and demo panel name, rewritten into the reader's locale wherever it appears. */
function localize<T>(value: T, locale: Locale): T {
  if (locale === "es") return value;
  const pairs = SITES.flatMap(({ es, words }) => [
    [`demo-${es}.com`, `demo-${words[locale]}.com`],
    [`Demo ${capitalize(es)}`, `Demo ${capitalize(words[locale])}`],
  ]);
  const replace = (text: string) => pairs.reduce((out, [from, to]) => out.split(from).join(to), text);
  const walk = (node: unknown): unknown => {
    if (typeof node === "string") return replace(node);
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
