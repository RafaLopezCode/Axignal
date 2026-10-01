"""Canonical identity governance application boundary."""

from application.identity_resolution.governance import (
    IdentityDecisionAuthority,
    IdentityDecisionKind,
    IdentityDecisionRecord,
    IdentityGovernanceConflict,
    IdentityGovernanceStore,
    IdentitySubjectPointer,
    IdentitySubjectState,
    merge_identities,
    observation_matches_current_subject,
    resolve_current_subject,
    reverse_identity_decision,
    split_identity,
)

__all__ = [
    "IdentityDecisionAuthority",
    "IdentityDecisionKind",
    "IdentityDecisionRecord",
    "IdentityGovernanceConflict",
    "IdentityGovernanceStore",
    "IdentitySubjectPointer",
    "IdentitySubjectState",
    "merge_identities",
    "observation_matches_current_subject",
    "resolve_current_subject",
    "reverse_identity_decision",
    "split_identity",
]
