from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.identity_resolution import (
    IdentityDecisionAuthority,
    IdentityDecisionKind,
    IdentityGovernanceConflict,
    IdentitySubjectState,
    merge_identities,
    observation_matches_current_subject,
    resolve_current_subject,
    reverse_identity_decision,
    split_identity,
)
from domain.identity import OrganizationId
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore

NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def _store(tmp_path) -> SqliteIdentityGovernanceStore:
    store = SqliteIdentityGovernanceStore(tmp_path / "identity.sqlite3")
    for organization_id in ("org-a", "org-b", "org-c", "org-d"):
        assert store.seed_subject(OrganizationId(organization_id)) is True
    return store


def test_merge_redirects_only_through_explicit_append_only_decision(tmp_path) -> None:
    store = _store(tmp_path)

    decision = merge_identities(
        absorbed_organization_ids=(OrganizationId("org-a"),),
        retained_organization_id=OrganizationId("org-b"),
        evidence_refs=("evidence:registry:1",),
        reason_code="VERIFIED_SAME_LEGAL_ENTITY",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:merge:1",
        store=store,
    )

    assert decision.kind is IdentityDecisionKind.MERGE
    pointer = store.current(OrganizationId("org-a"))
    assert pointer is not None
    assert pointer.state is IdentitySubjectState.REDIRECTED
    assert pointer.redirect_to == OrganizationId("org-b")
    assert resolve_current_subject(
        store, OrganizationId("org-a")
    ).organization_id == OrganizationId("org-b")
    assert store.history() == (decision,)


def test_name_or_subscriber_context_cannot_create_identity_decision(tmp_path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="requires evidence"):
        merge_identities(
            absorbed_organization_ids=(OrganizationId("org-a"),),
            retained_organization_id=OrganizationId("org-b"),
            evidence_refs=(),
            reason_code="SUBSCRIBER_SAYS_SAME_COMPANY",
            authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
            decided_by="subscriber:tenant-1",
            decided_at=NOW,
            decision_id="identity:merge:no-evidence",
            store=store,
        )

    assert store.current(OrganizationId("org-a")).state is IdentitySubjectState.ACTIVE
    assert store.history() == ()


def test_split_makes_old_identity_ambiguous_and_never_picks_a_child(tmp_path) -> None:
    store = _store(tmp_path)

    decision = split_identity(
        source_organization_id=OrganizationId("org-a"),
        target_organization_ids=(OrganizationId("org-b"), OrganizationId("org-c")),
        evidence_refs=("evidence:registry:split",),
        reason_code="LEGAL_PERSON_SPLIT_CONFIRMED",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:split:1",
        store=store,
    )

    pointer = store.current(OrganizationId("org-a"))
    assert pointer is not None
    assert pointer.state is IdentitySubjectState.AMBIGUOUS
    assert pointer.redirect_to is None
    assert pointer.requires_revalidation is True
    assert decision.requires_revalidation_ids == (
        OrganizationId("org-a"),
        OrganizationId("org-b"),
        OrganizationId("org-c"),
    )

    with pytest.raises(IdentityGovernanceConflict, match="ambiguous after split"):
        resolve_current_subject(store, OrganizationId("org-a"))


def test_reversal_appends_history_and_restores_merge_without_erasing_original(tmp_path) -> None:
    path = tmp_path / "identity.sqlite3"
    store = SqliteIdentityGovernanceStore(path)
    for organization_id in ("org-a", "org-b"):
        store.seed_subject(OrganizationId(organization_id))

    merge = merge_identities(
        absorbed_organization_ids=(OrganizationId("org-a"),),
        retained_organization_id=OrganizationId("org-b"),
        evidence_refs=("evidence:registry:merge",),
        reason_code="VERIFIED_SAME_LEGAL_ENTITY",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:merge:1",
        store=store,
    )
    reversal = reverse_identity_decision(
        target_decision_id=merge.decision_id,
        evidence_refs=("evidence:registry:correction",),
        reason_code="ERRONEOUS_MERGE_CORRECTED",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:2",
        decided_at=NOW + timedelta(hours=1),
        decision_id="identity:reversal:1",
        store=store,
    )

    assert reversal.kind is IdentityDecisionKind.REVERSAL
    assert reversal.reverses_decision_id == merge.decision_id
    assert store.current(OrganizationId("org-a")).state is IdentitySubjectState.ACTIVE
    assert store.current(OrganizationId("org-b")).state is IdentitySubjectState.ACTIVE
    assert store.current(OrganizationId("org-a")).requires_revalidation is True
    assert store.current(OrganizationId("org-b")).requires_revalidation is True
    assert store.history() == (merge, reversal)

    reopened = SqliteIdentityGovernanceStore(path)
    assert reopened.get_decision(merge.decision_id) == merge
    assert reopened.get_decision(reversal.decision_id) == reversal
    assert reopened.history() == (merge, reversal)


