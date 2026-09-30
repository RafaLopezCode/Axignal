"""FR-20 policy promotion / rollback gate contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "application" / "economic_discovery" / "policy_governance.py"
STORE = ROOT / "pipeline" / "policy_governance" / "sqlite_store.py"


def test_promotion_requires_explicit_governance_approval_and_holdout_evidence() -> None:
    source = APP.read_text(encoding="utf-8")

    assert "class GovernanceApproval" in source
    assert "class PromotionGatePolicy" in source
    assert "comparison_fingerprint(report)" in source
    assert "policy promotion requires explicit APPROVE decision" in source
    assert "promotion evidence has insufficient evaluated holdout cases" in source
    assert "promotion evidence exceeds non-replayable case limit" in source
    assert "promotion evidence contains governed regressions" in source
    assert "promotion report metrics do not match sealed evaluations" in source
    assert "candidate baseline is stale relative to active production policy" in source


def test_runtime_yield_and_learning_memory_are_not_promotion_authorities() -> None:
    source = APP.read_text(encoding="utf-8")

    assert "LearningYield" not in source
    assert "LearningMemory" not in source
    assert "candidate: PolicyCandidate" in source
    assert "report: PolicyComparisonReport" in source
    assert "approval: GovernanceApproval" in source


def test_canary_and_action_scoped_approval_are_enforced() -> None:
    source = APP.read_text(encoding="utf-8")

    assert "class RolloutMode" in source
    assert "CANARY" in source
    assert "promotion gate requires canary rollout" in source
    assert "class GovernanceAction" in source
    assert "policy promotion requires a promotion-scoped approval" in source
    assert "policy rollback requires a rollback-scoped approval" in source
    assert "rollback approval targets a different promotion decision" in source


def test_rollback_is_append_only_and_has_explicit_history_pointer() -> None:
    source = APP.read_text(encoding="utf-8")
    store = STORE.read_text(encoding="utf-8")

    assert "rollback_of: str | None" in source
    assert "previous_decision_id: str | None" in source
    assert "GOVERNED_POLICY_ROLLBACK" in source
    assert "append_and_activate(record)" in source
    assert "DELETE FROM policy_decisions" not in store
    assert "UPDATE policy_decisions" not in store
    assert "INSERT INTO policy_decisions" in store


def test_durable_store_updates_decision_and_active_pointer_atomically() -> None:
    store = STORE.read_text(encoding="utf-8")

    assert 'connection.execute("BEGIN IMMEDIATE")' in store
    assert "policy_decisions" in store
    assert "active_policies" in store
    assert "policy decision from-policy does not match current active pointer" in store
    assert "policy decision previous pointer does not match durable history" in store
    assert "idempotent decision does not match active policy pointer" in store


def test_durable_decision_record_contains_full_approval_trace() -> None:
    source = APP.read_text(encoding="utf-8")

    for field in (
        "approved_by: str",
        "approved_at: datetime",
        "approval_rationale: str",
        "approval_id: str",
        "approval_action: GovernanceAction",
        "candidate_fingerprint: str",
        "comparison_fingerprint: str",
        "gate_policy_id: str",
        "gate_policy_version: str",
    ):
        assert field in source
