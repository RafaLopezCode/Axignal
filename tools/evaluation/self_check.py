"""AXIGNAL checks its own reading of axignal.com against what we know to be true.

Nobody knows AXIGNAL better than we do, so every disagreement is an engine defect (CTO,
2026-10-15): a false positive (it states what is false), a false negative (it misses what
exists) or a wrong classification. Input: a reading (a first-observation view or a stored
proof: anything with "discoveries"). Output: one verdict per check, PASS, FAIL or
NOT_MEASURED (the reading carries nothing to judge it with), with the evidence.

Usage: python -m tools.evaluation.self_check reading.json [--out report.json]
       [--previous last-report.json] [--fail-on-regression]

After each deploy the reading is compared with the previous report: a check that passed
and now fails is a regression, named per family (``deploy/production/run-self-check.sh``).

A golden-runner row list is checked organization by organization: AXIGNAL against
``self_truth.json`` and every other domain with a file in ``truths/`` (organizations whose
activity is known with certainty), so a fix found on AXIGNAL is measured on many.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

TRUTH = Path(__file__).with_name("self_truth.json")
TRUTHS = Path(__file__).with_name("truths")


def truth_for(domain: str) -> Mapping[str, Any] | None:
    path = TRUTH if domain == "axignal.com" else TRUTHS / f"{domain}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def evaluate_set(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Each organization against its own truth; verdict ids are prefixed with its domain."""
    by_org: dict[str, Any] = {}
    verdicts: list[dict[str, Any]] = []
    for row in rows:
        domain = str(row.get("domain") or "")
        truth = truth_for(domain)
        if truth is None or not isinstance(row.get("view"), Mapping):
            continue
        report = evaluate(row["view"], truth)
        by_org[domain] = {k: report[k] for k in ("accuracy", "measured", "passed", "byFamily")}
        if report.get("unreachable"):
            by_org[domain]["unreachable"] = True
        verdicts += [{**v, "id": f"{domain}/{v['id']}"} for v in report["verdicts"]]
    measured = [v for v in verdicts if v["status"] != "NOT_MEASURED"]
    passed = sum(v["status"] == "PASS" for v in measured)
    by_family: dict[str, dict[str, int]] = {}
    for v in verdicts:
        tally = by_family.setdefault(v["family"], {"PASS": 0, "FAIL": 0, "NOT_MEASURED": 0})
        tally[v["status"]] += 1
    return {
        "truth": "truth-set",
        "accuracy": None if not measured else round(100 * passed / len(measured), 1),
        # Accuracy excludes what was not measured; coverage says how much was measured.
        "coverage": None if not verdicts else round(100 * len(measured) / len(verdicts), 1),
        "checks": len(verdicts),
        "measured": len(measured),
        "passed": passed,
        "byFamily": by_family,
        "byOrganization": by_org,
        "defects": [v for v in verdicts if v["status"] == "FAIL"],
        "verdicts": verdicts,
    }


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


#: The website did not load: nothing about the engine can be judged from this reading.
UNREACHABLE = "SITE_UNREACHABLE"


def evaluate(reading: Mapping[str, Any], truth: Mapping[str, Any]) -> dict[str, Any]:
    found = _discoveries(reading)
    audit = _audit(found)
    verdicts: list[dict[str, Any]] = []
    if reading.get("state") == "SOURCE_UNAVAILABLE":
        # An external failure (the site shed load, refused or timed out), not a wrong
        # reading: every check is unmeasured and named as such, never a FAIL or a PASS.
        verdicts = [{"id": c["id"], "family": c["family"], "status": "NOT_MEASURED",
                     "defect": None, "detail": UNREACHABLE} for c in truth["checks"]]  # fmt: skip
        return _report(truth["version"], verdicts) | {"unreachable": True}

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
                    "codes": (d.get("detail") or {}).get("codes"),
                    "classifiedAs": (d.get("detail") or {}).get("classifiedAs")}
                   for d in items
                   if not any(t in str((d.get("detail") or {}).get("title") or d.get("statement")).casefold()
                              for t in terms)]  # fmt: skip
            # A call said to be mainly about something else (the activity only an additional
            # code) is presented truthfully; one presented as about the activity is a defect.
            presented = [o for o in off if o["classifiedAs"] != "ADDITIONAL"]
            verdict(check, "FAIL" if presented else "PASS",
                    {"opportunities": len(items), "unrelated": presented,
                     "labelledAdditional": len(off) - len(presented)}, "FALSE_POSITIVE")  # fmt: skip
    return _report(truth["version"], verdicts)


