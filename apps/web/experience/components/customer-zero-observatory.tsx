"use client";

/**
 * Customer Zero uses the same read-only Observatory vocabulary as a subscriber.
 * It receives ONLY the Admin-authorized runtime projection. Staff actions retain
 * their existing server-side authority and the detailed legacy view is preserved.
 */
import { useMemo, useState } from "react";
import { X } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { insightsFor, laneCopy, type Insight } from "@/lib/observatory";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { InsightBody, SummaryView } from "./observatory";
import { RuntimeProductProjection } from "./runtime-product";

export function CustomerZeroObservatory({
  projection, onProjection, staffControls, embedded,
}: {
  projection: RuntimeProjection;
  onProjection: (value: RuntimeProjection) => void;
  staffControls: React.ReactNode;
  embedded: boolean;
}) {
  const { t, locale } = useLocale();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const reading = useMemo(() => ({ projection, firstObservation: null }), [projection]);
  const insights = useMemo(() => insightsFor(reading, t, locale), [reading, t, locale]);
  const selected = insights.find(item => item.id === selectedId) ?? null;

  return <div className={`obs obs-customer-zero${embedded ? " obs-embedded" : ""}`} data-product-surface="living-observatory" data-customer-zero="true">
    <main className="obs-main" id="customer-zero-main">
      <div className={`obs-org-view${selected ? " obs-has-depth" : ""}`}>
        <div className="obs-org-main">
          <header className="obs-org-head">
            <div className="obs-org-title">
              <span className="obs-focus-lens" aria-hidden="true"><img src="/brand/isotope.svg" alt="" width={34} height={34}/></span>
              <div><h1>{projection.organization.name}</h1>
                <p className="obs-org-meta"><span className="obs-chip">Customer Zero</span><span>{t("Observación interna con evidencia gobernada", "Internal observation with governed evidence")}</span></p>
              </div>
            </div>
          </header>
          <div className="obs-cz-staff">{staffControls}</div>
          <div className="obs-panel">
            <SummaryView reading={reading} name={projection.organization.name} insights={insights} lit={new Set()} openId={selectedId}
              onOpen={item => setSelectedId(item.id)} onSeenAll={()=>{}} item={{observation:undefined}}/>
          </div>
          <details className="obs-cz-detail" open={detailsOpen} onToggle={event=>setDetailsOpen(event.currentTarget.open)}>
            <summary>{t("Abrir la lectura técnica completa", "Open the complete technical reading")}</summary>
            {detailsOpen && <RuntimeProductProjection key={projection.context.id} projection={projection}
              onProjection={onProjection} embedded={embedded}/>}
          </details>
        </div>
        {selected && <aside id="obs-depth" className={`obs-depth obs-lane-${selected.lane}`} aria-label={t("Profundizar", "Go deeper")}>
          <div className="obs-depth-bar"><button className="obs-icon" aria-label={t("Cerrar", "Close")} onClick={()=>setSelectedId(null)}><X size={18}/></button><span>{laneCopy(selected.lane,t).title}</span></div>
          <InsightBody insight={selected}/>
        </aside>}
      </div>
    </main>
  </div>;
}
