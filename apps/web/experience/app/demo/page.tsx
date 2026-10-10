import { Suspense } from "react";
import { DemoObservatory } from "@/components/demo-observatory";

export const metadata = {
  title: "Observatorio · Ejemplo guiado",
  robots: { index: false, follow: false },
};

/** The subscriber Observatory in its demonstration context. The page adds nothing of its own. */
export default function Page() {
  return <Suspense><DemoObservatory/></Suspense>;
}
