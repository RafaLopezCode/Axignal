import { notFound } from "next/navigation";
import { PolicyDocument } from "@/components/trust";
const slugs=["privacy","terms","cookies"];
export function generateStaticParams(){return slugs.map(slug=>({slug}));}
export async function generateMetadata({params}:{params:Promise<{slug:string}>}){const {slug}=await params;return {title:slug==="privacy"?"Privacidad":slug==="terms"?"Uso y límites":"Cookies y almacenamiento",robots:{index:false,follow:true}};}
export default async function Page({params}:{params:Promise<{slug:string}>}){const {slug}=await params;if(!slugs.includes(slug))notFound();return <PolicyDocument slug={slug} />;}
