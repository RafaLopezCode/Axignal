"""The archived history of an organization's website, as a finding (spec 102).

From the Internet Archive's monthly captures of the home page: since when the domain is
archived (never the organization's founding date: a domain may have had an earlier owner,
as huel.com and bombas.com did), when it was last archived, and how often its home page
changed (distinct content digests among successful captures, overall and in the last
twelve months). Without a successful capture in the last twelve months (a home page that
redirects is archived as a redirect) the recent changes are UNKNOWN, never zero. Archiving
is sampled: a month without a capture is not a month without a website, and a changed
digest may be a small edit.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

UNCERTAINTY = (
    "The Internet Archive samples the web: the first capture dates the domain, which may have "
    "had an earlier owner, not the organization; months without captures are not months "
    "without a website, and a changed home page may be a small edit."
)


def summarize(captures: Sequence[tuple[str, str, str]], *, today: date) -> dict[str, object]:
    """First and last capture, and home-page versions (overall and in the last 12 months)."""
    if not captures:
        return {"captures": 0}
    ok = [c for c in captures if c[1] == "200"]
    versions = 0
    recent_versions = 0
    previous: str | None = None
    since = date(today.year - 1, today.month, 1).strftime("%Y%m")
    for stamp, _status, digest in ok:
        if digest != previous:
            versions += 1
            if stamp[:6] >= since:
                recent_versions += 1
        previous = digest
    return {
        "captures": len(captures),
        "firstCapture": _iso(captures[0][0]),
        "lastCapture": _iso(captures[-1][0]),
        "successfulMonths": len(ok),
        "homeVersions": versions,
        # No successful capture in 12 months (a redirecting home page): unknown, not zero.
        "homeVersionsLast12Months": recent_versions if any(c[0][:6] >= since for c in ok) else None,
        "monthsCapturedLast12Months": sum(1 for c in ok if c[0][:6] >= since),
    }


def _iso(stamp: str) -> str:
    return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"


def history_discoveries(
    measurement: Mapping[str, object], *, observed_at: str
) -> list[dict[str, object]]:
    summary = measurement.get("summary")
    if not isinstance(summary, Mapping):
        return []
    archived = int(str(summary.get("captures") or 0)) > 0
    return [
        {
            "kind": "OPERATING_SIGNAL",
            "code": "WEBSITE_HISTORY" if archived else "WEBSITE_NOT_ARCHIVED",
            "statement": str(summary.get("firstCapture") or ""),
            "epistemicState": "OBSERVED",
            "sourceUrl": f"https://web.archive.org/web/*/{measurement.get('host')}"
            if archived
            else None,
            "excerpt": None,
            "observedAt": str(measurement.get("measuredAt") or observed_at),
            "detail": {
                "instrument": measurement.get("instrument"),
                "conditions": {
                    "host": measurement.get("host"),
                    "page": "home",
                    "collapse": "one capture per month",
                },
                "measuredAt": measurement.get("measuredAt"),
                "sample": "The archive's monthly captures of the home page",
                "uncertainty": UNCERTAINTY,
                **dict(summary),
            },
        }
    ]
