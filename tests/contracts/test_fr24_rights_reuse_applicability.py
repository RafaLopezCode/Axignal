"""FR-24 rights / reuse / applicability contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REUSE = ROOT / "application" / "economic_discovery" / "observation_reuse.py"
MEMORY = ROOT / "application" / "economic_discovery" / "observation_memory.py"
BOOTSTRAP = ROOT / "application" / "xeed_germination" / "bootstrap.py"
PRIME = ROOT / "application" / "economic_discovery" / "prime_execution.py"
SOURCE = ROOT / "application" / "source_acquisition" / "runtime.py"


def test_reuse_gate_requires_rights_provenance_scope_currentness_and_applicability() -> None:
    source = REUSE.read_text(encoding="utf-8")

    for token in (
        "RIGHTS_PROHIBITED",
        "RIGHTS_UNKNOWN",
        "INACCESSIBLE",
        "PROVENANCE_MISSING",
        "RESTRICTED_SCOPE",
        "PRIVATE_SCOPE_GLOBAL_LEAK",
        "PRIVATE_SCOPE_MISMATCH",
        "SUBJECT_NOT_APPLICABLE",
        "PURPOSE_NOT_APPLICABLE",
        "STALE_FOR_CURRENT_USE",
        "CURRENTNESS_UNKNOWN",
    ):
        assert token in source


def test_private_scope_has_explicit_global_world_block() -> None:
    source = REUSE.read_text(encoding="utf-8")

    assert 'GLOBAL_WORLD = "GLOBAL_WORLD"' in source
    assert 'TENANT_PRIVATE = "TENANT_PRIVATE"' in source
    assert "PRIVATE_SCOPE_GLOBAL_LEAK" in source
    assert "authority.scope is ObservationReuseScope.TENANT_PRIVATE" in source


def test_stale_and_inaccessible_are_reuse_states_not_truth_booleans() -> None:
    source = REUSE.read_text(encoding="utf-8")

    assert "STALE_FOR_CURRENT_USE" in source
    assert "INACCESSIBLE" in source
    assert "return False" not in source
    assert "truth_value" not in source


def test_legacy_or_unspecified_observation_reuse_is_restrictive() -> None:
    source = MEMORY.read_text(encoding="utf-8")

    assert "rights_status: ObservationRightsStatus = ObservationRightsStatus.UNKNOWN" in source
    assert "scope: ObservationReuseScope = ObservationReuseScope.RESTRICTED" in source
    assert "currentness: Currentness = Currentness.UNKNOWN" in source


def test_bootstrap_and_prime_validate_reused_rich_state_against_memory() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    prime = PRIME.read_text(encoding="utf-8")

    assert "select_reusable_observations(" in bootstrap
    assert "bootstrap reused state requires Observation Memory and reuse policy" in bootstrap
    assert "bootstrap rich-state provenance does not match reusable observation" in bootstrap

    assert "select_reusable_observations(" in prime
    assert "Prime reused state requires an observation reuse policy" in prime
    assert "Prime prior rich-state provenance does not match reusable observation" in prime


def test_source_acquisition_does_not_grant_reuse_by_default() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "reuse_authority: ObservationReuseAuthority | None = None" in source
    assert "ObservationReuseAuthority()" in source
    assert "reuse_authority = existing.reuse_authority" in source


def test_reuse_gate_does_not_bypass_evidence_admission() -> None:
    source = REUSE.read_text(encoding="utf-8")

    assert "EvidenceAdmission" not in source
    assert "FAXT" not in source
    assert "canonical truth" not in source.lower()
