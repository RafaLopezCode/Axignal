"""Deterministic entity-resolution tests."""

from __future__ import annotations

from pipeline.entity_resolution.resolver import ExactNameResolver, ResolutionCandidate


def _resolver() -> ExactNameResolver:
    return ExactNameResolver(
        [
            ResolutionCandidate(organization_id="org-acme", canonical_name="ACME Industrial"),
            ResolutionCandidate(organization_id="org-beta", canonical_name="Beta Logistics"),
        ]
    )


def test_exact_resolution_ignores_case_and_accents() -> None:
    match = _resolver().resolve("acme industrial")
    assert match is not None
    assert match.organization_id == "org-acme"


def test_unknown_name_resolves_to_none() -> None:
    assert _resolver().resolve("Unknown Company") is None
