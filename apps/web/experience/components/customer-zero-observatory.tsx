"use client";

/**
 * Customer Zero is the Admin's AXIGNAL: the same Observatory a subscriber uses, mounted over the Admin
 * session's own source. It adds no interface of its own; the source declares where readings come from and
 * which operations the Admin has (add an organization as attention, without checkout; observe again).
 * Inside the Admin shell the page has one sidebar: the portfolio navigation is drawn in the shell's own
 * sidebar, and the shell's top bar carries the breadcrumb and the language. Staff controls and the complete
 * technical reading stay available beneath the reading.
 */
import { useEffect, useState } from "react";
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
  projection: RuntimeProjection | null;
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
  const [technicalProjection, setTechnicalProjection] = useState<RuntimeProjection | null>(projection);
  useEffect(() => { setTechnicalProjection(projection); }, [projection]);
  // A failed or insufficient reading must never expose the previous organization as the selected one.
  const onOutputStart = () => { setTechnicalProjection(null); setDetailsOpen(false); };
  const onOutputRead = (next: RuntimeProjection) => { setTechnicalProjection(next); onProjection(next); };
  return <div className={`obs-customer-zero${embedded ? " obs-embedded" : ""}`} data-customer-zero="true">
    {embedded && toolbarHost && createPortal(<>
      <div className="navigation-controls"><span className="breadcrumb-root">Admin</span></div>
      <div className="topbar-right"><LocaleToggle/></div>
    </>, toolbarHost)}
    <SubscriberPortfolioExperience source={adminSource} onOutputStart={onOutputStart} onOutputProjection={onOutputRead} shell={embedded ? { host: navigationHost ?? null, active, onNavigate } : undefined}
      notice={staffControls ? <div className="obs-cz-staff">{staffControls}</div> : undefined}/>
    {technicalProjection && <details className="obs-cz-detail" open={detailsOpen} onToggle={event => setDetailsOpen(event.currentTarget.open)}>
      <summary>{t("Abrir la lectura técnica completa", "Open the complete technical reading")}</summary>
      {detailsOpen && <RuntimeProductProjection key={technicalProjection.context.id} projection={technicalProjection}
        onProjection={onProjection} embedded={embedded}/>}
    </details>}
  </div>;
}
