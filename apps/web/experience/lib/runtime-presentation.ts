import type { Locale } from "./languages";
import type { RuntimeProjection, RuntimeSignal } from "./runtime-projection";

const PUBLIC_HOMEPAGE_WHY =
  "AXIGNAL retrieved the public homepage through the governed source sensor and can trace this Xignal back to the stored observation.";
const PUBLIC_HOMEPAGE_INTERPRETATION =
  "The authorized public homepage was reachable and contained visible text when AXIGNAL observed it.";
const PUBLIC_HOMEPAGE_UNCERTAINTY =
  "This observation covers only the authorized public homepage at this observation time. Search, generative, social, reputation and other public surfaces remain UNKNOWN.";

const localized = {
  sourceObserved: {
    es: "Texto observado en la fuente",
    en: "Source-observed text",
    de: "In der Quelle beobachteter Text",
    pt: "Texto observado na fonte",
    fr: "Texte observé dans la source",
    it: "Testo osservato nella fonte",
  },
  why: {
    es: "AXIGNAL recuperó la página pública mediante el sensor de fuentes gobernado y puede rastrear esta señal hasta la observación almacenada.",
    en: PUBLIC_HOMEPAGE_WHY,
    de: "AXIGNAL hat die öffentliche Startseite über den gesteuerten Quellensensor abgerufen und kann dieses Xignal bis zur gespeicherten Beobachtung zurückverfolgen.",
    pt: "AXIGNAL recuperou a página pública através do sensor de fontes governado e consegue rastrear este Xignal até à observação armazenada.",
    fr: "AXIGNAL a récupéré la page publique via le capteur de sources gouverné et peut retracer ce Xignal jusqu’à l’observation enregistrée.",
    it: "AXIGNAL ha recuperato la pagina pubblica tramite il sensore di fonti governato e può ricondurre questo Xignal all’osservazione memorizzata.",
  },
  interpretation: {
    es: "La página pública autorizada era accesible y contenía texto visible cuando AXIGNAL la observó.",
    en: PUBLIC_HOMEPAGE_INTERPRETATION,
    de: "Die autorisierte öffentliche Startseite war erreichbar und enthielt sichtbaren Text, als AXIGNAL sie beobachtete.",
    pt: "A página pública autorizada estava acessível e continha texto visível quando a AXIGNAL a observou.",
    fr: "La page publique autorisée était accessible et contenait du texte visible lorsque AXIGNAL l’a observée.",
    it: "La pagina pubblica autorizzata era raggiungibile e conteneva testo visibile quando AXIGNAL l’ha osservata.",
  },
  uncertainty: {
    es: "Esta observación cubre únicamente la página pública autorizada en este momento de observación. Búsqueda, presencia generativa, redes sociales, reputación y otras superficies públicas siguen siendo DESCONOCIDAS.",
    en: PUBLIC_HOMEPAGE_UNCERTAINTY,
    de: "Diese Beobachtung deckt zu diesem Zeitpunkt nur die autorisierte öffentliche Startseite ab. Suche, generative Präsenz, soziale Netzwerke, Reputation und andere öffentliche Oberflächen bleiben UNBEKANNT.",
    pt: "Esta observação cobre apenas a página pública autorizada neste momento. Pesquisa, presença generativa, redes sociais, reputação e outras superfícies públicas permanecem DESCONHECIDAS.",
    fr: "Cette observation ne couvre que la page publique autorisée à cet instant. Recherche, présence générative, réseaux sociaux, réputation et autres surfaces publiques restent INCONNUES.",
    it: "Questa osservazione copre solo la pagina pubblica autorizzata in questo momento. Ricerca, presenza generativa, social, reputazione e altre superfici pubbliche restano SCONOSCIUTE.",
  },
} satisfies Record<string, Record<Locale, string>>;

