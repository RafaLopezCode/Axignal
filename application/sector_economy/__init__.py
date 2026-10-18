"""Its sector's economy in each market it looks at: official structural business statistics.

The size of an organization's sector in a country (enterprises, persons employed, net
turnover), how its employment moves and how its enterprises split by size, from Eurostat's
structural business statistics (see tools/data/build_sector_economy.py). They describe the
sector, never the organization: they give its own figures, or their absence, a scale.

The sector is the one every family reads (``value_chain.company_industry``). Read from its
register's activity code it is DECLARED by the register; read from its website or its
activity codes it is POTENTIAL. Markets are its own country and the ones it looks at.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from functools import cache
from pathlib import Path
from typing import Any

from application.value_chain import company_industry, industry_divisions

TABLE = Path(__file__).with_name("eu_sbs.json")
MAX_MARKETS = 5
#: Eurostat writes Greece as EL.
_GEO = {"GR": "EL"}
#: NACE Rev.2 section of each division.
_SECTIONS = (
    ("A", 1, 3), ("B", 5, 9), ("C", 10, 33), ("D", 35, 35), ("E", 36, 39), ("F", 41, 43),
    ("G", 45, 47), ("H", 49, 53), ("I", 55, 56), ("J", 58, 63), ("K", 64, 66), ("L", 68, 68),
    ("M", 69, 75), ("N", 77, 82), ("O", 84, 84), ("P", 85, 85), ("Q", 86, 88), ("R", 90, 93),
    ("S", 94, 96),
)  # fmt: skip
#: Employee-band upper bounds of the size classes, to place an organization among them.
SIZE_BOUNDS = (("0-9", 0, 9), ("10-19", 10, 19), ("20-49", 20, 49), ("50-249", 50, 249),
               ("GE250", 250, None))  # fmt: skip


@cache
def table() -> dict[str, Any]:
    return dict(json.loads(TABLE.read_text(encoding="utf-8")))


def division_key(division: int) -> str | None:
    """Eurostat's code for a NACE division: 62 → "J62"."""
    for section, low, high in _SECTIONS:
        if low <= division <= high:
            return f"{section}{division:02d}"
    return None


def sector_figures(country: str, divisions: Sequence[int]) -> dict[str, Any] | None:
    """The sector's figures in one country, summed over its divisions; None when unknown."""
    rows = table()["countries"].get(_GEO.get(country.upper(), country.upper()), {})
    cells = [rows[k] for d in sorted(set(divisions)) if (k := division_key(d)) and k in rows]
    if not cells:
        return None

    def total(key: str) -> float | None:
        values = [c[key] for c in cells if isinstance(c.get(key), int | float)]
        return float(sum(values)) if len(values) == len(cells) else None

    persons, turnover, enterprises = (
        total("personsEmployed"),
        total("turnoverMeur"),
        total("enterprises"),
    )
    growth = [(c["employmentGrowthPc"], c.get("personsEmployed") or 0) for c in cells
              if isinstance(c.get("employmentGrowthPc"), int | float)]  # fmt: skip
    weight = sum(w for _g, w in growth)
    by_size: dict[str, dict[str, float]] = {}
    for size, _low, _high in SIZE_BOUNDS:
        parts = [c.get("bySize", {}).get(size, {}) for c in cells]
        for key in ("enterprises", "turnoverMeur"):
            values = [p[key] for p in parts if isinstance(p.get(key), int | float)]
            if len(values) == len(cells):
                by_size.setdefault(size, {})[key] = float(sum(values))
    return {
        "country": country.upper(),
        "divisions": [division_key(d) for d in sorted(set(divisions)) if division_key(d)],
        "year": max(str(c.get("year") or "") for c in cells),
        "enterprises": enterprises,
        "personsEmployed": persons,
        "turnoverMeur": turnover,
        "turnoverPerPersonTeur": round(turnover * 1000 / persons, 1) if turnover and persons else None,
        "employmentGrowthPc": round(sum(g * w for g, w in growth) / weight, 2) if weight and len(growth) == len(cells) else None,
        "bySize": by_size,
    }  # fmt: skip


def markets_of(view: Mapping[str, Any], directed: Sequence[str] = ()) -> list[str]:
    """Its own country first, then the markets it looks at (ISO alpha-2), at most five."""
    found: list[str] = []
    for scope in view.get("attentionScopes") or []:
        parts = (
            str(scope.get("jurisdiction") or "").split("/") if isinstance(scope, Mapping) else []
        )
        code = (
            parts[1]
            if parts and parts[0] == "EU" and len(parts) > 1
            else (parts[0] if parts else "")
        )
        if len(code) == 2 and code.isalpha():
            found.append(code.upper())
    for market in directed:
        code = str(market).split("/")[-1]
        if len(code) == 2:
            found.append(code.upper())
    return list(dict.fromkeys(found))[:MAX_MARKETS]


def sector_market_discoveries(
    industry: str, how: str, markets: Sequence[str], *, observed_at: str
) -> list[dict[str, object]]:
    """One SECTOR_MARKET fact per market where the statistics know its sector."""
    divisions = sorted(industry_divisions(industry))
    data = table()
    out: list[dict[str, object]] = []
    for country in markets:
        figures = sector_figures(country, divisions)
        if figures is None or not figures.get("enterprises"):
            continue
        out.append(
            {
                "kind": "ECONOMIC_FACT",
                "code": f"SECTOR_MARKET:{country}",
                "statement": f"{country} {','.join(figures['divisions'])} {figures['year']}",
                # The figures are official; that this is its sector is the register's word
                # (DECLARED) or a reading of its activity (POTENTIAL).
                "epistemicState": "DECLARED" if how == "REGISTER_ACTIVITY_CODE" else "POTENTIAL",
                "sourceUrl": data.get("url"),
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "fact": "sectorMarket",
                    "aboutSector": True,
                    "notAboutThisOrganization": True,
                    "industry": industry,
                    "industryReadFrom": how,
                    "source": data.get("source"),
                    "licence": data.get("licence"),
                    **figures,
                    "limitation": "Official statistics of its sector in that country, not of "
                    "the organization. An average enterprise is not a typical one: most are "
                    "micro-enterprises.",
                },
            }
        )
    return out


def apply_sector_economy(
    view: dict[str, Any],
    proof: Mapping[str, Any],
    *,
    directed: Sequence[str] = (),
    nace_of: Callable[[str], list[str]] | None = None,
) -> dict[str, Any]:
    """Add its sector's economy in each of its markets to an observation view."""
    cpvs = [
        str(pair[1])
        for capability in proof.get("capabilities") or []
        if isinstance(capability, Mapping)
        for pair in capability.get("demandCodes") or []
        if isinstance(pair, list | tuple) and len(pair) == 2 and pair[0] == "CPV"
    ]
    found = company_industry(view, cpvs, nace_of=nace_of)
    markets = markets_of(view, directed)
    if found is None or not markets:
        return view
    held = view.get("discoveries")
    discoveries = held if isinstance(held, list) else []
    added = sector_market_discoveries(
        found[0], found[1], markets, observed_at=str(view.get("observedAt") or "")
    )
    if added:
        view["discoveries"] = [*discoveries, *added]
    return view


def size_class_of(employees: float | None, band: str | None) -> str | None:
    """The size class an employee count or a register band ("50-99") falls in."""
    low: float | None = employees
    if low is None and band:
        head = band.split("-")[0].rstrip("+")
        low = float(head) if head.isdigit() else None
    if low is None:
        return None
    for size, lower, upper in SIZE_BOUNDS:
        if low >= lower and (upper is None or low <= upper):
            return size
    return None
