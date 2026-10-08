"""Governed place gazetteer: surface names → jurisdiction paths (NUTS 2021 / ISO).

Data, not semantics: it only says which jurisdiction a written place name denotes so a
stated area can be compared with where demand happens (``TaxonomyCode.within``). It
never says that a business serves a place. Demonyms are deliberately absent
("empresa valenciana" states origin, not reach). Extend by version, never by guess.
"""

from __future__ import annotations

import re
import unicodedata

from application.observation_intelligence.catalog import eu_nuts
from application.observation_intelligence.contracts import TaxonomyCode, geo

GAZETTEER_VERSION = "places:2026-10-08"

_PLACES: dict[str, TaxonomyCode] = {
    # Supranational and countries
    "europa": geo("EU"),
    "europe": geo("EU"),
    "union europea": geo("EU"),
    "european union": geo("EU"),
    "espana": geo("EU/ES"),
    "spain": geo("EU/ES"),
    "portugal": geo("EU/PT"),
    "francia": geo("EU/FR"),
    "france": geo("EU/FR"),
    "alemania": geo("EU/DE"),
    "germany": geo("EU/DE"),
    "italia": geo("EU/IT"),
    "italy": geo("EU/IT"),
    # Spanish regions and provinces (NUTS 2021)
    "comunidad de madrid": eu_nuts("ES30"),
    "madrid": eu_nuts("ES30"),
    "castilla-la mancha": eu_nuts("ES42"),
    "toledo": eu_nuts("ES425"),
    "guadalajara": eu_nuts("ES424"),
    "comunidad valenciana": eu_nuts("ES52"),
    "comunitat valenciana": eu_nuts("ES52"),
    "levante": eu_nuts("ES52"),
    "valencia": eu_nuts("ES523"),
    "alicante": eu_nuts("ES521"),
    "castellon": eu_nuts("ES522"),
    "cataluna": eu_nuts("ES51"),
    "barcelona": eu_nuts("ES511"),
    "andalucia": eu_nuts("ES61"),
    "sevilla": eu_nuts("ES618"),
    "malaga": eu_nuts("ES617"),
    "zaragoza": eu_nuts("ES243"),
    "bizkaia": eu_nuts("ES213"),
    "bilbao": eu_nuts("ES213"),
    "murcia": eu_nuts("ES62"),
    "canarias": eu_nuts("ES70"),
    "islas canarias": eu_nuts("ES70"),
    # A few non-Spanish cities used in public demand
    "hamburgo": eu_nuts("DE600"),
    "hamburg": eu_nuts("DE600"),
    "berlin": eu_nuts("DE300"),
    "lisboa": eu_nuts("PT170"),
    "lisbon": eu_nuts("PT170"),
    "paris": eu_nuts("FR101"),
}


def normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    return "".join(c for c in stripped if not unicodedata.combining(c)).casefold()


_PATTERN = re.compile(
    r"(?<![\w-])("
    + "|".join(re.escape(name) for name in sorted(_PLACES, key=len, reverse=True))
    + r")(?![\w-])"
)


def find_places(text: str) -> tuple[tuple[int, TaxonomyCode], ...]:
    """(position, jurisdiction) for every whole-word place name, longest name first."""
    return tuple(
        (match.start(), _PLACES[match.group(1)]) for match in _PATTERN.finditer(normalize(text))
    )


# Display names for the jurisdictions above, for people (accents and official forms).
# Presentation data only: it never decides reach and covers exactly the gazetteer.
_DISPLAY: dict[str, str] = {
    "EU": "Unión Europea",
    "EU/ES": "España",
    "EU/PT": "Portugal",
    "EU/FR": "Francia",
    "EU/DE": "Alemania",
    "EU/IT": "Italia",
    **{
        eu_nuts(code).code: name
        for code, name in (
            ("ES30", "Comunidad de Madrid"),
            ("ES42", "Castilla-La Mancha"),
            ("ES425", "Toledo"),
            ("ES424", "Guadalajara"),
            ("ES52", "Comunitat Valenciana"),
            ("ES523", "Valencia"),
            ("ES521", "Alicante"),
            ("ES522", "Castellón"),
            ("ES51", "Cataluña"),
            ("ES511", "Barcelona"),
            ("ES61", "Andalucía"),
            ("ES618", "Sevilla"),
            ("ES617", "Málaga"),
            ("ES243", "Zaragoza"),
            ("ES213", "Bizkaia"),
            ("ES62", "Región de Murcia"),
            ("ES70", "Canarias"),
            ("DE600", "Hamburgo"),
            ("DE300", "Berlín"),
            ("PT170", "Lisboa"),
            ("FR101", "París"),
        )
    },
}


def place_label(path: str) -> str | None:
    """Human name of a gazetteer jurisdiction; None (unknown), never a guessed name."""
    return _DISPLAY.get(path)
