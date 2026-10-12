import { notFound } from "next/navigation";
import { PolicyDocument } from "@/components/trust";
import { legalOperator } from "@/lib/subscriber-server";

// The holder's identity comes from the server configuration at request time.
export const dynamic = "force-dynamic";
const slugs = ["legal", "privacy", "terms", "cookies"];
const titles: Record<string, string> = { legal: "Aviso legal", privacy: "Privacidad", terms: "Uso y límites", cookies: "Cookies y almacenamiento" };
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return { title: titles[slug] ?? "AXIGNAL", robots: { index: false, follow: true } };
}
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!slugs.includes(slug)) notFound();
  return <PolicyDocument slug={slug} operator={await legalOperator()} />;
}
