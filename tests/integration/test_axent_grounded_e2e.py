"""E2E: authenticated subscribers ask AXENT through the real subscriber HTTP facade.

Two tenants follow the same canonical Organization. Only tenant B has had its
opportunities reobserved. A's questions retrieve only A's authorized reading;
B's opportunities, cache and context never reach A.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest

from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.axent import SqliteResearchRequestLedger
from pipeline.observation_intelligence import UrllibTedTransport
from tests.axent.fixtures import ScriptedLuna
from tests.integration.test_subscriber_composition import (
    _append_opportunity_capability_source,
    _build,
    _commit_verified_projection,
    _register_canonical_organization,
    _signup,
)
from tests.observation_intelligence.ted_fixture import FixtureTedTransport


def _subscriber(facade: Any, tmp_path: Path, subject: str) -> tuple[str, str]:
    token, tenant_id = _signup(facade, subject)
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    _commit_verified_projection(billing, tenant_id, now=datetime.now(UTC))
    added = facade.handle(
        "POST",
        "/subscriber/portfolio",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
        {"action": "add", "requestRef": f"add:{subject}", "locator": "Shared Registry Example SLU"},
    )
    assert added.status == 200
    return token, str(added.body["focusId"])


def _ask(
    facade: Any, token: str, focus: str, question: str, memory: object = None
) -> dict[str, Any]:
    body: dict[str, object] = {"question": question, "locale": "es"}
    if memory is not None:
        body["memory"] = memory
    response = facade.handle(
        "POST",
        f"/subscriber/organizations/{focus}/axent",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
        body,
    )
    assert response.status == 200, response.body
    return cast(dict[str, Any], response.body)


def test_tenant_grounded_axent_end_to_end(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _register_canonical_organization(tmp_path)
    plan = tmp_path / "subscriber-observation-plan.json"
    plan.write_text(
        '[{"organizationId":"org:registry:shared","markets":'
        '[{"jurisdiction":"EU/ES","roles":["PUBLIC_BUYERS"]}]}]',
        encoding="utf-8",
    )
    ted = FixtureTedTransport()
    monkeypatch.setattr(UrllibTedTransport, "post", lambda self, body: ted.post(body))
    facade = _build(tmp_path, observation_plan_path=plan)
    luna = ScriptedLuna()
    facade.axent.service.reasoner = luna

    token_a, focus_a = _subscriber(facade, tmp_path, "subject:tenant-a")
    token_b, focus_b = _subscriber(facade, tmp_path, "subject:tenant-b")
    _append_opportunity_capability_source(tmp_path)
    # Only tenant B reobserves: its opportunities exist only in B's private projection.
    reobserved = facade.handle(
        "POST",
        "/subscriber/portfolio",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token_b}"},
        {"action": "reobserve", "requestRef": "reobserve:b", "focusId": focus_b},
    )
    assert reobserved.status == 200 and reobserved.body["observationState"] == "COMPLETED"

    # Tenant B asks: tenant-scoped retrieval → compact pack → Luna → grounded, cited answer.
    b1 = _ask(facade, token_b, focus_b, "¿Qué oportunidades hay?")
    grounding = b1["grounding"]
    assert grounding["route"] == "MODEL" and grounding["claims"]
    cited = {ref for claim in grounding["claims"] for ref in claim["evidence"]}
    shown = {e["ref"]: e for e in grounding["evidence"]}
    assert cited <= set(shown) and all(shown[r]["source"] for r in cited)
    assert all(claim["epistemic"] == "POTENTIAL" for claim in grounding["claims"])
    assert b1["sourceRefs"] and b1["known"][0].startswith("Potencial · ")
    b_titles = [e["label"] for e in grounding["evidence"]]
    pack = luna.requests[-1].user
    assert "<evidence>" in pack and len(pack) < 4000, "a compact pack, not the whole reading"

    # Follow-up: minimal memory, fresh retrieval, no transcript resent.
    b2 = _ask(facade, token_b, focus_b, "¿Y en Francia?", memory=b1["memory"])
    assert b2["grounding"]["route"] == "ABSTAINED" and b2["grounding"]["research"][
        "geographies"
    ] == ["EU/FR"]
    assert all("¿Qué oportunidades hay?" not in r.user for r in luna.requests[1:])

    # Tenant A asks the same question about the same Organization: B's data is unreachable.
    calls = len(luna.requests)
    a1 = _ask(facade, token_a, focus_a, "¿Qué oportunidades hay?")
    assert a1["grounding"]["route"] == "ABSTAINED" and a1["grounding"]["research"] is not None
    assert not any(title in str(a1) for title in b_titles)
    assert len(luna.requests) == calls, "no evidence, no model call"
    ledger = SqliteResearchRequestLedger(tmp_path / "axent-research.sqlite3")
    tenant_a = facade.identity.authenticate(token_a).tenant_id
    assert ledger.pending(tenant_id=tenant_a, xeed_id=focus_a)

    # Tenant A cannot even address B's focus.
    denied = facade.handle(
        "POST",
        f"/subscriber/organizations/{focus_b}/axent",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token_a}"},
        {"question": "¿Qué oportunidades hay?", "locale": "es"},
    )
    assert denied.status == 403

    # Cached answer reused while evidence is unchanged; invalidated when currentness moves.
    again = _ask(facade, token_b, focus_b, "¿Qué oportunidades hay?")
    assert again["grounding"]["modelCalls"] == 0 and again["grounding"]["claims"]
    later = datetime.now(UTC) + timedelta(days=10)
    facade.axent.service.clock = lambda: later
    aged = _ask(facade, token_b, focus_b, "¿Qué oportunidades hay?")
    assert aged["grounding"]["modelCalls"] == 1, "currentness changed: no cached reuse"
    assert all(c["currentness"] != "CURRENT" for c in aged["grounding"]["claims"])

    # Exact questions never spend a model call.
    count = _ask(facade, token_b, focus_b, "¿Cuántas oportunidades hay?")
    assert count["grounding"]["route"] == "DETERMINISTIC" and count["grounding"]["modelCalls"] == 0