def test_reversal_fails_if_later_identity_change_touched_affected_subject(tmp_path) -> None:
    store = _store(tmp_path)

    first = merge_identities(
        absorbed_organization_ids=(OrganizationId("org-a"),),
        retained_organization_id=OrganizationId("org-b"),
        evidence_refs=("evidence:1",),
        reason_code="MERGE_1",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:merge:1",
        store=store,
    )
    merge_identities(
        absorbed_organization_ids=(OrganizationId("org-c"),),
        retained_organization_id=OrganizationId("org-b"),
        evidence_refs=("evidence:2",),
        reason_code="MERGE_2",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW + timedelta(minutes=5),
        decision_id="identity:merge:2",
        store=store,
    )

    with pytest.raises(IdentityGovernanceConflict, match="stale"):
        reverse_identity_decision(
            target_decision_id=first.decision_id,
            evidence_refs=("evidence:correction",),
            reason_code="TRY_STALE_REVERSAL",
            authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
            decided_by="governance:identity:2",
            decided_at=NOW + timedelta(hours=1),
            decision_id="identity:reversal:stale",
            store=store,
        )


def test_shared_observation_never_silently_crosses_merged_subject_boundary(tmp_path) -> None:
    store = _store(tmp_path)
    merge_identities(
        absorbed_organization_ids=(OrganizationId("org-a"),),
        retained_organization_id=OrganizationId("org-b"),
        evidence_refs=("evidence:registry:merge",),
        reason_code="VERIFIED_SAME_LEGAL_ENTITY",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:merge:1",
        store=store,
    )

    assert (
        observation_matches_current_subject(
            observation_subject_id=OrganizationId("org-a"),
            requested_subject_id=OrganizationId("org-a"),
            store=store,
        )
        is False
    )
    assert (
        observation_matches_current_subject(
            observation_subject_id=OrganizationId("org-b"),
            requested_subject_id=OrganizationId("org-a"),
            store=store,
        )
        is True
    )


def test_split_blocks_shared_observation_use_until_exact_subject_is_resolved(tmp_path) -> None:
    store = _store(tmp_path)
    split_identity(
        source_organization_id=OrganizationId("org-a"),
        target_organization_ids=(OrganizationId("org-b"), OrganizationId("org-c")),
        evidence_refs=("evidence:registry:split",),
        reason_code="LEGAL_PERSON_SPLIT_CONFIRMED",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:split:1",
        store=store,
    )

    with pytest.raises(IdentityGovernanceConflict, match="ambiguous after split"):
        observation_matches_current_subject(
            observation_subject_id=OrganizationId("org-b"),
            requested_subject_id=OrganizationId("org-a"),
            store=store,
        )


def test_store_is_append_only_and_subject_seed_cannot_overwrite_state(tmp_path) -> None:
    store = _store(tmp_path)
    assert store.seed_subject(OrganizationId("org-a")) is False

    merge = merge_identities(
        absorbed_organization_ids=(OrganizationId("org-a"),),
        retained_organization_id=OrganizationId("org-b"),
        evidence_refs=("evidence:merge",),
        reason_code="MERGE",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:merge:1",
        store=store,
    )

    assert store.seed_subject(OrganizationId("org-a")) is False
    assert store.current(OrganizationId("org-a")).state is IdentitySubjectState.REDIRECTED
    assert store.history() == (merge,)


def test_split_reversal_restores_source_without_erasing_split_history(tmp_path) -> None:
    store = _store(tmp_path)
    split = split_identity(
        source_organization_id=OrganizationId("org-a"),
        target_organization_ids=(OrganizationId("org-b"), OrganizationId("org-c")),
        evidence_refs=("evidence:split",),
        reason_code="LEGAL_PERSON_SPLIT_CONFIRMED",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:1",
        decided_at=NOW,
        decision_id="identity:split:1",
        store=store,
    )
    reversal = reverse_identity_decision(
        target_decision_id=split.decision_id,
        evidence_refs=("evidence:split-correction",),
        reason_code="SPLIT_CLASSIFICATION_REVERSED",
        authority=IdentityDecisionAuthority.GOVERNED_HUMAN,
        decided_by="governance:identity:2",
        decided_at=NOW + timedelta(hours=1),
        decision_id="identity:reversal:split:1",
        store=store,
    )

    assert store.current(OrganizationId("org-a")).state is IdentitySubjectState.ACTIVE
    assert store.current(OrganizationId("org-a")).requires_revalidation is True
    assert store.current(OrganizationId("org-b")).requires_revalidation is True
    assert store.current(OrganizationId("org-c")).requires_revalidation is True
    assert store.history() == (split, reversal)


def test_raw_untyped_authority_cannot_enter_identity_ledger(tmp_path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="authority must be governed"):
        merge_identities(
            absorbed_organization_ids=(OrganizationId("org-a"),),
            retained_organization_id=OrganizationId("org-b"),
            evidence_refs=("evidence:registry:1",),
            reason_code="CALLER_TRIES_UNGOVERNED_AUTHORITY",
            authority="SUBSCRIBER",  # type: ignore[arg-type]
            decided_by="subscriber:tenant-1",
            decided_at=NOW,
            decision_id="identity:merge:bad-authority",
            store=store,
        )

    assert store.history() == ()
