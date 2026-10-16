import { notFound } from "next/navigation";
import { IndustryPage } from "@/components/marketing-pages";
import { isLocale, locales } from "@/lib/languages";
import { industries, industryBySlug } from "@/lib/marketing-industries";
import { marketingMetadata } from "@/lib/marketing-seo";
type Props={params:Promise<{locale:string;industry:string}>};
export const dynamicParams=false;
export function generateStaticParams() { return locales.flatMap(({id})=>industries.map(i=>({locale:id,industry:i.slug}))); }
export async function generateMetadata({params}:Props) {
  const {locale,industry}=await params;
  if(!isLocale(locale)||!industryBySlug(industry)) notFound();
  return marketingMetadata(`/industries/${industry}`,locale);
}
export default async function Page({params}:Props) {
  const {locale,industry}=await params;
  if(!isLocale(locale)||!industryBySlug(industry)) notFound();
  return <IndustryPage slug={industry}/>;
}
