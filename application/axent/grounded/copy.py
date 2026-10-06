"""The few sentences AXENT composes without a model, in the six product languages."""

from __future__ import annotations

from application.observation_runtime.families import ObservationFamily

LOCALES = ("es", "en", "fr", "de", "it", "pt")

_FAMILY: dict[ObservationFamily, tuple[str, str, str, str, str, str]] = {
    ObservationFamily.PRESENCE: (
        "presencia",
        "presence",
        "présence",
        "Präsenz",
        "presenza",
        "presença",
    ),
    ObservationFamily.REPUTATION: (
        "reputación",
        "reputation",
        "réputation",
        "Reputation",
        "reputazione",
        "reputação",
    ),
    ObservationFamily.VALUE: ("oferta", "offer", "offre", "Angebot", "offerta", "oferta"),
    ObservationFamily.MARKETS: ("mercados", "markets", "marchés", "Märkte", "mercati", "mercados"),
    ObservationFamily.RELATIONSHIPS: (
        "relaciones",
        "relationships",
        "relations",
        "Beziehungen",
        "relazioni",
        "relações",
    ),
    ObservationFamily.DEMAND: ("demanda", "demand", "demande", "Nachfrage", "domanda", "procura"),
    ObservationFamily.ACTIVITY: (
        "actividad",
        "activity",
        "activité",
        "Aktivität",
        "attività",
        "atividade",
    ),
    ObservationFamily.ECONOMICS: (
        "economía",
        "economics",
        "économie",
        "Wirtschaft",
        "economia",
        "economia",
    ),
    ObservationFamily.ORGANIZATION: (
        "organización",
        "organization",
        "organisation",
        "Organisation",
        "organizzazione",
        "organização",
    ),
    ObservationFamily.CONTEXT: (
        "contexto",
        "context",
        "contexte",
        "Kontext",
        "contesto",
        "contexto",
    ),
}

