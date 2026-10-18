"""The countries an organization's website addresses its own versions to (Markets, spec 096).

Sites that sell or serve in several countries publish a version per country: alternate
language-region tags (``hreflang="fr-FR"``), country paths (``/es-es/``, ``/en_gb/``) and
country domains of the same brand (``brand.de``). Together they say where it declares it
serves: DECLARED by the site, never proof of sales there. A language alone ("en", "es")
names no country and is never read as one.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from urllib.parse import urlsplit

#: ISO 3166-1 alpha-2 codes a locale may carry (Eurostat-style EL/UK are normalised).
_ALIASES = {"UK": "GB", "EL": "GR"}
_NOT_COUNTRIES = {"EU", "UN", "XX", "ZZ", "AA", "QO", "XK"}
_LOCALE = re.compile(r"^[a-z]{2,3}[-_]([a-z]{2})$", re.IGNORECASE)
_PATH = re.compile(r"^/([a-z]{2}[-_][a-z]{2})(?:/|$)", re.IGNORECASE)
#: Country-code top-level domains that are country markets (not generic ".co", ".io", ".me", ".tv").
_CCTLD_GENERIC = {"co", "io", "me", "tv", "ai", "ly", "fm", "to", "cc", "ws", "gg", "sh", "app"}


def _country(code: str) -> str | None:
    value = _ALIASES.get(code.upper(), code.upper())
    return value if len(value) == 2 and value.isalpha() and value not in _NOT_COUNTRIES else None


def _brand(host: str) -> str:
    labels = host.lower().removeprefix("www.").split(".")
    return (
        labels[-3]
        if len(labels) >= 3 and labels[-2] in {"co", "com"}
        else labels[-2]
        if len(labels) >= 2
        else host
    )


def versions_for_countries(
    home_url: str, hreflang: Sequence[str], alternate_hosts: Sequence[str], links: Sequence[str]
) -> dict[str, list[str]]:
    """country → the kinds of evidence naming it (HREFLANG, COUNTRY_PATH, COUNTRY_DOMAIN)."""
    host = (urlsplit(home_url).hostname or "").lower()
    found: dict[str, list[str]] = {}

    def add(country: str | None, basis: str) -> None:
        if country and basis not in found.setdefault(country, []):
            found[country].append(basis)

    for tag in hreflang:
        match = _LOCALE.match(tag.strip())
        add(_country(match.group(1)) if match else None, "HREFLANG")
    for link in links:
        parts = urlsplit(link)
        if parts.hostname and parts.hostname.lower().removeprefix("www.") != host.removeprefix(
            "www."
        ):
            continue
        match = _PATH.match(parts.path or "")
        if match:
            add(_country(re.split("[-_]", match.group(1))[1]), "COUNTRY_PATH")
    brand = _brand(host)
    for other in alternate_hosts:
        name = other.lower().removeprefix("www.")
        tld = name.rsplit(".", 1)[-1]
        if _brand(name) == brand and len(tld) == 2 and tld not in _CCTLD_GENERIC:
            add(_country(tld), "COUNTRY_DOMAIN")
    return dict(sorted(found.items()))
