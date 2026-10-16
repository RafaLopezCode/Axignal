"""Versioned catalogs: capability lexicon, economic questions, concrete sources.

These are governed data, not code paths. A new family, market, classification
scheme or jurisdiction is a catalog entry; routing logic never names a sector,
country or portal. Source facts are only what official documentation states;
anything unverified keeps the source CANDIDATE with explicit adoption blockers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta

from application.observation_intelligence.contracts import (
    AccessMethod,
    AdoptionStatus,
    Band,
    BuyerLevel,
    EconomicQuestion,
    MarketRole,
    OpportunityFamily,
    RightsStatus,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
    geo,
)

CATALOG_VERSION = "eoil-catalog-2026-10-16.8"

#: Path depth that counts as a "region" inside each jurisdiction tree.
REGIONAL_DEPTH: dict[str, int] = {"EU": 4, "US": 2}


def cpv(code: str) -> TaxonomyCode:
    return TaxonomyCode("CPV", code)


def naics(code: str) -> TaxonomyCode:
    return TaxonomyCode("NAICS", code)


def psc(code: str) -> TaxonomyCode:
    return TaxonomyCode("PSC", code)


def eu_nuts(code: str) -> TaxonomyCode:
    """NUTS code → jurisdiction path: ES522 → EU/ES/ES5/ES52/ES522."""

    return geo("/".join(["EU", code[:2], *(code[:i] for i in range(3, len(code) + 1))]))


@dataclass(frozen=True, slots=True)
class CapabilityLexiconEntry:
    """Deterministic surface terms for one capability and how buyers classify it."""

    capability_id: str
    label: str
    terms: tuple[str, ...]
    demand_codes: tuple[TaxonomyCode, ...]
    families: tuple[str, ...]
    buyer_jobs: tuple[str, ...]


CAPABILITY_LEXICON: tuple[CapabilityLexiconEntry, ...] = (
    CapabilityLexiconEntry(
        capability_id="solar-pv-installation",
        label="Solar photovoltaic installation",
        # "autoconsumo" alone also means growing one's own food or saving water (found on
        # biocultor.com, an organic-fertiliser shop: "huerto urbano, autoconsumo y jardinería"):
        # only its solar forms name this activity.
        terms=("fotovoltaic", "photovoltaï", "photovoltaic", "paneles solares", "placas solares",
               "autoconsumo solar", "autoconsumo fotovoltaico", "autoconsumo eléctrico",
               "autoconsumo energético", "instalaciones de autoconsumo"),
        demand_codes=(
            cpv("09331200"), cpv("09332000"), cpv("45261215"), naics("221114"), naics("238210"),
        ),
        families=("energy", "construction"),
        buyer_jobs=("self-consumption on public buildings", "solar roofs for industrial sites"),
    ),
    CapabilityLexiconEntry(
        capability_id="electrical-installation",
        label="Electrical installation work",
        terms=("instalaciones eléctricas", "electrical installation", "installation électrique"),
        demand_codes=(cpv("45311000"), cpv("45317000"), naics("238210")),
        families=("construction",),
        buyer_jobs=("electrical works in public facilities",),
    ),
    CapabilityLexiconEntry(
        capability_id="industrial-hvac",
        label="Industrial HVAC installation and maintenance",
        terms=("climatización industrial", "industrial hvac", "climatisation industrielle"),
        demand_codes=(
            cpv("45331000"), cpv("42510000"), naics("238220"), psc("4120"), psc("J041"),
        ),
        families=("industrial-maintenance", "construction"),
        buyer_jobs=(
            "HVAC renewal in hospitals and public buildings",
            "climate control for new logistics centres and plants",
        ),
    ),
    CapabilityLexiconEntry(
        capability_id="industrial-refrigeration",
        label="Industrial refrigeration installation and maintenance",
        terms=("refrigeración industrial", "froid industriel", "industrial refrigeration"),
        demand_codes=(
            cpv("42513000"), cpv("50730000"), naics("238220"), naics("333415"),
            psc("4110"), psc("J041"),
        ),
        families=("industrial-maintenance", "construction"),
        buyer_jobs=(
            "cold rooms for new food manufacturing plants",
            "refrigeration maintenance for hospitals and logistics centres",
        ),
    ),
    CapabilityLexiconEntry(
        capability_id="consumer-mobile-app",
        label="Consumer mobile ordering app",
        terms=("descarga nuestra app", "mobile app", "app móvil"),
        demand_codes=(),
        families=("consumer-software",),
        buyer_jobs=("consumers ordering from local shops",),
    ),
    # --- Common SME activities (catalog .5). Each term is a distinctive phrase an
    # organization uses to say what it offers, in the six product languages; generic
    # words that also appear in footers or menus are avoided. A match stays a POTENTIAL
    # hypothesis with its exact sentence; codes only route the search for demand.
    CapabilityLexiconEntry(
        capability_id="legal-services", label="Legal services",
        terms=("servicios jurídicos", "servicios legales", "despacho de abogados", "asesoría jurídica",
               "asesoramiento legal", "legal services", "law firm", "services juridiques",
               "cabinet d'avocats", "anwaltskanzlei", "rechtsberatung", "servizi legali",
               "studio legale", "serviços jurídicos", "escritório de advogados"),
        demand_codes=(cpv("79100000"), cpv("79110000"), naics("541110")),
        families=("professional-services",),
        buyer_jobs=("legal advice and representation for public bodies",),
    ),
    CapabilityLexiconEntry(
        capability_id="accounting-tax", label="Accounting, audit and tax advisory",
        terms=("asesoría fiscal", "asesoría contable", "servicios de contabilidad", "auditoría de cuentas",
               "accounting services", "tax advisory", "audit services", "expertise comptable",
               "steuerberatung", "wirtschaftsprüfung", "consulenza fiscale", "serviços de contabilidade"),
        demand_codes=(cpv("79200000"), cpv("79212000"), cpv("79221000"), naics("541211")),
        families=("professional-services",),
        buyer_jobs=("annual audits and tax advice for public entities",),
    ),
    CapabilityLexiconEntry(
        capability_id="management-consulting", label="Management and business consulting",
        terms=("consultoría estratégica", "consultoría de gestión", "consultoría empresarial",
               "management consulting", "business consulting", "conseil en stratégie",
               "unternehmensberatung", "consulenza aziendale", "consultoria de gestão"),
        demand_codes=(cpv("79400000"), cpv("79410000"), naics("541611")),
        families=("professional-services",),
        buyer_jobs=("strategy and organisation studies for public administrations",),
    ),
    CapabilityLexiconEntry(
        capability_id="market-research", label="Market research and economic intelligence",
        terms=("estudios de mercado", "investigación de mercados", "inteligencia de mercado",
               "inteligencia económica", "market research", "market intelligence",
               "études de marché", "marktforschung", "ricerche di mercato", "pesquisa de mercado",
               "economic intelligence", "competitive intelligence", "inteligencia empresarial",
               "inteligencia competitiva", "intelligence économique", "wirtschaftsintelligenz",
               "intelligence economica", "inteligência económica", "inteligência empresarial"),
        # Not the 79300000 parent: in CPV it also holds advertising, marketing, events and
        # auctions (7934xxxx), which made 70 of 100 matches unrelated (self-check, 2026-10-15).
        demand_codes=(cpv("79310000"), cpv("79320000"), cpv("79330000"), naics("541910")),
        families=("professional-services",),
        buyer_jobs=("sector studies and economic observatories for public bodies",),
    ),
    CapabilityLexiconEntry(
        capability_id="software-development", label="Software development",
        terms=("desarrollo de software", "software a medida", "desarrollo de aplicaciones",
               "software development", "custom software", "développement logiciel",
               "softwareentwicklung", "sviluppo software", "desenvolvimento de software"),
        demand_codes=(cpv("72200000"), cpv("72230000"), cpv("72260000"), naics("541511")),
        families=("software",),
        buyer_jobs=("custom applications and digital services for public bodies",),
    ),
    CapabilityLexiconEntry(
        capability_id="business-software", label="Business management software",
        terms=("software de gestión", "software de recursos humanos", "software de nóminas",
               "programa de gestión", "software as a service", "hr software", "payroll software",
               "logiciel de gestion", "logiciel rh", "personalsoftware", "software gestionale",
               "software de gestão"),
        demand_codes=(cpv("48000000"), cpv("48450000"), cpv("72260000"), naics("513210")),
        families=("software",),
        buyer_jobs=("management software licences for administrations",),
    ),
    CapabilityLexiconEntry(
        capability_id="it-services", label="IT services and support",
        terms=("servicios informáticos", "soporte informático", "servicios gestionados de ti",
               "it services", "managed it services", "services informatiques",
               "it-dienstleistungen", "servizi informatici", "serviços de informática"),
        demand_codes=(cpv("72000000"), cpv("72500000"), cpv("72253000"), naics("541519")),
        families=("software",),
        buyer_jobs=("IT support and maintenance for public offices",),
    ),
    CapabilityLexiconEntry(
        capability_id="cybersecurity", label="Cybersecurity",
        terms=("servicios de ciberseguridad", "soluciones de ciberseguridad", "cybersecurity services",
               "cybersecurity solutions", "services de cybersécurité", "cybersicherheitslösungen",
               "servizi di sicurezza informatica", "serviços de cibersegurança"),
        demand_codes=(cpv("72212730"), cpv("48730000"), cpv("72800000"), naics("541519")),
        families=("software",),
        buyer_jobs=("security audits and protection for public systems",),
    ),
    CapabilityLexiconEntry(
        capability_id="telecommunications", label="Telecommunications and connectivity",
        # Service phrases only: the bare sector word is how others list the clients they serve.
        terms=("operador de telecomunicaciones", "servicios de telecomunicaciones",
               "instalaciones de telecomunicaciones", "fibra óptica", "telecommunications services",
               "telecom operator", "fibre optic", "fiber optic", "services de télécommunications",
               "opérateur télécom", "telekommunikationsdienst", "telekommunikationsanbieter",
               "servizi di telecomunicazione", "operatore di telecomunicazioni",
               "serviços de telecomunicações", "operador de telecomunicações"),
        demand_codes=(cpv("64200000"), cpv("32500000"), cpv("45314000"), naics("517111")),
        families=("telecommunications",),
        buyer_jobs=("connectivity and network deployments for public buildings",),
    ),
    CapabilityLexiconEntry(
        capability_id="engineering-services", label="Engineering services",
        terms=("servicios de ingeniería", "ingeniería de proyectos", "engineering services",
               "engineering consultancy", "bureau d'études", "ingenieurbüro", "servizi di ingegneria",
               "serviços de engenharia"),
        demand_codes=(cpv("71300000"), cpv("71320000"), naics("541330")),
        families=("professional-services", "construction"),
        buyer_jobs=("engineering studies and project design for public works",),
    ),
    CapabilityLexiconEntry(
        capability_id="architecture", label="Architectural services",
        terms=("estudio de arquitectura", "servicios de arquitectura", "architecture firm",
               "architectural services", "cabinet d'architecture", "architekturbüro",
               "studio di architettura", "gabinete de arquitetura"),
        demand_codes=(cpv("71200000"), cpv("71220000"), naics("541310")),
        families=("professional-services", "construction"),
        buyer_jobs=("design of public buildings and refurbishments",),
    ),
    CapabilityLexiconEntry(
        capability_id="building-construction", label="Building and civil construction",
        terms=("empresa constructora", "construcción de edificios", "obra civil", "construction company",
               "building construction", "civil engineering works", "entreprise de construction",
               "bauunternehmen", "impresa edile", "construtora"),
        demand_codes=(cpv("45000000"), cpv("45210000"), cpv("45220000"), naics("236220")),
        families=("construction",),
        buyer_jobs=("new public buildings and civil works",),
    ),
    CapabilityLexiconEntry(
        capability_id="formwork-scaffolding", label="Formwork and scaffolding",
        terms=("encofrado", "andamio", "formwork", "scaffolding", "coffrage", "échafaudage",
               "schalungstechnik", "casseforme", "ponteggi", "cofragem", "andaimes"),
        demand_codes=(cpv("44212310"), cpv("45262100"), cpv("44212300"), naics("238190")),
        families=("construction", "industrial"),
        buyer_jobs=("formwork and scaffolding for bridges, tunnels and buildings",),
    ),
    CapabilityLexiconEntry(
        capability_id="ventilation-systems", label="Ventilation systems",
        terms=("sistemas de ventilación", "ventilación industrial", "ventilación de túneles",
               "ventilation systems", "tunnel ventilation", "industrial fans",
               "systèmes de ventilation", "lüftungssysteme", "ventilazione industriale",
               "sistemas de ventilação"),
        demand_codes=(cpv("42520000"), cpv("45331210"), cpv("39717000"), naics("333413")),
        families=("industrial", "construction"),
        buyer_jobs=("ventilation for road, rail and metro tunnels",),
    ),
    CapabilityLexiconEntry(
        capability_id="automotive-components", label="Automotive components manufacturing",
        terms=("componentes de automoción", "componentes para automoción", "automotive components",
               "automotive parts", "équipementier automobile", "composants automobiles",
               "automobilzulieferer", "componenti per autoveicoli", "componentes automóveis"),
        demand_codes=(cpv("34300000"), cpv("34330000"), naics("336370")),
        families=("industrial",),
        buyer_jobs=("vehicle parts for public fleets",),
    ),
    CapabilityLexiconEntry(
        capability_id="metal-fabrication", label="Metal fabrication and machining",
        terms=("estructuras metálicas", "calderería", "mecanizado de precisión", "metal fabrication",
               "steel structures", "precision machining", "construction métallique", "stahlbau",
               "carpenteria metallica", "estruturas metálicas"),
        demand_codes=(cpv("44210000"), cpv("45223000"), naics("332312")),
        families=("industrial", "construction"),
        buyer_jobs=("steel structures and machined parts for public works",),
    ),
    CapabilityLexiconEntry(
        capability_id="food-retail", label="Food retail (supermarkets)",
        terms=("supermercado", "hipermercado", "supermarket", "supermarché", "supermarkt",
               "supermercato"),
        demand_codes=(),
        families=("retail",),
        buyer_jobs=("households buying groceries",),
    ),
    CapabilityLexiconEntry(
        capability_id="food-manufacturing", label="Food and beverage manufacturing",
        terms=("industria alimentaria", "fabricante de alimentos", "food manufacturing",
               "food manufacturer", "industrie agroalimentaire", "lebensmittelhersteller",
               "industria alimentare", "indústria alimentar"),
        demand_codes=(cpv("15000000"), naics("311")),
        families=("industrial", "food"),
        buyer_jobs=("food supply for public canteens and hospitals",),
    ),
    CapabilityLexiconEntry(
        capability_id="catering", label="Catering and contract food services",
        terms=("servicios de catering", "restauración colectiva", "comedores escolares",
               "catering services", "contract catering", "restauration collective",
               "gemeinschaftsverpflegung", "ristorazione collettiva", "restauração coletiva"),
        demand_codes=(cpv("55520000"), cpv("55320000"), cpv("55524000"), naics("722310")),
        families=("food", "facility-services"),
        buyer_jobs=("school, hospital and staff canteens",),
    ),
    CapabilityLexiconEntry(
        capability_id="hospitality", label="Hotel accommodation",
        terms=("reserva tu habitación", "nuestras habitaciones", "book your stay", "our rooms",
               "réservez votre séjour", "unsere zimmer", "le nostre camere", "os nossos quartos"),
        demand_codes=(cpv("55100000"), naics("721110")),
        families=("hospitality",),
        buyer_jobs=("accommodation for official delegations and events",),
    ),
    CapabilityLexiconEntry(
        capability_id="cleaning-services", label="Cleaning services",
        terms=("servicios de limpieza", "empresa de limpieza", "limpieza de oficinas",
               "limpieza de edificios", "limpieza industrial", "limpieza hospitalaria",
               "apoyo de limpieza",
               "cleaning services", "commercial cleaning", "services de nettoyage",
               "gebäudereinigung", "servizi di pulizia", "serviços de limpeza"),
        demand_codes=(cpv("90910000"), cpv("90911200"), naics("561720")),
        families=("facility-services",),
        buyer_jobs=("cleaning of public buildings, schools and hospitals",),
    ),
    CapabilityLexiconEntry(
        capability_id="security-guarding", label="Private security and guarding",
        terms=("seguridad privada", "vigilantes de seguridad", "security guard services",
               "manned guarding", "on-site guarding", "guarding services", "mobile security services",
               "gardiennage", "sicherheitsdienst", "vigilanza privata", "segurança privada"),
        demand_codes=(cpv("79710000"), cpv("79713000"), naics("561612")),
        families=("facility-services",),
        buyer_jobs=("guarding of public buildings and events",),
    ),
    CapabilityLexiconEntry(
        capability_id="security-systems", label="Security and surveillance systems",
        terms=("videovigilancia", "sistemas de alarma", "sistemas de seguridad electrónica",
               "cctv", "alarm systems", "electronic security", "remote video", "alarm monitoring",
               "vidéosurveillance", "videoüberwachung",
               "videosorveglianza", "videovigilância"),
        demand_codes=(cpv("35120000"), cpv("45312000"), naics("561621")),
        families=("facility-services", "construction"),
        buyer_jobs=("CCTV and alarm installations in public facilities",),
    ),
    CapabilityLexiconEntry(
        capability_id="facility-maintenance", label="Facility management and maintenance",
        terms=("mantenimiento de instalaciones", "facility management", "facility services",
               "servicios auxiliares",
               "gestión de instalaciones", "maintenance multitechnique", "gebäudemanagement",
               "manutenzione impianti", "manutenção de instalações"),
        demand_codes=(cpv("50700000"), cpv("79993000"), naics("561210")),
        families=("facility-services", "industrial-maintenance"),
        buyer_jobs=("integrated maintenance of public buildings",),
    ),
    CapabilityLexiconEntry(
        capability_id="waste-management", label="Waste management and recycling",
        terms=("gestión de residuos", "recogida de residuos", "reciclaje de residuos",
               "waste management", "waste collection", "gestion des déchets", "abfallentsorgung",
               "gestione dei rifiuti", "gestão de resíduos"),
        demand_codes=(cpv("90500000"), cpv("90510000"), cpv("90511000"), naics("562111")),
        families=("environment",),
        buyer_jobs=("municipal waste collection and treatment",),
    ),
    CapabilityLexiconEntry(
        capability_id="water-treatment", label="Water and wastewater treatment",
        terms=("tratamiento de aguas", "depuración de aguas", "potabilización", "water treatment",
               "wastewater treatment", "traitement des eaux", "wasseraufbereitung",
               "trattamento acque", "tratamento de águas"),
        demand_codes=(cpv("45252000"), cpv("90400000"), cpv("42912300"), naics("221320")),
        families=("environment", "construction"),
        buyer_jobs=("treatment plants and water network works",),
    ),
    CapabilityLexiconEntry(
        capability_id="freight-logistics", label="Freight transport and logistics",
        terms=("transporte de mercancías", "servicios logísticos", "operador logístico",
               "logistics services", "freight forwarding", "road freight", "transport de marchandises",
               "logistikdienstleister", "trasporto merci", "transporte de mercadorias"),
        demand_codes=(cpv("60100000"), cpv("63100000"), cpv("63520000"), naics("484")),
        families=("logistics",),
        buyer_jobs=("transport and storage for public supply chains",),
    ),
    CapabilityLexiconEntry(
        capability_id="courier-parcel", label="Courier and parcel delivery",
        terms=("mensajería urgente", "servicio de paquetería urgente", "courier services", "parcel delivery",
               "messagerie express", "paketdienst", "corriere espresso", "entregas expresso"),
        demand_codes=(cpv("64120000"), naics("492110")),
        families=("logistics",),
        buyer_jobs=("courier services for administrations",),
    ),
    CapabilityLexiconEntry(
        capability_id="energy-supply", label="Electricity and gas supply",
        terms=("comercializadora eléctrica", "compañía de luz", "tarifas de luz", "electricity supplier",
               "energy supplier", "fournisseur d'électricité", "stromanbieter", "fornitore di energia",
               "comercializadora de energia"),
        demand_codes=(cpv("09310000"), cpv("09123000"), naics("221122")),
        families=("energy",),
        buyer_jobs=("electricity and gas supply for public buildings",),
    ),
    CapabilityLexiconEntry(
        capability_id="medical-devices", label="Medical devices and equipment",
        terms=("productos sanitarios", "equipos médicos", "dispositivos médicos", "medical devices",
               "medical equipment", "dispositifs médicaux", "medizinprodukte", "dispositivi medici"),
        demand_codes=(cpv("33100000"), cpv("33140000"), naics("339112")),
        families=("health", "industrial"),
        buyer_jobs=("equipment and consumables for public hospitals",),
    ),
    CapabilityLexiconEntry(
        capability_id="pharmaceuticals", label="Pharmaceutical products",
        terms=("laboratorio farmacéutico", "medicamentos genéricos", "pharmaceutical company",
               "pharmaceutical products", "laboratoire pharmaceutique", "pharmaunternehmen",
               "azienda farmaceutica", "indústria farmacêutica"),
        demand_codes=(cpv("33600000"), naics("325412")),
        families=("health",),
        buyer_jobs=("medicines for public health systems",),
    ),
    CapabilityLexiconEntry(
        capability_id="healthcare-services", label="Healthcare services",
        terms=("clínica dental", "centro médico", "servicios sanitarios", "healthcare services",
               "medical centre", "medical center", "centre médical", "arztpraxis",
               "centro medico", "clínica médica"),
        demand_codes=(cpv("85100000"), cpv("85130000"), naics("621")),
        families=("health",),
        buyer_jobs=("outsourced care for public health services",),
    ),
    CapabilityLexiconEntry(
        capability_id="training", label="Training and education for companies",
        terms=("formación para empresas", "cursos de formación", "formación bonificada",
               "corporate training", "training courses", "formation professionnelle",
               "weiterbildung", "formazione aziendale", "formação profissional"),
        demand_codes=(cpv("80500000"), cpv("80530000"), naics("611430")),
        families=("education",),
        buyer_jobs=("staff and vocational training programmes",),
    ),
    CapabilityLexiconEntry(
        capability_id="marketing-advertising", label="Marketing and advertising",
        terms=("agencia de marketing", "agencia de publicidad", "marketing digital", "marketing agency",
               "advertising agency", "digital marketing", "agence de communication",
               "werbeagentur", "agenzia di marketing", "agência de marketing"),
        demand_codes=(cpv("79340000"), cpv("79341000"), cpv("79342000"), naics("541810")),
        families=("professional-services",),
        buyer_jobs=("institutional campaigns and tourism promotion",),
    ),
    CapabilityLexiconEntry(
        capability_id="web-design", label="Web design and development",
        terms=("diseño web", "diseño de páginas web", "web design", "website design",
               "création de site", "webdesign", "realizzazione siti web", "criação de sites"),
        demand_codes=(cpv("72413000"), cpv("72212224"), naics("541511")),
        families=("software",),
        buyer_jobs=("websites and portals for public bodies",),
    ),
    CapabilityLexiconEntry(
        capability_id="translation", label="Translation and interpreting",
        terms=("servicios de traducción", "agencia de traducción", "translation services",
               "services de traduction", "übersetzungsbüro", "servizi di traduzione",
               "serviços de tradução"),
        demand_codes=(cpv("79530000"), cpv("79540000"), naics("541930")),
        families=("professional-services",),
        buyer_jobs=("translation of official documents",),
    ),
    CapabilityLexiconEntry(
        capability_id="recruitment-staffing", label="Recruitment and staffing",
        terms=("selección de personal", "empresa de trabajo temporal", "recruitment agency",
               "staffing agency", "cabinet de recrutement", "personalvermittlung",
               "agenzia per il lavoro", "recrutamento e seleção"),
        demand_codes=(cpv("79600000"), cpv("79620000"), naics("561311")),
        families=("professional-services",),
        buyer_jobs=("temporary staff and selection processes",),
    ),
    CapabilityLexiconEntry(
        capability_id="insurance", label="Insurance",
        terms=("correduría de seguros", "seguros para empresas", "insurance broker",
               "insurance company", "courtier en assurances", "versicherungsmakler",
               "broker assicurativo", "corretora de seguros"),
        demand_codes=(cpv("66510000"), cpv("66518100"), naics("524210")),
        families=("financial",),
        buyer_jobs=("insurance policies for public entities",),
    ),
    CapabilityLexiconEntry(
        capability_id="real-estate", label="Real estate services",
        terms=("agencia inmobiliaria", "portal inmobiliario", "pisos en venta", "real estate agency",
               "property portal", "agence immobilière", "immobilienmakler", "agenzia immobiliare",
               "agência imobiliária"),
        demand_codes=(cpv("70000000"), cpv("70300000"), naics("531210")),
        families=("real-estate",),
        buyer_jobs=("property search and valuation",),
    ),
    CapabilityLexiconEntry(
        capability_id="printing", label="Printing services",
        terms=("imprenta", "servicios de impresión", "printing services", "commercial printing",
               "imprimerie", "druckerei", "tipografia", "gráfica e impressão"),
        demand_codes=(cpv("79810000"), cpv("79800000"), naics("323111")),
        families=("industrial",),
        buyer_jobs=("printed materials for administrations",),
    ),
    CapabilityLexiconEntry(
        capability_id="events", label="Event organisation",
        terms=("organización de eventos", "agencia de eventos", "event management", "event agency",
               "organisation d'événements", "eventagentur", "organizzazione eventi",
               "organização de eventos"),
        demand_codes=(cpv("79952000"), cpv("79950000"), naics("561920")),
        families=("professional-services",),
        buyer_jobs=("institutional events, congresses and fairs",),
    ),
    CapabilityLexiconEntry(
        capability_id="furniture", label="Furniture manufacturing and supply",
        terms=("mobiliario de oficina", "fabricante de muebles", "office furniture",
               "furniture manufacturer", "mobilier de bureau", "büromöbel", "mobili per ufficio",
               "mobiliário de escritório"),
        demand_codes=(cpv("39100000"), cpv("39130000"), naics("337214")),
        families=("industrial",),
        buyer_jobs=("furniture for schools, offices and hospitals",),
    ),
    CapabilityLexiconEntry(
        capability_id="workwear", label="Workwear and uniforms",
        terms=("ropa laboral", "vestuario laboral", "uniformes de trabajo", "workwear",
               "vêtements de travail", "berufsbekleidung", "abbigliamento da lavoro",
               "roupa de trabalho"),
        demand_codes=(cpv("18100000"), cpv("18110000"), naics("315250")),
        families=("industrial",),
        buyer_jobs=("uniforms for public services staff",),
    ),
    CapabilityLexiconEntry(
        capability_id="laboratory-testing", label="Laboratory testing and inspection",
        terms=("laboratorio de ensayos", "ensayos de laboratorio", "testing laboratory",
               "laboratory testing", "laboratoire d'essais", "prüflabor", "laboratorio di prove",
               "laboratório de ensaios"),
        demand_codes=(cpv("71900000"), cpv("71600000"), naics("541380")),
        families=("professional-services",),
        buyer_jobs=("testing and quality control for public works",),
    ),
    CapabilityLexiconEntry(
        capability_id="agriculture", label="Agricultural production",
        terms=("explotación agrícola", "productos agrícolas", "agricultural products", "farm produce",
               "exploitation agricole", "landwirtschaftsbetrieb", "azienda agricola",
               "exploração agrícola"),
        demand_codes=(cpv("03000000"), cpv("03200000"), naics("111")),
        families=("food",),
        buyer_jobs=("fresh produce for public canteens",),
    ),
)  # fmt: skip


#: The Brain's root question. It is never routed itself; each opportunity family
#: contributes sub-questions that require that family's source capabilities.
ROOT_QUESTION = (
    "Where is there economically plausible demand for this Xeed's observed capabilities, "
    "and what public evidence supports it?"
)

_F = OpportunityFamily
_ALL_BUYERS = frozenset({MarketRole.PUBLIC_BUYERS, MarketRole.PRIVATE_BUSINESSES})

QUESTIONS: tuple[EconomicQuestion, ...] = (
    EconomicQuestion(
        question_id="what-does-it-offer",
        version="1",
        text="What does this organization actually offer?",
        requires=frozenset({SourceCapability.CAPABILITY_DECLARATION}),
        market_roles=frozenset(MarketRole),
        economic_value=Band.MEDIUM,
        uses_capability_codes=False,
    ),
    EconomicQuestion(
        question_id="compatible-public-tenders",
        version="1",
        text="Which open public tenders ask for its observed capabilities?",
        requires=frozenset({SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES}),
        market_roles=frozenset({MarketRole.PUBLIC_BUYERS}),
        economic_value=Band.HIGH,
        opportunity_family=_F.PUBLIC_PROCUREMENT,
    ),
    EconomicQuestion(
        question_id="revealed-public-demand",
        version="1",
        text="Which recent awards reveal buyers and recurring demand for these capabilities?",
        requires=frozenset({SourceCapability.PUBLIC_PROCUREMENT_AWARDS}),
        market_roles=frozenset({MarketRole.PUBLIC_BUYERS}),
        economic_value=Band.MEDIUM,
        opportunity_family=_F.PUBLIC_PROCUREMENT,
    ),
    EconomicQuestion(
        question_id="public-investment-pipeline",
        version="1",
        text="Which planned public investments will need these capabilities?",
        requires=frozenset({SourceCapability.PUBLIC_INVESTMENT_PLANS}),
        market_roles=frozenset({MarketRole.PUBLIC_BUYERS}),
        economic_value=Band.HIGH,
        opportunity_family=_F.PUBLIC_INVESTMENT,
    ),
    EconomicQuestion(
        question_id="funding-driven-demand",
        version="1",
        text="Which grants or subsidies are funding work these capabilities can deliver?",
        requires=frozenset({SourceCapability.PUBLIC_FUNDING}),
        market_roles=_ALL_BUYERS,
        economic_value=Band.MEDIUM,
        opportunity_family=_F.GRANTS_AND_SUBSIDIES,
    ),
    EconomicQuestion(
        question_id="projects-needing-capability",
        version="1",
        text="Which permitted or planned projects will need this capability?",
        requires=frozenset({SourceCapability.PLANNING_AND_PERMITS}),
        market_roles=_ALL_BUYERS,
        economic_value=Band.HIGH,
        opportunity_family=_F.PLANNING_AND_PERMITS,
    ),
    EconomicQuestion(
        question_id="private-project-announcements",
        version="1",
        text="Which announced private projects (plants, logistics, hospitality) need it?",
        requires=frozenset({SourceCapability.PRIVATE_PROJECT_ANNOUNCEMENTS}),
        market_roles=frozenset({MarketRole.PRIVATE_BUSINESSES}),
        economic_value=Band.HIGH,
        opportunity_family=_F.PRIVATE_PROJECT_SIGNALS,
    ),
    EconomicQuestion(
        question_id="regulation-driven-demand",
        version="1",
        text="Which regulatory changes oblige buyers to purchase what it offers?",
        requires=frozenset({SourceCapability.REGULATORY_CHANGE}),
        market_roles=_ALL_BUYERS,
        economic_value=Band.MEDIUM,
        uses_capability_codes=False,
        opportunity_family=_F.REGULATION_DRIVEN_DEMAND,
    ),
    EconomicQuestion(
        question_id="buyer-expansion",
        version="1",
        text="Which potential buyers show expansion through hiring or investment?",
        requires=frozenset(
            {SourceCapability.HIRING_DEMAND, SourceCapability.BUYER_INVESTMENT_SIGNALS}
        ),
        market_roles=frozenset({MarketRole.PRIVATE_BUSINESSES}),
        economic_value=Band.LOW,
        opportunity_family=_F.BUYER_EXPANSION_SIGNALS,
    ),
    EconomicQuestion(
        question_id="consumer-representation",
        version="1",
        text="How is it represented where consumers look for it?",
        requires=frozenset({SourceCapability.DIGITAL_REPRESENTATION}),
        market_roles=frozenset({MarketRole.CONSUMERS}),
        economic_value=Band.MEDIUM,
        uses_capability_codes=False,
    ),
)

_PROCUREMENT = frozenset(
    {
        SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
        SourceCapability.PUBLIC_PROCUREMENT_AWARDS,
    }
)


def _candidate(
    *,
    source_id: str,
    name: str,
    owner: str,
    capabilities: frozenset[SourceCapability],
    jurisdictions: tuple[TaxonomyCode, ...],
    classification_systems: frozenset[str],
    buyer_levels: frozenset[BuyerLevel],
    record_types: tuple[str, ...],
    access_method: AccessMethod,
    authentication_required: bool,
    expected_change_interval: timedelta,
    reference: str,
    blockers: tuple[str, ...],
    scope_limitations: tuple[str, ...] = (),
    alternatives: tuple[str, ...] = (),
) -> SourceDescriptor:
    """A source known to exist but not yet through the adoption gate: UNKNOWNs stay UNKNOWN."""

    return SourceDescriptor(
        source_id=source_id,
        version="0",
        name=name,
        owner=owner,
        capabilities=capabilities,
        jurisdictions=jurisdictions,
        classification_systems=classification_systems,
        buyer_levels=buyer_levels,
        record_types=record_types,
        access_method=access_method,
        authentication_required=authentication_required,
        rights=RightsStatus.UNKNOWN,
        reliability=Band.UNKNOWN,
        precision=Band.UNKNOWN,
        coverage=Band.UNKNOWN,
        provenance_quality=Band.UNKNOWN,
        structured=True,
        expected_change_interval=expected_change_interval,
        historical_depth="TO_VERIFY",
        cost_per_request_microunits=None,
        computational_cost=Band.MEDIUM,
        expected_latency_ms=None,
        failure_modes=("TO_VERIFY",),
        alternatives=alternatives,
        adoption=AdoptionStatus.CANDIDATE,
        reference=reference,
        scope_limitations=scope_limitations,
        adoption_blockers=blockers,
    )


SOURCES: tuple[SourceDescriptor, ...] = (
    SourceDescriptor(
        source_id="official-public-website",
        version="1",
        name="Organization's own public website",
        owner="The observed organization",
        capabilities=frozenset(
            {SourceCapability.CAPABILITY_DECLARATION, SourceCapability.DIGITAL_REPRESENTATION}
        ),
        jurisdictions=(TaxonomyCode("GLOBAL", "ANY"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset(),
        record_types=("public web page",),
        access_method=AccessMethod.CRAWL,
        authentication_required=False,
        rights=RightsStatus.REUSE_DOCUMENTED,
        reliability=Band.MEDIUM,
        precision=Band.LOW,
        coverage=Band.LOW,
        provenance_quality=Band.HIGH,
        structured=False,
        expected_change_interval=timedelta(days=30),
        historical_depth="current page only",
        cost_per_request_microunits=0,
        computational_cost=Band.LOW,
        expected_latency_ms=1_500,
        failure_modes=("unreachable host", "script-only rendering", "self-declared claims"),
        alternatives=("corporate registries",),
        adoption=AdoptionStatus.ADOPTED,
        reference="registered public homepage policy (FR-30 FirstProof)",
        scope_limitations=("A declaration is evidence of the claim, not of the capability.",),
    ),
    SourceDescriptor(
        source_id="ted-search-v3",
        version="1",
        name="Tenders Electronic Daily — Search API v3",
        owner="Publications Office of the European Union",
        capabilities=_PROCUREMENT,
        jurisdictions=(geo("EU"),),
        classification_systems=frozenset({"CPV"}),
        buyer_levels=frozenset(BuyerLevel),
        record_types=("cn-standard", "cn-social", "can-standard", "can-social"),
        access_method=AccessMethod.API,
        authentication_required=False,
        rights=RightsStatus.REUSE_DOCUMENTED,
        reliability=Band.HIGH,
        precision=Band.HIGH,
        coverage=Band.MEDIUM,
        provenance_quality=Band.HIGH,
        structured=True,
        expected_change_interval=timedelta(days=1),
        historical_depth="published notices, eForms and legacy archives",
        cost_per_request_microunits=0,
        computational_cost=Band.LOW,
        expected_latency_ms=2_000,
        failure_modes=(
            "timeout on broad queries",
            "multilingual free-text fields",
            "award data missing or partial per lot",
        ),
        alternatives=("es-placsp", "fr-boamp"),
        adoption=AdoptionStatus.ADOPTED,
        reference="https://docs.ted.europa.eu/api/latest/search.html",
        scope_limitations=(
            "Notices published on TED, mostly above EU thresholds; national and regional "
            "below-threshold tenders are outside its scope.",
        ),
    ),
    SourceDescriptor(
        source_id="es-placsp",
        version="1",
        name="Plataforma de Contratación del Sector Público — ATOM syndication",
        owner="Ministerio de Hacienda, Spain (Dirección General del Patrimonio del Estado)",
        # Open tenders only: an award history would need gigabytes of syndication.
        capabilities=frozenset({SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES}),
        jurisdictions=(geo("EU/ES"),),
        classification_systems=frozenset({"CPV"}),
        buyer_levels=frozenset(
            {BuyerLevel.NATIONAL_OR_FEDERAL, BuyerLevel.REGIONAL_OR_STATE, BuyerLevel.LOCAL}
        ),
        record_types=("PUB",),
        access_method=AccessMethod.FEED,
        authentication_required=False,
        # Ley 37/2007 and RD 1495/2011 art. 8: reuse of State documents under general
        # conditions (cite the source, do not distort, keep the update date).
        rights=RightsStatus.REUSE_DOCUMENTED,
        reliability=Band.HIGH,
        # Official structured CODICE: CPV per tender and lot, like TED.
        precision=Band.HIGH,
        coverage=Band.HIGH,
        provenance_quality=Band.HIGH,
        structured=True,
        expected_change_interval=timedelta(days=1),
        historical_depth="rolling syndication, about two days per page, newest first",
        cost_per_request_microunits=0,
        # Answered from the local index; the feed's weight is paid at ingestion only.
        computational_cost=Band.LOW,
        expected_latency_ms=3_000,
        failure_modes=(
            "large feed pages (about 14 MB)",
            "lot-level classifications only",
            "regional platforms only through the aggregation feed",
        ),
        alternatives=("ted-search-v3",),
        adoption=AdoptionStatus.ADOPTED,
        reference=(
            "https://www.hacienda.gob.es/es-ES/GobiernoAbierto/Datos%20Abiertos/Paginas/"
            "licitaciones_plataforma_contratacion.aspx"
        ),
        scope_limitations=(
            "Spanish public sector tenders hosted on the platform or aggregated from regional "
            "platforms; minor contracts are excluded. Read for the index, never per request.",
            "Only open tenders updated within the last 30 days are read (feed size); a tender "
            "open for longer without any update, such as a dynamic purchasing system, may be "
            "missing.",
        ),
    ),
    _candidate(
        source_id="fr-boamp",
        name="BOAMP open data",
        owner="Direction de l'information légale et administrative, France",
        capabilities=_PROCUREMENT,
        jurisdictions=(geo("EU/FR"),),
        classification_systems=frozenset({"CPV"}),
        buyer_levels=frozenset(
            {BuyerLevel.NATIONAL_OR_FEDERAL, BuyerLevel.REGIONAL_OR_STATE, BuyerLevel.LOCAL}
        ),
        record_types=("TO_VERIFY",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=1),
        reference="https://www.boamp.fr (open data)",
        blockers=("RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        alternatives=("ted-search-v3",),
    ),
    _candidate(
        source_id="us-sam-opportunities",
        name="SAM.gov Get Opportunities Public API v2",
        owner="U.S. General Services Administration",
        capabilities=_PROCUREMENT,
        jurisdictions=(geo("US"),),
        classification_systems=frozenset({"NAICS", "PSC"}),
        buyer_levels=frozenset({BuyerLevel.NATIONAL_OR_FEDERAL}),
        record_types=(
            "o solicitation",
            "k combined synopsis",
            "p presolicitation",
            "a award notice",
        ),
        access_method=AccessMethod.API,
        authentication_required=True,
        expected_change_interval=timedelta(days=1),
        reference="https://open.gsa.gov/api/get-opportunities-public-api/",
        blockers=("API_KEY_NOT_PROVISIONED", "RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=(
            "Federal opportunities only; state and local procurement is outside its scope.",
        ),
        alternatives=("us-usaspending-awards",),
    ),
    _candidate(
        source_id="us-usaspending-awards",
        name="USAspending API v2 (award search)",
        owner="U.S. Department of the Treasury",
        capabilities=frozenset({SourceCapability.PUBLIC_PROCUREMENT_AWARDS}),
        jurisdictions=(geo("US"),),
        classification_systems=frozenset({"NAICS", "PSC"}),
        buyer_levels=frozenset({BuyerLevel.NATIONAL_OR_FEDERAL}),
        record_types=("contract awards",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=7),
        reference="https://api.usaspending.gov/docs/endpoints",
        blockers=("RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=("Federal spending; reveals buyers and history, not open calls.",),
        alternatives=("us-sam-opportunities",),
    ),
    _candidate(
        source_id="fr-installations-classees",
        name="Installations classées (ICPE) public register",
        owner="Ministère de la Transition écologique, France",
        capabilities=frozenset({SourceCapability.PLANNING_AND_PERMITS}),
        jurisdictions=(geo("EU/FR"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset(),
        record_types=("regulated industrial installation",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=7),
        reference="Géorisques ICPE data",
        blockers=("RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=("Permits reveal regulated sites, not purchasing intent.",),
    ),
    _candidate(
        source_id="eu-funding-tenders-portal",
        name="EU Funding & Tenders Portal",
        owner="European Commission",
        capabilities=frozenset({SourceCapability.PUBLIC_FUNDING}),
        jurisdictions=(geo("EU"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset({BuyerLevel.SUPRANATIONAL}),
        record_types=("calls for proposals",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=7),
        reference="https://ec.europa.eu/info/funding-tenders/opportunities/portal",
        blockers=("RIGHTS_TO_VERIFY", "ACCESS_METHOD_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=("EU-managed programmes; national and regional schemes are outside.",),
    ),
    _candidate(
        source_id="es-bdns",
        name="Base de Datos Nacional de Subvenciones",
        owner="Intervención General de la Administración del Estado, Spain",
        capabilities=frozenset({SourceCapability.PUBLIC_FUNDING}),
        jurisdictions=(geo("EU/ES"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset(
            {BuyerLevel.NATIONAL_OR_FEDERAL, BuyerLevel.REGIONAL_OR_STATE, BuyerLevel.LOCAL}
        ),
        record_types=("calls", "concessions of grants"),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=1),
        reference="https://www.infosubvenciones.es (TO_VERIFY)",
        blockers=("RIGHTS_TO_VERIFY", "ACCESS_METHOD_TO_VERIFY", "ADAPTER_NOT_BUILT"),
    ),
)


_BY_ID = {entry.capability_id: entry for entry in CAPABILITY_LEXICON}


def with_current_codes(capability: Mapping[str, object]) -> Mapping[str, object]:
    """A stored capability with the catalog's current demand codes, when the catalog knows it.

    Observations copy the codes they were read with; a correction to the catalog (a code
    that matched unrelated demand) must reach every reading at once, not only new ones.
    """
    entry = _BY_ID.get(str(capability.get("capabilityId") or ""))
    if entry is None:
        return capability
    return {**capability, "demandCodes": [[c.scheme, c.code] for c in entry.demand_codes]}
