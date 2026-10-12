"use client";
import { useState } from "react";
import { useLocale } from "@/lib/locale";
import { placeLabel } from "./first-observation";
import type { FirstObservation } from "@/lib/subscriber-contracts";

/** EU member states, where the adopted public-demand sources publish. */
const EU = ["AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"].map(code => `EU/${code}`);
const MAX = 5;

/**
 * Where the subscriber wants public tenders looked for. It directs attention only: it does
 * not change what AXIGNAL knows about the organization, and every match stays potential.
 */
export function DemandMarkets({ focusId, observation, canAct, onSaved }: {
  focusId: string; observation: FirstObservation; canAct: boolean; onSaved: () => void;
}) {
  const { t, locale } = useLocale();
  const observed = (observation.attentionScopes ?? []).map(s => s.jurisdiction).filter(j => /^EU\/[A-Z]{2}/.test(j)).map(j => j.slice(0, 5));
  const directed = observation.demandMarkets?.directed ?? [];
  const [open, setOpen] = useState(false);
  const [chosen, setChosen] = useState<string[]>(directed);
  const [state, setState] = useState<"idle" | "saving" | "error">("idle");
  const where = [...new Set([...observed, ...directed])];
  const toggle = (code: string) => setChosen(previous => previous.includes(code) ? previous.filter(c => c !== code) : previous.length < MAX ? [...previous, code] : previous);
  async function save() {
    setState("saving");
    try {
      const response = await fetch(`/api/subscriber/organizations/${encodeURIComponent(focusId)}/demand-markets`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ markets: chosen }),
      });
      if (!response.ok) throw new Error("SAVE_FAILED");
      setState("idle"); setOpen(false); onSaved();
    } catch { setState("error"); }
  }
  return <section className="obs-demand-markets" aria-labelledby={`demand-markets-${focusId}`}>
    <p id={`demand-markets-${focusId}`}>
      <strong>{t("Licitaciones públicas", "Public tenders")}:</strong>{" "}
      {where.length
        ? t("se buscan en {places}.", "looked for in {places}.").replace("{places}", where.map(w => placeLabel(w, locale)).join(", "))
        : t("todavía no sabemos dónde buscarlas. Elige uno o varios países.", "we do not know yet where to look. Choose one or more countries.")}
      {observation.demand?.preparing && <> {t("Preparando las licitaciones de los países elegidos; aparecerán en la próxima lectura.", "Preparing tenders for the chosen countries; they will appear in the next reading.")}</>}
      {" "}<button className="obs-link" disabled={!canAct} aria-expanded={open} onClick={() => { setChosen(directed); setOpen(v => !v); }}>{open ? t("Cerrar", "Close") : t("Elegir países", "Choose countries")}</button>
    </p>
    {open && <div className="obs-demand-markets-form">
      <p>{t("Hasta {max} países. Solo orienta dónde buscar: no cambia lo que AXIGNAL sabe de la organización.", "Up to {max} countries. It only directs where to look: it does not change what AXIGNAL knows about the organization.").replace("{max}", String(MAX))}</p>
      <fieldset><legend className="sr-only">{t("Países donde buscar licitaciones", "Countries to look for tenders in")}</legend>
        {EU.map(code => <label key={code}><input type="checkbox" checked={chosen.includes(code)} disabled={!chosen.includes(code) && chosen.length >= MAX} onChange={() => toggle(code)}/>{placeLabel(code, locale)}</label>)}
      </fieldset>
      <button className="obs-button obs-primary" disabled={state === "saving" || !canAct} onClick={() => void save()}>{state === "saving" ? t("Guardando…", "Saving…") : t("Guardar países", "Save countries")}</button>
      {state === "error" && <p role="alert">{t("No se pudieron guardar los países. Inténtalo de nuevo.", "The countries could not be saved. Try again.")}</p>}
    </div>}
  </section>;
}
