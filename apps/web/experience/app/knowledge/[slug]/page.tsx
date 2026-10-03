import { notFound } from "next/navigation";
import { articles } from "@/lib/editorial";
import { KnowledgeArticle } from "@/components/knowledge";
export function generateStaticParams() { return articles.map(a=>({slug:a.slug})); }
export async function generateMetadata({params}:{params:Promise<{slug:string}>}) { const {slug}=await params; const article=articles.find(a=>a.slug===slug); return {title:article?.title.es ?? "Lectura no disponible",description:article?.deck.es}; }
export default async function Page({params}:{params:Promise<{slug:string}>}) { const {slug}=await params; if(!articles.some(a=>a.slug===slug)) notFound(); return <KnowledgeArticle slug={slug} />; }
