"use client";
import { useState } from "react";
import Link from "next/link";
import { PublicShell } from "@/components/public-shell";

// Explicit design harness. No error trigger or fixture enters a product route.
export default function RecoveryHarness() {
  const [fail, setFail] = useState(false);
  if (fail) throw new Error("Controlled design recovery fixture");
  return <PublicShell className="public-recovery">
    <section>
      <span className="eyebrow">DESIGN / RECOVERY HARNESS</span>
      <h1>Recuperación de una lectura</h1>
      <p>Prueba controlada del error boundary. No consulta ni modifica datos económicos.</p>
      <div className="recovery-actions">
        <button className="button primary" onClick={() => setFail(true)}>Probar error de lectura</button>
        <Link className="button secondary" href="/design">Volver al sistema visual</Link>
      </div>
    </section>
  </PublicShell>;
}
