"""Value chain: which sectors buy from an organization's sector, and which it buys from.

Structural, official and inspectable: shares from Eurostat's EU-27 industry-by-industry
input-output table (see tools/data/build_value_chain.py). It says where demand for a
sector's output usually comes from and where its inputs usually come from — a POTENTIAL
reading about the sector, never a statement about this organization's own customers or
suppliers.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from functools import cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from application.world_demand.awards import is_company

TABLE = Path(__file__).with_name("eu_value_chain.json")
WIKIDATA_INDUSTRIES = Path(__file__).with_name("wikidata_industries.json")

#: CPV division (or longer prefix) → NACE Rev.2 division. Longest prefix wins. Curated from
#: the CPV 2008 ↔ CPA 2008 correspondence at division level; versioned with this module.
CPV_TO_NACE: dict[str, str] = {
    "03": "01", "031": "01", "032": "01", "034": "02", "035": "03", "09": "19", "091": "19",
    "093": "35", "094": "35", "14": "08", "15": "10", "159": "11", "16": "28", "18": "14",
    "184": "15", "19": "13", "22": "18", "24": "20", "246": "20", "33": "21", "336": "21",
    "30": "26", "301": "28", "31": "27", "32": "26", "34": "29", "345": "30", "347": "30",
    "35": "25", "37": "32", "38": "26", "39": "31", "395": "13", "398": "20", "41": "36",
    "42": "28", "43": "28", "44": "23", "441": "23", "442": "25", "443": "25", "445": "25",
    "45": "41", "452": "42", "453": "43", "454": "43", "48": "58", "50": "33", "505": "33",
    "51": "33", "55": "56", "551": "55", "60": "49", "601": "49", "602": "49", "604": "51",
    "606": "50", "63": "52", "64": "61", "641": "53", "65": "35", "651": "36", "66": "64",
    "665": "65", "70": "68", "71": "71", "713": "71", "72": "62", "73": "72", "75": "84",
    "76": "09", "77": "01", "79": "82", "791": "69", "792": "69", "793": "73", "794": "70",
    "795": "82", "796": "78", "797": "80", "798": "18", "799": "82", "7934": "73",
    "80": "85", "85": "86", "853": "88", "90": "38", "905": "38", "906": "81", "907": "39",
    "909": "81", "92": "90", "921": "59", "922": "60", "925": "91", "926": "93", "98": "94",
    "983": "96",
}  # fmt: skip

FINAL_USES = {"HOUSEHOLDS", "GOVERNMENT", "NON_PROFITS", "INVESTMENT", "EXPORTS"}
#: Sectors public bodies make up: an award winner "in" them sells to them, it is not one.
#: Public buyers are read directly from awards (recurrent public buyers) instead.
PUBLIC_SECTORS = {"O", "P", "Q86", "Q87_88", "T"}


@cache
def table() -> dict[str, Any]:
    return dict(json.loads(TABLE.read_text(encoding="utf-8")))


def _divisions(code: str) -> set[int]:
    """NACE divisions an industry code of the table covers (C10-12, J62_63, L68B, B...)."""
    found = re.findall(r"\d{2}", code)
    if not found:
        return set()
    numbers = [int(n) for n in found]
    if "-" in code and len(numbers) == 2:
        return set(range(numbers[0], numbers[1] + 1))
    return set(numbers)


@cache
def _by_division() -> dict[int, str]:
    out: dict[int, str] = {}
    sections = {"B": range(5, 10), "F": range(41, 44), "I": range(55, 57), "P": range(85, 86),
                "T": range(97, 99), "U": range(99, 100), "O": range(84, 85),
                "D": range(35, 36)}  # fmt: skip
    for code in table()["industries"]:
        if code == "L68A":
            continue  # imputed rents of owner-occupiers: households, never an organization's sector
        divisions = _divisions(code) or set(sections.get(code, ()))
        for division in divisions:
            out.setdefault(division, code)
    return out


@cache
def _wikidata_industries() -> dict[str, str]:
    data = json.loads(WIKIDATA_INDUSTRIES.read_text(encoding="utf-8"))["industries"]
    return {str(qid): str(entry["nace"]) for qid, entry in data.items()}


def wikidata_industry_nace(qid: str) -> str | None:
    """The NACE code curated for a common Wikidata industry that carries none (P4496)."""
    return _wikidata_industries().get(qid)


def wikidata_industries_for(nace: list[str]) -> list[str]:
    """Curated Wikidata industries whose NACE code is one of these (or below one)."""
    wanted = {n.upper() for n in nace}
    return [
        qid for qid, code in _wikidata_industries().items()
        if any(code == w or code.startswith(w + ".") for w in wanted)
    ]  # fmt: skip


def industry_of_code(code: str) -> str | None:
    """The table industry of a NACE division ("62", "10.1") or section letter ("F", "D")."""
    if code.isalpha():
        return code if code in table()["industries"] else None
    return industry_of_nace(code)


def nace_codes(code: str) -> list[str]:
    """NACE Rev. 2 codes of a table industry as Wikidata writes them: divisions ("10"), and
    the section letter for a section-level industry ("F", "I")."""
    divisions = sorted(d for d, c in _by_division().items() if c == code)
    out = [f"{d:02d}" for d in divisions]
    return [code, *out] if code.isalpha() else out


def buying_sectors(
    code: str, *, limit: int = 3, min_share: float = 0.02
) -> list[tuple[str, float]]:
    """Industries that buy most from this one: neither itself (competitors), final uses,
    public sectors (public buyers are read from awards) nor imputed rents (L68A: an
    accounting entry for households living in their own homes, not a buyer)."""
    own = "L68B" if code == "L68A" else code  # real estate is read as its services
    excluded = FINAL_USES | PUBLIC_SECTORS | {"L68A", own}
    return [
        (sector, share)
        for sector, share in flows(own, "buyers")
        if sector not in excluded and share >= min_share
    ][:limit]


def industry_of_nace(code: str | None) -> str | None:
    """The table industry of a NACE/NAF code ("62.02A", "06.100", "80.10Z")."""
    digits = re.findall(r"\d", code or "")
    if len(digits) < 2:
        return None
    return _by_division().get(int("".join(digits[:2])))


def industry_of_cpv(cpv: str | None) -> str | None:
    digits = re.sub(r"\D", "", cpv or "")
    for length in range(min(len(digits), 4), 1, -1):
        nace = CPV_TO_NACE.get(digits[:length])
        if nace is not None:
            return industry_of_nace(nace)
    return None


def label(code: str) -> str:
    entry = table()["industries"].get(code)
    return str(entry["label"]) if isinstance(entry, Mapping) else code


def flows(code: str, direction: str) -> list[tuple[str, float]]:
    """("buyers" | "suppliers") of an industry as (industry or final use, share)."""
    entry = table()["industries"].get(code)
    if not isinstance(entry, Mapping):
        return []
    return [(str(k), float(v)) for k, v in entry.get(direction, [])]


def non_operating(code: str) -> bool:
    """A head office (NACE 70.10) or a holding (64.20): the registered entity's legal role,
    not what the group does. It never decides its industry (golden set, 2026-10-14)."""
    digits = re.sub(r"\D", "", code)
    return digits[:3] in {"701", "642"}


#: Pages whose text describes contracts and policies, not what the organization does.
LEGAL_PAGE = re.compile(
    r"/(legal|terms|privacy|cookies?|aviso-legal|politica|impressum|mentions-legales|agb|"
    r"datenschutz|conditions|cgv|cgu|disclaimer)(?:[/\-_.]|$)",
    re.IGNORECASE,
)


def _activity_votes(view: Mapping[str, Any]) -> dict[str, int]:
    """One vote per activity its website establishes (not per code), never from a legal
    page; insertion order keeps the strongest method first on a tie."""
    votes: dict[str, int] = {}
    for d in view.get("discoveries") or []:
        if not isinstance(d, Mapping) or d.get("kind") != "ACTIVITY":
            continue
        if LEGAL_PAGE.search(urlsplit(str(d.get("sourceUrl") or "")).path):
            continue
        codes = (d.get("detail") or {}).get("routingCodes") or []
        found = next(
            (f for c in codes if str(c).startswith("CPV:") and (f := industry_of_cpv(str(c)[4:]))),
            None,
        )
        if found:
            votes[found] = votes.get(found, 0) + 1
    return votes


def company_industry(
    view: Mapping[str, Any],
    cpvs: list[str],
    *,
    nace_of: Callable[[str], list[str]] | None = None,
) -> tuple[str, str] | None:
    """Its industry and how it was read, one reading for every consumer:

    1. the register's activity code, unless it only names a head office or holding;
    2. the industry Wikidata states (community-curated), with the same exception;
    3. the activities its website establishes (one vote each, legal pages excluded);
    4. the activity codes of its stored observation, when the view carries none.
    """
    discoveries = [d for d in view.get("discoveries") or [] if isinstance(d, Mapping)]
    for d in discoveries:
        if d.get("kind") == "ECONOMIC_FACT" and str(d.get("code", "")).endswith(":activity"):
            value = str((d.get("detail") or {}).get("value") or "")
            found = None if non_operating(value) else industry_of_nace(value)
            if found:
                return found, "REGISTER_ACTIVITY_CODE"
    stated = next((d for d in discoveries if d.get("code") == "WIKIDATA:industry"), None)
    qid = str((stated.get("detail") or {}).get("value") or "") if stated else ""
    if nace_of is not None and qid.startswith("Q"):
        for code in nace_of(qid):
            found = None if non_operating(code) else industry_of_code(code)
            if found:
                return found, "WIKIDATA_INDUSTRY"
    votes = _activity_votes(view)
    if votes:
        return max(votes.items(), key=lambda x: x[1])[0], "WEBSITE_ACTIVITY"
    counts: dict[str, int] = {}
    for cpv in cpvs:
        found = industry_of_cpv(cpv)
        if found:
            counts[found] = counts.get(found, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda x: x[1])[0], "ACTIVITY_CPV_CODES"


def sector_discoveries(industry: str, how: str, *, observed_at: str) -> list[dict[str, object]]:
    data = table()
    out: list[dict[str, object]] = []
    for direction, kind, code in (
        ("buyers", "DEMAND", "VALUE_CHAIN_BUYERS"),
        ("suppliers", "RELATIONSHIP", "VALUE_CHAIN_SUPPLIERS"),
    ):
        rows = [(k, s) for k, s in flows(industry, direction) if k != industry][:6]
        if not rows:
            continue
        out.append(
            {
                "kind": kind,
                "code": code,
                "statement": ", ".join(k for k, _s in rows),
                "epistemicState": "POTENTIAL",
                "sourceUrl": data["url"],
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "industry": industry,
                    "industryLabel": label(industry),
                    "industryFrom": how,
                    "sectors": [
                        {"code": k, "share": s, "label": k if k in FINAL_USES else label(k)}
                        for k, s in rows
                    ],
                    "source": data["source"],
                    "year": data["year"],
                    "basis": "How the EU-27 economy's flows run for its sector: where its output "
                    "usually goes, or where its inputs usually come from. About the sector, "
                    "not this organization's own customers or suppliers.",
                },
            }
        )
    return out


def chain_organizations(
    awards: list[Any],
    industry: str,
    *,
    in_area: Any,
    own_ids: set[str],
    own_names: set[str],
    normalize: Any,
    observed_at: str,
) -> list[dict[str, object]]:
    """Companies active in its supplier and buyer sectors, in its area, from public awards.

    A company that wins public contracts selling what its sector buys is a possible
    supplier; one active in a sector that buys from its sector, a possible customer. Both
    POTENTIAL, with the awards that show the activity — never a relationship.
    """
    by_industry: dict[str, dict[str, list[Any]]] = {}
    for award in awards:
        if not in_area(award) or not award.demand_codes:
            continue
        if (award.winner_id and award.winner_id in own_ids) or normalize(
            award.winner_name
        ) in own_names:
            continue
        if not is_company(award.winner_name, award.winner_id):
            continue  # individuals are never listed
        sector = industry_of_cpv(award.demand_codes[0].code)
        if sector is None or sector == industry:
            continue
        key = award.winner_id or normalize(award.winner_name)
        by_industry.setdefault(sector, {}).setdefault(key, []).append(award)
    out: list[dict[str, object]] = []
    shown: set[str] = set()
    weight = {d: dict(flows(industry, d)) for d in ("buyers", "suppliers")}
    other = {"buyers": "suppliers", "suppliers": "buyers"}
    for direction, kind, code in (
        ("buyers", "DEMAND", "POTENTIAL_PRIVATE_CUSTOMER"),
        ("suppliers", "RELATIONSHIP", "POTENTIAL_SUPPLIER"),
    ):
        picked = 0
        for sector, share in flows(industry, direction):
            if (
                sector in FINAL_USES
                or sector in PUBLIC_SECTORS
                or sector == industry
                or sector not in by_industry
                # A sector both sells to and buys from it: read where its weight is larger.
                or share < weight[other[direction]].get(sector, 0.0)
            ):
                continue
            ranked = sorted(by_industry[sector].items(), key=lambda kv: -len(kv[1]))
            companies = [won for key, won in ranked if key not in shown][:2]
            for won in companies:
                if picked >= 6:
                    break
                picked += 1
                shown.add(won[0].winner_id or normalize(won[0].winner_name))
                out.append(
                    {
                        "kind": kind,
                        "code": code,
                        "statement": won[0].winner_name,
                        "epistemicState": "POTENTIAL",
                        "sourceUrl": won[0].source_url,
                        "excerpt": None,
                        "observedAt": observed_at,
                        "detail": {
                            "sector": sector,
                            "sectorLabel": label(sector),
                            "share": share,
                            "industry": industry,
                            "winnerId": won[0].winner_id,
                            "contracts": len(won),
                            "amount": round(sum(a.amount or 0 for a in won), 2),
                            "currency": next((a.currency for a in won if a.currency), None),
                            "awards": [
                                {
                                    "title": a.title,
                                    "buyer": a.buyer_name,
                                    "amount": a.amount,
                                    "awardedOn": a.awarded_on.isoformat() if a.awarded_on else None,
                                    "url": a.source_url,
                                }
                                for a in won[:3]
                            ],
                            "basis": (
                                "Active in its area in a sector its sector usually buys from "
                                "(it wins public contracts for it). A possible supplier, not "
                                "a relationship."
                                if direction == "suppliers"
                                else "Active in its area in a sector that usually buys from "
                                "its sector (it wins public contracts in it). A possible "
                                "customer, not a relationship."
                            ),
                        },
                    }
                )
    return out


def apply_value_chain(
    view: dict[str, Any],
    proof: Mapping[str, Any],
    *,
    nace_of: Callable[[str], list[str]] | None = None,
) -> dict[str, Any]:
    """Add the sector's buyers and suppliers (EU-27 structure) to an observation view."""
    cpvs = [
        str(pair[1])
        for capability in proof.get("capabilities") or []
        if isinstance(capability, Mapping)
        for pair in capability.get("demandCodes") or []
        if isinstance(pair, list | tuple) and len(pair) == 2 and pair[0] == "CPV"
    ]
    found = company_industry(view, cpvs, nace_of=nace_of)
    if found is None:
        return view
    held = view.get("discoveries")
    discoveries = held if isinstance(held, list) else []
    view["discoveries"] = [
        *discoveries,
        *sector_discoveries(found[0], found[1], observed_at=str(view.get("observedAt") or "")),
    ]
    return view
