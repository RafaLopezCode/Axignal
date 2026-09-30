from datetime import UTC, datetime

import pytest

from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
    require_explainable_basis,
)

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def _datum(contribution: BasisContribution = BasisContribution.SUPPORTS) -> BasisDatum:
    return BasisDatum(
        datum_id=f"datum:{contribution}",
        observation_id="obs:1",
        source_ref="https://example.test/source",
        source_type="PUBLIC_WEB",
        observed_at=NOW,
        excerpt_or_summary="Observed commercial context relevant to the role.",
        contribution=contribution,
    )


def _basis(*data: BasisDatum) -> ExplainableBasis:
    return ExplainableBasis(
        basis_id="basis:1",
        subject_id="xeed:a",
        candidate_id="org:zara",
        semantic_target="SUPPLIER_ROLE",
        state_fingerprint="state:1",
        contract_fingerprint="contract:1",
        evaluated_at=NOW,
        data=data,
        interpretation="The observed data warrants considering this supplier role.",
        uncertainty="Role is scoped and may coexist with customer role.",
    )


def test_visible_association_fails_closed_without_basis() -> None:
    with pytest.raises(ValueError, match="requires explainable basis"):
        require_explainable_basis(
            association_id="assoc:1",
            xeed_id="xeed:a",
            candidate_id="org:zara",
            semantic_target="SUPPLIER_ROLE",
            presentation_label="Supplier",
            basis=None,
        )


def test_basis_requires_real_supporting_datum_not_only_context() -> None:
    with pytest.raises(ValueError, match="supporting datum"):
        _basis(_datum(BasisContribution.CONTEXT))


def test_basis_preserves_contradictions_for_show_me_how_axignal_knows() -> None:
    basis = _basis(
        _datum(BasisContribution.SUPPORTS),
        BasisDatum(
            datum_id="datum:contradiction",
            observation_id="obs:2",
            source_ref="registry:2",
            source_type="PUBLIC_REGISTRY",
            observed_at=NOW,
            excerpt_or_summary="A second observation conflicts with the inferred direction.",
            contribution=BasisContribution.CONTRADICTS,
        ),
    )
    visible = require_explainable_basis(
        association_id="assoc:1",
        xeed_id="xeed:a",
        candidate_id="org:zara",
        semantic_target="SUPPLIER_ROLE",
        presentation_label="Supplier",
        basis=basis,
    )
    assert [item.contribution for item in visible.basis.data] == [
        BasisContribution.SUPPORTS,
        BasisContribution.CONTRADICTS,
    ]


def test_basis_cannot_be_reused_for_different_semantic_target() -> None:
    with pytest.raises(ValueError, match="semantic target"):
        require_explainable_basis(
            association_id="assoc:2",
            xeed_id="xeed:a",
            candidate_id="org:zara",
            semantic_target="CUSTOMER_ROLE",
            presentation_label="Customer",
            basis=_basis(_datum()),
        )
