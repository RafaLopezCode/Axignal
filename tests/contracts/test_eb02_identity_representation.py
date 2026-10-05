"""EB-02 deterministic adversarial identity, visibility and support proofs."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.economic_discovery.economic_state import (
    EconomicObservation,
    EvidenceBackedEconomicState,
)
from application.economic_discovery.explanation import BasisContribution, BasisDatum
from application.semantic_extraction import (
    SemanticExtractionContract,
    SemanticTarget,
    build_semantic_extraction_request,
    normalize_semantic_extraction_payload,
)
from application.source_acquisition import SourceObservation, SourceRequest
from application.source_representation import (
    DocumentRepresentation,
    RichStateDatum,
    compile_rich_subject_state,
    representation_state_data,
)
from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    GroundedClaim,
    SourceAuthority,
    evidence_fingerprint,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.identity import (
    GovernedIdentityName,
    IdentityBindingAuthority,
    IdentityNameKind,
    identity_name_key,
)
from domain.identity_binding import (
    GovernedIdentityBinding,
    IdentityBindingAdmission,
)
from domain.relationships.model import ObservedRelationship
from domain.representation import RepresentationSpan, TextSurface, text_fingerprint
from pipeline.entity_resolution import (
    ExactNameResolver,
    ResolutionCandidate,
    ResolutionStatus,
    VerifiedIdentifier,
)
from pipeline.source_acquisition import ContentAddressedArtifactStore
from pipeline.source_representation import DocumentRepresentationError, represent_html_observation

NOW = datetime(2026, 10, 5, 12, tzinfo=UTC)
CLAIM = "ACME supplies Beta."


def _document(
    tmp_path: Path, html: str = f"<html><body><p>{CLAIM}</p></body></html>"
) -> DocumentRepresentation:
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    raw = html.encode("utf-8")
    request = SourceRequest(
        request_id="request:eb02",
        subject_id="org:acme",
        observation_slot="website",
        target_uri="https://example.test/about",
        source_type="COUNTERPARTY",
        policy_id="synthetic-policy:1",
        policy_fingerprint="synthetic-policy-fingerprint",
    )
    observation = SourceObservation(
        request_id=request.request_id,
        subject_id=request.subject_id,
        observation_slot=request.observation_slot,
        requested_uri=request.target_uri,
        final_uri=request.target_uri,
        retrieved_at=NOW,
        http_status=200,
        content_type="text/html; charset=utf-8",
        body_fingerprint=text_fingerprint(html),
        body_artifact_ref=artifacts.put_bytes(raw),
        raw_observation_ref=artifacts.put_json({"synthetic": True}),
        observation_fingerprint=text_fingerprint(html + NOW.isoformat()),
        instrument_ref="synthetic-http:1",
        policy_id=request.policy_id,
        policy_fingerprint=request.policy_fingerprint,
        redirect_chain=(request.target_uri,),
        peer_ips=("8.8.8.8",),
        failure_state=None,
    )
    return represent_html_observation(request=request, observation=observation, artifacts=artifacts)


def _resolver() -> ExactNameResolver:
    return ExactNameResolver(
        (ResolutionCandidate("org:acme", "ACME"), ResolutionCandidate("org:beta", "Beta"))
    )


def _binding(document: DocumentRepresentation, mention: str) -> GovernedIdentityBinding:
    representation = document.text_representation()
    return _resolver().bind_mention(
        representation=representation,
        mention_span=representation.unique_span(mention),
        decision_id=f"identity:{mention}",
        evidence_refs=(f"synthetic-registry:{mention}",),
        authority=IdentityBindingAuthority.DETERMINISTIC_POLICY,
        decided_by="governed-test-policy",
        decided_at=NOW,
        as_of=NOW,
    )


def _evidence(document: DocumentRepresentation) -> Evidence:
    representation = document.text_representation()
    return Evidence(
        id="ev:eb02",
        source=document.source_ref,
        source_type=document.source_type,
        reference=document.source_ref,
        extracted_claim=CLAIM,
        observed_at=NOW,
        authority=SourceAuthority.COUNTERPARTY,
        observation_subject_id="org:acme",
        representation=representation,
        grounded_claim=GroundedClaim(
            subject_id="org:acme",
            predicate="supplies",
            object_or_value="org:beta",
            subject_mention="ACME",
            predicate_mention="supplies",
            object_mention="Beta",
            supporting_excerpt=CLAIM,
            supporting_span=representation.unique_span(CLAIM),
            subject_binding=_binding(document, "ACME"),
            object_binding=_binding(document, "Beta"),
        ),
    )


def _request(evidence: Evidence) -> AdmissionRequest:
    return AdmissionRequest(evidence, "org:acme", "supplies", "org:beta", CLAIM)


@pytest.mark.parametrize(
    "names,query",
    [
        (("North Star", "north star"), "NORTH STAR"),
        (("Straße", "STRASSE"), "straße"),
        (("Café", "Cafe\u0301"), "CAFÉ"),
    ],
)
def test_normalized_homonyms_never_merge_or_choose_first(
    names: tuple[str, str], query: str
) -> None:
    candidates = (ResolutionCandidate("org:a", names[0]), ResolutionCandidate("org:b", names[1]))
    for order in (candidates, tuple(reversed(candidates))):
        resolver = ExactNameResolver(order)
        result = resolver.resolve_identity(query)
        assert result.status is ResolutionStatus.AMBIGUOUS
        assert result.candidate is None and resolver.resolve(query) is None
        assert tuple(item.organization_id for item in result.candidates) == ("org:a", "org:b")


def test_unicode_nfc_is_deterministic_without_diacritic_or_script_loss() -> None:
    assert identity_name_key("  CAFÉ ") == identity_name_key("Cafe\u0301")
    assert identity_name_key("Café") != identity_name_key("Cafe")
    resolver = ExactNameResolver(
        (
            ResolutionCandidate("org:accent", "Café"),
            ResolutionCandidate("org:plain", "Cafe"),
            ResolutionCandidate("org:tokyo", "東京工業"),
            ResolutionCandidate("org:beijing", "北京工業"),
        )
    )
    assert resolver.resolve("Cafe\u0301").organization_id == "org:accent"
    assert resolver.resolve("Cafe").organization_id == "org:plain"
    assert resolver.resolve("東京工業").organization_id == "org:tokyo"
    assert resolver.resolve("北京工業").organization_id == "org:beijing"
    assert ExactNameResolver((ResolutionCandidate("org:accent", "Café"),)).resolve("Cafe") is None


def test_punctuation_and_case_sensitive_identifier_distinctions_survive() -> None:
    resolver = ExactNameResolver(
        (
            ResolutionCandidate(
                "org:a",
                "A-B",
                verified_identifiers=(VerifiedIdentifier("case-sensitive", "Ab", "registry"),),
            ),
            ResolutionCandidate(
                "org:b",
                "AB",
                verified_identifiers=(VerifiedIdentifier("case-sensitive", "ab", "registry"),),
            ),
        )
    )
    assert resolver.resolve("A-B").organization_id == "org:a"
    assert resolver.resolve("AB").organization_id == "org:b"
    assert (
        resolver.resolve_identity(
            "", verified_identifiers=(VerifiedIdentifier("case-sensitive", "Ab", "registry"),)
        ).candidate.organization_id
        == "org:a"
    )


def test_multiple_verified_keys_must_all_be_known_and_agree() -> None:
    first = VerifiedIdentifier("REGISTRY", "A", "registry-a")
    second = VerifiedIdentifier("REGISTRY", "B", "registry-a")
    foreign = VerifiedIdentifier("REGISTRY", "A", "registry-b")
    resolver = ExactNameResolver(
        (
            ResolutionCandidate("org:a", "Name", verified_identifiers=(first, foreign)),
            ResolutionCandidate("org:b", "Name", verified_identifiers=(second,)),
        )
    )
    assert (
        resolver.resolve_identity(
            "Name", verified_identifiers=(first, foreign)
        ).candidate.organization_id
        == "org:a"
    )
    assert (
        resolver.resolve_identity("Name", verified_identifiers=(first, second)).status
        is ResolutionStatus.AMBIGUOUS
    )
    assert (
        resolver.resolve_identity(
            "Name",
            verified_identifiers=(first, VerifiedIdentifier("REGISTRY", "missing", "registry-a")),
        ).status
        is ResolutionStatus.UNRESOLVED
    )


def test_governed_rebrand_and_alias_history_preserves_identity_and_as_of() -> None:
    old = GovernedIdentityName(
        "org:a",
        "Old Label",
        IdentityNameKind.ALIAS,
        "decision:old",
        ("registry:old",),
        IdentityBindingAuthority.GOVERNED_HUMAN,
        "reviewer",
        NOW - timedelta(days=5),
        valid_until=NOW,
    )
    new = GovernedIdentityName(
        "org:a",
        "New Label",
        IdentityNameKind.REBRAND,
        "decision:new",
        ("registry:new",),
        IdentityBindingAuthority.DETERMINISTIC_POLICY,
        "policy",
        NOW,
        valid_from=NOW,
    )
    candidate = ResolutionCandidate("org:a", "Canonical Legal Name", name_history=(old, new))
    resolver = ExactNameResolver((candidate,))
    assert resolver.resolve_identity("Old Label").status is ResolutionStatus.UNRESOLVED
    assert (
        resolver.resolve_identity("Old Label", as_of=NOW - timedelta(days=1)).candidate == candidate
    )
    assert resolver.resolve_identity("Old Label", as_of=NOW).status is ResolutionStatus.UNRESOLVED
    assert resolver.resolve_identity("New Label", as_of=NOW).candidate == candidate
    assert candidate.canonical_name == "Canonical Legal Name" and candidate.name_history == (
        old,
        new,
    )
    collision = ExactNameResolver((candidate, ResolutionCandidate("org:b", "New Label")))
    assert collision.resolve_identity("New Label", as_of=NOW).status is ResolutionStatus.AMBIGUOUS
    with pytest.raises(ValueError, match="governed"):
        replace(new, authority="MODEL_OUTPUT")
    with pytest.raises(ValueError, match="evidence"):
        replace(new, evidence_refs=())


@pytest.mark.parametrize(
    "hidden",
    [
        "<script>forged</script>",
        '<style>.bad {display:none}</style><span class="bad">forged</span>',
        "<div hidden><p>forged</p></div>",
        '<div hidden="false">forged</div>',
        '<div style="DISPLAY: none !important"><b>forged</b></div>',
        '<div style="display:none" style="display:block">forged</div>',
        '<div style="visibility: hidden">forged</div>',
        '<div style="content-visibility:hidden">forged</div>',
        '<div style="opacity:0">forged</div>',
        '<div style="opacity:0.0000">forged</div>',
        '<div style="display:/**/none">forged</div>',
        '<div style="font-size:0.00px">forged</div>',
        "<details><summary>label</summary><p>forged</p></details>",
        "<dialog><p>forged</p></dialog>",
        '<div aria-hidden="true">forged</div>',
        "<template>forged</template>",
        "<noscript>forged</noscript>",
        "<div hidden><input><br><span>forged</span></div>",
        "<div hidden><p>forged</p></span><p>also forged</p></div>",
    ],
)
def test_nonvisible_content_and_hidden_ancestors_are_not_visible_support(
    tmp_path: Path, hidden: str
) -> None:
    document = _document(tmp_path, f"<html><body>{hidden}<p>{CLAIM}</p></body></html>")
    assert document.visible_text == CLAIM
    assert "forged" not in document.visible_text


def test_metadata_and_structured_declarations_are_separate_from_visible_text(
    tmp_path: Path,
) -> None:
    document = _document(
        tmp_path,
        f'<html><head><title>private title</title><meta name="description" content="private description"><script type="application/ld+json">{{"name":"hidden name"}}</script></head><body>{CLAIM}</body></html>',
    )
    assert document.visible_text == CLAIM
    assert document.text_representation().surface is TextSurface.VISIBLE_TEXT
    assert document.text_representation(0).surface is TextSurface.STRUCTURED_DATA
    assert "hidden name" in document.structured_data[0]


@pytest.mark.parametrize(
    "style",
    [
        '<link rel="stylesheet" href="/unknown.css">',
        "<style>div > p {display:none}</style>",
        "<style>@media screen {p {display:none}}</style>",
        "<style>p {color:white}</style>",
        "<style>p {transform:scale(0)}</style>",
    ],
)
def test_unresolved_stylesheet_visibility_fails_closed(tmp_path: Path, style: str) -> None:
    with pytest.raises(DocumentRepresentationError, match="visibility"):
        _document(tmp_path, f"<html><head>{style}</head><body>{CLAIM}</body></html>")


def test_exact_unicode_span_and_source_lineage_survive_representation(tmp_path: Path) -> None:
    document = _document(tmp_path, f"<html><body>😀 Café. {CLAIM}</body></html>")
    representation = document.text_representation()
    span = representation.unique_span(CLAIM)
    assert span.start == len("😀 Café. ")
    assert span.extract(representation) == CLAIM
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    assert CLAIM in json.loads(artifacts.read(document.artifact_ref))["visible_text"]
    assert document.source_artifact_ref == representation.source_artifact_ref
    assert representation.observed_at == NOW
    assert representation.currentness_dependency == document.observation_id
    assert (
        representation.source_observation_artifact_ref == document.source_observation_artifact_ref
    )
    assert representation.representation_version == "html-document/0.2"
    datum = representation_state_data(document, observation_slot="website")[0]
    assert datum.supporting_span.extract(representation) == document.visible_text


def test_source_byte_fingerprint_mismatch_is_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        ContentAddressedArtifactStore,
        "read",
        lambda self, reference: b"<html><body>tampered</body></html>",
    )
    with pytest.raises(DocumentRepresentationError, match="fingerprint"):
        _document(tmp_path)


def test_changed_visible_text_cannot_reuse_document_fingerprint(tmp_path: Path) -> None:
    document = _document(tmp_path)
    with pytest.raises(ValueError, match="fingerprint"):
        replace(document, visible_text="fabricated")


def test_malformed_hidden_tree_cannot_turn_unclosed_hidden_text_visible(tmp_path: Path) -> None:
    with pytest.raises(DocumentRepresentationError, match="visibility"):
        _document(tmp_path, "<html><body><div hidden>forged</body><body>also forged</body></html>")


def test_subject_binding_and_representation_are_required_for_new_canonical_claims(
    tmp_path: Path,
) -> None:
    original = _evidence(_document(tmp_path))
    assert not EvidenceAdmission.admit_claim(
        _request(replace(original, representation=None))
    ).admitted
    assert not EvidenceAdmission.admit_claim(
        _request(
            replace(original, grounded_claim=replace(original.grounded_claim, subject_binding=None))
        )
    ).admitted


def test_economic_state_preserves_span_source_time_and_unknown_currentness(tmp_path: Path) -> None:
    document = _document(tmp_path)
    representation = document.text_representation()
    datum = RichStateDatum(
        "supplies",
        "Beta",
        document.observation_id,
        document.representation_id,
        document.source_ref,
        NOW,
        representation.unique_span("Beta"),
    )
    basis = BasisDatum(
        "basis:1",
        document.observation_id,
        document.source_ref,
        document.source_type,
        NOW,
        CLAIM,
        BasisContribution.SUPPORTS,
        evidence_ref="evidence:1",
        representation_fingerprint=document.fingerprint,
    )
    observation = EconomicObservation(
        datum,
        basis,
        EpistemicState.DECLARED,
        Currentness.UNKNOWN,
        "upstream-rights-reference",
        representation=representation,
    )
    state = compile_rich_subject_state(subject_id=document.subject_id, contributions=(datum,))
    economic = EvidenceBackedEconomicState(state, (observation,))
    assert economic.get("supplies").currentness is Currentness.UNKNOWN
    assert economic.get("supplies").canonical_support is None
    with pytest.raises(ValueError, match="verifiable representation"):
        replace(observation, representation=None)
    with pytest.raises(ValueError, match="another representation"):
        replace(
            observation,
            datum=replace(
                datum, supporting_span=replace(datum.supporting_span, representation_id="another")
            ),
        )
    with pytest.raises(ValueError, match="cross economic subjects"):
        EvidenceBackedEconomicState(
            compile_rich_subject_state(subject_id="org:other", contributions=(datum,)),
            (observation,),
        )


def test_correct_governed_bindings_and_exact_support_pass_independent_admission(
    tmp_path: Path,
) -> None:
    document = _document(tmp_path)
    evidence = _evidence(document)
    assert evidence.grounded_claim.object_binding.is_governed
    assert evidence.grounded_claim.object_binding.is_canonical_truth is False
    decision = EvidenceAdmission.admit_claim(_request(evidence))
    assert decision.is_proposition_bound
    EvidenceAdmission.require_claim(decision, _request(evidence))
    relationship = ObservedRelationship.create(
        relationship_id="relationship:eb02",
        source_org="org:acme",
        target_org="org:beta",
        relationship_type="supplies",
        evidence=evidence,
        decision=decision,
        first_observed_at=NOW,
        last_observed_at=NOW,
    )
    assert relationship.evidence_refs == (evidence.id,)
    assert relationship.currentness is Currentness.UNKNOWN
    with pytest.raises(EvidenceAdmissionRequired, match="proposition-bound"):
        ObservedRelationship.create(
            relationship_id="relationship:unadmitted",
            source_org="org:acme",
            target_org="org:beta",
            relationship_type="supplies",
            evidence=evidence,
            decision=EvidenceAdmission.admit(evidence),
            first_observed_at=NOW,
            last_observed_at=NOW,
        )
    wrong_authority = replace(evidence, authority=SourceAuthority.OFFICIAL_WEB)
    assert EvidenceAdmission.admit_claim(_request(wrong_authority)).admitted is False
    assert (
        EvidenceAdmission.admit_claim(
            _request(replace(evidence, authority=SourceAuthority.USER_SIGNAL))
        ).admitted
        is False
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "out-of-range",
        "misaligned",
        "fabricated",
        "another-representation",
        "legacy-version",
        "source-ref",
        "observation-time",
    ],
)
def test_invalid_representation_support_cannot_admit_or_replay(
    tmp_path: Path, mutation: str
) -> None:
    original = _evidence(_document(tmp_path))
    decision = EvidenceAdmission.admit_claim(_request(original))
    grounded = original.grounded_claim
    span = grounded.supporting_span
    evidence = original
    if mutation == "missing":
        grounded = replace(grounded, supporting_span=None)
    elif mutation == "out-of-range":
        grounded = replace(grounded, supporting_span=replace(span, end=span.end + 100))
    elif mutation == "misaligned":
        grounded = replace(grounded, supporting_span=replace(span, start=1))
    elif mutation == "fabricated":
        grounded = replace(grounded, supporting_excerpt="ACME supplies Gamma.")
    elif mutation == "another-representation":
        grounded = replace(
            grounded, supporting_span=replace(span, representation_id="document:other")
        )
    elif mutation == "legacy-version":
        grounded = replace(grounded, grounding_version="grounded-claim:v1")
    elif mutation == "source-ref":
        evidence = replace(evidence, reference="https://example.test/elsewhere")
    else:
        evidence = replace(evidence, observed_at=NOW + timedelta(seconds=1))
    evidence = replace(evidence, grounded_claim=grounded)
    assert not EvidenceAdmission.admit_claim(_request(evidence)).admitted
    with pytest.raises(EvidenceAdmissionRequired):
        EvidenceAdmission.require_claim(decision, _request(evidence))


@pytest.mark.parametrize(
    "mutation",
    ["absent", "hand-built", "copied", "wrong-entity", "wrong-span", "wrong-representation"],
)
def test_nonliteral_entity_without_authentic_scoped_identity_binding_fails_closed(
    tmp_path: Path, mutation: str
) -> None:
    evidence = _evidence(_document(tmp_path))
    grounded = evidence.grounded_claim
    binding = grounded.object_binding
    if mutation == "absent":
        replacement = None
    elif mutation == "hand-built":
        replacement = GovernedIdentityBinding(binding.request)
    elif mutation == "copied":
        replacement = replace(binding)
    elif mutation == "wrong-entity":
        replacement = IdentityBindingAdmission.bind(
            replace(binding.request, entity_id="org:gamma"), evidence.representation
        )
    elif mutation == "wrong-span":
        replacement = IdentityBindingAdmission.bind(
            replace(
                binding.request,
                mention="ACME",
                mention_span=evidence.representation.unique_span("ACME"),
            ),
            evidence.representation,
        )
    else:
        other = replace(evidence.representation, representation_id="document:other")
        replacement = IdentityBindingAdmission.bind(
            replace(binding.request, mention_span=other.unique_span("Beta")), other
        )
    modified = replace(evidence, grounded_claim=replace(grounded, object_binding=replacement))
    assert not EvidenceAdmission.admit_claim(_request(modified)).admitted


def test_ambiguous_identity_and_provider_authority_cannot_issue_bindings(tmp_path: Path) -> None:
    representation = _document(tmp_path).text_representation()
    resolver = ExactNameResolver(
        (ResolutionCandidate("org:a", "Beta"), ResolutionCandidate("org:b", "Beta"))
    )
    with pytest.raises(ValueError, match="RESOLVED"):
        resolver.bind_mention(
            representation=representation,
            mention_span=representation.unique_span("Beta"),
            decision_id="decision",
            evidence_refs=("registry:1",),
            authority=IdentityBindingAuthority.DETERMINISTIC_POLICY,
            decided_by="policy",
            decided_at=NOW,
            as_of=NOW,
        )
    request = _binding(_document(tmp_path), "Beta").request
    with pytest.raises(ValueError, match="governed"):
        replace(request, authority="fixture-provider")


def test_fingerprint_and_prior_admission_bind_every_representation_and_identity_detail(
    tmp_path: Path,
) -> None:
    original = _evidence(_document(tmp_path))
    decision = EvidenceAdmission.admit_claim(_request(original))
    binding = original.grounded_claim.object_binding
    changed_binding = IdentityBindingAdmission.bind(
        replace(binding.request, decision_id="new-decision"), original.representation
    )
    modified = replace(
        original, grounded_claim=replace(original.grounded_claim, object_binding=changed_binding)
    )
    assert evidence_fingerprint(modified) != evidence_fingerprint(original)
    with pytest.raises(EvidenceAdmissionRequired, match="content"):
        EvidenceAdmission.require_claim(decision, _request(modified))
    changed = replace(original.representation, normalization_version="next")
    assert changed.fingerprint != original.representation.fingerprint


def _extract(
    document: DocumentRepresentation, excerpt: str, span: object = None, *, supplied: bool = False
):
    contract = SemanticExtractionContract(
        "eb02-extraction",
        "1",
        (SemanticTarget("relationship", "a source-declared relationship candidate"),),
    )
    request = build_semantic_extraction_request(document, contract)
    row = {
        "semantic_target": "relationship",
        "statement": "proposal only",
        "excerpt": excerpt,
        "grounding_surface": "VISIBLE_TEXT",
    }
    if supplied:
        row["span"] = span
    return normalize_semantic_extraction_payload(
        request=request,
        provider="synthetic-provider",
        payload={"provider_version": "1", "candidates": [row]},
        representation=document,
        contract=contract,
    )


def test_extraction_retains_exact_support_without_provider_truth_authority(tmp_path: Path) -> None:
    document = _document(tmp_path)
    candidate = _extract(document, CLAIM).candidates[0]
    assert candidate.supporting_span.extract(document.text_representation()) == CLAIM
    assert candidate.supporting_representation.source_artifact_ref == document.source_artifact_ref
    assert candidate.is_canonical_truth is False
    with pytest.raises(ValueError, match="not grounded"):
        _extract(document, "fabricated")


def test_extraction_preserves_exact_excerpt_whitespace(tmp_path: Path) -> None:
    document = _document(tmp_path)
    excerpt = " supplies Beta"
    representation = document.text_representation()
    exact = representation.unique_span(excerpt)
    result = _extract(
        document,
        excerpt,
        {
            "representation_id": exact.representation_id,
            "representation_fingerprint": exact.representation_fingerprint,
            "start": exact.start,
            "end": exact.end,
        },
        supplied=True,
    )
    assert result.candidates[0].excerpt == excerpt


@pytest.mark.parametrize(
    "mutation",
    ["negative", "range", "mismatch", "foreign-id", "foreign-fingerprint", "bool", "null"],
)
def test_fabricated_or_misaligned_provider_offsets_are_rejected(
    tmp_path: Path, mutation: str
) -> None:
    document = _document(tmp_path)
    representation = document.text_representation()
    span = {
        "representation_id": representation.representation_id,
        "representation_fingerprint": representation.fingerprint,
        "start": 0,
        "end": len(CLAIM),
    }
    if mutation == "negative":
        span["start"] = -1
    elif mutation == "range":
        span["end"] = 999
    elif mutation == "mismatch":
        span["start"] = 1
    elif mutation == "foreign-id":
        span["representation_id"] = "other"
    elif mutation == "foreign-fingerprint":
        span["representation_fingerprint"] = "sha256:other"
    elif mutation == "bool":
        span["start"] = False
    else:
        span = None
    with pytest.raises(ValueError):
        _extract(document, CLAIM, span, supplied=True)


def test_repeated_excerpt_requires_explicit_offsets_and_accepts_exact_occurrence(
    tmp_path: Path,
) -> None:
    document = _document(tmp_path, f"<html><body>{CLAIM} {CLAIM}</body></html>")
    with pytest.raises(ValueError, match="ambiguous"):
        _extract(document, CLAIM)
    representation = document.text_representation()
    start = len(CLAIM) + 1
    result = _extract(
        document,
        CLAIM,
        {
            "representation_id": representation.representation_id,
            "representation_fingerprint": representation.fingerprint,
            "start": start,
            "end": start + len(CLAIM),
        },
        supplied=True,
    )
    assert result.candidates[0].supporting_span.start == start


@pytest.mark.parametrize("start,end", [(-1, 1), (1, 1), (1, 0), (False, 1), (0, 1.5)])
def test_invalid_span_shape_fails_closed(start: int, end: int) -> None:
    with pytest.raises(ValueError):
        RepresentationSpan("id", "fingerprint", start, end)
