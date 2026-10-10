"use client";

/**
 * Public, fictional example of the actual subscriber Observatory.
 * Reuses the production SummaryView + InsightBody; no subscriber authority,
 * runtime request, fabricated URL, or browser session is involved.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Menu, X } from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  EXAMPLE_MOMENTS, exampleInsights, exampleOrganization, type ExampleMoment,
} from "@/lib/landing-observatory";
import { laneCopy } from "@/lib/observatory";
import { InsightBody, SummaryView } from "./observatory";
import { LocaleToggle, useFocusTrap } from "./ui";
import "./observatory.css";
import "./example-observatory.css";

type DemoView = "summary" | "evolution" | "evidence";
const latest: ExampleMoment = "2026-10-03";

export function ExampleObservatory() {
  const { t, copy, locale } = useLocale();
  const params = useSearchParams();
  const [moment, setMoment] = useState<ExampleMoment>(
    EXAMPLE_MOMENTS.find(value => value === params.get("asOf")) ?? latest,
  );
  const [view, setView] = useState<DemoView>("summary");
  const [openId, setOpenId] = useState<string | null>(null);
  const [mobileRail, setMobileRail] = useState(false);
  const sheetRef = useRef<HTMLDivElement>(null);
  useFocusTrap(mobileRail, sheetRef, () => setMobileRail(false));
  const organization = exampleOrganization();
  const name = organization.name;
  const insights = useMemo(() => exampleInsights(moment, copy), [moment, copy]);
  const selected = insights.find(insight => insight.id === openId) ?? null;

  useEffect(() => {
    const initial = params.get("signal");
    if (initial && exampleInsights(moment, copy).some(i => i.id === initial))
      setOpenId(initial);
  }, [params, moment, copy]);

  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setOpenId(null); setMobileRail(false); }
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, []);

  function selectMoment(next: ExampleMoment) {
    setMoment(next);
    setOpenId(null);
    const url = new URL(window.location.href);
    if (next === latest) url.searchParams.delete("asOf");
    else url.searchParams.set("asOf", next);
    url.searchParams.delete("signal");
    url.searchParams.delete("depth");
    window.history.replaceState(null, "", url);
  }

  const rail = <nav className="obs-rail" aria-label={t("Ejemplo de cartera", "Example portfolio")}>
    <Link className="obs-rail-brand" href="/" aria-label="AXIGNAL"><img src="/brand/logo-light.svg" alt="AXIGNAL" width={124} height={36}/></Link>
    <div className="obs-rail-head"><h2>{t("Organizaciones", "Organizations")}</h2><span className="obs-rail-count">1</span></div>
    <ul className="obs-orgs"><li><button className="obs-org" aria-current="page" onClick={() => { setView("summary"); setOpenId(null); setMobileRail(false); }}>
      <span className="obs-lens obs-lens-ready" aria-hidden="true"><svg viewBox="0 0 24 24" width="22" height="22"><circle className="obs-lens-ring" cx="12" cy="10.5" r="7.5"/><path className="obs-lens-stem" d="M12 18v3.5"/></svg></span>
      <span className="obs-org-text"><span className="obs-org-name">{name}</span><span className="obs-org-sub">{t("Organización ficticia", "Fictional organization")}</span></span>
    </button></li></ul>
    <div className="obs-rail-foot"><Link className="obs-rail-action" href="/signup">{t("Observar mi organización", "Observe my organization")}<ArrowRight size={15} aria-hidden="true"/></Link><div className="obs-rail-locale"><LocaleToggle/></div></div>
  </nav>;

  return <div className="obs obs-example" data-product-surface="living-observatory" data-example="fictional">
    <a className="obs-skip" href="#obs-main">{t("Ir al contenido", "Skip to content")}</a>
    <div className="obs-rail-desktop">{rail}</div>
    <header className="obs-mobilebar">
      <button className="obs-icon obs-mobilebar-menu" aria-expanded={mobileRail} aria-label={t("Abrir la cartera", "Open portfolio")} onClick={() => setMobileRail(true)}><Menu size={20}/></button>
      <span className="obs-mobilebar-title">{name}</span>
      <Link href="/" aria-label="AXIGNAL"><img src="/brand/isotope.svg" alt="" width={26} height={26}/></Link>
    </header>
    {mobileRail && <div className="obs-sheet-backdrop" onClick={() => setMobileRail(false)}><div ref={sheetRef} className="obs-sheet" role="dialog" aria-modal="true" aria-label={t("Ejemplo de cartera", "Example portfolio")} onClick={event => event.stopPropagation()}><button className="obs-icon obs-sheet-close" onClick={() => setMobileRail(false)} aria-label={t("Cerrar", "Close")}><X size={20}/></button>{rail}</div></div>}
    <main className="obs-main" id="obs-main">
      <div className={`obs-org-view${selected ? " obs-has-depth" : ""}`}>
        <div className="obs-org-main">
          <div className="obs-example-notice" role="note">
            <strong>{t("Ejemplo guiado · datos ficticios", "Guided example · fictional data")}</strong>
            <span>{t("Así se lee el Observatorio real. Esta organización y sus hallazgos son ilustrativos; no se está realizando ninguna investigación.", "This is how the real Observatory is read. This organization and its findings are illustrative; no investigation is taking place.")}</span>
            <Link href="/signup">{t("Empezar con datos reales", "Start with real data")}<ArrowRight size={14} aria-hidden="true"/></Link>
          </div>
          <header className="obs-org-head">
            <div className="obs-org-title">
              <span className="obs-focus-lens" aria-hidden="true"><img src="/brand/isotope.svg" alt="" width={34} height={34}/></span>
              <div><h1>{name}</h1><p className="obs-org-meta"><span className="obs-chip">{t("Identidad ficticia", "Fictional identity")}</span><span>{t("Momento del ejemplo", "Example as of")} <time dateTime={moment}>{new Intl.DateTimeFormat(locale, {year:"numeric",month:"short",day:"numeric",timeZone:"UTC"}).format(new Date(moment+"T12:00:00Z"))}</time></span></p></div>
            </div>
            <div className="obs-org-actions"><Link className="obs-button" href="/signup">{t("Empezar", "Get started")}<ArrowRight size={16} aria-hidden="true"/></Link></div>
          </header>
          <div className="obs-tabs" role="tablist" aria-label={t("Profundidad", "Depth")}>
            {([["summary",t("Resumen","Summary")],["evolution",t("Evolución","Evolution")],["evidence",t("Evidencias","Evidence")]] as const).map(([id,label]) => <button key={id} role="tab" id={`tab-${id}`} aria-selected={view===id} aria-controls={`panel-${id}`} tabIndex={view===id?0:-1} onClick={() => {setView(id);setOpenId(null);}}>{label}</button>)}
          </div>
          <div className="obs-panel" role="tabpanel" id={`panel-${view}`} aria-labelledby={`tab-${view}`}>
            {view==="summary" && <SummaryView reading={{projection:null,firstObservation:null}} name={name} insights={insights} lit={new Set()} openId={openId} onOpen={insight=>setOpenId(insight.id)} onSeenAll={()=>{}} item={{observation:undefined}} exampleLead={copy(organization.does)}/>}
            {view==="evolution" && <section className="obs-example-history"><h2>{t("Una historia que conserva el tiempo", "A history that preserves time")}</h2><p>{t("Elige cuándo mirar. Solo aparecen los hallazgos disponibles en ese momento del ejemplo.", "Choose a moment. Only findings available at that moment in the example are shown.")}</p><div className="obs-example-moments">{EXAMPLE_MOMENTS.map(date=><button key={date} type="button" aria-pressed={date===moment} onClick={()=>selectMoment(date)}>{date}</button>)}</div><p>{insights.length} {t("hallazgos ilustrativos visibles", "illustrative findings visible")}</p></section>}
            {view==="evidence" && <section className="obs-example-evidence"><h2>{t("Evidencia del ejemplo", "Example evidence")}</h2><p>{t("Las fuentes aquí son ilustrativas y no enlaces a investigaciones reales. En tu cuenta, las fuentes admitidas muestran su procedencia y fecha.", "Sources here are illustrative, not links to real research. In your account, admitted sources show their provenance and date.")}</p><ul>{insights.flatMap(i=>i.sources.map((source,index)=><li key={i.id+index}><strong>{i.headline}</strong> · {source.label} · {source.observedAt??t("Fecha desconocida","Date unknown")}</li>))}</ul></section>}
          </div>
          <div className="obs-example-footer"><Link href="/">{<ArrowLeft size={15} aria-hidden="true"/>}{t("Volver a AXIGNAL", "Back to AXIGNAL")}</Link><Link href="/signup">{t("Empieza con tu organización", "Start with your organization")}<ArrowRight size={15} aria-hidden="true"/></Link></div>
        </div>
        {selected && <aside id="obs-depth" className={`obs-depth obs-lane-${selected.lane}`} aria-label={t("Profundizar", "Go deeper")}>
          <div className="obs-depth-bar"><button className="obs-icon" aria-label={t("Cerrar", "Close")} onClick={()=>setOpenId(null)}><X size={18}/></button><span>{laneCopy(selected.lane,t).title}</span></div>
          <InsightBody insight={selected} onEvidence={()=>{setOpenId(null);setView("evidence");}}/>
          <p className="obs-example-depth-note">{t("El ejemplo no consulta a AXENT ni afirma haber observado una empresa real.", "The example does not contact AXENT or claim to have observed a real company.")}</p>
        </aside>}
      </div>
    </main>
  </div>;
}
