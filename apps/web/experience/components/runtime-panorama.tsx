"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useLocale } from "@/lib/locale";
import {
  readCustomerZeroResponse,
  type CustomerZeroState,
} from "@/lib/runtime-projection";
import { Brand, LocaleToggle } from "./ui";
import { RuntimeProductProjection } from "./runtime-product";

// FR-30 is currently an authorized first-proof read. This is the same product
// projection shown inside Customer Zero, without private operational records.
export function RuntimePanorama() {
  const { t } = useLocale();
  const [result, setResult] = useState<CustomerZeroState>({ state: "loading" });
  useEffect(() => {
    let active = true;
    fetch("/api/subscriber-context", { cache: "no-store" })
      .then(async (response) =>
        readCustomerZeroResponse(await response.json(), response.status),
      )
      .then((value) => {
        if (active) setResult(value);
      })
      .catch(() => {
        if (active)
          setResult({ state: "failure", reason: "RUNTIME_UNAVAILABLE" });
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <div className="runtime-panorama">
      <header className="product-topbar">
        <Brand />
        <LocaleToggle />
      </header>
      <main id="main" className="customer-zero">
        <Link className="text-link" href="/admin/customer-zero">
          {t("Volver a Customer Zero", "Return to Customer Zero")}
        </Link>
        <h1>{t("Panorama", "Panorama")}</h1>
        {result.state === "success" ? (
          <RuntimeProductProjection projection={result.projection} />
        ) : (
          <section aria-live="polite">
            <p>{result.state}</p>
            <p>
              {t(
                "Esta lectura depende de una sesión autorizada y una proyección real del runtime. Vuelve a Customer Zero para revisar su estado.",
                "This reading requires an authorized session and a real runtime projection. Return to Customer Zero to review its state.",
              )}
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
