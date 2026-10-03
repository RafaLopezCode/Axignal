import { notFound } from "next/navigation";
import { DoctrineBasis } from "@/components/doctrine-basis";
import { basisSources, type BasisSource } from "@/lib/doctrine-basis";
export function generateStaticParams() { return Object.keys(basisSources).map(source=>({source})); }
export const metadata = {title:"La base de nuestras ideas",robots:{index:false,follow:true}};
export default async function Page({params}:{params:Promise<{source:string}>}) {
  const {source}=await params;
  if(!Object.hasOwn(basisSources,source)) notFound();
  return <DoctrineBasis source={source as BasisSource}/>;
}
