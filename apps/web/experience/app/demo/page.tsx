import { Suspense } from "react";
import { ExampleObservatory } from "@/components/example-observatory";

export const metadata = {
  title: "Observatorio · Ejemplo guiado",
  robots: { index: false, follow: false },
};

export default function Page() {
  return <Suspense><ExampleObservatory /></Suspense>;
}
