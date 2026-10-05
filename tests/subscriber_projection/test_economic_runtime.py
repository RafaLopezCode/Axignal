from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from application.economic_discovery.brain_contracts import AttentionDisposition
from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.subscriber_projection.economic_output import EconomicHumanOutput
from application.subscriber_projection.economic_runtime import (
    attach_economic_output,
    economic_output_runtime_signal,
)
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState

NOW = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)


def _output(*, epistemic: XignalEpistemicState = XignalEpistemicState.POTENTIAL):
    basis = ExplainableBasis(
        basis_id="basis:economic:1",
        subject_id="org:supplier",
        candidate_id="candidate:1",
        semantic_target="capability_need_opportunity",
        state_fingerprint="state:1",
        contract_fingerprint="contract:1",
        evaluated_at=NOW,
        data=(
            BasisDatum(
                datum_id="datum:1",
                observation_id="obs:supplier:1",
                source_ref="https://supplier.example/capability",
                source_type="OFFICIAL_WEB",
                observed_at=NOW,
                excerpt_or_summary="Supplier states CNC machining capability.",
                contribution=BasisContribution.SUPPORTS,
            ),
            BasisDatum(
                datum_id="datum:2",
                observation_id="obs:need:1",
                source_ref="https://buyer.example/project",
                source_type="OFFICIAL_WEB",
                observed_at=NOW,
                excerpt_or_summary="Project states a CNC machining need.",
                contribution=BasisContribution.SUPPORTS,
            ),
        ),
        interpretation="Potential functional relevance warrants attention.",
        uncertainty="Price and capacity remain unassessed.",
    )
    candidate = SimpleNamespace(
        candidate_id="candidate:1",
        subject=SimpleNamespace(
            state=SimpleNamespace(subject_id="org:supplier"),
            observations=(),
        ),
        activity=SimpleNamespace(
            state=SimpleNamespace(subject_id="org:need"),
            observations=(),
        ),
        as_of=NOW,
    )
    result = SimpleNamespace(
        candidate=candidate,
        vector=SimpleNamespace(
            state_fingerprint="state:1",
            evaluated_at=NOW,
            evaluations=(),
        ),
        interpretation=SimpleNamespace(
            epistemic_state=epistemic,
            attention=(
                AttentionDisposition.WARRANTED_ATTENTION
                if epistemic is XignalEpistemicState.POTENTIAL
                else AttentionDisposition.INVESTIGATE
            ),
            reason_codes=("ALIGNED_CAPABILITY_NEED_WITH_REACH_WINDOW_AND_ELIGIBILITY",),
            policy_version="capability-announced-need:v1",
        ),
        basis=basis,
        dimension_bases=(),
        raw_judgments=(),
    )
    return EconomicHumanOutput(
        output_id="economic-output:abc123",
        result=result,
        headline=(
            "Potential project relevance"
            if epistemic is XignalEpistemicState.POTENTIAL
            else "Project relevance remains unresolved"
        ),
        one_sentence_meaning="CNC machining could address the stated project need.",
        why_it_may_matter="The available public evidence warrants investigation.",
        temporal_state=Currentness.CURRENT,
        unknowns=("Price has not been assessed.",),
        contradictions=(),
    )


def _projection() -> dict[str, object]:
    return {
        "realityLevel": "CONTROLLED_PRODUCT_PROOF",
        "runtimeCodeSha": "sha",
        "lifecycleStatus": "LIVE",
        "context": {"id": "xeed:1", "label": "Supplier"},
        "organization": {"id": "org:supplier", "name": "Supplier"},
        "nodes": [],
        "temporalHistory": {"disposition": "EMPTY", "items": []},
        "memberships": [],
        "today": {"disposition": "EMPTY", "items": []},
        "reloadContinuity": "PERSISTED_RUNTIME_READ_MODEL",
    }


def test_economic_output_compiles_into_existing_runtime_signal_contract() -> None:
    signal = economic_output_runtime_signal(_output())

    assert signal["nodeKind"] == "XIGNAL"
    assert signal["epistemicState"] == "POTENTIAL"
    assert signal["currentness"] == "CURRENT"
    assert signal["id"] == "xignal:economic:abc123"
    assert signal["sourceRefs"] == [
        "https://supplier.example/capability",
        "https://buyer.example/project",
    ]
    assert signal["observationSupportRefs"] == []
    narrative = signal["evidenceNarrative"]
    assert isinstance(narrative, dict)
    assert len(narrative["steps"]) == 3
    assert "Price has not been assessed." in signal["uncertainty"]


def test_attach_economic_output_is_copying_idempotent_and_today_visible() -> None:
    original = _projection()
    first = attach_economic_output(original, _output())
    second = attach_economic_output(first, _output())

    assert original["nodes"] == []
    assert len(first["nodes"]) == 1
    assert len(second["nodes"]) == 1
    today = first["today"]
    assert isinstance(today, dict)
    assert today["disposition"] == "READY"
    assert len(today["items"]) == 1
    memberships = first["memberships"]
    assert isinstance(memberships, list)
    assert memberships == [
        {
            "from": "xeed:1",
            "to": "xignal:economic:abc123",
            "meaning": "Xeed observes Xignal",
        }
    ]


def test_unknown_economic_output_remains_unknown_in_product_surface() -> None:
    attached = attach_economic_output(
        _projection(),
        _output(epistemic=XignalEpistemicState.UNKNOWN),
    )
    nodes = attached["nodes"]
    assert isinstance(nodes, list)
    assert nodes[0]["epistemicState"] == "UNKNOWN"
    assert nodes[0]["epistemicState"] != "OBSERVED"


def test_economic_output_cannot_cross_organization_context() -> None:
    projection = _projection()
    organization = projection["organization"]
    assert isinstance(organization, dict)
    organization["id"] = "org:other"

    with pytest.raises(ValueError, match="must match subscriber organization"):
        attach_economic_output(projection, _output())
