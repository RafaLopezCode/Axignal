"""AXIGNAL checks its own reading of axignal.com against what we know to be true.

Nobody knows AXIGNAL better than we do, so every disagreement is an engine defect (CTO,
2026-10-15): a false positive (it states what is false), a false negative (it misses what
exists) or a wrong classification. Input: a reading (a first-observation view or a stored
proof: anything with "discoveries"). Output: one verdict per check, PASS, FAIL or
NOT_MEASURED (the reading carries nothing to judge it with), with the evidence.

Usage: python -m tools.evaluation.self_check reading.json [--out report.json]
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

TRUTH = Path(__file__).with_name("self_truth.json")


def _discoveries(reading: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    held = reading.get("discoveries")
    return [d for d in held if isinstance(d, Mapping)] if isinstance(held, list) else []


def _matches(d: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    return all(str(d.get(key) or "") == str(value) for key, value in rule.items())


def _audit(found: list[Mapping[str, Any]]) -> dict[str, str]:
    for d in found:
        if d.get("code") == "PUBLIC_WEB_REPRESENTATION_MEASURED":
            checks = ((d.get("detail") or {}).get("audit") or {}).get("checks") or []
            return {
                str(c.get("id")): str(c.get("status")) for c in checks if isinstance(c, Mapping)
            }
    return {}


def evaluate(reading: Mapping[str, Any], truth: Mapping[str, Any]) -> dict[str, Any]:
    found = _discoveries(reading)
    audit = _audit(found)
    verdicts: list[dict[str, Any]] = []

    def verdict(
        check: Mapping[str, Any], status: str, detail: object, kind: str | None = None
    ) -> None:
        verdicts.append({"id": check["id"], "family": check["family"], "status": status,
                         "defect": kind if status == "FAIL" else None, "detail": detail})  # fmt: skip

    for check in truth["checks"]:
        if "require" in check:
            hits = [d for d in found if _matches(d, check["require"])]
            verdict(check, "PASS" if hits else "FAIL", check["require"], "FALSE_NEGATIVE")
        elif "forbid" in check:
            said = [str(d.get("statement"))[:80] for d in found if _matches(d, check["forbid"])]
            verdict(check, "FAIL" if said else "PASS", said, "FALSE_POSITIVE")
        elif "languages" in check:
            stated = next((d for d in found if d.get("code") == "LANGUAGES_PUBLISHED"), None)
            if stated is None:
                verdict(check, "NOT_MEASURED", None)
                continue
            seen = {x.strip() for x in str(stated.get("statement")).split(",")} - {"x-default"}
            missing = sorted(set(check["languages"]) - seen)
            extra = sorted(seen - set(check["languages"]))
            verdict(check, "PASS" if not missing and not extra else "FAIL",
                    {"missing": missing, "extra": extra}, "WRONG_READING")  # fmt: skip
        elif "audit" in check:
            if not audit:
                verdict(check, "NOT_MEASURED", None)
                continue
            expected = check["audit"]["status"]
            wrong = {
                c: audit.get(c, "ABSENT")
                for c in check["audit"]["checks"]
                if audit.get(c) != expected
            }
            verdict(check, "PASS" if not wrong else "FAIL", wrong,
                    "FALSE_POSITIVE" if expected == "PASS" else "FALSE_NEGATIVE")  # fmt: skip
        elif "activities" in check:
            read = [str(d.get("code")) for d in found if d.get("kind") == "ACTIVITY"
                    and d.get("code") not in {"REGISTERED_ACTIVITY", "STATED_INDUSTRY"}]  # fmt: skip
            outside = [
                c for c in read if c not in check["activities"] and not c.startswith("isic-")
            ]
            if not read:
                verdict(check, "NOT_MEASURED", None)
            else:
                verdict(check, "FAIL" if outside else "PASS", {"read": read, "outside": outside},
                        "WRONG_CLASSIFICATION")  # fmt: skip
        elif "industry" in check:
            industry = next((str((d.get("detail") or {}).get("industry")) for d in found
                             if d.get("code") == "VALUE_CHAIN_BUYERS"), None)  # fmt: skip
            if industry is None:
                verdict(check, "NOT_MEASURED", "no value-chain reading in this reading")
            else:
                ok = industry in check["industry"]["allowed"]
                verdict(check, "PASS" if ok else "FAIL",
                        {"read": industry, "preferred": check["industry"]["preferred"]},
                        "WRONG_CLASSIFICATION")  # fmt: skip
        elif "demand" in check:
            terms = [t.casefold() for t in check["demand"]["titleTerms"]]
            items = [
                d
                for d in found
                if d.get("kind") == "DEMAND" and d.get("code") == "POTENTIAL_DEMAND"
            ]
            if not items:
                verdict(check, "NOT_MEASURED", None)
                continue
            off = [{"title": str((d.get("detail") or {}).get("title") or d.get("statement"))[:100],
                    "codes": (d.get("detail") or {}).get("codes")}
                   for d in items
                   if not any(t in str((d.get("detail") or {}).get("title") or d.get("statement")).casefold()
                              for t in terms)]  # fmt: skip
            verdict(check, "FAIL" if off else "PASS",
                    {"opportunities": len(items), "unrelated": off}, "FALSE_POSITIVE")  # fmt: skip
    measured = [v for v in verdicts if v["status"] != "NOT_MEASURED"]
    passed = sum(v["status"] == "PASS" for v in measured)
    by_family: dict[str, dict[str, int]] = {}
    for v in verdicts:
        tally = by_family.setdefault(v["family"], {"PASS": 0, "FAIL": 0, "NOT_MEASURED": 0})
        tally[v["status"]] += 1
    return {
        "truth": truth["version"],
        "accuracy": None if not measured else round(100 * passed / len(measured), 1),
        "checks": len(verdicts),
        "measured": len(measured),
        "passed": passed,
        "byFamily": by_family,
        "defects": [v for v in verdicts if v["status"] == "FAIL"],
        "verdicts": verdicts,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reading", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    raw = json.loads(args.reading.read_text(encoding="utf-8"))
    # Accepts a reading, or a golden-runner row list ([{"view": ...}]).
    reading = raw[0]["view"] if isinstance(raw, list) else raw
    report = evaluate(reading, json.loads(TRUTH.read_text(encoding="utf-8")))
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"self-accuracy {report['accuracy']}% ({report['passed']}/{report['measured']} measured checks)"
    )
    for defect in report["defects"]:
        print(
            f"FAIL {defect['id']} [{defect['defect']}]: {json.dumps(defect['detail'], ensure_ascii=False)[:300]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
