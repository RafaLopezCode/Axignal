"""Build application/sector_economy/eu_sbs.json from Eurostat's structural business statistics.

Sources (Eurostat, CC BY 4.0 / reuse policy), per country and NACE Rev.2 division:
- ``sbs_ovw_act``: enterprises, persons employed, net turnover, turnover per person
  employed, employment growth and gross operating rate;
- ``sbs_sc_ovw``: enterprises and net turnover by size class of persons employed.

The latest year with a value is kept per cell, with its year. Confidential or missing
cells stay absent: unknown, never zero. Reproducible: ``python -m tools.data.build_sector_economy``.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
OUT = Path(__file__).parents[2] / "application" / "sector_economy" / "eu_sbs.json"
COUNTRIES = [
    "AT",
    "BE",
    "BG",
    "CY",
    "CZ",
    "DE",
    "DK",
    "EE",
    "EL",
    "ES",
    "FI",
    "FR",
    "HR",
    "HU",
    "IE",
    "IT",
    "LT",
    "LU",
    "LV",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SE",
    "SI",
    "SK",
    "NO",
    "IS",
    "LI",
    "CH",
]
#: indicator → key in the table
SECTOR = {
    "ENT_NR": "enterprises",
    "EMP_NR": "personsEmployed",
    "NETTUR_MEUR": "turnoverMeur",
    "NETTUR_EMP_TEUR": "turnoverPerPersonTeur",
    "GRW_EMP_PC": "employmentGrowthPc",
    "GOR_PC": "grossOperatingRatePc",
}
SIZES = ("0-9", "10-19", "20-49", "50-249", "GE250")
BY_SIZE = {"ENT_NR": "enterprises", "NETTUR_MEUR": "turnoverMeur"}
DIVISION = re.compile(r"^[A-S][0-9]{2}$")


def _get(dataset: str, params: list[tuple[str, str]]) -> dict[str, Any]:
    query = urllib.parse.urlencode([*params, ("format", "JSON"), ("lang", "EN")])
    request = urllib.request.Request(f"{API}{dataset}?{query}", headers={"User-Agent": "AXIGNAL"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return dict(json.load(response))


def _cells(data: dict[str, Any]) -> dict[tuple[str, ...], tuple[str, float]]:
    """(dimension codes without time) → (latest year, value)."""
    order, sizes = data["id"], data["size"]
    labels = {d: list(data["dimension"][d]["category"]["index"]) for d in order}
    out: dict[tuple[str, ...], tuple[str, float]] = {}
    for flat, value in data.get("value", {}).items():
        if value is None:
            continue
        rest, codes = int(flat), {}
        for dim, size in zip(reversed(order), reversed(sizes), strict=True):
            codes[dim] = labels[dim][rest % size]
            rest //= size
        year = codes.pop("time")
        key = tuple(codes[d] for d in order if d != "time")
        if key not in out or year > out[key][0]:
            out[key] = (year, float(value))
    return out


def _round(value: float) -> float:
    return round(value, 2) if abs(value) < 1000 else round(value)


def country(code: str) -> dict[str, object]:
    sector = _cells(_get("sbs_ovw_act", [("geo", code), ("lastTimePeriod", "3"),
                                          *(("indic_sbs", i) for i in SECTOR)]))  # fmt: skip
    sized = _cells(_get("sbs_sc_ovw", [("geo", code), ("lastTimePeriod", "3"),
                                        *(("indic_sbs", i) for i in BY_SIZE),
                                        *(("size_emp", s) for s in SIZES)]))  # fmt: skip
    divisions: dict[str, dict[str, Any]] = {}
    for key, (year, value) in sector.items():
        named = dict(zip(("freq", "nace_r2", "indic_sbs", "geo"), key, strict=False))
        nace, indicator = named.get("nace_r2", ""), named.get("indic_sbs", "")
        if not DIVISION.match(nace) or indicator not in SECTOR:
            continue
        cell = divisions.setdefault(nace, {"year": year})
        cell[SECTOR[indicator]] = _round(value)
        cell["year"] = max(str(cell["year"]), year)
    for key, (_year, value) in sized.items():
        named = dict(zip(("freq", "indic_sbs", "nace_r2", "size_emp", "geo"), key, strict=False))
        nace, indicator, size = named["nace_r2"], named["indic_sbs"], named["size_emp"]
        if nace in divisions and indicator in BY_SIZE and size in SIZES:
            divisions[nace].setdefault("bySize", {}).setdefault(size, {})[BY_SIZE[indicator]] = (
                _round(value)
            )
    return dict(sorted(divisions.items()))


def build() -> dict[str, object]:
    countries: dict[str, object] = {}
    for code in COUNTRIES:
        try:
            found = country(code)
        except Exception as error:  # a country Eurostat does not publish stays absent
            print(code, "skipped:", type(error).__name__, file=sys.stderr)
            continue
        if found:
            countries[code] = found
            print(code, len(found), "divisions", file=sys.stderr)
    return {
        "source": "Eurostat structural business statistics: sbs_ovw_act and sbs_sc_ovw "
        "(enterprises by NACE Rev.2 division and size class), latest year per cell",
        "licence": "Eurostat, CC BY 4.0",
        "url": "https://ec.europa.eu/eurostat/web/structural-business-statistics",
        "sizeClasses": list(SIZES),
        "countries": countries,
    }


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8", newline="\n")  # fmt: skip
    print("wrote", OUT, OUT.stat().st_size, "bytes")
