"""Lighthouse measurements of an organization's website, as findings (spec 100).

Google's PageSpeed Insights runs Lighthouse on the home page in a lab: a fixed, simulated
device and network, one run per strategy. Its category scores (SEO, performance,
accessibility, best practices) are that instrument's grades on that date, under those
conditions: each is shown with its instrument and version, conditions, time, sample and
uncertainty (MASTER §54), never folded into one universal score. Real users' experience is
CrUX's (field data), told apart. A failing audit is a fact about the page as Lighthouse
read it, not a ranking factor's weight nor a search position.
"""

from __future__ import annotations

from collections.abc import Mapping

STRATEGIES = ("MOBILE", "DESKTOP")


def lighthouse_discoveries(
    measurement: Mapping[str, object], *, observed_at: str
) -> list[dict[str, object]]:
    """One WEB_REPRESENTATION finding per measured strategy (mobile first)."""
    runs = measurement.get("runs")
    rows = [r for r in runs if isinstance(r, Mapping)] if isinstance(runs, list) else []
    out: list[dict[str, object]] = []
    for run in sorted(rows, key=lambda r: STRATEGIES.index(str(r.get("strategy") or "MOBILE"))):
        scores = run.get("scores")
        if not isinstance(scores, Mapping) or not any(isinstance(v, int) for v in scores.values()):
            continue
        out.append(
            {
                "kind": "WEB_REPRESENTATION",
                "code": "LIGHTHOUSE_AUDIT",
                "statement": " · ".join(
                    f"{name} {value}" for name, value in scores.items() if isinstance(value, int)
                ),
                "epistemicState": "OBSERVED",
                "sourceUrl": run.get("finalUrl"),
                "excerpt": None,
                "observedAt": str(
                    run.get("fetchTime") or measurement.get("measuredAt") or observed_at
                ),
                "detail": {
                    "instrument": {
                        "name": measurement.get("instrument"),
                        "lighthouseVersion": run.get("lighthouseVersion"),
                    },
                    "conditions": {
                        "strategy": run.get("strategy"),
                        "formFactor": run.get("formFactor"),
                        "throttling": run.get("throttling"),
                        "page": run.get("finalUrl"),
                    },
                    "measuredAt": run.get("fetchTime"),
                    "sample": "One lab run of the home page",
                    "uncertainty": "A lab run with a simulated device and network: scores vary "
                    "a few points between runs, and real visitors' experience may differ "
                    "(that is CrUX's field data).",
                    "scores": dict(scores),
                    "failing": run.get("failing"),
                    "notSearchPosition": True,
                },
            }
        )
    return out


def security_discoveries(
    measurement: Mapping[str, object], *, observed_at: str
) -> list[dict[str, object]]:
    """Mozilla's HTTP Observatory grade of its website (spec 106): one OBSERVED finding."""
    scan = measurement.get("scan")
    if not isinstance(scan, Mapping) or not scan.get("grade"):
        return []
    return [
        {
            "kind": "WEB_REPRESENTATION",
            "code": "SECURITY_HEADERS_GRADE",
            "statement": str(scan.get("grade")),
            "epistemicState": "OBSERVED",
            "sourceUrl": scan.get("detailsUrl"),
            "excerpt": None,
            "observedAt": str(
                scan.get("scannedAt") or measurement.get("measuredAt") or observed_at
            ),
            "detail": {
                "instrument": {"name": measurement.get("instrument")},
                "conditions": {
                    "host": measurement.get("host"),
                    "checks": scan.get("testsQuantity"),
                },
                "measuredAt": scan.get("scannedAt"),
                "sample": "One scan of the site's HTTPS and security headers",
                "uncertainty": "Grades HTTPS redirection, HSTS, content security policy and other "
                "headers as Mozilla's Observatory weighs them; not a penetration test nor a "
                "search position.",
                "grade": scan.get("grade"),
                "score": scan.get("score"),
                "testsPassed": scan.get("testsPassed"),
                "testsFailed": scan.get("testsFailed"),
                "testsQuantity": scan.get("testsQuantity"),
                "notSearchPosition": True,
            },
        }
    ]
