import type { Metadata } from "next";
import { Pricing } from "@/components/pricing";
import { absolutePublicUrl } from "@/lib/acquisition-seo";
import "./pricing.css";

export const metadata: Metadata = {
  title: "Pricing",
  description: "AXIGNAL costs 9.95 € per month for the first observed organization and 4.95 € for each additional one, tax excluded. Access is currently by Design Partner invitation.",
  alternates: { canonical: absolutePublicUrl("/pricing") },
};

export default function Page() {
  return <Pricing />;
}
