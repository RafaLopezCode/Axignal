import fs from "node:fs";
const rows = [
["Staff controls","Staff-Steuerung","Controlos Staff","Commandes Staff","Controlli Staff"],
["Return to Admin","Zurück zum Admin","Voltar ao Admin","Revenir à Admin","Torna ad Admin"],
["Technical diagnostics","Technische Diagnose","Diagnóstico técnico","Diagnostic technique","Diagnostica tecnica"],
["Observe AXIGNAL","AXIGNAL beobachten","Observar AXIGNAL","Observer AXIGNAL","Osserva AXIGNAL"],
["What do you know","Was weißt du","O que sabes","Que sais-tu","Cosa sai"],
["What changed","Was hat sich geändert","O que mudou","Qu’est-ce qui a changé","Cosa è cambiato"],
["Why it matters","Warum es wichtig ist","Porque importa","Pourquoi cela compte","Perché conta"],
["How do you know","Woher weißt du das","Como sabes","Comment le sais-tu","Come lo sai"],
["What would you investigate next","Was würdest du als Nächstes untersuchen","O que investigarias a seguir","Que rechercherais-tu ensuite","Cosa indagheresti dopo"],
["AUTHORIZED CONTEXT","AUTORISIERTER KONTEXT","CONTEXTO AUTORIZADO","CONTEXTE AUTORISÉ","CONTESTO AUTORIZZATO"],
["Reading available evidence. New research requires authorized tools.","Lesen verfügbarer Evidenz. Neue Forschung erfordert autorisierte Werkzeuge.","Leitura da evidência disponível. Nova investigação requer ferramentas autorizadas.","Lecture des preuves disponibles. Une nouvelle recherche nécessite des outils autorisés.","Lettura delle prove disponibili. Nuove ricerche richiedono strumenti autorizzati."],
["No research tools are connected to this reading. These questions remain open.","Mit dieser Ansicht sind keine Forschungswerkzeuge verbunden. Diese Fragen bleiben offen.","Não há ferramentas de investigação ligadas a esta leitura. Estas perguntas continuam abertas.","Aucun outil de recherche n’est connecté à cette lecture. Ces questions restent ouvertes.","Nessuno strumento di ricerca è collegato a questa lettura. Queste domande restano aperte."],
["Reading authorized context…","Autorisierten Kontext lesen…","A ler o contexto autorizado…","Lecture du contexte autorisé…","Lettura del contesto autorizzato…"],
["Observation","Beobachtung","Observação","Observation","Osservazione"],
["Source","Quelle","Fonte","Source","Fonte"],
["DIMENSIONS","DIMENSIONEN","DIMENSÕES","DIMENSIONS","DIMENSIONI"],
["Time and evidence","Zeit und Evidenz","Tempo e evidência","Temps et preuves","Tempo e prove"],
["A signal, in context.","Ein Signal im Kontext.","Um sinal, em contexto.","Un signal, dans son contexte.","Un segnale, nel suo contesto."],
["Bring a signal closer. Understand its basis and what remains open.","Betrachte ein Signal genauer. Verstehe seine Grundlage und was offen bleibt.","Aproxima um sinal. Compreende a sua base e o que continua aberto.","Approche un signal. Comprends son fondement et ce qui reste ouvert.","Avvicina un segnale. Comprendi la sua base e ciò che resta aperto."],
["The authorized projection exposes no data for this dimension. Absence of evidence does not mean absence of capability, market or activity.","Die autorisierte Projektion enthält keine Daten zu dieser Dimension. Fehlende Evidenz bedeutet nicht, dass Fähigkeit, Markt oder Aktivität fehlen.","A projeção autorizada não expõe dados desta dimensão. Ausência de evidência não significa ausência de capacidade, mercado ou atividade.","La projection autorisée ne présente aucune donnée pour cette dimension. L’absence de preuves ne signifie pas l’absence de capacité, de marché ou d’activité.","La proiezione autorizzata non espone dati per questa dimensione. L’assenza di prove non significa assenza di capacità, mercato o attività."],
["Spatial panorama","Räumliches Panorama","Panorama espacial","Panorama spatial","Panorama spaziale"],
["No relationships are exposed in this projection. Visual proximity asserts no economic link.","Diese Projektion zeigt keine Beziehungen. Visuelle Nähe behauptet keine wirtschaftliche Verbindung.","Esta projeção não expõe relações. A proximidade visual não afirma um vínculo económico.","Cette projection ne présente aucune relation. La proximité visuelle n’affirme aucun lien économique.","Questa proiezione non espone relazioni. La vicinanza visiva non afferma alcun legame economico."],
["Mobile reading","Mobile Ansicht","Leitura móvel","Lecture mobile","Lettura mobile"],
["This projection contains one authorized focus. No other focuses are available in this contract.","Diese Projektion enthält einen autorisierten Fokus. Dieser Vertrag bietet keine weiteren Fokusse.","Esta projeção contém um foco autorizado. Não há outros focos disponíveis neste contrato.","Cette projection contient un seul foyer autorisé. Aucun autre foyer n’est disponible dans ce contrat.","Questa proiezione contiene un solo focus autorizzato. Nessun altro focus è disponibile in questo contratto."],
["The runtime exposes the current observation, not a navigable historical snapshot series. An observation date does not prove when an economic change happened.","Die Laufzeit zeigt die aktuelle Beobachtung, keine navigierbare Reihe historischer Zustände. Ein Beobachtungsdatum beweist nicht, wann eine wirtschaftliche Veränderung stattfand.","O runtime expõe a observação atual, não uma série histórica navegável. Uma data de observação não prova quando ocorreu uma mudança económica.","Le runtime expose l’observation actuelle, pas une série historique navigable. Une date d’observation ne prouve pas quand un changement économique a eu lieu.","Il runtime espone l’osservazione attuale, non una serie storica navigabile. Una data di osservazione non prova quando è avvenuto un cambiamento economico."],
];
const catalog=JSON.parse(fs.readFileSync("lib/translations.json","utf8"));
for(const [key,...translations] of rows)catalog[key]=translations;
fs.writeFileSync("lib/translations.json",JSON.stringify(catalog,null,2)+"\n");
