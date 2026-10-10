import { Suspense } from "react";
import { SubscriberPortfolioExperience } from "@/components/subscriber-portfolio";
import { DemoNotice } from "@/components/demo-notice";

export const metadata = {
  title: "Observatorio · Ejemplo guiado",
  robots: { index: false, follow: false },
};

/** The subscriber Observatory over a fictional snapshot: the same reading surface, no account, no private data. */
export default function Page() {
  return <Suspense><SubscriberPortfolioExperience source="synthetic" notice={<DemoNotice/>}/></Suspense>;
}
