"""FR-23 identity-resolution hardening contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESOLVER = ROOT / "pipeline" / "entity_resolution" / "resolver.py"
GOVERNANCE = ROOT / "application" / "identity_resolution" / "governance.py"
STORE = ROOT / "pipeline" / "entity_resolution" / "sqlite_store.py"


def test_resolver_preserves_ambiguity_instead_of_first_match_wins() -> None:
    source = RESOLVER.read_text(encoding="utf-8")

    assert "ResolutionStatus.AMBIGUOUS" in source
    assert "NAME_OR_ALIAS_COLLISION" in source
    assert "VERIFIED_IDENTIFIER_COLLISION" in source
    assert "setdefault(normalize_name(candidate.canonical_name), candidate)" not in source


def test_resolution_can_use_verified_identifier_and_alias_without_fuzzy_score() -> None:
    source = RESOLVER.read_text(encoding="utf-8")

    assert "VerifiedIdentifier" in source
    assert "candidate.aliases" in source
    assert "VERIFIED_IDENTIFIER_EXACT" in source
    assert "fuzzy" not in source.lower()
    assert "confidence" not in source.lower()
    assert "score" not in source.lower()


def test_identity_authority_has_no_subscriber_or_xeed_scope() -> None:
    source = GOVERNANCE.read_text(encoding="utf-8")

    for forbidden in (
        "subscriber_id",
        "tenant_id",
        "xeed_id",
        "account_id",
        "profile_owner",
    ):
        assert forbidden not in source
    assert "IdentityDecisionAuthority" in source
    assert 'GOVERNED_HUMAN = "GOVERNED_HUMAN"' in source
    assert 'DETERMINISTIC_POLICY = "DETERMINISTIC_POLICY"' in source


def test_merge_split_reversal_and_revalidation_are_explicit() -> None:
    source = GOVERNANCE.read_text(encoding="utf-8")

    assert 'MERGE = "MERGE"' in source
    assert 'SPLIT = "SPLIT"' in source
    assert 'REVERSAL = "REVERSAL"' in source
    assert "reverses_decision_id" in source
    assert "requires_revalidation_ids" in source
    assert "identity subject is ambiguous after split" in source


def test_identity_decision_history_is_append_only() -> None:
    source = STORE.read_text(encoding="utf-8")

    assert "INSERT INTO identity_decisions" in source
    assert "DELETE FROM identity_decisions" not in source
    assert "UPDATE identity_decisions" not in source
    assert 'connection.execute("BEGIN IMMEDIATE")' in source
    assert "identity decision previous pointer does not match durable history" in source


def test_shared_observation_requires_exact_current_subject() -> None:
    source = GOVERNANCE.read_text(encoding="utf-8")

    assert "observation_matches_current_subject" in source
    assert "observation_subject_id == current.organization_id" in source
    assert "historical observations are never silently rebound" in source
