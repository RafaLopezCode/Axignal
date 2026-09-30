from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.xeed_germination import (
    EvidenceSupportClass,
    InvestigationFinding,
)
from domain.evidence.admission import Evidence, SourceAuthority
from domain.identity import FaxtId, OrganizationId
from experiments.decision_lab.germination_jev_judge import JevEvidenceSupportJudge
from experiments.decision_lab.models import LabError, NormalizedJudgment, OperationalFailure


def finding() -> InvestigationFinding:
    return InvestigationFinding(
        faxt_id=FaxtId("faxt-carrier-cold-chain"),
        subject_id=OrganizationId("org-carrier"),
        predicate="capability",
        object_or_value="temperature-controlled cold-chain transport",
        claim_proposition="Carrier provides cold-chain solutions for temperature-controlled transport.",
        evidence=Evidence(
            id="ev-carrier-cold-chain",
            source="Carrier",
            source_type="official_web",
            reference="https://www.carrier.com/us/en/cold-chain/",
            extracted_claim=(
                "Carrier's cold chain solutions help ensure intelligent, connected, "
                "temperature-controlled transport and monitoring across the end-to-end cold chain."
            ),
            observed_at=datetime(2026, 9, 30, tzinfo=UTC),
            authority=SourceAuthority.OFFICIAL_WEB,
        ),
    )


class FakeEvaluator:
    def __init__(self, selected: str = "SUPPORTED") -> None:
        self.selected = selected
        self.state: dict[str, object] | None = None

    def evaluate(
        self, request: object, *, model: str
    ) -> tuple[list[NormalizedJudgment], None, dict[str, object]]:
        state, question = request.provider_payload()  # type: ignore[attr-defined]
        self.state = state
        assert model == "jev-1.13.0"
        assert question["question_id"] == "CES.SUPPORT.vNext.2"
        return (
            [
                NormalizedJudgment(
                    "CES.SUPPORT.vNext.2",
                    "CHOICE",
                    self.selected,
                    distribution={self.selected: 1.0},
                    evaluator="fake",
                    requested_model=model,
                    resolved_model=model,
                )
            ],
            None,
            {},
        )


class FailingEvaluator:
    def evaluate(
        self, request: object, *, model: str
    ) -> tuple[list[NormalizedJudgment], OperationalFailure, dict[str, object]]:
        return [], OperationalFailure("TIMEOUT", retryable=True), {}


def test_jev_judge_sends_claim_semantics_and_exact_evidence_not_identifiers_only() -> None:
    evaluator = FakeEvaluator()
    judge = JevEvidenceSupportJudge(evaluator)  # type: ignore[arg-type]

    result = judge.judge(finding())

    assert result.support is EvidenceSupportClass.SUPPORTED
    assert result.raw_reference is not None
    assert result.state_fingerprint is not None
    assert result.question_fingerprint is not None
    assert result.model == "jev-1.13.0"
    assert result.distribution == (("SUPPORTED", 1.0),)
    assert evaluator.state is not None
    assert evaluator.state["claim"] == {
        "proposition": "Carrier provides cold-chain solutions for temperature-controlled transport."
    }
    evidence = evaluator.state["evidence"]
    assert isinstance(evidence, list)
    assert "temperature-controlled transport" in evidence[0]["content"]
    assert evidence[0]["provenance"]["source_ref"].startswith("https://")


def test_non_support_is_preserved_as_semantic_class_not_coerced_to_false() -> None:
    judge = JevEvidenceSupportJudge(FakeEvaluator("NO_EVIDENCE"))  # type: ignore[arg-type]

    result = judge.judge(finding())

    assert result.support is EvidenceSupportClass.NO_EVIDENCE


def test_provider_failure_fails_closed_instead_of_becoming_semantic_unknown() -> None:
    judge = JevEvidenceSupportJudge(FailingEvaluator())  # type: ignore[arg-type]

    with pytest.raises(LabError, match="JEV_OPERATIONAL_FAILURE:TIMEOUT"):
        judge.judge(finding())
