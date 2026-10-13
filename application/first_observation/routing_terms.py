"""Controlled economic vocabulary in the languages AXIGNAL reads, for semantic routing.

The activity judgment never receives page text, only these fixed, non-identifying
economic words found in it (see ``activity.minimize``). An English-only list left a
German, Norwegian or Spanish site with almost nothing to judge and the activity
UNCLEAR; global by construction means the same words in every language we read.
Common nouns and verbs of economic activity only: no names, places of people or
identifiers can be expressed with them.
"""

from __future__ import annotations

_WORDS = {
    # Information, analysis and intelligence services: without them an analytics,
    # research or intelligence firm reached the judgment almost empty (2026-10-13).
    "information": """
    próximamente construcción demnächst bientôt prossimamente brevemente binnenkort snart
    intelligence observation observes observing monitoring analysis analytics data
    research evidence insights insight platform subscription reports report
    organizations organisations companies information sources benchmarking
    competitive competitors economic economy business market markets trends
    inteligencia observación observa análisis datos investigación evidencia plataforma
    suscripción informes organizaciones fuentes competencia mercado mercados tendencias
    beobachtung analyse daten forschung plattform abonnement berichte organisationen
    quellen wettbewerb wirtschaft markt märkte
    observation analyse données recherche plateforme abonnement rapports organisations
    sources concurrence économie marché marchés tendances
    osservazione analisi dati ricerca piattaforma abbonamento rapporti organizzazioni
    fonti concorrenza economia mercato mercati tendenze
    inteligência observação análise dados pesquisa plataforma assinatura relatórios
    organizações fontes concorrência economia mercado mercados tendências
    """,
    "es": """
    escuela escuelas colegio colegios academia academias idiomas idioma clases cursos curso
    educación educativo enseñanza profesores formación alumnos estudiantes niños infantil
    primaria secundaria bachillerato universidad aprendizaje software nube facturación
    contabilidad banca banco pagos pago finanzas financiero seguros seguro solar fotovoltaica
    placas electricidad eléctrico renovables energía construcción obras reformas
    mantenimiento calefacción climatización ventilación industrial fabricación fabricante
    comercio tienda mayorista reparación reparaciones productos servicios servicio
    instalación instalaciones logística transporte agricultura alimentación
    marketing publicidad comunicación consultoría consultora agencia diseño digital
    seguridad vigilancia alarmas limpieza salud clínica médico dental farmacia
    abogados jurídico legal asesoría inmobiliaria arquitectura ingeniería tecnología
    restaurante hotel turismo viajes moda textil automoción vehículos
    clientes empresas particulares público administración contratación venta envío
    """,
    "de": """
    schule schulen akademie sprachen sprache kurse kurs bildung unterricht lehrer
    ausbildung schüler studenten kinder universität lernen software cloud rechnung
    buchhaltung bank banking zahlungen zahlung finanzen versicherung solar photovoltaik
    strom elektro erneuerbare energie bau bauunternehmen wartung heizung lüftung
    klima industrie fertigung hersteller handel großhandel reparatur produkte
    dienstleistungen dienstleistung installation logistik transport landwirtschaft
    lebensmittel marketing werbung kommunikation beratung agentur werbeagentur design
    digital sicherheit reinigung gesundheit klinik arzt zahnarzt apotheke anwalt
    rechtsanwalt recht immobilien architektur ingenieur technologie restaurant hotel
    tourismus reisen mode textil automobil fahrzeuge kunden unternehmen öffentlich
    verwaltung vergabe verkauf lieferung marken kampagnen kreativ
    """,
    "fr": """
    école écoles académie langues langue cours formation éducation enseignement
    professeurs élèves étudiants enfants université apprentissage logiciel facturation
    comptabilité banque paiements paiement finance assurance solaire photovoltaïque
    électricité électrique renouvelables énergie construction bâtiment travaux
    maintenance chauffage climatisation ventilation industrie fabrication fabricant
    commerce magasin grossiste réparation produits services service installation
    logistique transport agriculture alimentation marketing publicité communication
    conseil agence design numérique sécurité nettoyage santé clinique médecin
    dentaire pharmacie avocat juridique immobilier architecture ingénierie technologie
    restaurant hôtel tourisme voyages mode textile automobile véhicules clients
    entreprises particuliers public administration marchés vente livraison mutuelle
    """,
    "it": """
    scuola scuole accademia lingue lingua corsi corso formazione istruzione insegnamento
    insegnanti studenti bambini università software fatturazione contabilità banca
    pagamenti finanza assicurazione solare fotovoltaico elettricità energia costruzioni
    edilizia manutenzione riscaldamento climatizzazione industria produzione produttore
    commercio negozio ingrosso riparazione prodotti servizi servizio installazione
    logistica trasporti agricoltura alimentare marketing pubblicità comunicazione
    consulenza agenzia design digitale sicurezza pulizia salute clinica medico
    farmacia avvocato legale immobiliare architettura ingegneria tecnologia ristorante
    albergo turismo viaggi moda tessile automobili veicoli clienti aziende pubblico
    vendita consegna
    """,
    "pt": """
    escola escolas academia línguas idiomas aulas cursos curso educação ensino
    professores formação alunos estudantes crianças universidade software faturação
    contabilidade banco pagamentos finanças seguros solar fotovoltaico eletricidade
    energia construção obras manutenção aquecimento climatização indústria fabrico
    fabricante comércio loja grossista reparação produtos serviços serviço instalação
    logística transporte agricultura alimentação marketing publicidade comunicação
    consultoria agência design digital segurança limpeza saúde clínica médico
    farmácia advogados jurídico imobiliária arquitetura engenharia tecnologia
    restaurante hotel turismo viagens moda têxtil automóvel veículos clientes
    empresas público venda entrega
    """,
    "nl": """
    school scholen academie talen taal cursussen cursus onderwijs opleiding leraren
    leerlingen studenten kinderen universiteit software facturatie boekhouding bank
    betalingen betaling financiën verzekering zonnepanelen elektriciteit energie bouw
    onderhoud verwarming ventilatie industrie productie fabrikant handel winkel
    groothandel reparatie producten diensten dienst installatie logistiek transport
    landbouw voeding marketing reclame communicatie advies bureau ontwerp digitaal
    beveiliging schoonmaak gezondheid kliniek arts tandarts apotheek advocaat
    juridisch vastgoed architectuur techniek technologie restaurant hotel toerisme
    reizen mode textiel auto voertuigen klanten bedrijven overheid verkoop levering
    """,
    "nordic": """
    skole skoler skola utdanning utbildning uddannelse kurs kurser språk undervisning
    lærere elever studenter barn universitet programvare programvara software
    regnskap bokföring bank betaling betalinger betalning betalningar finans
    forsikring försäkring forsikring solenergi strøm ström energi bygg byggeri
    vedlikehold underhåll oppvarming industri produksjon produktion produsent
    handel butikk butik reparasjon produkter tjenester tjänster tjenester installasjon
    logistikk logistik transport landbruk jordbruk mat markedsføring marknadsföring
    reklame reklam kommunikasjon kommunikation rådgivning konsult byrå byrå design
    digital sikkerhet säkerhet rengjøring helse hälsa klinikk lege apotek advokat
    eiendom fastigheter arkitektur ingeniør teknologi restaurant hotell turisme
    reiser mote mode tekstil bil kjøretøy kunder kunder bedrifter företag offentlig
    salg försäljning levering leverans mobilbetaling
    """,
}

MULTILINGUAL_ROUTING_TERMS: frozenset[str] = frozenset(
    word.casefold() for block in _WORDS.values() for word in block.split()
)
