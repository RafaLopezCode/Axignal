"""Code declared places into AXIGNAL's jurisdiction tree (governed data, no inference).

Only exact matches of a declared value (ISO 3166 code or a listed name) are coded; any
other value stays as uncoded text. Coding a place says *where to look*, never where an
organization operates (ADR-0091 §4).
"""

from __future__ import annotations

import re
import unicodedata

from application.observation_intelligence.catalog import eu_nuts
from application.observation_intelligence.contracts import TaxonomyCode, geo

GEOGRAPHY_VERSION = "declared-place-coding.v1"

#: ISO 3166-1 alpha-2 of EU member states → NUTS country code (Greece is EL in NUTS).
EU_MEMBERS: dict[str, str] = {
    code: ("EL" if code == "GR" else code)
    for code in (
        "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "GR", "ES", "FI", "FR", "HR", "HU",
        "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    )
}  # fmt: skip

#: Country names as commonly declared (en / native / es / fr / de / it / pt) → ISO alpha-2.
_COUNTRY_NAMES: dict[str, str] = {
    **dict.fromkeys(["austria", "osterreich", "autriche"], "AT"),
    **dict.fromkeys(["belgium", "belgique", "belgie", "belgica"], "BE"),
    **dict.fromkeys(["bulgaria", "bulgarie"], "BG"),
    **dict.fromkeys(["cyprus", "chipre", "chypre"], "CY"),
    **dict.fromkeys(["czechia", "czech republic", "cesko", "republica checa"], "CZ"),
    **dict.fromkeys(["germany", "deutschland", "alemania", "allemagne", "germania", "alemanha"], "DE"),
    **dict.fromkeys(["denmark", "danmark", "dinamarca", "danemark"], "DK"),
    **dict.fromkeys(["estonia", "eesti", "estonie"], "EE"),
    **dict.fromkeys(["greece", "hellas", "grecia", "grece"], "GR"),
    **dict.fromkeys(["spain", "espana", "espagne", "spanien", "spagna", "espanha"], "ES"),
    **dict.fromkeys(["finland", "suomi", "finlandia", "finlande"], "FI"),
    **dict.fromkeys(["france", "francia", "frankreich", "franca"], "FR"),
    **dict.fromkeys(["croatia", "hrvatska", "croacia", "croatie"], "HR"),
    **dict.fromkeys(["hungary", "magyarorszag", "hungria", "hongrie"], "HU"),
    **dict.fromkeys(["ireland", "eire", "irlanda", "irlande"], "IE"),
    **dict.fromkeys(["italy", "italia", "italie", "italien"], "IT"),
    **dict.fromkeys(["lithuania", "lietuva", "lituania", "lituanie"], "LT"),
    **dict.fromkeys(["luxembourg", "luxemburgo", "luxemburg", "lussemburgo"], "LU"),
    **dict.fromkeys(["latvia", "latvija", "letonia", "lettonie"], "LV"),
    **dict.fromkeys(["malta", "malte"], "MT"),
    **dict.fromkeys(["netherlands", "nederland", "the netherlands", "paises bajos", "pays-bas"], "NL"),
    **dict.fromkeys(["poland", "polska", "polonia", "pologne"], "PL"),
    **dict.fromkeys(["portugal"], "PT"),
    **dict.fromkeys(["romania", "rumania", "roumanie"], "RO"),
    **dict.fromkeys(["sweden", "sverige", "suecia", "suede"], "SE"),
    **dict.fromkeys(["slovenia", "slovenija", "eslovenia", "slovenie"], "SI"),
    **dict.fromkeys(["slovakia", "slovensko", "eslovaquia", "slovaquie"], "SK"),
    **dict.fromkeys(
        ["united states", "united states of america", "usa", "u.s.", "u.s.a.", "estados unidos",
         "etats-unis", "vereinigte staaten", "stati uniti"],
        "US",
    ),
    **dict.fromkeys(["united kingdom", "uk", "great britain", "reino unido", "royaume-uni"], "GB"),
    **dict.fromkeys(["switzerland", "schweiz", "suisse", "svizzera", "suiza"], "CH"),
    **dict.fromkeys(["norway", "norge", "noruega", "norvege"], "NO"),
    **dict.fromkeys(["canada", "canada"], "CA"),
    **dict.fromkeys(["mexico"], "MX"),
    **dict.fromkeys(["brazil", "brasil", "bresil"], "BR"),
    **dict.fromkeys(["argentina", "argentine"], "AR"),
    **dict.fromkeys(["chile", "chili"], "CL"),
    **dict.fromkeys(["colombia", "colombie"], "CO"),
    **dict.fromkeys(["japan", "japon", "nippon", "日本"], "JP"),
    **dict.fromkeys(["china", "chine", "中国"], "CN"),
    **dict.fromkeys(["india", "inde"], "IN"),
    **dict.fromkeys(["australia", "australie"], "AU"),
}  # fmt: skip

_US_STATES: dict[str, str] = {
    "AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas", "CA": "california",
    "CO": "colorado", "CT": "connecticut", "DE": "delaware", "DC": "district of columbia",
    "FL": "florida", "GA": "georgia", "HI": "hawaii", "ID": "idaho", "IL": "illinois",
    "IN": "indiana", "IA": "iowa", "KS": "kansas", "KY": "kentucky", "LA": "louisiana",
    "ME": "maine", "MD": "maryland", "MA": "massachusetts", "MI": "michigan",
    "MN": "minnesota", "MS": "mississippi", "MO": "missouri", "MT": "montana",
    "NE": "nebraska", "NV": "nevada", "NH": "new hampshire", "NJ": "new jersey",
    "NM": "new mexico", "NY": "new york", "NC": "north carolina", "ND": "north dakota",
    "OH": "ohio", "OK": "oklahoma", "OR": "oregon", "PA": "pennsylvania",
    "RI": "rhode island", "SC": "south carolina", "SD": "south dakota", "TN": "tennessee",
    "TX": "texas", "UT": "utah", "VT": "vermont", "VA": "virginia", "WA": "washington",
    "WV": "west virginia", "WI": "wisconsin", "WY": "wyoming",
}  # fmt: skip
_US_STATE_NAMES = {name: code for code, name in _US_STATES.items()}


def _fold(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.strip().casefold())
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


def country_code(value: str | None) -> str | None:
    """ISO alpha-2 for an exact declared code or listed name; otherwise None (UNKNOWN)."""
    if value is None or not value.strip():
        return None
    raw = value.strip()
    if len(raw) == 2 and raw.isalpha():
        return {"UK": "GB", "EL": "GR"}.get(raw.upper(), raw.upper())
    if len(raw) == 3 and raw.upper() in {"USA", "ESP", "FRA", "DEU", "ITA", "PRT", "GBR"}:
        return {"USA": "US", "ESP": "ES", "FRA": "FR", "DEU": "DE", "ITA": "IT",
                "PRT": "PT", "GBR": "GB"}[raw.upper()]  # fmt: skip
    return _COUNTRY_NAMES.get(_fold(raw))


def us_state(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    raw = value.strip()
    if raw.upper() in _US_STATES:
        return raw.upper()
    if raw.upper().startswith("US-") and raw.upper()[3:] in _US_STATES:
        return raw.upper()[3:]
    return _US_STATE_NAMES.get(_fold(raw))


def jurisdiction(country: str | None, region: str | None = None) -> TaxonomyCode | None:
    """Jurisdiction path for a declared country (and, for the US, state)."""
    code = country_code(country)
    if code is None:  # a region without its country is not coded (no inference)
        return None
    if code in EU_MEMBERS:
        return geo(f"EU/{EU_MEMBERS[code]}")
    if code == "US":
        state = us_state(region)
        return geo(f"US/US-{state}") if state else geo("US")
    return geo(code)


def mentioned_places(text: str, *, limit: int = 12) -> tuple[tuple[TaxonomyCode, str], ...]:
    """Listed country / US-state names mentioned in ``text`` (whole words), in order.

    A mention is not a location: it only proposes candidates a judgment may confirm.
    """
    folded = " " + " ".join(re.split(r"[^\w]+", _fold(text))) + " "
    found: dict[str, tuple[TaxonomyCode, str]] = {}
    names = [
        (name, code, False)
        for name, code in _COUNTRY_NAMES.items()
        if len(name) > 3 and re.fullmatch(r"[\w ]+", name)
    ]
    names += [(name, code, True) for name, code in _US_STATE_NAMES.items()]
    hits: list[tuple[int, TaxonomyCode, str]] = []
    for name, code, is_state in names:
        index = folded.find(f" {name} ")
        if index < 0:
            continue
        place = geo(f"US/US-{code}") if is_state else jurisdiction(code)
        if place is not None:
            hits.append((index, place, name))
    for _index, place, name in sorted(hits, key=lambda hit: hit[0]):
        found.setdefault(place.code, (place, name))
    return tuple(found.values())[:limit]


def area_jurisdiction(name: str | None, nuts: str | None) -> TaxonomyCode | None:
    """A declared service area: exact NUTS identifier, country or US state name."""
    if nuts:
        return eu_nuts(nuts)
    if name is None:
        return None
    code = jurisdiction(name)
    if code is not None:
        return code
    state = us_state(name)
    return geo(f"US/US-{state}") if state else None


def place_words() -> frozenset[str]:
    """Casefolded words of every listed country and US-state name (minimization allowlist)."""
    words: set[str] = set()
    for name in (*_COUNTRY_NAMES, *_US_STATE_NAMES):
        words.update(name.split())
    return frozenset(words)
