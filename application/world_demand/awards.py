"""Public contract awards: who won which contract, from which buyer, for how much.

An award is an official publication: the buyer formalized a contract with a named winner
(and its tax identifier). It is OBSERVED evidence of a past commercial relationship
between that buyer and that winner — nothing more. It is not a current relationship, a
measure of quality, a guarantee of future business, nor proof that two winners of similar
contracts compete (that reading stays POTENTIAL and is labelled as such).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from application.observation_intelligence.contracts import TaxonomyCode


@dataclass(frozen=True, slots=True)
class AwardRecord:
    source_id: str
    record_id: str  # the tender folder
    lot: str  # contract id within the folder (one award per lot)
    title: str
    buyer_name: str | None
    winner_name: str
    winner_id: str | None  # as published (NIF/CIF for Spain); None when absent
    amount: float | None  # tax-exclusive, as published
    currency: str | None
    awarded_on: date | None
    offers_received: int | None
    demand_codes: tuple[TaxonomyCode, ...]
    places: tuple[TaxonomyCode, ...]
    source_url: str

    @property
    def key(self) -> str:
        return f"{self.source_id}|{self.record_id}|{self.lot}|{self.winner_id or self.winner_name}"


_LEGAL_FORMS = re.compile(
    r"\b(s\.?\s?a\.?\s?u?|s\.?\s?l\.?\s?u?|s\.?\s?l\.?\s?l|s\.?\s?coop|s\.?\s?a\.?\s?l|"
    r"sociedad (anonima|limitada)( unipersonal)?|ltd|limited|gmbh|sas|sarl|srl|spa|bv|nv|inc)\b\.?"
)


def normalized_name(name: str) -> str:
    """A comparable name: no accents, case, punctuation or legal form (S.A., S.L.U.)."""
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().casefold()
    folded = _LEGAL_FORMS.sub(" ", folded)
    return " ".join(re.findall(r"[a-z0-9]+", folded))


def normalized_tax_id(value: str | None) -> str | None:
    """A Spanish NIF/CIF as published, upper-case, without separators or country prefix."""
    if not value:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    if cleaned.startswith("ES") and len(cleaned) == 11:
        cleaned = cleaned[2:]
    return cleaned if 8 <= len(cleaned) <= 12 else None
