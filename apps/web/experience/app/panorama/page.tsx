import { Suspense } from "react";
import { Panorama } from "@/components/panorama";
export default function Page() {
  return (
    <Suspense
      fallback={
        <main id="main" className="route-loading">
          Preparando la vista…
        </main>
      }
    >
      <Panorama />
    </Suspense>
  );
}
