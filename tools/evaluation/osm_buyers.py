"""Experiment: OpenStreetMap establishments as potential buyers, against the Wikidata route.

Evaluation tooling only (no product change, no canonical write). For organizations of the
golden set whose buying sectors (Eurostat input-output) have establishments in OSM, it reads
named establishments of those sectors in one bounded urban area of the organization's country
and samples them next to the Wikidata sector-route candidates AXIGNAL already shows. The
output is a blind annotation sheet (source hidden) plus a key file and automatic metrics.

Source use: the public Overpass instance, within its usage policy (a few dozen queries, free
slots checked first, stop on HTTP 429). OSM data (c) OpenStreetMap contributors, ODbL 1.0.
Outputs may name natural persons (a sole trader's shop): they stay in ignored working data,
are never committed and are deleted after the review (30 days at most).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.value_chain import buying_sectors, label

OVERPASS = "https://overpass-api.de/api/interpreter"
STATUS = "https://overpass-api.de/api/status"
USER_AGENT = "AXIGNAL/1.0 (https://axignal.com; evaluation) osm-buyers-experiment"
PER_SOURCE = 20
MAX_QUERIES = 40
#: One bounded urban area per country (south, west, north, east): a local market sample,
#: not the organization's whole reach.
AREAS = {
    "ES": ("Madrid", (40.36, -3.78, 40.50, -3.60)),
    "DE": ("Berlin", (52.46, 13.30, 52.56, 13.48)),
    "FR": ("Paris", (48.82, 2.27, 48.90, 2.41)),
    "GB": ("London", (51.47, -0.20, 51.54, -0.05)),
    "US": ("New York (Manhattan)", (40.70, -74.02, 40.80, -73.93)),
    "NO": ("Oslo", (59.89, 10.68, 59.96, 10.82)),
    "CA": ("Toronto", (43.63, -79.45, 43.70, -79.35)),
    "AU": ("Sydney", (-33.90, 151.17, -33.85, 151.23)),
}
#: OSM tags of establishments in each table industry (organizations that operate there).
OSM_TAGS: dict[str, tuple[tuple[str, str], ...]] = {
    "G47": (
        (
            "shop",
            "supermarket|convenience|clothes|electronics|furniture|hardware|doityourself|department_store|books|sports",
        ),
    ),
    "G46": (("shop", "wholesale"), ("wholesale", ".+")),
    "G45": (("shop", "car|car_repair|car_parts|motorcycle"),),
    "I": (
        ("amenity", "restaurant|cafe|bar|pub|fast_food"),
        ("tourism", "hotel|guest_house|hostel"),
    ),
    "F": (
        (
            "craft",
            "builder|electrician|plumber|carpenter|roofer|tiler|painter|hvac|plasterer|glaziery",
        ),
    ),
    "M69_70": (("office", "lawyer|accountant|tax_advisor|consulting|notary"),),
    "M71": (("office", "architect|engineer|surveyor"),),
    "M73": (("office", "advertising_agency"),),
    "J62_63": (("office", "it|telecommunication"),),
    "K64": (("amenity", "bank"),),
    "K65": (("office", "insurance"),),
    "K66": (("office", "financial|financial_advisor"),),
    "L68B": (("office", "estate_agent|property_management"),),
    "N78": (("office", "employment_agency"),),
    "N79": (("shop", "travel_agency"), ("office", "travel_agent")),
    "S96": (("shop", "hairdresser|beauty|laundry|dry_cleaning"),),
    "R93": (("leisure", "fitness_centre|sports_centre"),),
    "C10-12": (("craft", "bakery|brewery|winery|distillery|confectionery"),),
}
#: A name that reads as a person's practice: measured, never used to filter here.
_PERSON_HINT = re.compile(r"^(dr\.?|dra\.?|mr\.?|mrs\.?|ms\.?|abogad[oa]|me\.?|maître)\s", re.I)


def _get(url: str, data: bytes | None = None) -> bytes:
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return bytes(response.read(30_000_000))


def _wait_for_slot() -> None:
    """Wait until the public instance offers a free slot (its documented etiquette)."""
    for _ in range(12):
        status = _get(STATUS).decode("utf-8", "replace")
        if "slots available now" in status or "available now" in status:
            return
        waits = [int(n) for n in re.findall(r"in (\d+) seconds", status)]
        time.sleep(min(max(min(waits, default=10), 2), 60))


def overpass(
    tags: Sequence[tuple[str, str]], box: tuple[float, ...], limit: int
) -> list[dict[str, Any]]:
    south, west, north, east = box
    parts = "".join(
        f'nwr["{key}"~"^({value})$"]["name"]({south},{west},{north},{east});' for key, value in tags
    )
    query = f"[out:json][timeout:60];({parts});out tags center meta {limit};"
    for attempt in range(2):  # a gateway timeout is retried once, after a pause
        _wait_for_slot()
        try:
            raw = _get(OVERPASS, urllib.parse.urlencode({"data": query}).encode())
            break
        except urllib.error.HTTPError as error:
            if error.code != 504 or attempt:
                raise
            time.sleep(20)
    payload = json.loads(raw)
    if payload.get("remark"):
        raise RuntimeError("OVERPASS_INCOMPLETE: " + str(payload["remark"])[:120])
    return [e for e in payload.get("elements", []) if isinstance(e, dict)]


def _industry(view: Mapping[str, Any]) -> str | None:
    for d in view.get("discoveries") or []:
        if isinstance(d, Mapping) and d.get("code") == "VALUE_CHAIN_BUYERS":
            return str((d.get("detail") or {}).get("industry") or "") or None
    return None


def _wikidata_candidates(view: Mapping[str, Any]) -> list[dict[str, Any]]:
    out = []
    for d in view.get("discoveries") or []:
        if not isinstance(d, Mapping) or d.get("code") != "POTENTIAL_BUYER":
            continue
        signal = next((s for s in (d.get("detail") or {}).get("signals") or []
                       if s.get("type") == "SECTOR_BUYS_FROM_ITS_SECTOR"
                       and "Wikidata" in str(s.get("basis"))), None)  # fmt: skip
        if signal is None:
            continue
        ids = (d.get("detail") or {}).get("identifiers") or {}
        out.append({"name": d.get("statement"), "category": signal.get("via"),
                    "website": ids.get("website"), "link": signal.get("sourceUrl"),
                    "lastEdit": None})  # fmt: skip
    return out


def run(views: Path, output: Path, *, seed: int = 14) -> dict[str, Any]:
    rows = json.loads(views.read_text(encoding="utf-8"))
    chosen = []
    for row in rows:
        view = row.get("view") or {}
        industry = _industry(view)
        country = str(row.get("country") or "")
        if industry is None or country not in AREAS:
            continue
        sectors = [(code, share) for code, share in buying_sectors(industry) if code in OSM_TAGS]
        if sectors:
            chosen.append((row, industry, sectors))
    rng = random.Random(seed)
    sheet: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {"organizations": [], "queries": 0, "failures": []}
    # Every country first (round robin), those with Wikidata candidates to compare first.
    chosen.sort(key=lambda c: not _wikidata_candidates(c[0].get("view") or {}))
    by_country: dict[str, list[Any]] = {}
    for item in chosen:
        by_country.setdefault(str(item[0]["country"]), []).append(item)
    picked: list[Any] = []
    while len(picked) < 10 and any(by_country.values()):
        for country in sorted(by_country):
            if by_country[country] and len(picked) < 10:
                picked.append(by_country[country].pop(0))
    for row, industry, sectors in picked:
        city, box = AREAS[str(row["country"])]
        osm: list[dict[str, Any]] = []
        for code, _share in sectors:
            if metrics["queries"] >= MAX_QUERIES:
                break
            try:
                metrics["queries"] += 1
                elements = overpass(OSM_TAGS[code], box, 60)
            except Exception as error:  # a failure is recorded, never read as "no establishments"
                metrics["failures"].append({"domain": row["domain"], "sector": code,
                                            "error": str(error)[:160]})  # fmt: skip
                if "429" in str(error):
                    break
                continue
            for e in elements:
                tags = e.get("tags") or {}
                osm.append({"name": tags.get("name"), "category": f"{label(code)} ({code})",
                            "website": tags.get("website") or tags.get("contact:website"),
                            "link": f"https://www.openstreetmap.org/{e.get('type')}/{e.get('id')}",
                            "lastEdit": e.get("timestamp")})  # fmt: skip
        unique: dict[str, dict[str, Any]] = {}
        for c in osm:  # one entry per name: chains repeat their brand across branches
            if c["name"]:
                unique.setdefault(str(c["name"]).casefold(), c)
        osm = list(unique.values())
        osm_sample = rng.sample(osm, min(PER_SOURCE, len(osm)))
        wiki = _wikidata_candidates(row.get("view") or {})
        wiki_sample = rng.sample(wiki, min(PER_SOURCE, len(wiki)))
        overlap = {c["name"].casefold() for c in osm} & {str(c["name"]).casefold() for c in wiki}
        candidates = [("OSM", c) for c in osm_sample] + [("WIKIDATA", c) for c in wiki_sample]
        rng.shuffle(candidates)
        for source, c in candidates:
            cid = f"c{len(key) + 1:04d}"
            sheet.append({"id": cid, "subscriber": row["domain"],
                          "subscriber_activity": f"{label(industry)} ({industry})",
                          "candidate": c["name"], "category": c["category"],
                          "area": f"{city}, {row['country']}" if source == "OSM" else row["country"],
                          "website": c["website"] or "",
                          "real_active_organization": "", "correct_sector": "",
                          "natural_person": "", "plausible_buyer": "", "notes": ""})  # fmt: skip
            key.append({"id": cid, "source": source, "link": c["link"], "lastEdit": c["lastEdit"],
                        "personHint": bool(_PERSON_HINT.match(str(c["name"])))})  # fmt: skip
        edits = sorted(c["lastEdit"] for c in osm if c.get("lastEdit"))
        metrics["organizations"].append({
            "domain": row["domain"], "country": row["country"], "industry": industry,
            "buyingSectors": [code for code, _ in sectors], "area": city,
            "osmEstablishments": len(osm), "osmSampled": len(osm_sample),
            "wikidataCandidates": len(wiki), "wikidataSampled": len(wiki_sample),
            "overlapByName": len(overlap),
            "osmWithWebsite": sum(1 for c in osm if c["website"]),
            "osmMedianLastEdit": edits[len(edits) // 2] if edits else None,
            "osmPersonHints": sum(1 for c in osm if _PERSON_HINT.match(str(c["name"]))),
        })  # fmt: skip
    output.mkdir(parents=True, exist_ok=True)
    with (output / "annotation-sheet.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sheet[0]) if sheet else ["id"])
        writer.writeheader()
        writer.writerows(sheet)
    (output / "key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    metrics["generatedAt"] = datetime.now(UTC).isoformat()
    metrics["rights"] = "OSM data (c) OpenStreetMap contributors, ODbL 1.0; Wikidata CC0"
    (output / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return metrics


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("views", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    metrics = run(args.views, args.out)
    print(
        json.dumps({k: v for k, v in metrics.items() if k != "organizations"}, ensure_ascii=False)
    )
    for org in metrics["organizations"]:
        print(json.dumps(org, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