const codeLabels: Record<string, Record<Locale, string>> = {
  OFFICIAL_WEB: { es:"Web oficial", en:"Official web", de:"Offizielle Website", pt:"Web oficial", fr:"Web officiel", it:"Sito web ufficiale" },
  CURRENT: { es:"Actual", en:"Current", de:"Aktuell", pt:"Atual", fr:"Actuel", it:"Attuale" },
  STALE: { es:"Desactualizado", en:"Stale", de:"Veraltet", pt:"Desatualizado", fr:"Périmé", it:"Obsoleto" },
  HISTORICAL: { es:"Histórico", en:"Historical", de:"Historisch", pt:"Histórico", fr:"Historique", it:"Storico" },
  UNKNOWN: { es:"Desconocido", en:"Unknown", de:"Unbekannt", pt:"Desconhecido", fr:"Inconnu", it:"Sconosciuto" },
  OBSERVED: { es:"Observado", en:"Observed", de:"Beobachtet", pt:"Observado", fr:"Observé", it:"Osservato" },
  POTENTIAL: { es:"Potencial", en:"Potential", de:"Potenziell", pt:"Potencial", fr:"Potentiel", it:"Potenziale" },
  AVAILABLE: { es:"Disponible", en:"Available", de:"Verfügbar", pt:"Disponível", fr:"Disponible", it:"Disponibile" },
};

const titleTemplates: Record<Locale,(name:string)=>string> = {
  es: (name)=>`La página pública de ${name} es observable desde fuera`,
  en: (name)=>`${name}'s public homepage is observable from the outside`,
  de: (name)=>`Die öffentliche Startseite von ${name} ist von außen beobachtbar`,
  pt: (name)=>`A página pública de ${name} é observável a partir do exterior`,
  fr: (name)=>`La page d’accueil publique de ${name} est observable depuis l’extérieur`,
  it: (name)=>`La pagina pubblica di ${name} è osservabile dall’esterno`,
};

export const presentSourceObservedLabel=(locale:Locale)=>localized.sourceObserved[locale];

export function presentRuntimeCode(value:string, locale:Locale):string {
  return codeLabels[value]?.[locale] ?? value;
}

export function presentRuntimeText(value:string, organizationName:string, locale:Locale):string {
  const canonicalTitle=titleTemplates.en(organizationName);
  if(value===canonicalTitle) return titleTemplates[locale](organizationName);
  if(value===PUBLIC_HOMEPAGE_WHY) return localized.why[locale];
  if(value===PUBLIC_HOMEPAGE_INTERPRETATION) return localized.interpretation[locale];
  if(value===PUBLIC_HOMEPAGE_UNCERTAINTY) return localized.uncertainty[locale];
  return value;
}

export function presentSignal(signal:RuntimeSignal, organizationName:string, locale:Locale) {
  return {
    title: presentRuntimeText(signal.title,organizationName,locale),
    whyAttention: presentRuntimeText(signal.whyAttention,organizationName,locale),
    interpretation: presentRuntimeText(signal.interpretation,organizationName,locale),
    currentness: presentRuntimeCode(signal.currentness,locale),
  };
}

export function presentEvidenceStepLabel(
  step: RuntimeSignal["evidenceNarrative"]["steps"][number],
  organizationName:string,
  locale:Locale,
):string {
  if(step.kind==="OBSERVATION" || step.kind==="CLAIM") return step.label;
  if(step.kind==="SOURCE") return presentRuntimeCode(step.label,locale);
  return presentRuntimeText(step.label,organizationName,locale);
}

export function presentRuntimePassage(value:string, projection:RuntimeProjection, locale:Locale):string {
  for(const signal of projection.nodes){
    if(signal.evidenceNarrative.steps.some((step)=>
      (step.kind==="OBSERVATION" || step.kind==="CLAIM") && step.label===value
    )) return value;
    if(signal.evidenceNarrative.steps.some((step)=>step.kind==="SOURCE" && step.label===value))
      return presentRuntimeCode(value,locale);
  }
  return presentRuntimeText(value,projection.organization.name,locale);
}
