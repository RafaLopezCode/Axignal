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
    `Pricing: ${euros(EUR_REFERENCE.baseMinor)} EUR per month for the first observed organization and ${euros(EUR_REFERENCE.additionalMinor)} EUR for each additional one, tax excluded. Access is currently by Design Partner invitation.`,
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
    "## Optional",
    `- [Contact](${absolutePublicUrl("/contact")})`,
    `- [Privacy](${absolutePublicUrl("/policies/privacy")})`,
    "",
  ].join("\n");
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=3600" } });
}
