"""Revenue a third-party page reports for an organization (spec 104).

Deterministic and conservative: a figure counts only when, in the page's own text and near
where the organization is named, a revenue word and an amount with its scale and currency
appear together ("12,5 millones de euros", "£40m", "1.200 Mio. Euro"). Ambiguous numbers are
left out rather than guessed. What a page reports is POTENTIAL, never an official account.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

#: Revenue in the languages the observatory reads (folded, no accents).
_REVENUE = re.compile(
    r"factur\w*|ventas|ingresos|cifra de negocio\w*|revenues?|sales|turnover|umsatz\w*|"
    r"chiffre d.affaires|fatturat\w*|faturac\w*|receitas|omzet",
    re.IGNORECASE,
)
_SCALES: tuple[tuple[str, float], ...] = (
    (r"mil millones|billones?|billions?|bn|milliards?|mrd\.?|miliardi|mil milhoes|miljard", 1e9),
    (r"millones|millon|millions?|mio\.?|mill\.?|milioni|milhoes|miljoen|m(?![a-z])", 1e6),
)
_CURRENCY = {
    "eur": "EUR", "euro": "EUR", "euros": "EUR", "usd": "USD",
    "dolares": "USD", "dollars": "USD", "gbp": "GBP", "libras": "GBP",
    "pounds": "GBP", "chf": "CHF", "nok": "NOK", "sek": "SEK", "dkk": "DKK",
}  # fmt: skip
_NUMBER = r"\d{1,4}(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?"
_SCALE = "|".join(f"(?:{pattern})" for pattern, _ in _SCALES)
_CUR = r"eur(?:os?)?|usd|gbp|chf|nok|sek|dkk|dolares|dollars|libras|pounds"
#: "€12.5m", "£40 million", "12,5 millones de euros", "1.200 Mio. Euro", "$3bn".
_AMOUNT = re.compile(
    rf"(?P<pre>{_CUR})?\s?(?P<num>{_NUMBER})\s?(?P<scale>{_SCALE})\b\.?\s?(?:de\s|d.)?\s?(?P<post>{_CUR})?",
    re.IGNORECASE,
)
#: Sentences about a target, a forecast or a cumulative total (Donte Group "aspira a duplicar
#: su facturación, hasta 750 millones"; Bombas "USD 2 billion in lifetime sales", 2026-10-19).
_NOT_REPORTED = re.compile(
    r"\b(aspira\w*|prev(e|en|ista|isto|ision\w*)|objetivo\w*|meta|plan(es)? estrategic\w*|"
    r"espera\w*|hasta alcanzar|alcanzar\w* los|target\w*|aims?|expect\w*|forecast\w*|projected|"
    r"goal|guidance|plans? to|ziel\w*|erwart\w*|prevoit|objectif\w*|obiettiv\w*|prevede|"
    r"lifetime|cumulat\w*|acumulad\w*|since (its )?founding|desde su fundacion)\b",
    re.IGNORECASE,
)
#: Another figure's word between the revenue word and the amount ("revenue … profit of £20m").
_OTHER_FIGURE = re.compile(
    r"\b(beneficio\w*|perdida\w*|ebitda|ebit|profit\w*|loss(es)?|gewinn\w*|verlust\w*|"
    r"benefice\w*|utile|utili|lucro\w*|valoracion|valuation|valued|financiacion|funding|raised|"
    r"ronda|inversion|investment|deuda|debt)\b",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(20[12]\d)\b")
WINDOW = 220


@dataclass(frozen=True, slots=True)
class ReportedRevenue:
    value: float  # in currency units
    currency: str
    year: int | None
    excerpt: str


_SYMBOLS = {"€": " EUR ", "£": " GBP ", "$": " USD "}
#: Scale abbreviations end in a period that does not end a sentence.
_ABBREVIATIONS = re.compile(r"(?<![a-z])(mio|mrd|mill)\.", re.IGNORECASE)
#: A sentence ends at ";" or at ".!?" followed by a space (never inside "1.200").
_SENTENCE = re.compile(r";|[.!?](?=\s|$)")


def _fold(text: str) -> str:
    """Accents folded; currency symbols kept as their codes (folding would drop them)."""
    for symbol, code in _SYMBOLS.items():
        text = text.replace(symbol, code)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def _number(raw: str) -> float | None:
    """Thousands separators are groups of exactly three digits; anything else is a decimal."""
    raw = raw.replace(" ", "")
    parts = re.split(r"[.,]", raw)
    if len(parts) == 1:
        return float(parts[0])
    if all(len(p) == 3 for p in parts[1:]):
        return float("".join(parts))
    if len(parts) == 2:
        return float(f"{parts[0]}.{parts[1]}")
    return None  # "1.234,5,6": not a number a page would write


def _scale(word: str) -> float:
    lowered = _fold(word).lower()
    for pattern, factor in _SCALES:
        if re.fullmatch(pattern, lowered):
            return factor
    return 1.0


def reported_revenue(
    text: str, needles: Sequence[str], *, current_year: int
) -> ReportedRevenue | None:
    """The first revenue figure reported in the same sentence as the organization, or None.

    Same sentence, not merely nearby: "the fashion market turns over 1,200 million; Ecoalf
    grows" is the market's figure, never Ecoalf's.
    """
    folded = _ABBREVIATIONS.sub(lambda m: m.group(1), _fold(text[:200_000]))
    sentences = [s.strip() for s in _SENTENCE.split(folded) if s.strip()]
    for needle in needles:
        pattern = re.compile(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])")
        for window in sentences:
            if len(window) > 2 * WINDOW or not pattern.search(window.lower()):
                continue
            if not _REVENUE.search(window) or _NOT_REPORTED.search(window):
                continue  # a target, a forecast or a cumulative figure is not reported revenue
            for amount in _AMOUNT.finditer(window):
                currency_raw = (amount.group("pre") or amount.group("post") or "").lower()
                currency = _CURRENCY.get(currency_raw)
                value = _number(amount.group("num"))
                if currency is None or value is None:
                    continue  # no currency, or an unreadable number: not a reported revenue
                before = window[max(0, amount.start() - 80) : amount.start()]
                words = list(_REVENUE.finditer(before))
                if not words:
                    continue  # the revenue word leads to the figure ("revenue of £214m")
                if _OTHER_FIGURE.search(before[words[-1].end() :]):
                    continue  # "revenue … profit of £20m": the figure is the profit's
                near = window[max(0, amount.start() - 80) : amount.end() + 80]
                years = [int(y) for y in _YEAR.findall(near) if int(y) <= current_year]
                if not years or max(years) < current_year - 3:
                    # Without its year, or years old ("sales from £20m when he joined in
                    # 2017"), a figure is not its revenue today.
                    continue
                return ReportedRevenue(
                    value=value * _scale(amount.group("scale")),
                    currency=currency,
                    year=max(years) if years else None,
                    excerpt=" ".join(window.split())[: 2 * WINDOW],
                )
    return None