def _report(version: str, verdicts: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [v for v in verdicts if v["status"] != "NOT_MEASURED"]
    passed = sum(v["status"] == "PASS" for v in measured)
    by_family: dict[str, dict[str, int]] = {}
    for v in verdicts:
        tally = by_family.setdefault(v["family"], {"PASS": 0, "FAIL": 0, "NOT_MEASURED": 0})
        tally[v["status"]] += 1
    return {
        "truth": version,
        "accuracy": None if not measured else round(100 * passed / len(measured), 1),
        # Accuracy excludes what was not measured; coverage says how much was measured.
        "coverage": None if not verdicts else round(100 * len(measured) / len(verdicts), 1),
        "checks": len(verdicts),
        "measured": len(measured),
        "passed": passed,
        "byFamily": by_family,
        "defects": [v for v in verdicts if v["status"] == "FAIL"],
        "verdicts": verdicts,
    }


def lost_measurements(
    report: Mapping[str, Any], previous: Mapping[str, Any]
) -> list[dict[str, str]]:
    """Checks measured in the previous report (PASS or FAIL) and unmeasured now: not a wrong
    reading, but a lost capability to read (a source blocked, an instrument gone). Reported
    apart from regressions so accuracy is never inflated by measuring less (audit 2026-10-15)."""
    before = {v["id"]: v["status"] for v in previous.get("verdicts") or ()}
    return [
        {"id": v["id"], "family": v["family"], "was": before[v["id"]]}
        | ({"reason": UNREACHABLE} if v.get("detail") == UNREACHABLE else {})
        for v in report["verdicts"]
        if v["status"] == "NOT_MEASURED" and before.get(v["id"]) in {"PASS", "FAIL"}
    ]


def regressions(report: Mapping[str, Any], previous: Mapping[str, Any]) -> list[dict[str, str]]:
    """Checks that passed in the previous report and fail now (a check newly unmeasured is
    not a regression: it says the reading lacked the evidence, not that it is wrong)."""
    before = {v["id"]: v["status"] for v in previous.get("verdicts") or ()}
    return [
        {"id": v["id"], "family": v["family"], "defect": v["defect"]}
        for v in report["verdicts"]
        if v["status"] == "FAIL" and before.get(v["id"]) == "PASS"
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reading", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--previous", type=Path, help="The last report, to name regressions")
    parser.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args(argv)
    raw = json.loads(args.reading.read_text(encoding="utf-8"))
    # Accepts a reading (AXIGNAL's), or a golden-runner row list ([{"domain", "view"}]).
    if isinstance(raw, list) and len(raw) > 1:
        report = evaluate_set(raw)
    else:
        reading = raw[0]["view"] if isinstance(raw, list) else raw
        report = evaluate(reading, json.loads(TRUTH.read_text(encoding="utf-8")))
    previous = (
        json.loads(args.previous.read_text(encoding="utf-8"))
        if args.previous is not None and args.previous.is_file()
        else None
    )
    report["previousAccuracy"] = None if previous is None else previous.get("accuracy")
    report["regressions"] = [] if previous is None else regressions(report, previous)
    report["previousCoverage"] = None if previous is None else previous.get("coverage")
    report["lostMeasurements"] = [] if previous is None else lost_measurements(report, previous)
    # "--out -": the report on stdout and the summary on stderr (a container with no
    # writable mount hands both to the host).
    to_stdout = args.out is not None and str(args.out) == "-"
    if args.out is not None and not to_stdout:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [
        f"self-accuracy {report['accuracy']}% ({report['passed']}/{report['measured']} measured checks)"
    ]
    for domain, org in (report.get("byOrganization") or {}).items():
        if org.get("unreachable"):
            lines.append(f"  {domain}: UNREACHABLE (website did not load twice; not measured)")
            continue
        lines.append(f"  {domain}: {org['accuracy']}% ({org['passed']}/{org['measured']})")
    lines += [f"FAIL {d['id']} [{d['defect']}]: {json.dumps(d['detail'], ensure_ascii=False)[:300]}"
              for d in report["defects"]]  # fmt: skip
    lines.append(
        f"coverage {report['coverage']}% ({report['measured']}/{report['checks']} checks measured)"
    )
    lines += [f"REGRESSION {r['family']}: {r['id']} [{r['defect']}]" for r in report["regressions"]]
    lines += [
        f"LOST_MEASUREMENT {r['family']}: {r['id']} (was {r['was']})"
        for r in report["lostMeasurements"]
        if r.get("reason") != UNREACHABLE
    ]
    unreachable = sorted({r["id"].split("/")[0] for r in report["lostMeasurements"]
                          if r.get("reason") == UNREACHABLE})  # fmt: skip
    lines += [
        f"UNREACHABLE {domain}: website did not load; its checks are unmeasured"
        for domain in unreachable
    ]
    if report["previousAccuracy"] is not None:
        lines.append(f"previous self-accuracy {report['previousAccuracy']}%")
    print("\n".join(lines), file=sys.stderr if to_stdout else sys.stdout)
    if to_stdout:
        print(json.dumps(report, ensure_ascii=False))
    return (
        3
        if args.fail_on_regression and (report["regressions"] or report["lostMeasurements"])
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
