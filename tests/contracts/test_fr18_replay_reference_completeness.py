"""FR-18 replay reference completeness contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_learning_event_has_explicit_replay_contract() -> None:
    script = (ROOT / "application" / "economic_discovery" / "learning_memory.py").read_text(
        encoding="utf-8"
    )

    assert "class ReplayDisposition" in script
    assert "class LearningReplayReference" in script
    assert 'REPLAYABLE = "REPLAYABLE"' in script
    assert 'NON_REPLAYABLE = "NON_REPLAYABLE"' in script
    assert "replay: LearningReplayReference" in script
    assert "def require(self, name: str, expected: str | None = None)" in script


def test_prime_execution_records_replay_inputs_not_fingerprints_alone() -> None:
    script = (ROOT / "application" / "economic_discovery" / "prime_execution.py").read_text(
        encoding="utf-8"
    )

    assert "LearningReplayReference.replayable(" in script
    assert "artifact_ref=observation.raw_observation_ref" in script
    assert "representation_artifact_ref=representation.artifact_ref" in script
    assert "representation_version=representation.representation_version" in script
    assert "normalization_version=representation.normalization_version" in script
    assert "source_policy_fingerprint=request.policy_fingerprint" in script
    assert "routing_policy_version=item.policy_version" in script
    assert "state_fingerprint=rich_state.fingerprint" in script


def test_provider_bound_work_is_non_replayable_without_model_and_harness_refs() -> None:
    script = (ROOT / "application" / "economic_discovery" / "prime_execution.py").read_text(
        encoding="utf-8"
    )

    assert '"PROVIDER_MODEL_OR_HARNESS_REFERENCE_UNAVAILABLE"' in script
    assert "provider=candidate_set.provider" in script
    assert "provider_version=candidate_set.provider_version" in script


def test_bootstrap_and_budget_stops_declare_why_exact_replay_is_unavailable() -> None:
    runtime = (ROOT / "application" / "xeed_germination" / "runtime.py").read_text(encoding="utf-8")
    budget = (ROOT / "application" / "economic_discovery" / "execution_learning.py").read_text(
        encoding="utf-8"
    )

    assert '"BOOTSTRAP_PLAN_PAYLOAD_NOT_RETAINED"' in runtime
    assert "plan_fingerprint=plan.plan_fingerprint" in runtime
    assert '"EXECUTION_BUDGET_STATE_PAYLOAD_NOT_RETAINED"' in budget
    assert "execution_budget_policy_fingerprint=policy.fingerprint" in budget


def test_learning_store_persists_replay_classification_and_legacy_fallback() -> None:
    store = (ROOT / "pipeline" / "learning_memory" / "sqlite_store.py").read_text(encoding="utf-8")

    assert '"disposition": event.replay.disposition.value' in store
    assert '"references": list(event.replay.references)' in store
    assert 'data.get("replay")' in store
    assert '"REPLAY_REFERENCE_NOT_RECORDED"' in store
