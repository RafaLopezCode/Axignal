"""Build application/value_chain/eu_value_chain.json from Eurostat's EU-27 input-output table.

Source: Eurostat ``naio_10_cp1750`` — symmetric input-output table at basic prices,
industry by industry, EU27_2020, million EUR (licence: Eurostat, CC BY 4.0 / reuse
policy). For each industry: who buys its output (other industries and final uses:
households, government, investment, exports) and from whom it buys its inputs, as
shares. Reproducible: ``python -m tools.data.build_value_chain [year]``.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/naio_10_cp1750"
    "?geo=EU27_2020&unit=MIO_EUR&stk_flow=TOTAL&format=JSON&lang=EN&time={year}"
)
OUT = Path(__file__).parents[2] / "application" / "value_chain" / "eu_value_chain.json"
FINAL = {
    "P3_S14": "HOUSEHOLDS",
    "P3_S13": "GOVERNMENT",
    "P3_S15": "NON_PROFITS",
    "P51G": "INVESTMENT",
    "P6": "EXPORTS",
}
TOP = 8


def build(year: str) -> dict[str, object]:
    request = urllib.request.Request(URL.format(year=year), headers={"User-Agent": "AXIGNAL"})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 (fixed host)
        data = json.load(response)
    ava = data["dimension"]["ind_ava"]["category"]
    use = data["dimension"]["ind_use"]["category"]
    sizes = dict(zip(data["id"], data["size"], strict=True))
    order = data["id"]
    values = data["value"]

    def value(row: str, column: str) -> float:
        index = {"ind_ava": ava["index"][row], "ind_use": use["index"][column]}
        flat = 0
        for dim in order:
            flat = flat * sizes[dim] + index.get(dim, 0)
        return float(values.get(str(flat), 0.0) or 0.0)

    codes = [c for c in use["index"] if c in ava["index"] and c != "TOTAL"]
    has_values = {c for c in codes if any(value(c, u) for u in codes)}
    # Leaves: industries no other industry code refines (C is the sum of C10-C12...).
    leaves = [
        c for c in codes
        if c in has_values and not any(o != c and o.startswith(c) and o in has_values for o in codes)
    ]  # fmt: skip
    industries: dict[str, object] = {}
    for code in leaves:
        sales = {u: value(code, u) for u in leaves}
        sales.update({label: value(code, column) for column, label in FINAL.items()})
        total_sales = sum(v for v in sales.values() if v > 0)
        inputs = {a: value(a, code) for a in leaves}
        total_inputs = sum(v for v in inputs.values() if v > 0)
        if total_sales <= 0:
            continue

        def top(flows: dict[str, float], total: float) -> list[list[object]]:
            ranked = sorted(((k, v) for k, v in flows.items() if v > 0), key=lambda x: -x[1])
            return [[k, round(v / total, 4)] for k, v in ranked[:TOP]] if total > 0 else []

        industries[code] = {
            "label": ava["label"][code],
            "buyers": top(sales, total_sales),
            "suppliers": top(inputs, total_inputs),
        }
    return {
        "source": "Eurostat naio_10_cp1750, EU27_2020, industry by industry, million EUR",
        "year": year,
        "url": URL.format(year=year),
        "finalUses": FINAL,
        "industries": industries,
    }


if __name__ == "__main__":
    table = build(sys.argv[1] if len(sys.argv) > 1 else "2023")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(OUT, len(table["industries"]))  # type: ignore[arg-type]
