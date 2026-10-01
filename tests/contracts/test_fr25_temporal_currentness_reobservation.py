"""FR-25 temporal currentness / reobservation contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPORAL = ROOT / "application" / "economic_discovery" / "temporal_currentness.py"
EPISTEMICS = ROOT / "domain" / "evidence" / "epistemics.py"
REUSE = ROOT / "application" / "economic_discovery" / "observation_reuse.py"


def test_currentness_has_explicit_historical_state() -> None:
    source = EPISTEMICS.read_text(encoding="utf-8")

    assert 'CURRENT = "CURRENT"' in source
    assert 'STALE = "STALE"' in source
    assert 'HISTORICAL = "HISTORICAL"' in source
    assert 'UNKNOWN = "UNKNOWN"' in source


def test_temporal_policy_is_versioned_and_deterministic() -> None:
    source = TEMPORAL.read_text(encoding="utf-8")

    assert "class TemporalCurrentnessPolicy" in source
    assert "stale_after" in source
    assert "historical_after" in source
    assert "evaluate_currentness(" in source
    assert "as_of < observation.record.observed_at" in source


def test_reobservation_is_append_only_not_overwrite() -> None:
    source = TEMPORAL.read_text(encoding="utf-8")

    assert "append_reobservation(" in source
    assert "ingest_observation(memory, observation)" in source
    assert "reobservation requires a new observation id" in source
    assert "reobservation predecessor must already exist in Observation Memory" in source
    assert "UPDATE observations" not in source
    assert "DELETE FROM observations" not in source


def test_temporal_change_uses_dependency_aware_reevaluation() -> None:
    source = TEMPORAL.read_text(encoding="utf-8")

    assert 'changed_dependency_fields=frozenset({"source.currentness"})' in source
    assert "affected_temporal_dimensions(" in source
    assert "return affected_dimensions(synthetic, contracts)" in source


def test_reobservation_planning_uses_latest_observation_per_source() -> None:
    source = TEMPORAL.read_text(encoding="utf-8")

    assert "latest_by_source" in source
    assert "memory.for_subject(subject_id)" in source
    assert "reobservation_requirement(" in source


def test_current_use_explicitly_rejects_historical_reuse() -> None:
    source = REUSE.read_text(encoding="utf-8")

    assert "HISTORICAL_FOR_CURRENT_USE" in source
    assert "Currentness.HISTORICAL" in source
