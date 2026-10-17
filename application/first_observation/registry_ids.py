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
ES_CIF = "ES_CIF"
DE_HR = "DE_HR"
REGISTER_SCHEMES = frozenset({SIREN, COMPANIES_HOUSE, ORGNR, ES_CIF, DE_HR})

#: The label, then a short run of words before the number: "RCS Paris B", "RCS de Paris sous
#: le numéro", "immatriculée au registre du commerce et des sociétés de Lyon sous le n°"
#: (eskimoz.fr, 2026-10-18: "RCS de Paris sous le numéro 528 338 494" was not read). The
#: SIREN check digit (Luhn) still rejects any other number.
_FR = re.compile(
    r"\b(?:SIREN|SIRET|R\.?\s?C\.?\s?S\.?|registre\s+du\s+commerce\s+et\s+des\s+soci[ée]t[ée]s)"
    r"(?:[\s,]+(?:n[°ºo]\.?|[A-Za-zÀ-ÿ'\u2019\-]{1,30})){0,7}?"
    r"\s*[:\s]\s*([0-9]{3}[\s.]?[0-9]{3}[\s.]?[0-9]{3})(?![0-9])",
    re.IGNORECASE,
)
#: A German commercial-register entry with its register court ("HRB 3771, AG Bonn",
#: "Amtsgericht München, HRB 123456"). Without the court the number is not unique: not read.
_DE_COURT = (
    r"(?:Amtsgericht|AG|Registergericht)[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:[\s-][A-ZÄÖÜ][a-zäöüß]+)?)"
)
_DE = re.compile(
    rf"\b(HR[AB])\s*(?:Nr\.?\s*)?[:.]?\s*([0-9]{{1,6}})(?:\s?[A-Z]{{1,2}}\b)?[\s,;()]*{_DE_COURT}"
    rf"|{_DE_COURT}[\s,;:()-]*(?:Handelsregister[\s,:-]*)?(HR[AB])\s*(?:Nr\.?\s*)?[:.]?\s*([0-9]{{1,6}})\b"
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


_ES = re.compile(
    r"\b(?:C\.?\s?I\.?\s?F\.?|N\.?\s?I\.?\s?F\.?)\s*(?:n[\u00ba\u00b0o]\.?|[\u00ba\u00b0])?\s*[:.]?\s*"
    r"(?:ES[\s-]?)?([ABCDEFGHJNPQRSUVW][\s.-]?[0-9]{2}[\s.]?[0-9]{3}[\s.]?[0-9]{2}[\s.-]?[0-9A-J])\b",
    re.IGNORECASE,
)


def _cif_ok(cif: str) -> bool:
    """Spanish company tax identifier (CIF) control character."""
    digits = cif[1:8]
    if not digits.isdigit():
        return False
    even = sum(int(d) for d in digits[1::2])
    odd = sum(sum(divmod(int(d) * 2, 10)) for d in digits[0::2])
    control = (10 - (even + odd) % 10) % 10
    last = cif[8]
    letter = "JABCDEFGHI"[control]
    if cif[0] in "ABEH":
        return last == str(control)
    if cif[0] in "KPQS" or cif[0] in "NW":
        return last == letter
    return last in {str(control), letter}


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
    for match in _ES.finditer(text):
        cif = _digits(match.group(1))
        if len(cif) == 9 and _cif_ok(cif):
            keep(ES_CIF, cif)
    for match in _DE.finditer(text):
        section, number, court = (
            (match.group(1), match.group(2), match.group(3))
            if match.group(1)
            else (match.group(5), match.group(6), match.group(4))
        )
        court = re.sub(r"^(?:Amtsgericht|AG)\s+", "", court)
        keep(DE_HR, f"{section} {int(number)} {court}")
    for match in _NO.finditer(text):
        orgnr = _digits(match.group(1))
        if len(orgnr) == 9 and orgnr[0] in "89" and _orgnr_ok(orgnr):
            keep(ORGNR, orgnr)
    return found
