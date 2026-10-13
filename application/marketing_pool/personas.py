"""Who AXIGNAL sells to, versioned: the buyer personas the pool searches for on its own.

From the approved Account-Based Pull strategy (docs/communication, 2026-10-08): agencies
and consultancies that can use AXIGNAL as independent, evidence-backed added value for
their clients. Each persona says where to find candidates (public, open registries), how to
recognise one on its own website, and which families of findings speak to it first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PERSONAS_VERSION = "personas-v3"
#: A persona needs at least this many distinct offer words on the site itself.
MIN_OFFER_WORDS = 2


@dataclass(frozen=True, slots=True)
class Persona:
    id: str
    label: str
    #: OpenStreetMap ``office=*`` values that list such organizations with a website.
    osm_offices: tuple[str, ...]
    #: Wikidata classes (P31) of such organizations.
    wikidata_classes: tuple[str, ...]
    #: Words that, on its own website, show it offers this (several languages).
    offer_words: tuple[str, ...]
    #: Families whose evidenced findings lead the message to this persona.
    lead_families: tuple[str, ...]
    #: What AXIGNAL could add for it, said once and without claiming its interest.
    value_angle: str
    #: Other OpenStreetMap selectors (tags that must all hold), e.g. private schools.
    osm_selectors: tuple[str, ...] = ()

    def overpass_selectors(self) -> tuple[str, ...]:
        return (*(f'["office"="{o}"]' for o in self.osm_offices), *self.osm_selectors)


PERSONAS: tuple[Persona, ...] = (
    Persona(
        "SEO_GEO_AGENCY",
        "SEO / GEO / AI-search agency",
        ("advertising_agency",),
        ("Q1369723", "Q4048723"),
        (
            "seo",
            "posicionamiento",
            "suchmaschinenoptimierung",
            "référencement",
            "referenciamento",
            "posizionamento",
            "search engine",
            "geo",
            "aeo",
            "ai search",
            "generative engine",
            "llm",
            "chatgpt",
        ),
        ("presence", "reputation", "relationships"),
        "independent, repeatable measurement of how search engines and AI assistants "
        "represent each client, before and after their work",
    ),
    Persona(
        "DIGITAL_MARKETING_AGENCY",
        "Digital marketing / growth agency",
        ("advertising_agency",),
        ("Q1369723", "Q216931"),
        (
            "marketing digital",
            "digital marketing",
            "online marketing",
            "growth marketing",
            "performance marketing",
            "paid media",
            "social media",
            "inbound",
            "agence digitale",
            "agenzia digitale",
            "werbeagentur",
            "agencia de marketing",
            "agência de marketing",
            "marketing agency",
            "digital agency",
            "web agency",
            "agence web",
            "agence marketing",
            "agencia web",
            "agencia digital",
            "webagentur",
            "digitalagentur",
            "content marketing",
            "branding",
            "e-commerce",
            "agence de communication",
            "agenzia di comunicazione",
        ),
        ("presence", "demand", "markets"),
        "an outside-in reading of each client's markets, demand and digital presence, "
        "with the evidence behind every finding",
    ),
    Persona(
        "REPUTATION_PR_AGENCY",
        "Reputation / PR agency",
        ("advertising_agency", "consulting"),
        ("Q12043474",),
        (
            "reputación",
            "reputation",
            "relaciones públicas",
            "public relations",
            "comunicación corporativa",
            "relations presse",
            "relazioni pubbliche",
            "öffentlichkeitsarbeit",
            "pr agency",
            "agencia de comunicación",
        ),
        ("reputation", "presence", "context"),
        "a continuous, sourced view of what is said publicly about each client and how "
        "AI assistants describe it",
    ),
    Persona(
        "B2B_CONSULTANCY",
        "B2B strategy consultancy",
        ("consulting",),
        ("Q2089936", "Q122229703"),
        (
            "consultoría",
            "consulting",
            "beratung",
            "conseil",
            "consulenza",
            "consultoria",
            "management consulting",
            "consultora estratégica",
            "go-to-market",
            "internacionalización",
            "market entry",
            "business development",
        ),
        ("demand", "relationships", "economics"),
        "evidence-backed outside-in intelligence on each client's demand, relationships "
        "and competitors, refreshed over time",
    ),
)


PERSONAS = (
    *PERSONAS,
    Persona(
        "CONSTRUCTION",
        "Construction / installation company",
        ("construction_company",),
        ("Q811930",),
        (
            "constructora",
            "construcción",
            "construcciones",
            "obra civil",
            "edificación",
            "rehabilitación",
            "reformas integrales",
            "construction company",
            "general contractor",
            "building contractor",
            "civil engineering",
            "bauunternehmen",
            "hochbau",
            "tiefbau",
            "entreprise de construction",
            "bâtiment",
            "travaux publics",
            "impresa edile",
            "costruzioni",
            "construtora",
            "empreiteiro",
        ),
        ("demand", "relationships", "economics"),
        "who awards its kind of works near it, what is open now and who wins it, refreshed "
        "every day from official sources",
    ),
    Persona(
        "PRIVATE_SCHOOL",
        "Private school or academy",
        (),
        ("Q423208", "Q572835", "Q897403"),
        (
            "colegio privado",
            "colegio internacional",
            "escuela infantil",
            "academia",
            "bachillerato internacional",
            "admisiones",
            "matrícula",
            "private school",
            "international school",
            "admissions",
            "enrolment",
            "enrollment",
            "école privée",
            "inscriptions",
            "privatschule",
            "internationale schule",
            "scuola privata",
            "iscrizioni",
            "escola privada",
            "matrículas",
        ),
        ("presence", "reputation", "context"),
        "how families find it on search engines and AI assistants, and what is said about "
        "it, measured independently over time",
        osm_selectors=(
            '["amenity"="school"]["operator:type"="private"]',
            '["amenity"="language_school"]',
        ),
    ),
)


def persona(persona_id: str) -> Persona | None:
    return next((p for p in PERSONAS if p.id == persona_id), None)


def persona_fit(text: str, candidate: Persona) -> tuple[str, ...]:
    """The persona's offer words its own site states (whole words, case-insensitive)."""
    lowered = f" {text.lower()} "
    return tuple(
        word
        for word in candidate.offer_words
        if re.search(r"(?<![\w])" + re.escape(word) + r"(?![\w])", lowered)
    )


def best_persona(text: str, hint: str | None) -> tuple[Persona | None, tuple[str, ...]]:
    """The persona its own site supports best.

    The hint is the persona of the open registry class it was found under (a declared
    organization type): with it, one offer word on its own site suffices; otherwise two.
    """
    ranked = sorted(
        ((len(persona_fit(text, p)), p.id == hint, p) for p in PERSONAS),
        key=lambda row: (row[0], row[1]),
        reverse=True,
    )
    for hits, hinted, chosen in ranked:
        if hits >= MIN_OFFER_WORDS or (hinted and hits >= 1):
            return chosen, persona_fit(text, chosen)
    return None, ()
