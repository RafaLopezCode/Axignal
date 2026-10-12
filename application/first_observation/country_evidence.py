"""Home country from independent signals the website itself publishes.

A website that does not declare a postal address in structured data still says where it
is in other ways: its country-code domain, the region of its declared language, its
telephone prefix, a national tax identifier, a postal code beside the country's name.
One signal proves little (a ``.es`` domain can be a brand; a ``+34`` number can be a
branch). Two independent signals pointing to the same country are kept as a POTENTIAL
attention scope with every signal cited. It starts where to look for demand; it never
defines the organization's market, its reach or where it operates.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import urlsplit

from application.first_observation.geography import jurisdiction
from application.first_observation.site import PageReading
from application.observation_intelligence.contracts import TaxonomyCode

#: Countries whose signals are recognized: domain, phone prefix, names, tax-id and
#: postal-code patterns. Bounded on purpose: only where demand sources are adopted or near.
_COUNTRIES: dict[str, dict[str, object]] = {
    "ES": {
        "tld": "es", "phone": "34", "names": ("españa", "spain", "espagne", "spanien"),
        "tax": r"\b(?:CIF|NIF)[:\s]*[A-HJ-NP-SUVW]\d{7}[0-9A-J]\b",
        "postal": r"\b(?:0[1-9]|[1-4]\d|5[0-2])\d{3}\b",
    },
    "PT": {
        "tld": "pt", "phone": "351", "names": ("portugal",),
        "tax": r"\bNIPC[:\s]*\d{9}\b", "postal": r"\b\d{4}-\d{3}\b",
    },
    "FR": {
        "tld": "fr", "phone": "33", "names": ("france", "francia"),
        "tax": r"\bSIRE[NT][:\s]*\d{3}\s?\d{3}\s?\d{3}", "postal": r"\b\d{5}\b",
    },
    "IT": {
        "tld": "it", "phone": "39", "names": ("italia", "italy"),
        "tax": r"\bP\.?\s?IVA[:\s]*\d{11}\b", "postal": r"\b\d{5}\b",
    },
    "DE": {
        "tld": "de", "phone": "49", "names": ("deutschland", "germany", "alemania"),
        "tax": r"\bUSt-?IdNr\.?[:\s]*DE\d{9}\b", "postal": r"\b\d{5}\b",
    },
}  # fmt: skip


@dataclass(frozen=True, slots=True)
class CountrySignal:
    kind: str  # DOMAIN | LANGUAGE_REGION | PHONE_PREFIX | TAX_IDENTIFIER | POSTAL_AND_NAME
    value: str
    page_url: str


@dataclass(frozen=True, slots=True)
class CountryEvidence:
    country: str
    scope: TaxonomyCode
    signals: tuple[CountrySignal, ...]


def _line_with(text: str, start: int) -> str:
    begin = text.rfind("\n", 0, start) + 1
    end = text.find("\n", start)
    return text[begin : end if end >= 0 else len(text)].strip()[:200]


def country_evidence(pages: Sequence[PageReading]) -> CountryEvidence | None:
    """The single country at least two independent signals point to, or None."""
    if not pages:
        return None
    found: dict[str, dict[str, CountrySignal]] = {}

    def add(country: str, signal: CountrySignal) -> None:
        found.setdefault(country, {}).setdefault(signal.kind, signal)

    home = pages[0]
    host = (urlsplit(home.url).hostname or "").lower()
    for country, rule in _COUNTRIES.items():
        if host.endswith("." + str(rule["tld"])):
            add(country, CountrySignal("DOMAIN", host, home.url))
    for page in pages:
        language = (page.language or "").replace("_", "-").upper()
        if "-" in language and language.split("-")[-1] in _COUNTRIES:
            add(language.split("-")[-1], CountrySignal("LANGUAGE_REGION", language, page.url))
        text = page.text
        lowered = text.lower()
        for country, rule in _COUNTRIES.items():
            phone = re.search(rf"(?:\+|\b00){rule['phone']}[\s.-]?\d", text)
            if phone:
                add(
                    country,
                    CountrySignal("PHONE_PREFIX", _line_with(text, phone.start()), page.url),
                )
            tax = re.search(str(rule["tax"]), text, re.IGNORECASE)
            if tax:
                add(
                    country,
                    CountrySignal("TAX_IDENTIFIER", _line_with(text, tax.start()), page.url),
                )
            for name in rule["names"]:  # type: ignore[attr-defined]
                at = lowered.find(str(name))
                if at < 0:
                    continue
                line = _line_with(text, at)
                if re.search(str(rule["postal"]), line):
                    add(country, CountrySignal("POSTAL_AND_NAME", line, page.url))
                    break
    supported = {c: s for c, s in found.items() if len(s) >= 2}
    if len(supported) != 1:
        return None  # no country, or conflicting countries: nothing is guessed
    ((country, signals),) = supported.items()
    scope = jurisdiction(country)
    if scope is None:
        return None
    return CountryEvidence(country, scope, tuple(signals.values()))
