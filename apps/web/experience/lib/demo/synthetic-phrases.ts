import type { Locale } from "@/lib/languages";

/**
 * The words of the synthetic SEO and GEO measurements, in every locale. The snapshot's own language is English;
 * a phrase is replaced only when a value equals it exactly, so nothing else in a reading is ever rewritten.
 * These are data of the fictional demo organization, not copy of the interface.
 */
type Phrase = Record<Exclude<Locale, "en">, string>;

const row = (es: string, de: string, pt: string, fr: string, it: string): Phrase => ({ es, de, pt, fr, it });

export const SYNTHETIC_PHRASES: Record<string, Phrase> = {
  "It appears on the first results page for 2 of 3 branded queries.": row(
    "Aparece en la primera página de resultados en 2 de 3 consultas de marca.",
    "Sie erscheint auf der ersten Ergebnisseite bei 2 von 3 Markenanfragen.",
    "Aparece na primeira página de resultados em 2 de 3 pesquisas de marca.",
    "Elle apparaît sur la première page de résultats pour 2 requêtes de marque sur 3.",
    "Compare nella prima pagina dei risultati per 2 query di marca su 3."),
  "It does not appear on the first results page for the category query.": row(
    "No aparece en la primera página de resultados para la consulta de categoría.",
    "Sie erscheint nicht auf der ersten Ergebnisseite bei der Kategorieanfrage.",
    "Não aparece na primeira página de resultados na pesquisa de categoria.",
    "Elle n'apparaît pas sur la première page de résultats pour la requête de catégorie.",
    "Non compare nella prima pagina dei risultati per la query di categoria."),
  "It is mentioned in 1 of 4 sampled AI answers and cited in none.": row(
    "Se la menciona en 1 de 4 respuestas de IA muestreadas y no se la cita en ninguna.",
    "Sie wird in 1 von 4 untersuchten KI-Antworten erwähnt und in keiner zitiert.",
    "É mencionada em 1 de 4 respostas de IA amostradas e não é citada em nenhuma.",
    "Elle est mentionnée dans 1 réponse d'IA échantillonnée sur 4 et citée dans aucune.",
    "È menzionata in 1 risposta di IA campionata su 4 e non è citata in nessuna."),
  "3 branded queries · Spain · Spanish · desktop": row(
    "3 consultas de marca · España · español · escritorio",
    "3 Markenanfragen · Spanien · Spanisch · Desktop",
    "3 pesquisas de marca · Espanha · espanhol · computador",
    "3 requêtes de marque · Espagne · espagnol · ordinateur",
    "3 query di marca · Spagna · spagnolo · desktop"),
  "1 category query · Spain · Spanish · desktop": row(
    "1 consulta de categoría · España · español · escritorio",
    "1 Kategorieanfrage · Spanien · Spanisch · Desktop",
    "1 pesquisa de categoria · Espanha · espanhol · computador",
    "1 requête de catégorie · Espagne · espagnol · ordinateur",
    "1 query di categoria · Spagna · spagnolo · desktop"),
  "4 questions · Spanish · 1 assistant, no sign-in": row(
    "4 preguntas · español · 1 asistente, sin iniciar sesión",
    "4 Fragen · Spanisch · 1 Assistent, ohne Anmeldung",
    "4 perguntas · espanhol · 1 assistente, sem iniciar sessão",
    "4 questions · espagnol · 1 assistant, sans connexion",
    "4 domande · spagnolo · 1 assistente, senza accesso"),
  "3 queries · 1 market · 1 device": row(
    "3 consultas · 1 mercado · 1 dispositivo", "3 Anfragen · 1 Markt · 1 Gerät",
    "3 pesquisas · 1 mercado · 1 dispositivo", "3 requêtes · 1 marché · 1 appareil", "3 query · 1 mercato · 1 dispositivo"),
  "1 query · 1 market · 1 device": row(
    "1 consulta · 1 mercado · 1 dispositivo", "1 Anfrage · 1 Markt · 1 Gerät",
    "1 pesquisa · 1 mercado · 1 dispositivo", "1 requête · 1 marché · 1 appareil", "1 query · 1 mercato · 1 dispositivo"),
  "4 questions · 1 run each": row(
    "4 preguntas · 1 ejecución cada una", "4 Fragen · je 1 Durchlauf",
    "4 perguntas · 1 execução cada", "4 questions · 1 exécution chacune", "4 domande · 1 esecuzione ciascuna"),
  "First results page only; paid results excluded.": row(
    "Solo la primera página de resultados; sin resultados de pago.",
    "Nur die erste Ergebnisseite; bezahlte Ergebnisse ausgeschlossen.",
    "Apenas a primeira página de resultados; resultados pagos excluídos.",
    "Première page de résultats uniquement ; résultats payants exclus.",
    "Solo la prima pagina dei risultati; risultati a pagamento esclusi."),
  "One assistant; answers vary between runs.": row(
    "Un asistente; las respuestas varían entre ejecuciones.",
    "Ein Assistent; die Antworten variieren zwischen den Durchläufen.",
    "Um assistente; as respostas variam entre execuções.",
    "Un assistant ; les réponses varient d'une exécution à l'autre.",
    "Un assistente; le risposte variano tra le esecuzioni."),
  "It appeared for 1 of 3 branded queries on 25 Sep 2026.": row(
    "Aparecía en 1 de 3 consultas de marca el 25 sep 2026.",
    "Sie erschien am 25. Sep. 2026 bei 1 von 3 Markenanfragen.",
    "Aparecia em 1 de 3 pesquisas de marca a 25 set 2026.",
    "Elle apparaissait pour 1 requête de marque sur 3 le 25 sept. 2026.",
    "Compariva per 1 query di marca su 3 il 25 set 2026."),
  "It was mentioned in 0 of 4 sampled AI answers on 25 Sep 2026.": row(
    "No se la mencionaba en ninguna de 4 respuestas de IA muestreadas el 25 sep 2026.",
    "Sie wurde am 25. Sep. 2026 in keiner von 4 untersuchten KI-Antworten erwähnt.",
    "Não era mencionada em nenhuma de 4 respostas de IA amostradas a 25 set 2026.",
    "Elle n'était mentionnée dans aucune des 4 réponses d'IA échantillonnées le 25 sept. 2026.",
    "Non era menzionata in nessuna delle 4 risposte di IA campionate il 25 set 2026."),
  "A sample of queries, not its whole search visibility.": row(
    "Una muestra de consultas, no toda su visibilidad en buscadores.",
    "Eine Stichprobe von Anfragen, nicht die gesamte Sichtbarkeit in Suchmaschinen.",
    "Uma amostra de pesquisas, não toda a sua visibilidade nos motores de busca.",
    "Un échantillon de requêtes, pas toute sa visibilité dans les moteurs de recherche.",
    "Un campione di query, non tutta la sua visibilità nei motori di ricerca."),
  "A single query: absence on one page is not absence from search.": row(
    "Una sola consulta: no aparecer en una página no es no aparecer en buscadores.",
    "Eine einzelne Anfrage: Das Fehlen auf einer Seite ist kein Fehlen in der Suche.",
    "Uma única pesquisa: não aparecer numa página não é não aparecer nos motores de busca.",
    "Une seule requête : l'absence sur une page n'est pas l'absence dans la recherche.",
    "Una sola query: l'assenza in una pagina non è assenza dalla ricerca."),
  "A mention is not a citation, and a citation is not an endorsement.": row(
    "Mencionar no es citar, y citar no es recomendar.",
    "Eine Erwähnung ist keine Zitierung, und eine Zitierung ist keine Empfehlung.",
    "Mencionar não é citar, e citar não é recomendar.",
    "Mentionner n'est pas citer, et citer n'est pas recommander.",
    "Menzionare non è citare, e citare non è raccomandare."),
};
