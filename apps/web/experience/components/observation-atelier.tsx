"use client";
import { useState } from "react";
import { Pause, Play } from "lucide-react";
import { useLocale } from "@/lib/locale";

export function ObservationAtelier({ organization, onFocus }: {
  organization: string;
  onFocus: () => void;
}) {
  const { t, reducedMotion } = useLocale();
  const [paused, setPaused] = useState(false);
  return (
    <div className="family-atlas-centre observation-atelier" data-paused={paused || reducedMotion}>
      <span className="atelier-note">{t("Trabajando!!!!", "Working!!!!")}</span>
      <svg className="atelier-observer" viewBox="105 190 925 1080" role="img"
        aria-label={t("El Observador con su portátil", "The Observer with a laptop")}>
        <image href="/observer/observer-laptop.png" width="1122" height="1402" />
      </svg>
      <div className="atelier-terminal" aria-hidden="true">
        <span className="atelier-prompt">&gt;</span>
        <code>panorama.read(context);</code>
      </div>
      <div className="atelier-motion">
        <span>{t("Animación ilustrativa", "Illustrative animation")}</span>
        <button type="button" aria-pressed={paused} disabled={reducedMotion}
          aria-label={paused ? t("Reanudar animación", "Resume animation") : t("Pausar animación", "Pause animation")}
          onClick={() => setPaused(!paused)}>
          {paused ? <Play size={12} aria-hidden="true" /> : <Pause size={12} aria-hidden="true" />}
        </button>
      </div>
      <button type="button" className="atelier-focus" onClick={onFocus}>
        {organization}
      </button>
    </div>
  );
}