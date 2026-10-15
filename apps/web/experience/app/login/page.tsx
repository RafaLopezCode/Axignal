import { Access } from "@/components/access";
export const metadata = { title: "Acceder", robots: {index:false,follow:true} };
export default async function Page({ searchParams }: {
  searchParams: Promise<{ access?: string | string[] }>;
}) {
  const query = await searchParams;
  return <Access intent="login" callbackFailed={query.access === "failed"} />;
}
