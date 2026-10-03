import { notFound } from "next/navigation";
import { evidence } from "@/lib/projection";
import { SourceDocument } from "@/components/source-document";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const item = evidence.find((e) => e.id === id);
  if (!item) notFound();
  return <SourceDocument item={item} />;
}
