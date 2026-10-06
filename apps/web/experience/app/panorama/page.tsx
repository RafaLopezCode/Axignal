import { Suspense } from "react";
import { Panorama } from "@/components/panorama";
export const metadata = { title: "Panorama · Demo ilustrativa", robots: { index: false, follow: false } };
export default function Page() {
  return <Suspense><Panorama /></Suspense>;
}
