"""Countries a page reports an organization has entered (spec 107, Markets).

Deterministic and conservative, like reported revenue: a country counts only when the same
sentence names the organization, an expansion verb ("abre en", "enters", "s'implante en")
and the country, and the sentence is not about a plan, a target or a forecast. The home
country is never "entered". What a page reports is POTENTIAL, never a market confirmed.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

#: Country names (folded, lower case) in Spanish, English, French, German, Italian and
#: Portuguese, for the markets an agency's clients usually reach.
_NAMES: dict[str, tuple[str, ...]] = {
    "ES": ("espana", "spain", "espagne", "spanien", "spagna", "espanha"),
    "FR": ("francia", "france", "frankreich", "franca"),
    "DE": ("alemania", "germany", "allemagne", "deutschland", "germania", "alemanha"),
    "IT": ("italia", "italy", "italie", "italien"),
    "PT": ("portugal", "portogallo"),
    "GB": ("reino unido", "united kingdom", "royaume-uni", "grossbritannien", "regno unito", "uk"),
    "IE": ("irlanda", "ireland", "irlande", "irland"),
    "NL": (
        "paises bajos",
        "holanda",
        "netherlands",
        "pays-bas",
        "niederlande",
        "paesi bassi",
        "paises baixos",
    ),
    "BE": ("belgica", "belgium", "belgique", "belgien", "belgio"),
    "LU": ("luxemburgo", "luxembourg", "luxemburg", "lussemburgo"),
    "CH": ("suiza", "switzerland", "suisse", "schweiz", "svizzera", "suica"),
    "AT": ("austria", "autriche", "osterreich"),
    "DK": ("dinamarca", "denmark", "danemark", "danemark", "danimarca"),
    "SE": ("suecia", "sweden", "suede", "schweden", "svezia", "suecia"),
    "NO": ("noruega", "norway", "norvege", "norwegen", "norvegia"),
    "FI": ("finlandia", "finland", "finlande", "finnland"),
    "PL": ("polonia", "poland", "pologne", "polen", "polonia"),
    "CZ": ("chequia", "republica checa", "czech republic", "czechia", "tchequie", "tschechien"),
    "GR": ("grecia", "greece", "grece", "griechenland"),
    "US": (
        "estados unidos",
        "eeuu",
        "ee. uu",
        "united states",
        "usa",
        "etats-unis",
        "vereinigte staaten",
        "stati uniti",
        "estados unidos",
    ),
    "CA": ("canada", "kanada"),
    "MX": ("mexico", "mexique", "mexiko", "messico"),
    "BR": ("brasil", "brazil", "bresil", "brasilien", "brasile"),
    "AR": ("argentina", "argentine", "argentinien"),
    "CL": ("chile", "chili", "cile"),
    "CO": ("colombia", "colombie", "kolumbien"),
    "PE": ("peru", "perou"),
    "AU": ("australia", "australie", "australien"),
    "JP": ("japon", "japan", "giappone", "japao"),
    "CN": ("china", "chine", "cina"),
    "KR": ("corea del sur", "south korea", "coree du sud", "sudkorea", "corea del sud"),
    "IN": ("india", "inde", "indien"),
    "AE": ("emiratos arabes", "united arab emirates", "emirats arabes", "dubai"),
    "SA": ("arabia saudi", "saudi arabia", "arabie saoudite", "saudi-arabien"),
    "MA": ("marruecos", "morocco", "maroc", "marokko", "marocco"),
    "TR": ("turquia", "turkey", "turquie", "turkei", "turchia"),
}
_COUNTRY = re.compile(
    r"(?<![a-z])("
    + "|".join(sorted({re.escape(n) for ns in _NAMES.values() for n in ns}, key=len, reverse=True))
    + r")(?![a-z])"
)
_BY_NAME = {name: code for code, names in _NAMES.items() for name in names}
#: Entering a country, in the same six languages (folded).
_ENTER = re.compile(
    r"\b(abre|abrio|abrira|aterriza|desembarca|entra|entro|llega|llego|se expande|expande|"
    r"inaugura|inauguro|lanza|lanzo|opens?|opened|launch(es|ed)?|enters?|entered|expands?|"
    r"expanded|arrives?|arrived|debuts?|s.implante|ouvre|a ouvert|arrive|lance|debarque|"
    r"eroffnet|startet|expandiert|kommt nach|apre|ha aperto|sbarca|arriva|lancia|"
    r"inaugura|chega|abriu|entrou|lancou)\b",
    re.IGNORECASE,
)
#: Plans and forecasts are not an entry (same rule as reported revenue).
_NOT_DONE = re.compile(
    r"\b(preve|prevista|previsto|planea|planes?|plan de|proxim[oa]s?|aspira|objetivo|quiere|"
    r"espera|podria|plans? to|aims? to|will|would|could|intends?|expects?|next year|"
    r"prevoit|souhaite|plant|will|vorhaben|prevede|intende|pretende|vai)\b",
    re.IGNORECASE,
)
_SENTENCE = re.compile(r";|[.!?](?=\s|$)")
MAX_SENTENCE = 400


@dataclass(frozen=True, slots=True)
class ReportedEntry:
    countries: tuple[str, ...]
    excerpt: str


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def names_in(sentence: str, needles: Sequence[str]) -> bool:
    """Whether a folded sentence names one of the needles, word for word ("Bloom & Wild" names
    "bloom wild"), as the press index matches names."""
    words = " " + " ".join(re.findall(r"[a-z0-9]+", sentence.lower())) + " "
    return any(f" {needle} " in words for needle in needles)


def reported_entries(
    text: str, needles: Sequence[str], *, home: str | None
) -> ReportedEntry | None:
    """Countries a sentence naming the organization reports it has entered, or None."""
    found: list[str] = []
    excerpt = ""
    for sentence in (s.strip() for s in _SENTENCE.split(_fold(text[:200_000]))):
        lower = sentence.lower()
        if not sentence or len(sentence) > MAX_SENTENCE:
            continue
        if not names_in(lower, needles):
            continue
        if not _ENTER.search(lower) or _NOT_DONE.search(lower):
            continue
        countries = [_BY_NAME[m.group(1)] for m in _COUNTRY.finditer(lower)]
        new = [c for c in dict.fromkeys(countries) if c != home and c not in found]
        if new:
            found += new
            excerpt = excerpt or " ".join(sentence.split())
    return ReportedEntry(tuple(found), excerpt) if found else None
