import { notFound } from "next/navigation";
import { Suspense } from "react";
import { DemoObservatory } from "@/components/demo-observatory";

export const metadata = {
  title: "Vista previa · Panel del suscriptor",
  robots: { index: false, follow: false },
};

/**
 * Development preview of the subscriber panel: the account's own Observatory in its demonstration context.
 * It is not served in production, and no account data is read.
 */
export default function Page() {
  if (process.env.NODE_ENV === "production") notFound();
  return <Suspense><DemoObservatory/></Suspense>;
}
