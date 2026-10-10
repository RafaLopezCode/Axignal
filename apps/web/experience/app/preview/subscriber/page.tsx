import { notFound } from "next/navigation";
import { Suspense } from "react";
import { SubscriberPortfolioExperience } from "@/components/subscriber-portfolio";

export const metadata = {
  title: "Vista previa · Panel del suscriptor",
  robots: { index: false, follow: false },
};

/**
 * Development preview of the subscriber panel over the synthetic snapshot: the account's own component,
 * without the demo's notice. It is not served in production, and no account data is read.
 */
export default function Page() {
  if (process.env.NODE_ENV === "production") notFound();
  return <Suspense><SubscriberPortfolioExperience source="synthetic" /></Suspense>;
}
