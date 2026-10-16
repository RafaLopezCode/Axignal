import { notFound } from "next/navigation";
import { IndustriesPage } from "@/components/marketing-pages";
import { isLocale, locales } from "@/lib/languages";
import { marketingMetadata } from "@/lib/marketing-seo";

export const dynamicParams=false;
export function generateStaticParams() { return locales.map(({id})=>({locale:id})); }
export async function generateMetadata({params}:{params:Promise<{locale:string}>}) {
  const {locale}=await params;
  if(!isLocale(locale)) notFound();
  return marketingMetadata("/industries",locale);
}
export default async function Page({params}:{params:Promise<{locale:string}>}) {
  const {locale}=await params;
  if(!isLocale(locale)) notFound();
  return <IndustriesPage/>;
}
