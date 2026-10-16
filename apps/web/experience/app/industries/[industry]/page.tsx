import { notFound, permanentRedirect } from "next/navigation";
import { industries, industryBySlug } from "@/lib/marketing-industries";
export const dynamicParams=false;
export function generateStaticParams() { return industries.map(i=>({industry:i.slug})); }
export default async function Page({params}:{params:Promise<{industry:string}>}) {
  const {industry}=await params;
  if(!industryBySlug(industry)) notFound();
  permanentRedirect(`/en/industries/${industry}`);
}
