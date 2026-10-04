import { Suspense } from "react";
import { Panorama } from "@/components/panorama";
export default function Page() {
  return (
    <Suspense>
      <Panorama />
    </Suspense>
  );
}
