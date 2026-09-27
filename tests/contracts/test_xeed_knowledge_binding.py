"""P0-CORE-02 contextual FAXT reference and authorization invariants."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import get_type_hints

import pytest

from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_knowledge.reader import (
    AuthorizedXeedFaxt,
    AuthorizedXeedKnowledgeReader,
    KnowledgeReadError,
    KnowledgeReadFailure,
)
from domain.evidence.admission import Evidence, EvidenceAdmission, SourceAuthority
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
        decision=EvidenceAdmission.admit(evidence),
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


def test_observation_seed_does_not_create_a_knowledge_reference() -> None:
    from domain.xignal.observation_seed import ObservationSeed

    assert "xeed_id" not in ObservationSeed.__dataclass_fields__
    assert not hasattr(ObservationSeed, "faxt_id")


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
