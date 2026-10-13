"""Sector vocabulary for activities known only by their ISIC section.

An activity established by the semantic judgment (``isic-P``) or by the official register
(NACE/NAF/SIC classes) has no lexicon entry, so regulation and sector context found
nothing for it. These phrases, folded and multilingual, name each section the way
official journal titles and sector headlines do. Phrases are precise (several words);
keywords are single words of at least seven letters, for headlines only.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

#: ISIC Rev.4 / NACE Rev.2 division -> section (they share divisions).
_DIVISIONS: tuple[tuple[int, int, str], ...] = (
    (1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (41, 43, "F"),
    (45, 47, "G"), (49, 53, "H"), (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"),
    (69, 75, "M"), (77, 82, "N"), (84, 84, "O"), (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"),
    (94, 96, "S"),
)  # fmt: skip

SECTIONS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    # section: (label, phrases for journal titles, keywords for headlines)
    "A": (
        "Agriculture",
        (
            "politica agricola",
            "explotaciones agrarias",
            "sector agrario",
            "agricultural holdings",
            "common agricultural policy",
            "landwirtschaftliche betriebe",
            "exploitations agricoles",
        ),
        ("agricultura", "agriculture", "landwirtschaft", "agricole", "ganaderia"),
    ),
    "C": (
        "Manufacturing",
        (
            "productos industriales",
            "seguridad industrial",
            "industrial emissions",
            "product safety",
            "machinery regulation",
            "produktsicherheit",
            "securite des produits",
        ),
        ("industria", "manufacturing", "fabricacion", "industrie", "fabricants"),
    ),
    "D": (
        "Energy",
        (
            "sector electrico",
            "energia electrica",
            "energias renovables",
            "autoconsumo",
            "electricity market",
            "renewable energy",
            "erneuerbare energien",
            "energies renouvelables",
        ),
        ("electricidad", "electricity", "renovables", "renewable", "energiewende"),
    ),
    "F": (
        "Construction",
        (
            "codigo tecnico de la edificacion",
            "contratos del sector publico",
            "obras de construccion",
            "building regulations",
            "construction products",
            "bauprodukte",
            "batiment et travaux",
        ),
        ("construccion", "construction", "edificacion", "vivienda", "baugewerbe"),
    ),
    "G": (
        "Retail and wholesale",
        (
            "comercio minorista",
            "comercio electronico",
            "consumer protection",
            "derechos de los consumidores",
            "e-commerce",
            "verbraucherschutz",
            "protection des consommateurs",
        ),
        ("comercio", "retailers", "consumidores", "consumers", "minoristas"),
    ),
    "H": (
        "Transport and logistics",
        (
            "transporte por carretera",
            "transporte de mercancias",
            "road transport",
            "carriage of goods",
            "gueterverkehr",
            "transport routier",
        ),
        ("transporte", "logistica", "logistics", "transport", "mercancias"),
    ),
    "I": (
        "Hospitality",
        (
            "viviendas de uso turistico",
            "establecimientos hoteleros",
            "short-term rentals",
            "package travel",
            "tourist accommodation",
            "hebergement touristique",
        ),
        ("turismo", "tourism", "hosteleria", "hospitality", "hoteles"),
    ),
    "J": (
        "Information and communication",
        (
            "servicios digitales",
            "inteligencia artificial",
            "proteccion de datos",
            "telecomunicaciones",
            "digital services",
            "artificial intelligence",
            "data protection",
            "cybersecurity",
            "ciberseguridad",
            "kuenstliche intelligenz",
            "services numeriques",
        ),
        ("software", "digital", "ciberseguridad", "cybersecurity", "telecomunicaciones"),
    ),
    "K": (
        "Finance and insurance",
        (
            "servicios de pago",
            "entidades de credito",
            "entidades aseguradoras",
            "payment services",
            "credit institutions",
            "anti-money laundering",
            "blanqueo de capitales",
            "zahlungsdienste",
            "services de paiement",
            "markets in crypto-assets",
        ),
        ("bancos", "banking", "pagos", "payments", "seguros", "insurance", "fintech"),
    ),
    "L": (
        "Real estate",
        (
            "mercado inmobiliario",
            "arrendamientos urbanos",
            "ley de vivienda",
            "residential tenancies",
            "mietrecht",
            "baux d'habitation",
        ),
        ("vivienda", "inmobiliario", "housing", "alquiler", "property"),
    ),
    "M": (
        "Professional services",
        (
            "auditoria de cuentas",
            "servicios profesionales",
            "colegios profesionales",
            "professional services",
            "statutory audit",
            "advertising standards",
            "publicidad enganosa",
            "werbung",
            "publicite",
        ),
        ("consultoria", "consulting", "publicidad", "advertising", "auditoria"),
    ),
    "N": (
        "Business support services",
        (
            "seguridad privada",
            "empresas de trabajo temporal",
            "private security",
            "temporary agency work",
            "arbeitnehmerueberlassung",
            "securite privee",
        ),
        ("seguridad", "vigilancia", "limpieza", "outsourcing", "temporal"),
    ),
    "P": (
        "Education",
        (
            "centros educativos",
            "centros docentes",
            "ensenanza privada",
            "educacion infantil",
            "formacion profesional",
            "curriculo",
            "school standards",
            "independent schools",
            "higher education",
            "bildungswesen",
            "etablissements d'enseignement",
        ),
        ("educacion", "education", "colegios", "schools", "ensenanza", "alumnos", "students"),
    ),
    "Q": (
        "Health",
        (
            "productos sanitarios",
            "centros sanitarios",
            "medical devices",
            "health services",
            "medizinprodukte",
            "dispositifs medicaux",
            "medicamentos",
        ),
        ("sanidad", "health", "sanitario", "healthcare", "pacientes"),
    ),
    "R": (
        "Arts and recreation",
        (
            "espectaculos publicos",
            "propiedad intelectual",
            "juego online",
            "copyright",
            "gambling",
            "urheberrecht",
        ),
        ("cultura", "culture", "espectaculos", "gambling", "deportes"),
    ),
}


def section_of(classification: str) -> str | None:
    """The ISIC section of a register class ("NACE 64.190", "NAF 70.22Z", "SIC 73110")."""
    found = re.search(r"(\d{2})", classification)
    if found is None:
        return None
    division = int(found.group(1))
    return next((s for low, high, s in _DIVISIONS if low <= division <= high), None)


#: Words of an industry label (Wikidata P452, English labels) -> ISIC section.
_INDUSTRY_WORDS: tuple[tuple[str, str], ...] = (
    ("software", "J"), ("internet", "J"), ("telecommunication", "J"), ("information technology", "J"),
    ("media", "J"), ("publishing", "J"), ("video game", "J"), ("insurance", "K"), ("bank", "K"),
    ("financial", "K"), ("payment", "K"), ("fintech", "K"), ("investment", "K"),
    ("construction", "F"), ("civil engineering", "F"), ("real estate", "L"), ("retail", "G"),
    ("wholesale", "G"), ("e-commerce", "G"), ("advertising", "M"), ("marketing", "M"),
    ("consulting", "M"), ("architecture", "M"), ("legal", "M"), ("accounting", "M"),
    ("research", "M"), ("engineering", "C"), ("manufactur", "C"), ("machine", "C"),
    ("automotive", "C"), ("chemical", "C"), ("pharmaceutical", "C"), ("steel", "C"),
    ("building material", "C"), ("energy", "D"), ("electric", "D"), ("utility", "D"),
    ("transport", "H"), ("logistic", "H"), ("airline", "H"), ("shipping", "H"),
    ("hospitality", "I"), ("hotel", "I"), ("restaurant", "I"), ("education", "P"),
    ("school", "P"), ("health", "Q"), ("hospital", "Q"), ("medical", "Q"),
    ("security", "N"), ("staffing", "N"), ("cleaning", "N"), ("agricultur", "A"),
    ("mining", "B"), ("oil and gas", "B"), ("entertainment", "R"), ("sport", "R"),
)  # fmt: skip


def section_of_label(label: str) -> str | None:
    """The ISIC section an industry label names, by its words; None when it is unclear."""
    folded = label.casefold()
    return next((section for word, section in _INDUSTRY_WORDS if word in folded), None)


def route_of(discovery: Mapping[str, Any]) -> str | None:
    """The routing code of an ACTIVITY finding: its capability, or ``isic-<section>``."""
    code = str(discovery.get("code") or "")
    if code == "STATED_INDUSTRY":
        detail = discovery.get("detail")
        section = detail.get("isicSection") if isinstance(detail, Mapping) else None
        return f"isic-{section}" if isinstance(section, str) and section else None
    if code == "REGISTERED_ACTIVITY":
        detail = discovery.get("detail")
        classification = detail.get("classification") if isinstance(detail, Mapping) else None
        section = section_of(str(classification or ""))
        return f"isic-{section}" if section else None
    return code or None


def isic_section(capability_id: str) -> str | None:
    return capability_id[5:] if capability_id.startswith("isic-") else None


def section_phrases(capability_id: str) -> tuple[str, ...]:
    entry = SECTIONS.get(isic_section(capability_id) or "")
    return () if entry is None else tuple(sorted(entry[1]))


def section_keywords(capability_id: str) -> tuple[str, ...]:
    entry = SECTIONS.get(isic_section(capability_id) or "")
    return () if entry is None else tuple(sorted(entry[2]))


def section_label(capability_id: str) -> str | None:
    entry = SECTIONS.get(isic_section(capability_id) or "")
    return None if entry is None else entry[0]
