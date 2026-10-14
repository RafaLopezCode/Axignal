"""MCP for a subscriber's assistant: interpret everything AXIGNAL holds about an organization."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from application.product_mcp.oauth import McpGrant
from application.product_mcp.panorama import finding_id
from application.product_mcp.server import ProductMcpServer, XeedSummary
from application.timeline import history as timeline_history
from domain.identity import PrincipalId, TenantId

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
GRANT = McpGrant("g1", PrincipalId("p1"), TenantId("t1"), "client", "read", "https://x/mcp", NOW)


def _d(kind: str, code: str, statement: str, state: str = "OBSERVED", at: str = "2026-10-13",
       **detail: Any) -> dict[str, Any]:  # fmt: skip
    return {"kind": kind, "code": code, "statement": statement, "epistemicState": state,
            "sourceUrl": f"https://src/{code}", "excerpt": "quoted", "observedAt": at,
            "detail": detail}  # fmt: skip


RIVAL = _d("COMPETITION", "WINS_IN_SAME_CODES", "Rival SA")
BUYER = _d("DEMAND", "RECURRING_PUBLIC_BUYER", "City council", "POTENTIAL")
VIEW = {
    "state": "FIRST_PROOF_READY",
    "timeline": {"firstDay": "2026-09-01", "days": 30, "baselineDay": "2026-10-06"},
    "publicUnderstanding": {"status": "MEASURED", "measuredAt": "2026-10-12",
                            "dimensions": [{"dimension": "OFFER", "state": "CLEAR", "cause": None}],
                            "history": [{}], "comparison": {"state": "COMPARABLE", "changes": []}},
    "discoveries": [
        _d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED", "Acme", ownSiteVersion="own-site-v1"),
        _d("WEB_REPRESENTATION", "AUDIT", "Audit", audit={"huge": "payload"}),
        _d("GENERATIVE_VISIBILITY", "AI_NAMED_FOR_CATEGORY", "1/4 answers"),
        _d("RELATIONSHIP", "TECHNOLOGY_SUPPLIER_OBSERVED", "HubSpot", category="CRM_MARKETING",
           ownSiteVersion="own-site-v1", limitation="No contract established."),
        RIVAL, BUYER,
        _d("CREDENTIAL", "CERTIFICATION_CLAIMED", "ISO 9001", "DECLARED"),
        _d("ECONOMIC_FACT", "WIKIDATA:revenue", "12M", at="2024-01-01"),
        _d("SIGNIFICANT_UNKNOWN", "NO_PRESS_MENTION_FOUND", "No headline names it", "UNKNOWN"),
        _d("INXIGHT", "relationships:COMPETITORS_WIN_WITH_ITS_BUYERS", "Rival wins there",
           "POTENTIAL", rule="COMPETITORS_WIN_WITH_ITS_BUYERS", why="The door is open.",
           evidence=[{k: RIVAL[k] for k in ("kind", "code", "statement", "sourceUrl")},
                     {k: BUYER[k] for k in ("kind", "code", "statement", "sourceUrl")}],
           evidenceCount=2),
        _d("INXIGHT", "organization:FOUNDING_YEAR_SOURCES_DISAGREE", "1998 vs 2001", "POTENTIAL",
           rule="FOUNDING_YEAR_SOURCES_DISAGREE"),
        _d("CHANGE", "presence:presence.ai_named_share:EVOLUTION", "0.25 -> 0.5"),
        _d("CHANGE", "presence:presence.lcp_ms:REGRESSION", "1800 -> 3200"),
    ],
}  # fmt: skip
SNAPSHOTS = [
    ("2026-09-01", {"relationships.technology": ["HubSpot"], "activity.job_postings": 0}),
    ("2026-09-15", {"relationships.technology": ["HubSpot"]}),
    ("2026-10-13", {"relationships.technology": ["Salesforce"], "activity.job_postings": 4}),
]


class _Memory:
    def authorized_xeeds(self, context: object, *, now: datetime) -> tuple[XeedSummary, ...]:
        return (XeedSummary("focus_1", "Acme"),)

    def reading(self, context: object, xeed_id: str, *, now: datetime) -> dict[str, Any]:
        return {"state": "success", "projection": {}, "firstObservation": VIEW}

    def history(self, context: object, xeed_id: str, *, family: str | None = None) -> Any:
        return timeline_history(SNAPSHOTS, family=family)


def _call(tool: str, **arguments: object) -> dict[str, Any]:
    server = ProductMcpServer(_Memory(), clock=lambda: NOW)  # type: ignore[arg-type]
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments}}  # fmt: skip
    response = server.handle(message, grant=GRANT)
    assert response is not None
    result: dict[str, Any] = response["result"]  # type: ignore[assignment]
    return {"isError": result["isError"], **result["structuredContent"]}


def test_panorama_reads_each_family_by_observability_and_frontier_never_a_score() -> None:
    page = _call("get_organization_panorama", organization_id="focus_1")
    assert page["organization"] == "Acme" and "value report" in page["report_guide"]
    by = {f["family"]: f for f in page["families"]}
    assert len(by) == 10
    assert by["presence"]["observability"] == "STRONG"
    assert by["value"]["observability"] == "PARTIAL"
    assert "Only the organization's own claims" in by["value"]["frontier"][0]
    assert by["reputation"]["observability"] == "LIMITED"
    assert by["reputation"]["frontier"] == ["No headline names it"]
    assert by["economics"]["observability"] == "STALE"  # newest figure is from 2024
    assert by["organization"]["observability"] == "CONFLICTING"
    assert by["markets"]["observability"] == "UNKNOWN"
    assert "1 possibilities not yet confirmed (POTENTIAL)." in by["demand"]["frontier"]


def test_crossings_are_traced_to_their_findings_and_regressions_lead() -> None:
    page = _call("get_organization_panorama", organization_id="focus_1")
    crossing = page["signals"]["crossings"][0]
    assert crossing["supported_by"] == [finding_id(RIVAL), finding_id(BUYER)]
    assert crossing["why"] == "The door is open."
    relationships = _call("get_organization_findings", organization_id="focus_1",
                          family="relationships")  # fmt: skip
    ids = {i["id"] for i in relationships["items"]}
    assert finding_id(RIVAL) in ids  # the agent can open what supports the crossing
    assert [c["code"].rsplit(":", 1)[-1] for c in page["signals"]["changes"]] == [
        "REGRESSION", "EVOLUTION"
    ]  # fmt: skip
    assert page["record"]["instruments"] == ["own-site-v1"]
    assert page["public_understanding"]["earlier_reports"] == 1


def test_findings_carry_instrument_and_limitation_never_raw_payloads() -> None:
    page = _call("get_organization_findings", organization_id="focus_1", family="presence")
    audit = next(i for i in page["items"] if i["code"] == "AUDIT")
    assert audit["detail"] == {}
    tech = _call("get_organization_findings", organization_id="focus_1", family="relationships")
    hub = next(i for i in tech["items"] if i["statement"] == "HubSpot")
    assert hub["instrument"] == "own-site-v1" and hub["limitation"] == "No contract established."


def test_history_answers_when_things_appeared_and_since_last_report() -> None:
    full = _call("get_organization_history", organization_id="focus_1")
    assert full["days_recorded"] == 3
    assert full["series"]["activity.job_postings"] == [["2026-09-01", 0], ["2026-10-13", 4]]
    since = _call("get_organization_history", organization_id="focus_1", since="2026-10-01")
    assert [e["day"] for e in since["events"]] == ["2026-10-13"]
    assert since["events"][0]["added"] == ["Salesforce"]
    assert since["events"][0]["removed"] == ["HubSpot"]
    # The last reading before `since` stays as the starting point of each series.
    assert since["series"]["activity.job_postings"] == [["2026-09-01", 0], ["2026-10-13", 4]]
    assert since["summary"]["relationships"] == {"added": 1, "removed": 1}
    assert since["summary"]["activity"]["metrics_moved"] == 1


def test_everything_fails_closed() -> None:
    assert _call("get_organization_panorama", organization_id="other")["error"] == (
        "XEED_NOT_AVAILABLE"
    )
    assert _call("get_organization_findings", organization_id="focus_1", family="gossip")["isError"]
    assert _call("get_organization_findings", organization_id="focus_1")["isError"]
    assert _call("get_organization_history", organization_id="focus_1", since="last week")[
        "isError"
    ]
    assert _call("get_organization_panorama", organization_id="focus_1", extra=1)["isError"]


def test_public_vocabulary_and_read_only() -> None:
    server = ProductMcpServer(_Memory(), clock=lambda: NOW)  # type: ignore[arg-type]
    listed = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, grant=GRANT)
    tools = {t["name"]: t for t in listed["result"]["tools"]}  # type: ignore[index]
    for name in ("list_organizations", "get_organization_panorama",
                 "get_organization_findings", "get_organization_history",
                 "get_potential_buyers"):  # fmt: skip
        assert tools[name]["annotations"]["readOnlyHint"] is True
        assert "xeed" not in str(tools[name]).lower()
    assert _call("list_organizations")["organizations"] == [
        {"organization_id": "focus_1", "organization": "Acme"}
    ]


def test_potential_buyers_keep_each_signal_and_are_never_a_score(monkeypatch: Any) -> None:
    buyer = _d("DEMAND", "POTENTIAL_BUYER", "Endesa", "POTENTIAL",
               signalTypes=["CUSTOMER_OF_COMPETITOR", "SIMILAR_TO_CUSTOMERS"],
               signals=[{"type": "CUSTOMER_OF_COMPETITOR", "via": "Rival SA",
                         "sourceUrl": "https://award", "observedAt": "2026-10-01"}],
               identifiers={"wikidata": "Q8"})  # fmt: skip
    monkeypatch.setitem(VIEW, "discoveries", [*VIEW["discoveries"], buyer])  # type: ignore[list-item]
    page = _call("get_potential_buyers", organization_id="focus_1")
    assert not page["isError"] and "never a customer" in page["how_to_read"]
    assert page["buyers"] == [{
        "finding_id": finding_id(buyer), "organization": "Endesa",
        "signal_types": ["CUSTOMER_OF_COMPETITOR", "SIMILAR_TO_CUSTOMERS"],
        "signals": buyer["detail"]["signals"], "identifiers": {"wikidata": "Q8"},
    }]  # fmt: skip
    assert page["unknown"] is None
    assert _call("get_potential_buyers", organization_id="other")["error"] == "XEED_NOT_AVAILABLE"
