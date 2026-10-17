"""Provider-neutral findings returned by source adapters.

A record is an immutable assertion about what a source published at retrieval
time. A named buyer or winner is a source claim, not an admitted relationship.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.observation_intelligence.contracts import SourceCapability, TaxonomyCode

_MONTHS_PER_UNIT = {"MONTH": 1, "MON": 1, "YEAR": 12, "ANN": 12}
_DAYS_PER_UNIT = {"DAY": 1, "DAYS": 1, "WEEK": 7, "WEE": 7}


def duration_months(value: str | float | None, unit: str | None) -> int | None:
    """A published contract duration in whole months (rounded up); None when unsaid."""
    try:
        amount = None if value is None else float(value)
    except ValueError:
        return None
    unit = (unit or "").upper()
    if amount is None or amount <= 0:
        return None
    if unit in _MONTHS_PER_UNIT:
        return max(1, round(amount * _MONTHS_PER_UNIT[unit]))
    if unit in _DAYS_PER_UNIT:
        return max(1, -(-int(amount * _DAYS_PER_UNIT[unit]) // 30))
    return None


@dataclass(frozen=True, slots=True)
class ContractScale:
    """How big a contract is, as its source publishes it (spec 081): observed facts that
    let a person judge whether it is within reach, never a filter or a score. Every field
    is None when the source does not say it."""

    estimated_value: float | None = None
    currency: str | None = None
    #: Lots let smaller suppliers bid for part of a contract: how many, and the smallest.
    lots: int | None = None
    smallest_lot_value: float | None = None
    duration_months: int | None = None

    def known(self) -> bool:
        return any(v is not None for v in (self.estimated_value, self.lots, self.duration_months))

    def to_wire(self) -> dict[str, object]:
        return {
            "estimatedValue": self.estimated_value,
            "currency": self.currency,
            "lots": self.lots,
            "smallestLotValue": self.smallest_lot_value,
            "durationMonths": self.duration_months,
        }

    @classmethod
    def from_wire(cls, raw: object) -> ContractScale | None:
        if not isinstance(raw, dict):
            return None

        def number(key: str) -> float | None:
            value = raw.get(key)
            return float(value) if isinstance(value, int | float) else None

        def whole(key: str) -> int | None:
            value = raw.get(key)
            return int(value) if isinstance(value, int) else None

        currency = raw.get("currency")
        return cls(
            estimated_value=number("estimatedValue"),
            currency=currency if isinstance(currency, str) else None,
            lots=whole("lots"),
            smallest_lot_value=number("smallestLotValue"),
            duration_months=whole("durationMonths"),
        )


@dataclass(frozen=True, slots=True)
class ProcurementRecord:
    record_id: str
    source_id: str
    kind: SourceCapability
    title: str
    buyer_name: str | None
    places: tuple[TaxonomyCode, ...]
    demand_codes: tuple[TaxonomyCode, ...]
    published_at: datetime
    source_url: str
    deadline: str | None = None
    winners: tuple[str, ...] = ()
    #: What the notice is principally about, as its buyer classified it (the procedure's
    #: and each lot's main code); empty when the source does not say.
    main_codes: tuple[TaxonomyCode, ...] = ()
    #: SUPPLIES, SERVICES or WORKS as the source declares it; None when not declared or mixed.
    contract_nature: str | None = None
    #: Value, lots and duration as published (spec 081); None when the source says nothing.
    scale: ContractScale | None = None

    def __post_init__(self) -> None:
        if not self.record_id.strip() or not self.source_id.strip() or not self.title.strip():
            raise ValueError("procurement record identity and title are required")
        if self.kind not in {
            SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
            SourceCapability.PUBLIC_PROCUREMENT_AWARDS,
        }:
            raise ValueError("procurement record kind must be a notice or an award")
        if self.published_at.tzinfo is None:
            raise ValueError("procurement publication time must be timezone-aware")
        if self.contract_nature not in CONTRACT_NATURES | {None}:
            raise ValueError("contract nature must be SUPPLIES, SERVICES or WORKS")


CONTRACT_NATURES = frozenset({"SUPPLIES", "SERVICES", "WORKS"})
#: The notice is principally about the activity (its main code, or a lot's, lies within it).
MAIN = "MAIN"
#: The activity appears only among the notice's additional codes: its main object is other.
ADDITIONAL = "ADDITIONAL"


def _cpv_significant(code: str) -> str:
    return code[: max(2, len(code.rstrip("0")))]


def cpv_nature(code: str) -> str:
    """CPV divisions 03-44 and 48 are supplies, 45 is works, the rest are services."""
    division = int(code[:2]) if code[:2].isdigit() else 99
    if division == 45:
        return "WORKS"
    return "SUPPLIES" if division < 45 or division == 48 else "SERVICES"


def classified_as(record: ProcurementRecord, codes: tuple[TaxonomyCode, ...]) -> str | None:
    """Whether the activity's ``codes`` are what a notice is mainly about: MAIN, ADDITIONAL or None.

    Buyers list a main code and, often, additional ones; an electricity supply may add
    "survey services" for a side task. Only the source's own main classification or its
    declared contract nature decide; a main code too broad to say (a CPV division such as
    "business services") and an undeclared one stay None: unknown, never ADDITIONAL.
    """
    cpv = [c.code for c in codes if c.scheme == "CPV"]
    if not cpv:
        return None
    mains = [m.code for m in record.main_codes if m.scheme == "CPV"]
    if mains:
        broad = False
        for main in mains:
            for code in cpv:
                if main.startswith(_cpv_significant(code)):
                    return MAIN
                if code.startswith(_cpv_significant(main)):
                    # A parent group ("market and economic research") is about the activity;
                    # a whole division is too broad to say either way.
                    if len(_cpv_significant(main)) >= 3:
                        return MAIN
                    broad = True
        # A whole division says nothing, unless a specific main object names something else.
        specific = any(len(_cpv_significant(m)) >= 3 for m in mains)
        return ADDITIONAL if specific or not broad else None
    if record.contract_nature is not None and all(
        cpv_nature(code) != record.contract_nature for code in cpv
    ):
        return ADDITIONAL
    return None


@dataclass(frozen=True, slots=True)
class SourceFindings:
    source_id: str
    retrieved_at: datetime
    requests: int
    amount_microunits: int | None
    latency_ms: int | None
    records: tuple[ProcurementRecord, ...] = ()
    total_available: int | None = None
    failure: str | None = None
    #: Whether the source has another page for this query. None: the page size tells
    #: (a short page is the last); feeds filtered locally say it explicitly.
    has_more: bool | None = None

    def __post_init__(self) -> None:
        if self.requests < 0:
            raise ValueError("findings request count cannot be negative")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("findings retrieval time must be timezone-aware")
