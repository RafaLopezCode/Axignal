"""Official business-register identifiers a website states in its own text.

Legal notices and footers carry them (often by law: France's SIREN/RCS, the UK company
number, Norway's organisasjonsnummer). Only labelled numbers are read, and every number
must pass its register's check digits, so a phone or order number is never mistaken
for one. Reading one establishes only that the site declares it.
"""

from __future__ import annotations

import re

#: scheme → (pattern with one group, normalizer)
SIREN = "SIREN"
COMPANIES_HOUSE = "COMPANIES_HOUSE"
ORGNR = "ORGNR"
REGISTER_SCHEMES = frozenset({SIREN, COMPANIES_HOUSE, ORGNR})

_FR = re.compile(
    r"\b(?:SIREN|SIRET|R\.?\s?C\.?\s?S\.?(?:\s+[A-Za-zÀ-ÿ'\u2019\-]{2,30}){0,3}(?:\s+[AB])?)"
    r"\s*(?:n[°ºo]\.?\s*)?[:\s]\s*([0-9]{3}[\s.]?[0-9]{3}[\s.]?[0-9]{3})",
    re.IGNORECASE,
)
_GB = re.compile(
    r"\b(?:company|registration|registered|reg\.?)\s+(?:registration\s+|company\s+)?"
    r"(?:number|no\.?|nº)\s*[:.]?\s*((?:SC|NI|OC|SO|NC|FC|SL|LP)?\s?[0-9]{6,8})\b"
    r"|\bregistered\s+in\s+(?:england|scotland|wales|england\s+(?:and|&)\s+wales)"
    r"[^0-9]{0,40}?([0-9]{7,8}|(?:SC|NI|OC)[0-9]{6})\b",
    re.IGNORECASE,
)
_NO = re.compile(
    r"\b(?:org\.?\s?(?:nr|no)\.?|organisasjonsnummer|organisasjonsnr\.?|foretaksregisteret)"
    r"\s*[:.]?\s*(?:NO\s?)?([0-9]{3}[\s]?[0-9]{3}[\s]?[0-9]{3})(?:\s?MVA)?\b",
    re.IGNORECASE,
)


def _digits(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", value).upper()


def _luhn(number: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(number)):
        digit = int(char)
        if index % 2 == 1:
            digit = digit * 2 - 9 if digit > 4 else digit * 2
        total += digit
    return total % 10 == 0


def _orgnr_ok(number: str) -> bool:
    weights = (3, 2, 7, 6, 5, 4, 3, 2)
    remainder = sum(int(d) * w for d, w in zip(number[:8], weights, strict=True)) % 11
    check = 0 if remainder == 0 else 11 - remainder
    return check != 10 and check == int(number[8])


def registry_identifiers(text: str, *, limit: int = 4) -> list[tuple[str, str]]:
    """(scheme, normalized value) the text declares, check digits verified, deduplicated."""
    found: list[tuple[str, str]] = []

    def keep(scheme: str, value: str) -> None:
        if (scheme, value) not in found and len(found) < limit:
            found.append((scheme, value))

    for match in _FR.finditer(text):
        siren = _digits(match.group(1))
        if len(siren) == 9 and _luhn(siren):
            keep(SIREN, siren)
    for match in _GB.finditer(text):
        raw = _digits(match.group(1) or match.group(2) or "")
        if raw.isdigit() and 6 <= len(raw) <= 8:
            raw = raw.zfill(8)
        if re.fullmatch(r"(?:[0-9]{8}|(?:SC|NI|OC|SO|NC|FC|SL|LP)[0-9]{6})", raw):
            keep(COMPANIES_HOUSE, raw)
    for match in _NO.finditer(text):
        orgnr = _digits(match.group(1))
        if len(orgnr) == 9 and orgnr[0] in "89" and _orgnr_ok(orgnr):
            keep(ORGNR, orgnr)
    return found
