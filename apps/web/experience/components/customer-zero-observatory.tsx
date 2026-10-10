"use client";

/**
 * Customer Zero is the Admin's AXIGNAL: the same Observatory a subscriber uses, mounted over the Admin
 * session's own source. It adds no interface of its own; the source declares where readings come from and
 * which operations the Admin has (add an organization as attention, without checkout; observe again).
 * Staff controls and the complete technical reading stay available beneath it.
 */
import { useState } from "react";
import { useLocale } from "@/lib/locale";
import { adminSource } from "@/lib/admin-source";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { RuntimeProductProjection } from "./runtime-product";
import { SubscriberPortfolioExperience } from "./subscriber-portfolio";

export function CustomerZeroObservatory({
  projection, onProjection, staffControls, embedded,
}: {
  projection: RuntimeProjection;
  onProjection: (value: RuntimeProjection) => void;
  staffControls: React.ReactNode;
  embedded: boolean;
}) {
  const { t } = useLocale();
  const [detailsOpen, setDetailsOpen] = useState(false);
  return <div className={`obs-customer-zero${embedded ? " obs-embedded" : ""}`} data-customer-zero="true">
    <SubscriberPortfolioExperience source={adminSource}
      notice={staffControls ? <div className="obs-cz-staff">{staffControls}</div> : undefined}/>
    <details className="obs-cz-detail" open={detailsOpen} onToggle={event => setDetailsOpen(event.currentTarget.open)}>
      <summary>{t("Abrir la lectura técnica completa", "Open the complete technical reading")}</summary>
      {detailsOpen && <RuntimeProductProjection key={projection.context.id} projection={projection}
        onProjection={onProjection} embedded={embedded}/>}
    </details>
  </div>;
}
