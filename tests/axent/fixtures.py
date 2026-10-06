"""Two tenants' authorized readings, an authorization-checking reader and scripted Lunas."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from application.axent.grounded import ReasoningRequest, ReasoningResult
from application.xeed_access.reader import ReadFailure, TrustedRequestContext, XeedReadError
from domain.identity import PrincipalId, TenantId, XeedId

NOW = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
TENANT_A = TrustedRequestContext(PrincipalId("principal:a"), TenantId("tenant:a"))
TENANT_B = TrustedRequestContext(PrincipalId("principal:b"), TenantId("tenant:b"))
FOCUS_A = XeedId("focus:a")
FOCUS_B = XeedId("focus:b")


def opportunity(
    oid: str,
    title: str,
    *,
    market: str = "EU/ES",
    epistemic: str = "POTENTIAL",
    currentness: str = "CURRENT",
    observed: datetime = NOW - timedelta(days=1),
    buyer: str = "Ayuntamiento de Getafe",
) -> dict[str, Any]:
    return {
        "id": oid,
        "familyId": "demand",
        "opportunityFamily": "PUBLIC_PROCUREMENT",
        "title": title,
        "buyer": buyer,
        "market": market,
        "deadline": "2026-10-27",
        "epistemic": epistemic,
        "capability": {
            "label": "Solar PV installation",
            "excerpt": "instalaciones fotovoltaicas",
            "sourceId": "obs:home",
        },
        "demand": {"label": title, "code": "09332000", "sourceId": f"opportunity-evidence:{oid}"},
        "unknown": ["technical requirements", "incumbent supplier"],
        "whyPotential": "Published demand matches an observed capability code.",
        "observedAt": observed.isoformat(),
        "currentness": currentness,
    }


def reading(
    *,
    xeed: str,
    organization: str,
    opportunities: list[dict[str, Any]] = (),  # type: ignore[assignment]
    homepage_currentness: str = "CURRENT",
    extra_sources: list[dict[str, Any]] = (),  # type: ignore[assignment]
) -> dict[str, Any]:
    sources = [
        {
            "id": "obs:home",
            "title": f"https://{organization.split()[0].lower()}.example/",
            "observedAt": (NOW - timedelta(days=2)).isoformat(),
            "currentness": homepage_currentness,
            "limitation": "One authorized source observation.",
            "sourceRef": f"https://{organization.split()[0].lower()}.example/",
        },
        *extra_sources,
    ]
    for item in opportunities:
        sources.append(
            {
                "id": f"opportunity-evidence:{item['id']}",
                "title": item["title"],
                "observedAt": item["observedAt"],
                "currentness": item["currentness"],
                "instrument": "ted-search-v3@1",
                "sourceRef": f"https://ted.europa.eu/notice/{item['id']}",
            }
        )
    return {
        "context": {"id": xeed, "label": organization},
        "organization": {"id": f"org:{xeed}", "name": organization},
        "nodes": [],
        "today": {"items": []},
        "temporalHistory": {"items": []},
        "digitalRepresentation": {"state": "NOT_MEASURED", "reason": "No measurement."},
        "cognition": {"sources": sources, "signals": [], "opportunities": list(opportunities)},
    }


@dataclass
class _Read:
    projection: dict[str, object]


@dataclass
class AuthorizingReader:
    """Fails closed like the subscriber read: wrong principal, tenant or Xeed → denied."""

    grants: dict[tuple[str, str], tuple[str, dict[str, Any]]] = field(default_factory=dict)
    reads: list[tuple[str, str]] = field(default_factory=list)

    def grant(self, context: TrustedRequestContext, focus: str, projection: dict[str, Any]) -> None:
        self.grants[(context.principal_id, focus)] = (context.tenant_id, projection)

    def read(
        self, authorized_context: TrustedRequestContext, xeed_id: XeedId, as_of: datetime
    ) -> _Read:
        granted = self.grants.get((authorized_context.principal_id, xeed_id))
        if granted is None or granted[0] != authorized_context.tenant_id:
            raise XeedReadError(ReadFailure.XEED_ACCESS_DENIED)
        self.reads.append((authorized_context.tenant_id, xeed_id))
        return _Read(granted[1])


_LINE = re.compile(r'^(E\d+) (\w+) (\w+) (\w+) \S* "([^"]*)"', re.MULTILINE)


@dataclass
class ScriptedLuna:
    """Stands in for Luna: cites what it is given. ``script`` can make it misbehave."""

    script: Callable[[list[tuple[str, str, str]]], Mapping[str, object]] | None = None
    requests: list[ReasoningRequest] = field(default_factory=list)
    model: str = "gpt-6-luna"

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        self.requests.append(request)
        lines = [(m[0], m[1], m[4]) for m in _LINE.findall(request.user)]
        payload = (
            self.script(lines)
            if self.script
            else {
                "claims": [
                    {"text": f"AXIGNAL observed: {text[:80]}", "refs": [ref]}
                    for ref, kind, text in lines
                    if kind != "GAP"
                ][:3],
                "unknowns": [],
                "insufficient_evidence": not lines,
            }
        )
        return ReasoningResult(payload, self.model, len(request.system + request.user) // 4, 60, 5)
