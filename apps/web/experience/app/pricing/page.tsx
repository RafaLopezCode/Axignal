import type { Metadata } from "next";
import { Pricing } from "@/components/pricing";
import { absolutePublicUrl } from "@/lib/acquisition-seo";
import { publicSocialMetadata } from "@/lib/site-seo";
import { EUR_REFERENCE } from "@/lib/commercial-prices";
import "./pricing.css";

const description = `AXIGNAL costs ${(EUR_REFERENCE.baseMinor / 100).toFixed(2)} € per month for the first observed organization and ${(EUR_REFERENCE.additionalMinor / 100).toFixed(2)} € for each additional one, tax excluded. Access is currently by Design Partner invitation.`;

export const metadata: Metadata = {
  title: "Pricing",
  description,
  alternates: { canonical: absolutePublicUrl("/pricing") },
  ...publicSocialMetadata({ title: "Pricing · AXIGNAL", description, path: "/pricing", locale: "en" }),
};

export default function Page() {
  return <Pricing />;
}
