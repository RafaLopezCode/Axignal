"""Contracts for the minimum truthful AXIGLAND subscriber projection."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from application.subscriber_projection.axigland import (
    ProjectionError,
    ProjectionStatus,
    project_axigland,
)
from application.xeed_access.reader import TrustedRequestContext
from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    GroundedClaim,
    SourceAuthority,
)
from domain.evidence.epistemics import Currentness
from domain.faxt.model import FAXT
from tests.support.hfx01_demo import Hfx01Demo


def test_projection_preserves_global_and_private_identities_and_direct_values() -> None:
    demo = Hfx01Demo()
    projection = demo.selected_demo_projection()

    assert projection.organization.identity == "org-demo-shared"
    assert projection.xeed_id == "xeed-demo-a"
    assert projection.organization.identity != projection.xeed_id
    assert projection.organization.label == "Northwind Materials (synthetic demo)"
    assert projection.organization.capabilities == ()
    assert projection.organization.markets == ()
    assert tuple(node.identity for node in projection.faxt_nodes) == (
        "faxt-demo-a",
        "faxt-demo-a2",
    )
    assert projection.faxt_nodes[0].subject_id == "subject-demo-a-unknown-kind"
    assert projection.faxt_nodes[0].predicate == "MANUFACTURES"
    assert projection.faxt_nodes[0].object_or_value == "precision components"
    assert projection.faxt_nodes[0].status is ProjectionStatus.CANONICAL_DERIVED_DETERMINISTIC
    assert projection.faxt_nodes[0].epistemic_state == "OBSERVED"
    assert projection.faxt_nodes[0].currentness == "UNKNOWN"
    assert projection.faxt_nodes[0].membership_status is ProjectionStatus.CANONICAL_DIRECT
    assert projection.faxt_nodes[0].subject_kind is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.faxt_nodes[0].subject_resolution is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.faxt_nodes[0].semantic_relationships is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.faxt_nodes[0].cardinal_assignment is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.faxt_nodes[0].provenance is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.faxt_nodes[0].evidence_access is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.semantic_edges is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.historical_state is ProjectionStatus.UNKNOWN_UNSUPPORTED
    assert projection.reality_level == "TEST_DEV_IN_MEMORY_AUTHORITY"
    assert "evidence_refs" not in projection.faxt_nodes[0].__dataclass_fields__


def test_projection_uses_explicit_xeed_membership_not_global_faxts_or_other_tenants() -> None:
    demo = Hfx01Demo()
    first = demo.selected_demo_projection()
    second = demo.project_for("principal-demo-b", "tenant-demo-b", "xeed-demo-b")

    assert first.organization.identity == second.organization.identity
    assert first.organization.label == second.organization.label
    assert [node.identity for node in first.faxt_nodes] == ["faxt-demo-a", "faxt-demo-a2"]
    assert [node.identity for node in second.faxt_nodes] == ["faxt-demo-b"]
    assert "faxt-demo-b" not in {node.identity for node in first.faxt_nodes}
    assert not {"faxt-demo-a", "faxt-demo-a2"} & {node.identity for node in second.faxt_nodes}


def test_projection_is_immutable() -> None:
    projection = Hfx01Demo().selected_demo_projection()

    with pytest.raises(FrozenInstanceError):
        projection.xeed_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("raw_context", [None, "xeed-demo-a", object()])
def test_raw_or_missing_organization_context_fails_closed(raw_context: object) -> None:
    with pytest.raises(ProjectionError):
        project_axigland(raw_context, ())  # type: ignore[arg-type]


def test_mutable_or_wrong_type_collection_fails_closed() -> None:
    demo = Hfx01Demo()
    authorized = demo.xeed_reader.read(
        TrustedRequestContext("principal-demo-a", "tenant-demo-a"), "xeed-demo-a"
    )
    organization = demo.organization_reader.read(authorized)

    with pytest.raises(ProjectionError):
        project_axigland(organization, [])  # type: ignore[arg-type]
    with pytest.raises(ProjectionError):
        project_axigland(organization, (object(),))  # type: ignore[arg-type]


def test_mixed_authorized_xeed_context_fails_closed_even_for_same_global_organization() -> None:
    demo = Hfx01Demo()
    authorized_a = demo.xeed_reader.read(
        TrustedRequestContext("principal-demo-a", "tenant-demo-a"), "xeed-demo-a"
    )
    authorized_b = demo.xeed_reader.read(
        TrustedRequestContext("principal-demo-b", "tenant-demo-b"), "xeed-demo-b"
    )
    organization_a = demo.organization_reader.read(authorized_a)
    faxt_b = demo.faxt_reader.read(authorized_b)

    assert organization_a.organization is demo.organizations.items["org-demo-shared"]
    with pytest.raises(ProjectionError, match="share one AuthorizedXeed"):
        project_axigland(organization_a, faxt_b)  # type: ignore[arg-type]


def test_duplicate_canonical_identity_fails_closed() -> None:
    demo = Hfx01Demo()
    authorized = demo.xeed_reader.read(
        TrustedRequestContext("principal-demo-a", "tenant-demo-a"), "xeed-demo-a"
    )
    organization = demo.organization_reader.read(authorized)
    faxts = demo.faxt_reader.read(authorized)

    with pytest.raises(ProjectionError, match="duplicate FAXT identity"):
        project_axigland(organization, faxts + faxts)


def test_equal_raw_ids_in_distinct_identity_planes_keep_distinct_projection_keys() -> None:
    from datetime import UTC, datetime

    from domain.identity import FaxtId, XeedId
    from domain.xeed.knowledge_reference import XeedFaxtReference

    demo = Hfx01Demo()
    authorized = demo.xeed_reader.read(
        TrustedRequestContext("principal-demo-a", "tenant-demo-a"), "xeed-demo-a"
    )
    organization = demo.organization_reader.read(authorized)
    original = demo.knowledge.faxts.pop(FaxtId("faxt-demo-a"))
    collision_claim = f"{original.subject_id} capability {original.object_or_value}"
    evidence = Evidence(
        id="evidence-id-collision",
        source="synthetic://projection-id-collision",
        source_type="test",
        reference="synthetic://projection-id-collision",
        extracted_claim=collision_claim,
        observed_at=datetime(2026, 9, 1, tzinfo=UTC),
        authority=SourceAuthority.OFFICIAL_WEB,
        observation_subject_id=original.subject_id,
        grounded_claim=GroundedClaim(
            subject_id=original.subject_id,
            predicate="capability",
            object_or_value=original.object_or_value,
            subject_mention=original.subject_id,
            predicate_mention="capability",
            object_mention=original.object_or_value,
            supporting_excerpt=collision_claim,
        ),
    )
    request = AdmissionRequest(
        evidence=evidence,
        subject_id=original.subject_id,
        predicate="capability",
        object_or_value=original.object_or_value,
        claim_proposition=evidence.extracted_claim,
    )
    colliding_faxt = FAXT.create(
        faxt_id=FaxtId(organization.organization.id),
        subject_id=original.subject_id,
        predicate="capability",
        object_or_value=original.object_or_value,
        evidence=evidence,
        decision=EvidenceAdmission.admit_claim(request),
        currentness=Currentness.UNKNOWN,
    )
    demo.knowledge.faxts[colliding_faxt.id] = colliding_faxt
    demo.knowledge.references.pop((XeedId("xeed-demo-a"), FaxtId("faxt-demo-a")))
    demo.knowledge.add_reference(XeedFaxtReference(XeedId("xeed-demo-a"), colliding_faxt.id))
    colliding_context = next(
        context
        for context in demo.faxt_reader.read(authorized)
        if context.faxt.id == colliding_faxt.id
    )

    projection = project_axigland(organization, (colliding_context,))
    colliding_node = next(
        node
        for node in projection.faxt_nodes
        if str(node.identity) == str(organization.organization.id)
    )

    assert str(projection.organization.identity) == str(colliding_node.identity)
    assert projection.organization.presentation_key == "ORGANIZATION:org-demo-shared"
    assert colliding_node.presentation_key == "FAXT:org-demo-shared"


def test_empty_authorized_collection_preserves_empty_without_claiming_world_absence() -> None:
    demo = Hfx01Demo()
    authorized = demo.xeed_reader.read(
        TrustedRequestContext("principal-demo-a", "tenant-demo-a"), "xeed-demo-a"
    )
    organization = demo.organization_reader.read(authorized)
    projection = project_axigland(organization, ())

    assert projection.faxt_nodes == ()
    assert projection.organization.identity == "org-demo-shared"
