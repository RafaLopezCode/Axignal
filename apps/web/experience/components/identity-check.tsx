"use client";

/**
 * Verify identity: the person picks their organization among current LEI holders the official
 * registry suggests. AXIGNAL never picks: the chosen LEI is read exactly by the registry, and the
 * website the person named stays theirs (never recorded as official by this choice).
 */
import { useState } from "react";
import { BadgeCheck, Search } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { identitySearchFrom, type IdentityCandidate } from "@/lib/identity";

export function IdentityCheck({ name, website, busy, onChoose }: {
  name: string;
  website: string | null;
  busy: boolean;
  onChoose: (locator: string) => Promise<void>;
}) {
  const { t } = useLocale();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(() => identitySearchFrom(name, website));
  const [state, setState] = useState<"idle" | "searching" | "done" | "unavailable">("idle");
  const [candidates, setCandidates] = useState<IdentityCandidate[]>([]);
  const [chosen, setChosen] = useState<string | null>(null);

  async function search(event: React.FormEvent) {
    event.preventDefault();
    setState("searching"); setChosen(null);
    try {
      const country = website?.match(/\.([a-z]{2})$/i)?.[1]?.toUpperCase();
      const response = await fetch("/api/subscriber/identity/candidates", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), ...(country && country !== "EU" ? { country } : {}) }),
      });
      const result = await response.json() as { state?: string; candidates?: IdentityCandidate[] };
      if (!response.ok || result.state !== "success") { setState("unavailable"); return; }
      setCandidates(result.candidates ?? []); setState("done");
    } catch { setState("unavailable"); }
  }

  if (!open) return <button type="button" className="obs-link obs-identity-open" onClick={() => setOpen(true)}>
    <BadgeCheck size={16} aria-hidden="true"/>{t("Verificar su identidad en el registro oficial", "Verify its identity in the official registry")}
  </button>;

  return <section className="obs-inline-form obs-identity" aria-labelledby="identity-title">
    <h2 id="identity-title">{t("Verificar su identidad", "Verify its identity")}</h2>
    <p>{t("Busca la entidad en el registro mundial de identificadores legales (GLEIF) y señala cuál es. AXIGNAL no elige por ti: la identidad se verifica con el código LEI que señales.",
      "Find the entity in the global legal identifier registry (GLEIF) and point out which one it is. AXIGNAL does not choose for you: identity is verified with the LEI code you point out.")}</p>
    <form className="obs-identity-search" onSubmit={event => void search(event)}>
      <label htmlFor="identity-query">{t("Nombre o razón social", "Name or legal name")}</label>
      <div className="obs-add-row">
        <input id="identity-query" value={query} onChange={event => setQuery(event.target.value)} minLength={2} maxLength={120} required disabled={busy || state === "searching"}/>
        <button className="obs-button" disabled={busy || state === "searching" || query.trim().length < 2}><Search size={16} aria-hidden="true"/>{t("Buscar", "Search")}</button>
      </div>
    </form>
    {state === "searching" && <p role="status">{t("Consultando el registro oficial…", "Querying the official registry…")}</p>}
    {state === "unavailable" && <p role="alert">{t("El registro oficial no responde ahora. Vuelve a intentarlo en un momento.", "The official registry is not answering right now. Try again in a moment.")}</p>}
    {state === "done" && !candidates.length && <p role="status">{t("El registro no tiene ninguna entidad activa con ese nombre. Prueba con su razón social; si no tiene código LEI, seguimos observando su web igualmente.",
      "The registry has no active entity with that name. Try its legal name; if it has no LEI code, we keep observing its website all the same.")}</p>}
    {state === "done" && candidates.length > 0 && <fieldset className="obs-identity-list">
      <legend>{t("¿Cuál es?", "Which one is it?")}</legend>
      {candidates.map(candidate => <label key={candidate.lei} className="obs-identity-option">
        <input type="radio" name="identity-choice" value={candidate.lei} checked={chosen === candidate.lei} onChange={() => setChosen(candidate.lei)}/>
        <span><strong>{candidate.legalName}</strong><small>{[candidate.country, candidate.city].filter(Boolean).join(" · ")} · LEI {candidate.lei}</small></span>
      </label>)}
    </fieldset>}
    <div className="obs-form-actions">
      {state === "done" && candidates.length > 0 && <button type="button" className="obs-button obs-primary" disabled={busy || !chosen}
        onClick={() => { if (chosen) void onChoose(website ? `${website} ${chosen}` : chosen); }}>{t("Es esta", "This is it")}</button>}
      <button type="button" className="obs-link" onClick={() => setOpen(false)}>{t("Cancelar", "Cancel")}</button>
    </div>
  </section>;
}
