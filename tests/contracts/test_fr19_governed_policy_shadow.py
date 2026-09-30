"""FR-19 governed policy candidate/replay/shadow contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "application" / "economic_discovery" / "policy_experiment.py"


def test_policy_candidate_and_shadow_have_no_production_authority() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "class PolicyCandidate" in source
    assert "class ShadowPolicy" in source
    assert "def production_authority(self) -> bool:" in source
    assert source.count("return False") >= 3
    assert "promote(" not in source
    assert "EvidenceAdmission" not in source
    assert "ObservationMemory" not in source


def test_candidate_creation_is_development_only_and_holdout_is_sealed() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "class HeldOutPolicySplit" in source
    assert "development_organization_ids" in source
    assert "holdout_organization_ids" in source
    assert "development_end_at" in source
    assert "holdout_start_at" in source
    assert '"policy candidate cannot use holdout or out-of-split evidence"' in source
    assert '"replay comparison cannot inspect development evidence"' in source
    assert "class PolicyReplayInput" in source
    replay_input = source.split("class PolicyReplayInput", 1)[1].split(
        "class OfflinePolicyEvaluator", 1
    )[0]
    assert "source_outcome" not in replay_input
    assert "reason_code" not in replay_input
    assert "output_fingerprint" not in replay_input


def test_replay_evaluation_fails_closed_for_non_replayable_learning_events() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "class ReplayEvaluation" in source
    assert "ReplayDisposition.REPLAYABLE" in source
    assert "PolicyEvaluationStatus.NON_REPLAYABLE" in source
    assert "baseline=None" in source
    assert "candidate=None" in source


def test_comparison_preserves_unknown_abstention_and_negative_runs() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "PolicyDecisionState.UNKNOWN" in source
    assert "PolicyDecisionState.ABSTAIN" in source
    assert "source_failed_cases" in source
    assert "unknown_lost" in source
    assert "abstention_lost" in source
    assert "failure_introduced" in source
    assert "value_disagreements" in source


def test_shadow_evaluator_failure_is_reported_not_dropped() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "def _safe_evaluate(" in source
    assert 'reason_code=f"EVALUATOR_FAILED:{type(exc).__name__}"' in source
    assert "PolicyDecisionState.FAILED" in source
