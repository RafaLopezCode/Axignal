"""P0-CORE-02/03 contextual FAXT read and collection authorization invariants."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import get_type_hints

import pytest

from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_knowledge.reader import (
    AuthorizedXeedFaxt,
    AuthorizedXeedFaxtCollectionReader,
    AuthorizedXeedKnowledgeReader,
    KnowledgeReadError,
    KnowledgeReadFailure,
)
from domain.evidence.admission import AdmissionRequest, Evidence, EvidenceAdmission, SourceAuthority
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import FaxtId, OrganizationId, PrincipalId, TenantId, XeedId
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.knowledge_reference import XeedFaxtReference
from domain.xeed.model import Xeed
from tests.support.xeed_authority import InMemoryXeedAuthority
from tests.support.xeed_knowledge import InMemoryXeedKnowledgeAuthority


def _faxt(faxt_id: str = "faxt-shared") -> FAXT:
    evidence = Evidence(
        id="evidence-1",
        source="https://example.test",
        source_type="web",
        reference="https://example.test/claim",
        extracted_claim="The organization manufactures pumps.",
        observed_at=datetime(2026, 1, 1),
        authority=SourceAuthority.OFFICIAL_WEB,
    )
    return FAXT.create(
        faxt_id=FaxtId(faxt_id),
        subject_id="org-shared",
        predicate="MANUFACTURES",
        object_or_value="pumps",
        evidence=evidence,
        decision=EvidenceAdmission.admit_claim(
            AdmissionRequest(
                evidence=evidence,
                subject_id="org-shared",
                predicate="MANUFACTURES",
                object_or_value="pumps",
                claim_proposition=evidence.extracted_claim,
            )
        ),
    )


def _setup() -> tuple[
    InMemoryXeedAuthority,
    InMemoryXeedKnowledgeAuthority,
    AuthorizedXeedKnowledgeReader,
    dict[str, object],
]:
    identities = InMemoryXeedAuthority()
    for principal_id in ("principal-a", "principal-b"):
        identities.add_principal(Principal(PrincipalId(principal_id)))
    for tenant_id in ("tenant-a", "tenant-b"):
        identities.add_tenant(Tenant(TenantId(tenant_id)))
    identities.add_membership(
        PrincipalTenantMembership(PrincipalId("principal-a"), TenantId("tenant-a"))
    )
    identities.add_membership(
        PrincipalTenantMembership(PrincipalId("principal-b"), TenantId("tenant-b"))
    )
    xeed_a = Xeed(
        XeedId("xeed-a"), TenantId("tenant-a"), OrganizationId("org-shared"), "Same label"
    )
    xeed_a2 = Xeed(
        XeedId("xeed-a2"), TenantId("tenant-a"), OrganizationId("org-shared"), "Same label"
    )
    xeed_b = Xeed(
        XeedId("xeed-b"), TenantId("tenant-b"), OrganizationId("org-shared"), "Same label"
    )
    for xeed in (xeed_a, xeed_a2, xeed_b):
        identities.add_xeed(xeed)
    xeed_reader = AuthorizedXeedReader(identities, identities, identities)
    authorized = {
        "a": xeed_reader.read(
            TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
            xeed_a.id,
        ),
        "a2": xeed_reader.read(
            TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
            xeed_a2.id,
        ),
        "b": xeed_reader.read(
            TrustedRequestContext(PrincipalId("principal-b"), TenantId("tenant-b")),
            xeed_b.id,
        ),
    }
    knowledge = InMemoryXeedKnowledgeAuthority()
    reader = AuthorizedXeedKnowledgeReader(knowledge, knowledge)
    return identities, knowledge, reader, authorized


def _reference(xeed_id: str = "xeed-a", faxt_id: str = "faxt-shared") -> XeedFaxtReference:
    return XeedFaxtReference(XeedId(xeed_id), FaxtId(faxt_id))


def _collection_reader(
    authority: InMemoryXeedKnowledgeAuthority,
) -> AuthorizedXeedFaxtCollectionReader:
    return AuthorizedXeedFaxtCollectionReader(authority, authority)


def test_authorized_xeed_reads_only_explicitly_referenced_global_faxt() -> None:
    _, authority, reader, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference())

    result = reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert isinstance(result, AuthorizedXeedFaxt)
    assert result.faxt is faxt
    assert result.reference == _reference()
    assert result.authorized_xeed is authorized["a"]
    assert authority.calls == ["reference", "faxt"]


def test_missing_reference_fails_before_global_faxt_lookup() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_faxt(_faxt())

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.REFERENCE_NOT_FOUND
    assert authority.calls == ["reference"]


def test_missing_canonical_faxt_fails_closed_after_reference_check() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_reference(_reference())

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.FAXT_NOT_FOUND
    assert authority.calls == ["reference", "faxt"]


@pytest.mark.parametrize(
    "malformed_reference",
    [
        XeedFaxtReference(XeedId("xeed-b"), FaxtId("faxt-shared")),
        XeedFaxtReference(XeedId("xeed-a"), FaxtId("faxt-other")),
        object(),
    ],
)
def test_mismatched_reference_result_fails_closed(
    malformed_reference: object,
) -> None:
    _, authority, reader, authorized = _setup()
    authority.add_faxt(_faxt())
    authority.get_reference = lambda _xeed_id, _faxt_id: malformed_reference  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.REFERENCE_NOT_FOUND
    assert authority.calls == []


def test_mismatched_faxt_result_fails_closed() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_reference(_reference())
    authority.get_faxt = lambda _faxt_id: _faxt("faxt-other")  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.FAXT_NOT_FOUND
    assert authority.calls == ["reference"]


def test_wrong_global_object_type_fails_closed() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_reference(_reference())
    authority.get_faxt = lambda _faxt_id: object()  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.FAXT_NOT_FOUND
    assert authority.calls == ["reference"]


def test_same_tenant_different_xeed_without_its_own_reference_is_denied() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_faxt(_faxt())
    authority.add_reference(_reference("xeed-a"))

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["a2"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.REFERENCE_NOT_FOUND
    assert authority.calls == ["reference"]


def test_other_tenant_cannot_use_its_authorized_xeed_for_another_xeeds_reference() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_faxt(_faxt())
    authority.add_reference(_reference("xeed-a"))

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["b"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.REFERENCE_NOT_FOUND
    assert authority.calls == ["reference"]


def test_same_global_faxt_can_be_explicitly_referenced_from_multiple_tenants() -> None:
    _, authority, reader, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference("xeed-a"))
    authority.add_reference(_reference("xeed-b"))

    result_a = reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]
    result_b = reader.read(authorized["b"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert result_a.faxt is faxt
    assert result_b.faxt is faxt
    assert result_a.reference != result_b.reference


def test_label_collision_does_not_collide_contextual_reference_identity() -> None:
    _, authority, reader, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference("xeed-a"))
    authority.add_reference(_reference("xeed-b"))

    result_a = reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]
    result_b = reader.read(authorized["b"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert result_a.authorized_xeed.xeed.label == result_b.authorized_xeed.xeed.label
    assert result_a.reference.xeed_id != result_b.reference.xeed_id
    assert result_a.faxt is result_b.faxt is faxt


@pytest.mark.parametrize(
    "raw_context", [None, XeedId("xeed-a"), TenantId("tenant-a"), OrganizationId("org-shared")]
)
def test_raw_ids_cannot_replace_authorized_xeed(raw_context: object) -> None:
    _, authority, reader, _ = _setup()

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(raw_context, FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.MISSING_AUTHORIZED_XEED
    assert authority.calls == []


def test_raw_knowledge_id_enumeration_never_reaches_global_faxt_reader() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_faxt(_faxt())

    with pytest.raises(KnowledgeReadError):
        reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert authority.calls == ["reference"]


def test_invalid_faxt_id_fails_before_any_private_or_global_lookup() -> None:
    _, authority, reader, authorized = _setup()

    with pytest.raises(KnowledgeReadError) as error:
        reader.read(authorized["a"], FaxtId(" "))  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.INVALID_FAXT_ID
    assert authority.calls == []


def test_binding_preserves_global_faxt_identity_state_and_currentness() -> None:
    _, authority, reader, authorized = _setup()
    faxt = replace(_faxt(), currentness=Currentness.STALE)
    authority.add_faxt(faxt)
    authority.add_reference(_reference())
    before = (faxt.id, faxt.epistemic_state, faxt.currentness, faxt.evidence_refs)

    result = reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert result.faxt is faxt
    assert (faxt.id, faxt.epistemic_state, faxt.currentness, faxt.evidence_refs) == before
    assert set(vars(result.reference)) == {"xeed_id", "faxt_id"}


def test_unknown_epistemic_state_is_not_promoted_by_reference_or_read() -> None:
    _, authority, reader, authorized = _setup()
    faxt = replace(_faxt(), epistemic_state=EpistemicState.UNKNOWN)
    authority.add_faxt(faxt)
    authority.add_reference(_reference())

    result = reader.read(authorized["a"], FaxtId("faxt-shared"))  # type: ignore[arg-type]

    assert result.faxt is faxt
    assert result.faxt.epistemic_state is EpistemicState.UNKNOWN


def test_reference_contains_no_provenance_or_epistemic_claims() -> None:
    reference = _reference()

    assert reference.__dataclass_fields__.keys() == {"xeed_id", "faxt_id"}
    assert not hasattr(reference, "evidence_refs")
    assert not hasattr(reference, "provenance")
    assert not hasattr(reference, "epistemic_state")
    assert not hasattr(reference, "currentness")


def test_reference_does_not_encode_discovery_relevance_or_source_rights() -> None:
    reference = _reference()

    assert reference.__dataclass_fields__.keys() == {"xeed_id", "faxt_id"}
    assert not hasattr(reference, "discovered_by")
    assert not hasattr(reference, "relevance")
    assert not hasattr(reference, "importance")
    assert not hasattr(reference, "source_rights")


def test_xeed_germination_state_does_not_create_a_knowledge_reference() -> None:
    from domain.xeed.germination import XeedGerminationState

    assert "xeed_id" in XeedGerminationState.__dataclass_fields__
    assert "faxt_id" not in XeedGerminationState.__dataclass_fields__


def test_label_collision_or_mutation_does_not_change_reference_identity() -> None:
    _, authority, reader, authorized = _setup()
    authority.add_faxt(_faxt())
    authority.add_reference(_reference("xeed-a"))
    original_xeed = authorized["a"].xeed  # type: ignore[union-attr]
    renamed_xeed = replace(original_xeed, label="Renamed label")
    identities, _, _, _ = _setup()
    identities.xeeds[renamed_xeed.id] = renamed_xeed
    from application.xeed_access.reader import AuthorizedXeedReader

    renamed_authorized = AuthorizedXeedReader(identities, identities, identities).read(
        TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
        renamed_xeed.id,
    )

    result = reader.read(renamed_authorized, FaxtId("faxt-shared"))

    assert renamed_authorized.xeed.label == "Renamed label"
    assert renamed_authorized.xeed.id == original_xeed.id
    assert result.reference == _reference("xeed-a")


def test_duplicate_contextual_reference_is_rejected_by_test_authority() -> None:
    authority = InMemoryXeedKnowledgeAuthority()
    reference = _reference()
    authority.add_reference(reference)

    with pytest.raises(ValueError, match="duplicate Xeed FAXT reference"):
        authority.add_reference(reference)


def test_duplicate_global_faxt_is_rejected_instead_of_cloned() -> None:
    authority = InMemoryXeedKnowledgeAuthority()
    faxt = _faxt()
    authority.add_faxt(faxt)

    with pytest.raises(ValueError, match="duplicate canonical FAXT identity"):
        authority.add_faxt(faxt)


def test_authorized_result_cannot_be_constructed_by_a_caller() -> None:
    _, authority, _, authorized = _setup()
    with pytest.raises(TypeError):
        AuthorizedXeedFaxt(
            authorized["a"],
            _reference(),
            _faxt(),
        )  # type: ignore[arg-type, call-arg]
    assert authority.calls == []


def test_faxt_id_is_a_distinct_static_identity_type() -> None:
    faxt = _faxt()

    assert FaxtId.__supertype__ is str
    assert get_type_hints(FAXT.create)["faxt_id"] is FaxtId
    assert isinstance(faxt.id, str)
    assert faxt.id == FaxtId("faxt-shared")


def test_reference_and_reader_accept_only_the_faxt_identity_type() -> None:
    assert get_type_hints(XeedFaxtReference)["faxt_id"] is FaxtId
    assert get_type_hints(AuthorizedXeedKnowledgeReader.read)["faxt_id"] is FaxtId


def test_empty_authorized_context_returns_an_immutable_empty_collection() -> None:
    _, authority, _, authorized = _setup()

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert result == ()
    assert isinstance(result, tuple)
    assert authority.calls == ["references"]
    assert authority.listed_xeeds == [XeedId("xeed-a")]


def test_single_explicit_reference_returns_original_global_faxt() -> None:
    _, authority, _, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference())

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert len(result) == 1
    assert result[0].faxt is faxt
    assert result[0].reference == _reference()
    assert result[0].authorized_xeed is authorized["a"]
    assert authority.calls == ["references", "faxt"]


def test_multiple_references_are_resolved_only_after_scoped_reference_enumeration() -> None:
    _, authority, _, authorized = _setup()
    faxt_b = _faxt("faxt-b")
    faxt_a = _faxt("faxt-a")
    authority.add_faxt(faxt_b)
    authority.add_faxt(faxt_a)
    authority.add_reference(_reference(faxt_id="faxt-b"))
    authority.add_reference(_reference(faxt_id="faxt-a"))

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert tuple(item.faxt.id for item in result) == (FaxtId("faxt-a"), FaxtId("faxt-b"))
    assert result[0].faxt is faxt_a
    assert result[1].faxt is faxt_b
    assert authority.calls == ["references", "faxt", "faxt"]


def test_same_global_faxt_is_returned_for_independently_referenced_xeeds_and_tenants() -> None:
    _, authority, _, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference("xeed-a"))
    authority.add_reference(_reference("xeed-b"))

    result_a = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]
    result_b = _collection_reader(authority).read(authorized["b"])  # type: ignore[arg-type]

    assert result_a[0].faxt is result_b[0].faxt is faxt
    assert result_a[0].reference != result_b[0].reference
    assert authority.listed_xeeds == [XeedId("xeed-a"), XeedId("xeed-b")]


def test_same_organization_different_xeed_does_not_imply_reference_membership() -> None:
    _, authority, _, authorized = _setup()
    authority.add_faxt(_faxt())
    authority.add_reference(_reference("xeed-a"))

    result = _collection_reader(authority).read(authorized["a2"])  # type: ignore[arg-type]

    assert authorized["a"].xeed.organization_id == authorized["a2"].xeed.organization_id  # type: ignore[union-attr]
    assert result == ()
    assert authority.listed_xeeds == [XeedId("xeed-a2")]
    assert authority.calls == ["references"]


def test_same_tenant_different_xeed_isolation_uses_only_selected_xeed_references() -> None:
    _, authority, _, authorized = _setup()
    faxt_a = _faxt("faxt-a")
    faxt_a2 = _faxt("faxt-a2")
    authority.add_faxt(faxt_a)
    authority.add_faxt(faxt_a2)
    authority.add_reference(_reference("xeed-a", "faxt-a"))
    authority.add_reference(_reference("xeed-a2", "faxt-a2"))

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert tuple(item.faxt for item in result) == (faxt_a,)
    assert authority.listed_xeeds == [XeedId("xeed-a")]


def test_cross_tenant_isolation_does_not_release_another_xeeds_reference() -> None:
    _, authority, _, authorized = _setup()
    authority.add_faxt(_faxt())
    authority.add_reference(_reference("xeed-a"))

    result = _collection_reader(authority).read(authorized["b"])  # type: ignore[arg-type]

    assert result == ()
    assert authority.listed_xeeds == [XeedId("xeed-b")]
    assert authority.calls == ["references"]


@pytest.mark.parametrize(
    "raw_context",
    [None, XeedId("xeed-a"), TenantId("tenant-a"), OrganizationId("org-shared")],
)
def test_raw_ids_cannot_establish_collection_authority(raw_context: object) -> None:
    _, authority, _, _ = _setup()

    with pytest.raises(KnowledgeReadError) as error:
        _collection_reader(authority).read(raw_context)  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.MISSING_AUTHORIZED_XEED
    assert authority.calls == []
    assert authority.listed_xeeds == []


def test_unreferenced_global_faxt_is_not_returned_or_enumerated() -> None:
    _, authority, _, authorized = _setup()
    authority.add_faxt(_faxt())

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert result == ()
    assert authority.calls == ["references"]
    assert not hasattr(authority, "list_all_faxts")


def test_invalid_reference_result_fails_before_global_faxt_resolution() -> None:
    _, authority, _, authorized = _setup()
    authority.add_faxt(_faxt())
    authority.list_for_xeed = lambda _xeed_id: (_reference("xeed-b"),)  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.INVALID_REFERENCE
    assert authority.calls == []


def test_non_tuple_reference_collection_fails_closed() -> None:
    _, authority, _, authorized = _setup()
    authority.list_for_xeed = lambda _xeed_id: []  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.INVALID_REFERENCE_COLLECTION
    assert authority.calls == []


def test_duplicate_reference_membership_fails_closed() -> None:
    _, authority, _, authorized = _setup()
    reference = _reference()
    authority.list_for_xeed = lambda _xeed_id: (reference, reference)  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.DUPLICATE_REFERENCE
    assert authority.calls == []


def test_dangling_reference_fails_closed_without_returning_a_partial_collection() -> None:
    _, authority, _, authorized = _setup()
    authority.add_faxt(_faxt("faxt-a"))
    authority.add_reference(_reference(faxt_id="faxt-a"))
    authority.add_reference(_reference(faxt_id="faxt-z-missing"))

    with pytest.raises(KnowledgeReadError) as error:
        _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.FAXT_NOT_FOUND
    assert authority.calls == ["references", "faxt", "faxt"]


def test_mismatched_faxt_identity_fails_collection_closed() -> None:
    _, authority, _, authorized = _setup()
    authority.add_reference(_reference())
    authority.get_faxt = lambda _faxt_id: _faxt("faxt-other")  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.FAXT_NOT_FOUND
    assert authority.calls == ["references"]


def test_wrong_global_object_type_fails_collection_closed() -> None:
    _, authority, _, authorized = _setup()
    authority.add_reference(_reference())
    authority.get_faxt = lambda _faxt_id: object()  # type: ignore[method-assign]

    with pytest.raises(KnowledgeReadError) as error:
        _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert error.value.failure is KnowledgeReadFailure.FAXT_NOT_FOUND
    assert authority.calls == ["references"]


def test_label_collision_or_mutation_does_not_change_collection_membership() -> None:
    _, authority, _, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference())
    original_authorized = authorized["a"]
    identities = InMemoryXeedAuthority()
    identities.add_principal(Principal(PrincipalId("principal-a")))
    identities.add_tenant(Tenant(TenantId("tenant-a")))
    identities.add_membership(
        PrincipalTenantMembership(PrincipalId("principal-a"), TenantId("tenant-a"))
    )
    renamed_xeed = replace(original_authorized.xeed, label="Renamed label")  # type: ignore[union-attr]
    identities.add_xeed(renamed_xeed)
    renamed_authorized = AuthorizedXeedReader(identities, identities, identities).read(
        TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
        renamed_xeed.id,
    )

    result = _collection_reader(authority).read(renamed_authorized)

    assert result[0].faxt is faxt
    assert result[0].reference == _reference()
    assert result[0].authorized_xeed.xeed.label == "Renamed label"


def test_unknown_epistemic_state_and_currentness_are_preserved_in_collection() -> None:
    _, authority, _, authorized = _setup()
    faxt = replace(
        _faxt(),
        epistemic_state=EpistemicState.UNKNOWN,
        currentness=Currentness.UNKNOWN,
    )
    authority.add_faxt(faxt)
    authority.add_reference(_reference())

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert result[0].faxt is faxt
    assert result[0].faxt.epistemic_state is EpistemicState.UNKNOWN
    assert result[0].faxt.currentness is Currentness.UNKNOWN


def test_collection_does_not_invent_provenance_or_dereference_evidence() -> None:
    _, authority, _, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference())

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert result[0].faxt is faxt
    assert result[0].faxt.evidence_refs == faxt.evidence_refs
    assert authority.calls == ["references", "faxt"]
    assert "evidence" not in authority.calls


def test_xeed_germination_state_does_not_authorize_collection_membership() -> None:
    from domain.xeed.germination import XeedGerminationState

    assert "xeed_id" in XeedGerminationState.__dataclass_fields__
    assert "faxt_id" not in XeedGerminationState.__dataclass_fields__


def test_collection_result_reuses_authorized_xeed_faxt_without_public_constructor() -> None:
    _, authority, _, authorized = _setup()
    faxt = _faxt()
    authority.add_faxt(faxt)
    authority.add_reference(_reference())

    result = _collection_reader(authority).read(authorized["a"])  # type: ignore[arg-type]

    assert isinstance(result[0], AuthorizedXeedFaxt)
    with pytest.raises(TypeError):
        AuthorizedXeedFaxt(authorized["a"], _reference(), faxt)  # type: ignore[arg-type]
