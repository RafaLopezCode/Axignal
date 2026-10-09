"""Adversarial regression for spec 063 First Proof rights after admission.

Registered content rights revoked at read must not outlive the grant; an
unregistered private observation remains on its separate bounded baseline.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.first_observation.rights import NoContentRights
from tests.first_observation.harness import SOLAR_ES, World, build, runtime
from tests.first_observation.test_first_observation_e2e import _attend, _pending_id, _view
from tests.first_observation.test_understanding_rights import EXAMPLE_HOSTS, _measured


def test_registered_rights_withdrawal_hides_first_proof_immediately_everywhere(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    initial = _view(facade, token, focus)
    assert initial["firstProofReady"] and any(d["excerpt"] for d in initial["discoveries"])
    initial_text = json.dumps(initial["discoveries"], ensure_ascii=False)
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    withdrawn = _view(facade, token, focus)
    assert not withdrawn["firstProofReady"]
    assert withdrawn["state"] == "SOURCE_UNAVAILABLE"
    assert [d["code"] for d in withdrawn["discoveries"]] == ["CONTENT_RIGHTS_WITHDRAWN"]
    assert not withdrawn["attentionScopes"]
    assert not any(d["excerpt"] for d in withdrawn["discoveries"])
    assert json.dumps(withdrawn["discoveries"], ensure_ascii=False) != initial_text

    context = facade.identity.authenticate(token)
    header = runtime(facade).summary(context, focus)
    assert header is not None
    assert not header["firstProofReady"] and header["headline"] is None

    # No old first-proof quotation may reenter an AXENT-authorized reading.
    from domain.identity import XeedId

    axent = facade.axent.service.reader.read(context, XeedId(focus), datetime.now(UTC))
    # The First Proof path in the authorized reader must be redacted. Other
    # independently published economic outputs have separate access contracts.
    observed = axent.projection.get("firstObservation")
    if observed is not None:
        assert [d["code"] for d in observed["discoveries"]] == ["CONTENT_RIGHTS_WITHDRAWN"]
    assert axent.projection["publicUnderstanding"]["citations"] == []

    # Purge physically removes the old page-derived claims from First Proof.
    assert runtime(facade).purge()["proofs"] >= 1
    internal = runtime(facade).store.proof(str(context.tenant_id), focus)
    assert internal is not None
    assert not internal["firstProofReady"]
    assert [d["code"] for d in internal["discoveries"]] == ["CONTENT_RIGHTS_WITHDRAWN"]
    assert not internal["capabilities"]


def test_provider_only_revocation_does_not_withdraw_first_proof(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    baseline = _view(facade, token, focus)
    rights.write(hosts=EXAMPLE_HOSTS, provider=False)
    still = _view(facade, token, focus)
    assert still["firstProofReady"] == baseline["firstProofReady"]
    assert still["discoveries"] == baseline["discoveries"]


def test_unregistered_private_first_proof_remains_displayable(tmp_path: Path) -> None:
    facade = build(tmp_path, World(), rights=NoContentRights())
    token, _ = _attend(facade, tmp_path, "subject:private-baseline", SOLAR_ES)
    runtime(facade).drain()
    focus = _pending_id(facade, token)
    before = _view(facade, token, focus)
    assert before["firstProofReady"]
    after = _view(facade, token, focus)
    assert after["discoveries"] == before["discoveries"]
    assert any(d["excerpt"] for d in after["discoveries"])
