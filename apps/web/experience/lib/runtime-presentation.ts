import type { Locale } from "./languages";
import type { RuntimeProjection, RuntimeSignal } from "./runtime-projection";

const PUBLIC_HOMEPAGE_WHY =
  "AXIGNAL retrieved the public homepage through the governed source sensor and can trace this Xignal back to the stored observation.";
const PUBLIC_HOMEPAGE_INTERPRETATION =
  "The authorized public homepage was reachable and contained visible text when AXIGNAL observed it.";
const PUBLIC_HOMEPAGE_UNCERTAINTY_OLD =
  "This observation covers only the authorized public homepage at this observation time. Search, generative, social, reputation and other public surfaces remain UNKNOWN.";
const PUBLIC_HOMEPAGE_UNCERTAINTY =
  "This signal covers only the authorized public homepage at this observation time. Search, AI assistants, reputation and other surfaces are read by their own instruments, in their families.";
const PUBLIC_HOMEPAGE_INTERPRETATION_DETERMINISTIC =
  "The authorized public homepage was reachable and contained deterministic document text when AXIGNAL observed it. Visual visibility remains UNKNOWN when external stylesheet effects are unresolved.";

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
    es: "Esta señal cubre solo la página pública en el momento de la observación. La búsqueda, los asistentes de IA, la reputación y otras superficies se miden con sus propios instrumentos, en sus familias.",
    en: PUBLIC_HOMEPAGE_UNCERTAINTY,
    de: "Dieses Signal deckt nur die öffentliche Startseite zum Zeitpunkt der Beobachtung ab. Suche, KI-Assistenten, Reputation und andere Oberflächen werden mit eigenen Instrumenten in ihren Familien gemessen.",
    pt: "Este sinal cobre apenas a página pública no momento da observação. A pesquisa, os assistentes de IA, a reputação e outras superfícies são medidos com os seus próprios instrumentos, nas suas famílias.",
    fr: "Ce signal ne couvre que la page publique au moment de l’observation. La recherche, les assistants d’IA, la réputation et les autres surfaces sont mesurés par leurs propres instruments, dans leurs familles.",
    it: "Questo segnale copre solo la pagina pubblica al momento dell’osservazione. Ricerca, assistenti di IA, reputazione e altre superfici sono misurati con i propri strumenti, nelle loro famiglie.",
  },
  interpretationDeterministic: {
    es: "La página pública era accesible y su texto se pudo leer cuando AXIGNAL la observó. No se ha comprobado cómo cambian su aspecto los estilos externos.",
    en: PUBLIC_HOMEPAGE_INTERPRETATION_DETERMINISTIC,
    de: "Die öffentliche Startseite war erreichbar und ihr Text lesbar, als AXIGNAL sie beobachtete. Wie externe Stylesheets ihr Aussehen verändern, wurde nicht geprüft.",
    pt: "A página pública estava acessível e o seu texto pôde ser lido quando a AXIGNAL a observou. Não se verificou como os estilos externos alteram o seu aspeto.",
    fr: "La page publique était accessible et son texte lisible lorsque AXIGNAL l’a observée. L’effet des feuilles de style externes sur son apparence n’a pas été vérifié.",
    it: "La pagina pubblica era raggiungibile e il suo testo leggibile quando AXIGNAL l’ha osservata. Non è stato verificato come gli stili esterni ne modificano l’aspetto.",
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
  if(value===PUBLIC_HOMEPAGE_UNCERTAINTY || value===PUBLIC_HOMEPAGE_UNCERTAINTY_OLD) return localized.uncertainty[locale];
  if(value===PUBLIC_HOMEPAGE_INTERPRETATION_DETERMINISTIC) return localized.interpretationDeterministic[locale];
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
