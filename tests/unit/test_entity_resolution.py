from __future__ import annotations

from pipeline.entity_resolution.resolver import (
    ExactNameResolver,
    ResolutionCandidate,
    ResolutionStatus,
    VerifiedIdentifier,
)


def _resolver() -> ExactNameResolver:
    return ExactNameResolver(
        [
            ResolutionCandidate(
                organization_id="org-acme",
                canonical_name="ACME Industrial",
                aliases=("ACME Industriál", "ACME Pumps"),
                verified_identifiers=(VerifiedIdentifier("LEI", "5493001KJTIIGC8Y1R12", "GLEIF"),),
            ),
            ResolutionCandidate(
                organization_id="org-beta",
                canonical_name="Beta Logistics",
                aliases=("Beta",),
                verified_identifiers=(VerifiedIdentifier("REGISTRY", "B-200", "REG-X"),),
            ),
        ]
    )


def test_exact_resolution_ignores_case_and_accents() -> None:
    match = _resolver().resolve("acme industrial")
    assert match is not None
    assert match.organization_id == "org-acme"


def test_alias_resolution_is_governed_exact_not_fuzzy() -> None:
    result = _resolver().resolve_identity("acme pumps")
    assert result.status is ResolutionStatus.RESOLVED
    assert result.candidate is not None
    assert result.candidate.organization_id == "org-acme"
    assert result.reason_code == "UNIQUE_CANONICAL_OR_ALIAS_NAME"

    assert _resolver().resolve_identity("acme pump").status is ResolutionStatus.UNRESOLVED


def test_verified_identifier_outranks_name_and_resolves_exact_legal_identity() -> None:
    result = _resolver().resolve_identity(
        "Completely different subscriber-entered label",
        verified_identifiers=(VerifiedIdentifier("lei", "5493001kjtiigc8y1r12", "gleif"),),
    )
    assert result.status is ResolutionStatus.RESOLVED
    assert result.candidate is not None
    assert result.candidate.organization_id == "org-acme"
    assert result.reason_code == "VERIFIED_IDENTIFIER_EXACT"


def test_unknown_verified_identifier_does_not_fall_back_to_same_name() -> None:
    result = _resolver().resolve_identity(
        "ACME Industrial",
        verified_identifiers=(VerifiedIdentifier("REGISTRY", "DIFFERENT-LEGAL-PERSON", "REG-X"),),
    )
    assert result.status is ResolutionStatus.UNRESOLVED
    assert result.reason_code == "VERIFIED_IDENTIFIER_NOT_FOUND"


def test_name_collision_is_ambiguous_and_legacy_resolve_fails_closed() -> None:
    resolver = ExactNameResolver(
        [
            ResolutionCandidate("org-a", "North Star", aliases=("Star",)),
            ResolutionCandidate("org-b", "South Star", aliases=("Star",)),
        ]
    )

    result = resolver.resolve_identity("Star")
    assert result.status is ResolutionStatus.AMBIGUOUS
    assert tuple(item.organization_id for item in result.candidates) == (
        "org-a",
        "org-b",
    )
    assert resolver.resolve("Star") is None


def test_verified_identifier_collision_is_ambiguous() -> None:
    identifier = VerifiedIdentifier("REGISTRY", "COLLISION", "REG-X")
    resolver = ExactNameResolver(
        [
            ResolutionCandidate(
                "org-a",
                "Alpha",
                verified_identifiers=(identifier,),
            ),
            ResolutionCandidate(
                "org-b",
                "Beta",
                verified_identifiers=(identifier,),
            ),
        ]
    )

    result = resolver.resolve_identity(
        "Alpha",
        verified_identifiers=(identifier,),
    )
    assert result.status is ResolutionStatus.AMBIGUOUS
    assert result.reason_code == "VERIFIED_IDENTIFIER_COLLISION"


def test_unknown_name_resolves_to_none() -> None:
    assert _resolver().resolve("Unknown Company") is None