_TEXT: dict[str, tuple[str, str, str, str, str, str]] = {
    "abstain": (
        "No tengo evidencia suficiente en AXIGNAL para responder esto sobre {org}.",
        "I do not have enough evidence in AXIGNAL to answer this about {org}.",
        "Je n'ai pas assez de preuves dans AXIGNAL pour répondre à cela sur {org}.",
        "Ich habe in AXIGNAL nicht genug Belege, um das zu {org} zu beantworten.",
        "Non ho prove sufficienti in AXIGNAL per rispondere su {org}.",
        "Não tenho evidência suficiente no AXIGNAL para responder isto sobre {org}.",
    ),
    "abstain_subject": (
        "La evidencia autorizada de {org} no menciona {subject}; no puedo afirmar nada sobre ello.",
        "The authorized evidence for {org} does not mention {subject}; I cannot claim anything about it.",
        "Les preuves autorisées de {org} ne mentionnent pas {subject} ; je ne peux rien affirmer à ce sujet.",
        "Die freigegebenen Belege zu {org} erwähnen {subject} nicht; dazu kann ich nichts sagen.",
        "Le prove autorizzate di {org} non menzionano {subject}; non posso affermare nulla al riguardo.",
        "A evidência autorizada de {org} não menciona {subject}; não posso afirmar nada sobre isso.",
    ),
    "research": (
        "He pedido a AXIGNAL que observe {scope}; la respuesta no se da por supuesta mientras tanto.",
        "I asked AXIGNAL to observe {scope}; nothing is assumed in the meantime.",
        "J'ai demandé à AXIGNAL d'observer {scope} ; rien n'est supposé entre-temps.",
        "Ich habe AXIGNAL gebeten, {scope} zu beobachten; bis dahin wird nichts angenommen.",
        "Ho chiesto ad AXIGNAL di osservare {scope}; nel frattempo nulla è dato per scontato.",
        "Pedi ao AXIGNAL que observe {scope}; entretanto nada é assumido.",
    ),
    "count": (
        "En la lectura actual AXIGNAL tiene {n} oportunidades potenciales{where}. Son posibles, no confirmadas.",
        "In the current reading AXIGNAL has {n} potential opportunities{where}. They are possible, not confirmed.",
        "Dans la lecture actuelle, AXIGNAL a {n} opportunités potentielles{where}. Elles sont possibles, non confirmées.",
        "In der aktuellen Lesart hat AXIGNAL {n} potenzielle Chancen{where}. Sie sind möglich, nicht bestätigt.",
        "Nella lettura attuale AXIGNAL ha {n} opportunità potenziali{where}. Sono possibili, non confermate.",
        "Na leitura atual o AXIGNAL tem {n} oportunidades potenciais{where}. São possíveis, não confirmadas.",
    ),
    "count_items": (
        "En la lectura actual hay {n} elementos de evidencia sobre {scope}.",
        "The current reading holds {n} pieces of evidence about {scope}.",
        "La lecture actuelle contient {n} éléments de preuve sur {scope}.",
        "Die aktuelle Lesart enthält {n} Belege zu {scope}.",
        "La lettura attuale contiene {n} elementi di prova su {scope}.",
        "A leitura atual contém {n} elementos de evidência sobre {scope}.",
    ),
    "where": (" en {geo}", " in {geo}", " en {geo}", " in {geo}", " in {geo}", " em {geo}"),
    "unknowns": (
        "Esto es lo que AXIGNAL todavía no sabe o no puede sostener:",
        "This is what AXIGNAL does not know yet or cannot support:",
        "Voici ce qu'AXIGNAL ne sait pas encore ou ne peut pas étayer :",
        "Das weiß AXIGNAL noch nicht oder kann es nicht belegen:",
        "Ecco cosa AXIGNAL non sa ancora o non può sostenere:",
        "Isto é o que o AXIGNAL ainda não sabe ou não consegue sustentar:",
    ),
    "sources": (
        "Esta lectura se apoya en estas observaciones:",
        "This reading rests on these observations:",
        "Cette lecture repose sur ces observations :",
        "Diese Lesart stützt sich auf diese Beobachtungen:",
        "Questa lettura si basa su queste osservazioni:",
        "Esta leitura baseia-se nestas observações:",
    ),
    "observed": (
        "AXIGNAL observó: {label} ({when}).",
        "AXIGNAL observed: {label} ({when}).",
        "AXIGNAL a observé : {label} ({when}).",
        "AXIGNAL hat beobachtet: {label} ({when}).",
        "AXIGNAL ha osservato: {label} ({when}).",
        "O AXIGNAL observou: {label} ({when}).",
    ),
    "extractive": (
        "No he podido razonar esta pregunta ahora; esta es la evidencia autorizada más relevante.",
        "I could not reason over this question now; this is the most relevant authorized evidence.",
        "Je n'ai pas pu raisonner sur cette question ; voici les preuves autorisées les plus pertinentes.",
        "Ich konnte diese Frage gerade nicht auswerten; das sind die relevantesten freigegebenen Belege.",
        "Non ho potuto ragionare ora su questa domanda; ecco le prove autorizzate più rilevanti.",
        "Não consegui raciocinar sobre esta pergunta agora; esta é a evidência autorizada mais relevante.",
    ),
    "stale": (
        "La evidencia disponible ya no es actual.",
        "The available evidence is no longer current.",
        "Les preuves disponibles ne sont plus actuelles.",
        "Die verfügbaren Belege sind nicht mehr aktuell.",
        "Le prove disponibili non sono più attuali.",
        "A evidência disponível já não é atual.",
    ),
    "gap_representation": (
        "No hay todavía una medición de visibilidad en buscadores o respuestas generativas.",
        "There is no measurement of search or generative visibility yet.",
        "Il n'existe pas encore de mesure de visibilité dans les moteurs ou les réponses génératives.",
        "Es gibt noch keine Messung der Sichtbarkeit in Suchmaschinen oder generativen Antworten.",
        "Non esiste ancora una misura della visibilità nei motori o nelle risposte generative.",
        "Ainda não há medição de visibilidade em motores de busca ou respostas generativas.",
    ),
    "gap_family": (
        "{family}: sin observar — {reason}.",
        "{family}: not observed — {reason}.",
        "{family} : non observé — {reason}.",
        "{family}: nicht beobachtet — {reason}.",
        "{family}: non osservato — {reason}.",
        "{family}: não observado — {reason}.",
    ),
    "NO_KNOWN_SOURCE": (
        "AXIGNAL todavía no tiene una fuente adoptada para observarlo",
        "AXIGNAL has no adopted source to observe it yet",
        "AXIGNAL n'a pas encore de source adoptée pour l'observer",
        "AXIGNAL hat noch keine zugelassene Quelle dafür",
        "AXIGNAL non ha ancora una fonte adottata per osservarlo",
        "O AXIGNAL ainda não tem uma fonte adotada para o observar",
    ),
    "NO_ADOPTED_SOURCE": (
        "hay fuentes candidatas pendientes de adopción",
        "candidate sources are awaiting adoption",
        "des sources candidates attendent leur adoption",
        "Kandidatenquellen warten auf Zulassung",
        "ci sono fonti candidate in attesa di adozione",
        "há fontes candidatas a aguardar adoção",
    ),
    "NO_ADAPTER": (
        "la fuente adoptada aún no está conectada",
        "the adopted source is not connected yet",
        "la source adoptée n'est pas encore connectée",
        "die zugelassene Quelle ist noch nicht angebunden",
        "la fonte adottata non è ancora collegata",
        "a fonte adotada ainda não está ligada",
    ),
    "NO_CONTEXT": (
        "falta una capacidad observada con la que contrastarlo",
        "there is no observed capability to compare it with",
        "il manque une capacité observée pour comparer",
        "es fehlt eine beobachtete Fähigkeit zum Abgleich",
        "manca una capacità osservata con cui confrontarlo",
        "falta uma capacidade observada para comparar",
    ),
    "NOT_OBSERVED": (
        "aún no se ha observado",
        "it has not been observed yet",
        "cela n'a pas encore été observé",
        "es wurde noch nicht beobachtet",
        "non è ancora stato osservato",
        "ainda não foi observado",
    ),
    "unknown_date": (
        "fecha desconocida",
        "date unknown",
        "date inconnue",
        "Datum unbekannt",
        "data sconosciuta",
        "data desconhecida",
    ),
    "POTENTIAL": ("Potencial", "Potential", "Potentiel", "Potenziell", "Potenziale", "Potencial"),
    "DECLARED": ("Declarado", "Declared", "Déclaré", "Erklärt", "Dichiarato", "Declarado"),
    "STALE": (
        "No actual",
        "Not current",
        "Pas actuel",
        "Nicht aktuell",
        "Non attuale",
        "Não atual",
    ),
}


def text(key: str, locale: str, **values: object) -> str:
    index = LOCALES.index(locale) if locale in LOCALES else 0
    return _TEXT[key][index].format(**values)


GAP_REASONS = ("NO_KNOWN_SOURCE", "NO_ADOPTED_SOURCE", "NO_ADAPTER", "NO_CONTEXT", "NOT_OBSERVED")


def gap_text(item_id: str, reason: str, locale: str) -> str | None:
    """Localized wording for the runtime's explicit UNKNOWNs; None if not a known gap."""
    if item_id == "gap:digital-representation":
        return text("gap_representation", locale)
    if item_id.startswith("gap:coverage:"):
        family = ObservationFamily(item_id.removeprefix("gap:coverage:"))
        code = reason if reason in GAP_REASONS else "NOT_OBSERVED"
        return text(
            "gap_family", locale, family=family_name(family, locale), reason=text(code, locale)
        )
    return None


def family_name(family: ObservationFamily, locale: str) -> str:
    index = LOCALES.index(locale) if locale in LOCALES else 0
    return _FAMILY[family][index]
