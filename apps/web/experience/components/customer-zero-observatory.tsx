"use client";

/**
 * Customer Zero is the Admin's AXIGNAL: the same Observatory a subscriber uses, mounted over the Admin
 * session's own source. It adds no interface of its own; the source declares where readings come from and
 * which operations the Admin has (add an organization as attention, without checkout; observe again).
 * Inside the Admin shell the page has one sidebar: the portfolio navigation is drawn in the shell's own
 * sidebar, and the shell's top bar carries the breadcrumb and the language. Staff controls and the complete
 * technical reading stay available beneath the reading.
 */
import { useState } from "react";
import { createPortal } from "react-dom";
import { useLocale } from "@/lib/locale";
import { adminSource } from "@/lib/admin-source";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { RuntimeProductProjection } from "./runtime-product";
import { SubscriberPortfolioExperience } from "./subscriber-portfolio";
import { LocaleToggle } from "./ui";

export function CustomerZeroObservatory({
  projection, onProjection, staffControls, embedded, navigationHost, toolbarHost, active = true, onNavigate,
}: {
  projection: RuntimeProjection;
  onProjection: (value: RuntimeProjection) => void;
  staffControls: React.ReactNode;
  embedded: boolean;
  navigationHost?: HTMLElement | null;
  toolbarHost?: HTMLElement | null;
  active?: boolean;
  onNavigate?: () => void;
}) {
  const { t } = useLocale();
  const [detailsOpen, setDetailsOpen] = useState(false);
  return <div className={`obs-customer-zero${embedded ? " obs-embedded" : ""}`} data-customer-zero="true">
    {embedded && toolbarHost && createPortal(<>
      <div className="navigation-controls"><span className="breadcrumb-root">AXIGNAL / Customer Zero</span></div>
      <div className="topbar-right"><LocaleToggle/></div>
    </>, toolbarHost)}
    <SubscriberPortfolioExperience source={adminSource} shell={embedded ? { host: navigationHost ?? null, active, onNavigate } : undefined}
      notice={staffControls ? <div className="obs-cz-staff">{staffControls}</div> : undefined}/>
    <details className="obs-cz-detail" open={detailsOpen} onToggle={event => setDetailsOpen(event.currentTarget.open)}>
      <summary>{t("Abrir la lectura técnica completa", "Open the complete technical reading")}</summary>
      {detailsOpen && <RuntimeProductProjection key={projection.context.id} projection={projection}
        onProjection={onProjection} embedded={embedded}/>}
    </details>
  </div>;
}
