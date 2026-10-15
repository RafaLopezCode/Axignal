"""Confirmation sample for OSM establishments as potential buyers (rules fixed in advance).

The first experiment (2026-10-15, inconclusive) suggested two rules, derived after the
fact. They are fixed here, before the new sample is drawn, and are not tuned on it:

1. WEBSITE_REQUIRED: only establishments whose OSM entry carries a website.
2. PERSON_FILTER: drop names starting with a personal title, and names in a professional
   category (lawyers, accountants) of 2-4 words with no firm or legal-form word.

Input: establishments read from dated Geofabrik extracts (one JSON per country, written by
an isolated pyosmium extractor). For every golden-set subscriber with a known industry, it
samples 30 establishments across its buying sectors in its country's urban area and writes
a blind annotation sheet (same columns as the first experiment), a key and metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.value_chain import buying_sectors, label
from tools.evaluation.osm_buyers import AREAS, OSM_TAGS, _industry, _wikidata_candidates

PER_SUBSCRIBER = 30
RULES = ("WEBSITE_REQUIRED", "PERSON_FILTER")
_TITLE = re.compile(r"^(dr\.?|dra\.?|ma[iî]tre|me\.?|mr\.?|mrs\.?|ms\.?)\s", re.IGNORECASE)
_FIRM = re.compile(
    r"\b(llp|llc|ltd|limited|inc|gmbh|ag|sa|sas|sarl|sl|slp|plc|pty|co\.?|group|partners?|"
    r"associates?|law|legal|firm|services|cabinet|avocats|kanzlei|abogados|asesores)\b|&",
    re.IGNORECASE,
)
_PROFESSIONAL = {"M69_70"}


def person_like(name: str, sector: str) -> bool:
    """The fixed person filter (rule 2)."""
    words = name.split()
    return bool(_TITLE.match(name)) or (
        sector in _PROFESSIONAL and not _FIRM.search(name) and 2 <= len(words) <= 4
    )


def eligible(e: Mapping[str, Any]) -> bool:
    """Both fixed rules."""
    return bool(e.get("website")) and not person_like(
        str(e.get("name") or ""), str(e.get("sector"))
    )


def run(views: Path, establishments: Path, output: Path, *, seed: int = 15) -> dict[str, Any]:
    rows = json.loads(views.read_text(encoding="utf-8"))
    by_country = {
        p.stem: json.loads(p.read_text(encoding="utf-8")) for p in establishments.glob("*.json")
    }
    rng = random.Random(seed)
    sheet: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {"rules": list(RULES), "organizations": [], "extracts": {}}
    for country, data in by_country.items():
        metrics["extracts"][country] = {
            "area": data.get("area"), "extract": data.get("extract"),
            "replicatedAt": data.get("extractReplicatedAt"),
            "establishments": len(data.get("establishments") or []),
        }  # fmt: skip
    for row in rows:
        view = row.get("view") or {}
        industry = _industry(view)
        country = str(row.get("country") or "")
        data = by_country.get(country)
        if industry is None or data is None or country not in AREAS:
            continue
        sectors = [c for c, _s in buying_sectors(industry) if c in OSM_TAGS]
        if not sectors:
            continue
        pool = [e for e in data.get("establishments") or [] if e.get("sector") in sectors]
        kept = [e for e in pool if eligible(e)]
        unique: dict[str, dict[str, Any]] = {}
        for e in kept:  # one entry per name: chains repeat their brand across branches
            unique.setdefault(str(e["name"]).casefold(), e)
        candidates = list(unique.values())
        # Round robin across its buying sectors, so no single sector fills the sample.
        per_sector = {s: rng.sample([e for e in candidates if e["sector"] == s],
                                    len([e for e in candidates if e["sector"] == s])) for s in sectors}  # fmt: skip
        sample: list[dict[str, Any]] = []
        while len(sample) < PER_SUBSCRIBER and any(per_sector.values()):
            for s in sectors:
                if per_sector[s] and len(sample) < PER_SUBSCRIBER:
                    sample.append(per_sector[s].pop())
        own = "L68B" if industry == "L68A" else industry
        wiki = {str(c["name"]).casefold() for c in _wikidata_candidates(view)}
        for e in sample:
            cid = f"k{len(key) + 1:04d}"
            sheet.append({"id": cid, "subscriber": row["domain"],
                          "subscriber_activity": f"{label(own)} ({own})",
                          "candidate": e["name"], "category": f"{label(e['sector'])} ({e['sector']})",
                          "area": f"{data.get('area')}, {country}", "website": e.get("website") or "",
                          "real_active_organization": "", "correct_sector": "",
                          "natural_person": "", "plausible_buyer": "", "notes": ""})  # fmt: skip
            key.append({"id": cid, "source": "OSM", "osm": f"{e['type']}/{e['id']}",
                        "lastEdit": e.get("lastEdit"), "version": e.get("version"),
                        "inWikidataRoute": str(e["name"]).casefold() in wiki})  # fmt: skip
        metrics["organizations"].append({
            "domain": row["domain"], "country": country, "industry": own,
            "buyingSectors": sectors, "pool": len(pool), "afterRules": len(kept),
            "uniqueAfterRules": len(candidates), "sampled": len(sample),
            "droppedNoWebsite": sum(1 for e in pool if not e.get("website")),
            "droppedPersonFilter": sum(1 for e in pool if e.get("website")
                                       and person_like(str(e.get("name")), str(e.get("sector")))),
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
    metrics["rows"] = len(sheet)
    (output / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return metrics


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("views", type=Path)
    parser.add_argument("--establishments", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    metrics = run(args.views, args.establishments, args.out)
    print(
        json.dumps({k: v for k, v in metrics.items() if k != "organizations"}, ensure_ascii=False)
    )
    for org in metrics["organizations"]:
        print(json.dumps(org, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
