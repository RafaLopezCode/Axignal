import type { Metadata } from "next";
import { permanentRedirect, notFound } from "next/navigation";
import { articles } from "@/lib/editorial";
import { acquisitionPages, localizedPagePath } from "@/lib/acquisition";
import { absolutePublicUrl } from "@/lib/acquisition-seo";

const legacyArticleTargets: Record<string, string> = {
  "una-senal-no-es-una-certeza": "evidence-observed-vs-potential",
  "una-organizacion-una-mirada-un-mundo": "commercial_external_observation",
  "el-contexto-tambien-tiene-fecha": "evidence-currentness",
  "no-saber-es-un-estado-util": "evidence-unknown-not-false",
  "axent-una-conversacion-con-contexto": "persistent-context-for-agents",
  "comprender-sin-empezar-de-cero": "business-memory-for-ai",
};

export const dynamicParams = false;
export function generateStaticParams() { return articles.map(({ slug }) => ({ slug })); }
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const page = acquisitionPages.find((candidate) => candidate.id === legacyArticleTargets[slug]);
  const content = page?.locales.es;
  return content ? { title: content.title, description: content.description, alternates: { canonical: absolutePublicUrl(`/es/knowledge/${content.slug}`) }, robots: { index: false, follow: true } } : { robots: { index: false, follow: false } };
}
export default async function LegacyArticleRoute({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const id = legacyArticleTargets[slug];
  const page = acquisitionPages.find((candidate) => candidate.id === id);
  if (!page?.locales.es) notFound();
  permanentRedirect(localizedPagePath(page, "es"));
}
