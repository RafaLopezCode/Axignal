import { EUR_REFERENCE } from "@/lib/commercial-prices";
import { absolutePublicUrl } from "@/lib/acquisition-seo";
import { locales } from "@/lib/languages";

/** A plain summary for language models and assistants (llmstxt.org): what AXIGNAL is and where to read more. */
export const dynamic = "force-static";

export function GET() {
  const euros = (minor: number) => (minor / 100).toFixed(2);
  const body = [
    "# AXIGNAL",
    "",
    "> AXIGNAL is business and economic intelligence from public evidence. It continuously observes the organizations you choose in public sources, remembers what it finds, and shows what changes and why it may matter, with source and date. It separates what is observed from what is potential and says what is not known yet.",
    "",
    `Published monthly reference prices: ${euros(EUR_REFERENCE.baseMinor)} EUR for the first observed organization and ${euros(EUR_REFERENCE.additionalMinor)} EUR for each additional one, tax excluded. Signals are not charged individually. Access is currently by Design Partner invitation, without payment during the programme. See the pricing page for current terms.`,
    "",
    "## How to understand the product",
    "- Economic opportunity intelligence connects public evidence, capabilities and context. An opportunity is potential; it does not establish buying intent, a contract or an observed commercial relationship.",
    "- Knowledge accumulates with sources, dates and memory. A later reading can explain what changed; unknown information remains unknown.",
    "- Search and generative representation are condition-bound observations. A mention is not a citation; a citation is not an endorsement. AXIGNAL does not guarantee search rankings or AI recommendations.",
    "- The guided example uses fictional organizations and illustrative sources. It demonstrates the interaction and evidence-reading method, not real customer activity.",
    "",
    "## Product",
    `- [Home](${absolutePublicUrl("/")}): what AXIGNAL observes and how it reads an organization`,
    `- [Guided example](${absolutePublicUrl("/demo")}): a fictional organization read end to end`,
    `- [Pricing](${absolutePublicUrl("/pricing")}): published prices and how access works today`,
    `- [What AXIGNAL does](${absolutePublicUrl("/en/knowledge/what-axignal-does")}): the ten families, evidence states, history and the MCP connection`,
    "",
    "## Knowledge",
    ...locales.map(({ id, name }) => `- [Knowledge (${name})](${absolutePublicUrl(`/${id}/knowledge`)})`),
    "",
    "## Language versions",
    ...locales.map(({ id, name }) => `- [AXIGNAL (${name})](${absolutePublicUrl(`/${id}`)}): localized product, audience, method and pricing`),
    "",
    "## Evidence and trust",
    `- [What AXIGNAL observes](${absolutePublicUrl("/en/data")}): observation families and their limits`,
    `- [Trust and policies](${absolutePublicUrl("/policies")}): privacy, terms and evidence boundaries`,
    "",
    "## Optional",
    `- [Contact](${absolutePublicUrl("/contact")})`,
    `- [Privacy](${absolutePublicUrl("/policies/privacy")})`,
    "",
  ].join("\n");
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=3600" } });
}
