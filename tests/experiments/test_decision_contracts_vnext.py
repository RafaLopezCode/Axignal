from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from experiments.decision_lab.answerability_vnext import validate_decision_request
from experiments.decision_lab.cli import _run_live
from experiments.decision_lab.compiler_vnext import (
    assemble_state,
    canonical_serialize,
    compile_decision_state,
)
from experiments.decision_lab.composer_vnext import compose_vnext
from experiments.decision_lab.contracts_vnext import (
    DECISION_CONTRACTS,
    DecisionFamily,
    Missingness,
    Primitive,
    deterministic_entity_identifier_result,
    missingness,
    path_value,
    question_semantic_fingerprint,
    validate_grammar_vnext,
    validate_primitive_contract,
    validate_question_binding,
    validate_required_arguments,
)
from experiments.decision_lab.failure_attribution_vnext import (
    AttributionBasis,
    FailureAttribution,
    FailureClass,
)
from experiments.decision_lab.models import LabError, NormalizedJudgment
from experiments.decision_lab.pilot import run_experiment as run_historical_experiment
from experiments.decision_lab.pilot import run_smoke as run_historical_smoke
from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator
from experiments.decision_lab.records_vnext import DecisionCaseRecord
from experiments.decision_lab.requests_vnext import (
    DeterministicDecisionResult,
    ValidatedProviderRequest,
    prepare_provider_request,
)
from experiments.decision_lab.validity_vnext import (
    VALIDITY_GATES,
    quality_eligible_cases,
    validate_experiment_validity,
)

ROOT = Path(__file__).resolve().parents[2]


def vnext_question(question_id: str) -> dict[str, object]:
    document = json.loads(
        (ROOT / "experiments/decision_lab/grammar/vnext/grammar.json").read_text()
    )
    return next(item for item in document["questions"] if item["question_id"] == question_id)


def vnext_2_claim_question() -> dict[str, object]:
    return json.loads(
        (
            ROOT / "experiments/decision_lab/grammar/vnext/claim-evidence-support.vNext.2.json"
        ).read_text(encoding="utf-8")
    )


def claim_state() -> dict[str, object]:
    return {
        "state_contract_version": "claim-evidence.vNext.1",
        "claim": {"proposition": "The fictional entity supplies component Q."},
        "evidence": [
            {
                "evidence_id": "ev-1",
                "content": "The fictional entity lists component Q in its public catalogue.",
                "provenance": {"source_ref": "synthetic://catalogue/1"},
            }
        ],
    }


def test_decision_contract_declares_the_full_owned_boundary() -> None:
    contract = DECISION_CONTRACTS["CES.SUPPORT.vNext"]
    assert contract.family is DecisionFamily.CLAIM_EVIDENCE_SUPPORT
    assert contract.semantic_target and contract.primitive is Primitive.CHOICE
    assert contract.answer_space == (
        "SUPPORTED",
        "PARTIAL",
        "NOT_SUPPORTED",
        "NO_EVIDENCE",
        "CONFLICTING",
        "UNRESOLVED",
    )
    assert contract.uncertainty_semantics and contract.composition_policy
    assert "EvidenceAdmission" in contract.authority_boundary


def test_vnext_1_claim_evidence_question_identity_and_answer_space_are_historical() -> None:
    question = vnext_question("CES.SUPPORT.vNext")
    contract = DECISION_CONTRACTS["CES.SUPPORT.vNext"]
    assert question["version"] == "vNext.1"
    assert question_semantic_fingerprint(question) == (
        "bdf8d25fce3fa66e5dd71e512085fcd81130109a792c7c7954681408f9c9f35b"
    )
    assert contract.question_semantic_fingerprint == (
        "bdf8d25fce3fa66e5dd71e512085fcd81130109a792c7c7954681408f9c9f35b"
    )
    assert contract.answer_space == (
        "SUPPORTED",
        "PARTIAL",
        "NOT_SUPPORTED",
        "NO_EVIDENCE",
        "CONFLICTING",
        "UNRESOLVED",
    )
    grammar = json.loads(
        (ROOT / "experiments/decision_lab/grammar/vnext/grammar.json").read_text(encoding="utf-8")
    )
    assert grammar["version"] == "vNext.1"
    assert len(grammar["questions"]) == 12
    assert validate_grammar_vnext(grammar) == []


def test_vnext_2_claim_evidence_semantics_close_the_answer_space() -> None:
    question = vnext_2_claim_question()
    contract = DECISION_CONTRACTS["CES.SUPPORT.vNext.2"]
    options = question["criteria"]["options"]
    meanings = {item["id"]: item["meaning"] for item in options}

    assert contract.question_id == "CES.SUPPORT.vNext.2"
    assert contract.question_version == "vNext.2"
    assert contract.version == "decision-contract.vNext.2"
    assert contract.state_contract_version == "claim-evidence.vNext.1"
    assert tuple(meanings) == contract.answer_space
    assert validate_question_binding("CES.SUPPORT.vNext.2", question, claim_state()) == []

    conceptual_cases = {
        "FULL_SUPPORT": "SUPPORTED",
        "PARTIAL_SUPPORT": "PARTIAL",
        "DIRECT_CONTRADICTION": "CONTRADICTED",
        "RELEVANT_NON_SUPPORT": "NOT_SUPPORTED",
        "NO_RELEVANT_EVIDENCE": "NO_EVIDENCE",
        "MULTI_EVIDENCE_CONFLICT": "CONFLICTING",
        "AMBIGUOUS_OR_UNRESOLVABLE": "UNRESOLVED",
    }
    assert set(conceptual_cases.values()) == set(contract.answer_space)
    assert "directly contradicts" in meanings["CONTRADICTED"]
    assert "incompatible assertions" in meanings["CONFLICTING"]
    assert "neither supports nor directly contradicts" in meanings["NOT_SUPPORTED"]
    assert "passages were supplied" in meanings["NO_EVIDENCE"]
    assert "no material refutation" in meanings["SUPPORTED"]
    assert "does not refute" in meanings["PARTIAL"]
    assert "prevents a determinate classification" in meanings["UNRESOLVED"]
    assert question["criteria"]["classification_precedence"] == [
        "CONFLICTING",
        "CONTRADICTED",
        "SUPPORTED",
        "PARTIAL",
        "NOT_SUPPORTED",
        "NO_EVIDENCE",
        "UNRESOLVED",
    ]


def test_vnext_2_no_relevant_evidence_requires_supplied_passage() -> None:
    state = claim_state()
    state["evidence"] = []
    result = validate_decision_request("CES.SUPPORT.vNext.2", state)
    assert result.status == "NOT_ANSWERABLE"
    assert "EMPTY_REQUIRED_INFORMATION" in result.reasons
    question = vnext_2_claim_question()
    no_evidence = next(
        item for item in question["criteria"]["options"] if item["id"] == "NO_EVIDENCE"
    )
    assert "passages were supplied" in no_evidence["meaning"]
    assert "none is relevant" in question["instructions"]


def test_provider_question_binding_rejects_vnext_cross_version_and_semantic_drift() -> None:
    v1_question = vnext_question("CES.SUPPORT.vNext")
    v2_question = vnext_2_claim_question()
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", v2_question, claim_state()
    )
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext.2", v1_question, claim_state()
    )
    changed_v2 = vnext_2_claim_question()
    changed_v2["criteria"]["options"][2]["meaning"] = "A different semantic definition."
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext.2", changed_v2, claim_state()
    )

    sealed = prepare_provider_request("CES.SUPPORT.vNext.2", claim_state(), v2_question, {})
    assert isinstance(sealed, ValidatedProviderRequest)
    _, bound_question = sealed.provider_payload()
    assert bound_question["question_id"] == "CES.SUPPORT.vNext.2"

    with pytest.raises(LabError, match="QUESTION_SEMANTIC_FINGERPRINT_MISMATCH"):
        prepare_provider_request(
            "CES.SUPPORT.vNext.2",
            claim_state(),
            v1_question,
            {},
        )


def test_vnext_grammar_audits_all_twelve_questions_with_machine_contracts() -> None:
    import json

    grammar = json.loads(
        (ROOT / "experiments/decision_lab/grammar/vnext/grammar.json").read_text(encoding="utf-8")
    )
    assert validate_grammar_vnext(grammar) == []
    assert len(grammar["questions"]) == 12
    assert {item["decision"] for item in grammar["questions"]} <= {
        "REWRITE",
        "REPLACE",
        "EXPERIMENTAL_COMPARATOR_ONLY",
    }


def test_claim_state_with_semantic_content_is_answerable() -> None:
    result = validate_decision_request("CES.SUPPORT.vNext", claim_state())
    assert result.status == "ANSWERABLE"
    assert result.reasons == ()
    assert result.authority == "AXIGNAL_PRE_PROVIDER_INFORMATION_CONTROL"


def test_missing_claim_and_identifier_only_evidence_fail_closed() -> None:
    state = claim_state()
    del state["claim"]
    state["evidence"][0]["content"] = state["evidence"][0]["evidence_id"]  # type: ignore[index]
    result = validate_decision_request("CES.SUPPORT.vNext", state)
    assert result.status == "NOT_ANSWERABLE"
    assert "MISSING_REQUIRED_INFORMATION" in result.reasons
    assert "MISSING_SEMANTIC_CONTENT" in result.reasons


def test_reference_resolution_includes_content_and_unresolved_ref_blocks() -> None:
    state = {
        "state_contract_version": "claim-evidence.vNext.1",
        "claim": {"proposition": "Q exists."},
        "evidence_refs": ["ev-1", "missing"],
    }
    assembled, unresolved = assemble_state(
        state,
        {"ev-1": {"content": "Catalogue lists Q.", "provenance": {"source_ref": "s1"}}},
    )
    assert assembled["evidence"][0]["content"] == "Catalogue lists Q."
    assert unresolved == ("missing",)
    compiled = compile_decision_state(
        "CES.SUPPORT.vNext", assembled, unresolved_references=unresolved
    )
    assert compiled.answerability.status == "NOT_ANSWERABLE"
    assert "UNRESOLVED_REFERENCE" in compiled.answerability.reasons


def test_compiler_separates_serialization_fingerprint_and_answerability() -> None:
    state = claim_state()
    compiled = compile_decision_state("CES.SUPPORT.vNext", state)
    assert compiled.answerability.status == "ANSWERABLE"
    assert compiled.canonical_json == canonical_serialize(state)
    assert compiled.fingerprint == hashlib.sha256(compiled.canonical_json.encode()).hexdigest()


def test_absent_empty_unknown_unavailable_and_not_applicable_are_distinct() -> None:
    assert missingness(None) is Missingness.EMPTY
    assert missingness("") is Missingness.EMPTY
    assert missingness({"status": "UNKNOWN"}) is Missingness.UNKNOWN
    assert missingness({"status": "UNAVAILABLE"}) is Missingness.UNAVAILABLE
    assert missingness({"status": "NOT_APPLICABLE"}) is Missingness.NOT_APPLICABLE
    assert missingness("present") is Missingness.PRESENT
    assert missingness(path_value({}, "claim.proposition")) is Missingness.ABSENT
    assert missingness(path_value({"evidence": []}, "evidence[*]")) is Missingness.EMPTY
    result = validate_decision_request(
        "CES.SUPPORT.vNext", {"state_contract_version": "claim-evidence.vNext.1"}
    )
    assert "MISSING_REQUIRED_INFORMATION" in result.reasons


def test_entity_alignment_requires_two_entity_records_and_semantic_evidence() -> None:
    state = {
        "state_contract_version": "entity-alignment.vNext.1",
        "entities": {"a": {"name": "Acme Europe"}},
        "evidence": [
            {
                "content": "A is a subsidiary of B",
                "evidence_id": "e1",
                "provenance": {"source_ref": "synthetic://entity/pair"},
            }
        ],
    }
    result = validate_decision_request("ENT.ALIGN.vNext", state)
    assert result.status == "NOT_ANSWERABLE"
    assert "MISSING_REQUIRED_INFORMATION" in result.reasons
    assert "INSUFFICIENT_CARDINALITY" in result.reasons
    complete_pair = {
        "state_contract_version": "entity-alignment.vNext.1",
        "entities": {"a": {"name": "A"}, "b": {"name": "B"}},
        "evidence": [
            {
                "content": "A is a subsidiary of B",
                "evidence_id": "e1",
                "provenance": {"source_ref": "synthetic://entity/pair"},
            }
        ],
    }
    assert validate_decision_request("ENT.ALIGN.vNext", complete_pair).status == "ANSWERABLE"
    assert (
        deterministic_entity_identifier_result(
            {
                "entities": {
                    "a": {
                        "name": "A",
                        "canonical_identifier": {
                            "scheme": "LEI",
                            "authority": "GLEIF",
                            "validation_status": "VERIFIED",
                            "value": "5493001KJTIIGC8Y1R12",
                        },
                    },
                    "b": {
                        "name": "A Ltd",
                        "canonical_identifier": {
                            "scheme": "LEI",
                            "authority": "GLEIF",
                            "validation_status": "VERIFIED",
                            "value": "5493001KJTIIGC8Y1R12",
                        },
                    },
                }
            }
        )
        == "SAME_LEGAL_ENTITY"
    )


def test_relationship_requires_endpoints_direction_provenance_and_temporal_context() -> None:
    state = {
        "state_contract_version": "economic-relationship.vNext.1",
        "relationship": {
            "endpoints": ["A", "B"],
            "proposition": "A supplies B.",
            "direction": "A_TO_B",
        },
        "evidence": [
            {"content": "A's report names B as a customer.", "provenance": {"source_ref": "r1"}}
        ],
        "requirements": {"temporal_context_required": True},
    }
    result = validate_decision_request("REL.EXISTENCE.vNext", state)
    assert "MISSING_TEMPORAL_REFERENCE" in result.reasons
    state["temporal_context"] = {"as_of": "2026-01-01"}
    assert validate_decision_request("REL.EXISTENCE.vNext", state).status == "ANSWERABLE"


def test_choice_score_and_noul_contracts_validate_their_own_semantics() -> None:
    assert (
        validate_primitive_contract(
            Primitive.CHOICE,
            {
                "mutually_exclusive": True,
                "coverage": "EXHAUSTIVE_WITH_UNRESOLVED",
                "options": [
                    {"id": "YES", "meaning": "Proposition supported."},
                    {"id": "NO", "meaning": "Proposition contradicted."},
                ],
            },
        )
        == []
    )
    assert validate_primitive_contract(
        Primitive.CHOICE,
        {
            "mutually_exclusive": True,
            "coverage": "EXHAUSTIVE_WITH_UNRESOLVED",
            "options": [{"id": "YES", "meaning": ""}, {"id": "NO", "meaning": "No."}],
        },
    ) == ["OPTION_MEANING_MISSING"]
    assert validate_primitive_contract(
        Primitive.SCORE,
        {"levels": [{"ordinal": 0, "meaning": "low"}, {"ordinal": 2, "meaning": "high"}]},
    ) == ["INVALID_SCORE_ORDER"]
    assert (
        validate_primitive_contract(
            Primitive.NOUL,
            {"proposition": "A supplies B", "required_arguments": ["relationship.endpoints"]},
        )
        == []
    )
    assert validate_primitive_contract(
        Primitive.NOUL, {"proposition": "", "required_arguments": []}
    ) == ["NOUL_PROPOSITION_ARGUMENT_MISSING"]
    assert (
        validate_required_arguments(
            {"claim": {"proposition": "A supplies B."}},
            {"proposition": "A supplies B", "required_arguments": ["claim.proposition"]},
        )
        == []
    )
    assert validate_required_arguments(
        {}, {"proposition": "A supplies B", "required_arguments": ["claim.proposition"]}
    ) == ["NOUL_PROPOSITION_ARGUMENT_MISSING"]


def test_provider_question_binding_rejects_answer_space_and_noul_argument_drift() -> None:
    claim_question = vnext_question("CES.SUPPORT.vNext")
    assert validate_question_binding("CES.SUPPORT.vNext", claim_question, claim_state()) == []
    claim_question["instructions"] = "Altered instructions"
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", claim_question, claim_state()
    )
    claim_question = vnext_question("CES.SUPPORT.vNext")
    claim_question["criteria"]["options"][0]["meaning"] = "Changed meaning; same option ID."
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", claim_question, claim_state()
    )
    claim_question = vnext_question("CES.SUPPORT.vNext")
    claim_question["criteria"]["options"] = list(reversed(claim_question["criteria"]["options"]))
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", claim_question, claim_state()
    )
    claim_question = vnext_question("CES.SUPPORT.vNext")
    claim_question["primitive"] = "SCORE"
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", claim_question, claim_state()
    )
    claim_question = vnext_question("CES.SUPPORT.vNext")
    claim_question["semantic_target"] = "Different target"
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", claim_question, claim_state()
    )
    claim_question = vnext_question("CES.SUPPORT.vNext")
    claim_question["version"] = "vNext.2"
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", claim_question, claim_state()
    )
    claim_question["criteria"]["options"] = claim_question["criteria"]["options"][:-1]
    assert "ANSWER_SPACE_CONTRACT_MISMATCH" in validate_question_binding(
        "CES.SUPPORT.vNext", claim_question, claim_state()
    )

    relationship_state = {
        "state_contract_version": "economic-relationship.vNext.1",
        "relationship": {
            "endpoints": ["A", "B"],
            "proposition": "A supplies B.",
            "direction": "A_TO_B",
        },
        "evidence": [{"content": "A supplies B.", "provenance": {"source_ref": "synthetic://r1"}}],
    }
    relationship_question = vnext_question("REL.EXISTENCE.vNext")
    assert (
        validate_question_binding("REL.EXISTENCE.vNext", relationship_question, relationship_state)
        == []
    )
    relationship_question["criteria"]["proposition"] = "Changed Noul proposition"
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH" in validate_question_binding(
        "REL.EXISTENCE.vNext", relationship_question, relationship_state
    )
    relationship_question = vnext_question("REL.EXISTENCE.vNext")
    relationship_question["criteria"]["required_arguments"] = ["unmodeled.secret"]
    assert "NOUL_ARGUMENT_NOT_IN_STATE_CONTRACT" in validate_question_binding(
        "REL.EXISTENCE.vNext", relationship_question, relationship_state
    )


def test_question_fingerprint_is_stable_and_binds_score_and_noul_semantics() -> None:
    base = vnext_question("CES.SUPPORT.vNext")
    reordered = {key: base[key] for key in reversed(list(base))}
    assert question_semantic_fingerprint(base) == question_semantic_fingerprint(reordered)
    score = json.loads((ROOT / "experiments/decision_lab/grammar/vnext/grammar.json").read_text())[
        "questions"
    ]
    score_question = next(
        item for item in score if item["question_id"] == "CES.SUPPORT_SCORE.vNext"
    )
    original = question_semantic_fingerprint(score_question)
    score_question["criteria"]["levels"].reverse()
    assert question_semantic_fingerprint(score_question) != original
    score_question["criteria"]["levels"].reverse()
    score_question["criteria"]["levels"][0]["meaning"] = "Changed meaning"
    assert question_semantic_fingerprint(score_question) != original
    grammar = json.loads((ROOT / "experiments/decision_lab/grammar/vnext/grammar.json").read_text())
    score_definition = next(
        item for item in grammar["questions"] if item["question_id"] == "CES.SUPPORT_SCORE.vNext"
    )
    score_definition["criteria"]["levels"][0]["meaning"] = "Changed meaning"
    assert "QUESTION_SEMANTIC_FINGERPRINT_MISMATCH:CES.SUPPORT_SCORE.vNext" in (
        validate_grammar_vnext(grammar)
    )
    noul = vnext_question("REL.EXISTENCE.vNext")
    original_noul = question_semantic_fingerprint(noul)
    noul["criteria"]["required_arguments"].pop()
    assert question_semantic_fingerprint(noul) != original_noul


def test_authoritative_gate_rejects_unresolved_empty_unknown_and_legacy_refs() -> None:
    question = vnext_question("CES.SUPPORT.vNext")
    base = claim_state()
    base.pop("evidence")
    base["evidence_refs"] = ["e1"]
    invalid = [
        (base, {}),
        (base, {"e1": {"content": "", "provenance": {"source_ref": "synthetic://empty"}}}),
        (
            base,
            {
                "e1": {
                    "status": "UNKNOWN",
                    "provenance": {"source_ref": "synthetic://unknown"},
                }
            },
        ),
    ]
    for state, catalog in invalid:
        with pytest.raises(LabError):
            prepare_provider_request("CES.SUPPORT.vNext", state, question, catalog)

    syntactic_only = claim_state()
    syntactic_only["evidence"] = [
        {"evidence_id": "present-id", "provenance": {"source_ref": "synthetic://no-content"}}
    ]
    with pytest.raises(LabError, match="NOT_ANSWERABLE"):
        prepare_provider_request("CES.SUPPORT.vNext", syntactic_only, question, {})

    legacy = claim_state()
    legacy.pop("evidence")
    legacy["evidence_ids"] = ["fake"]
    with pytest.raises(LabError, match="REFERENCE_UNRESOLVED"):
        prepare_provider_request("CES.SUPPORT.vNext", legacy, question, {})
    direct = validate_decision_request(
        "CES.SUPPORT.vNext",
        {**claim_state(), "evidence_ids": ["fake"]},
    )
    assert direct.status == "NOT_ANSWERABLE"
    assert "UNRESOLVED_REFERENCE" in direct.reasons
    preserved_unknown = compile_decision_state(
        "CES.SUPPORT.vNext",
        {
            **claim_state(),
            "evidence": [
                {
                    "status": "UNKNOWN",
                    "provenance": {"source_ref": "synthetic://unknown"},
                }
            ],
        },
    )
    assert preserved_unknown.payload["evidence"][0]["status"] == "UNKNOWN"
    assert preserved_unknown.answerability.status == "NOT_ANSWERABLE"


def test_resolved_references_create_request_and_payload_cannot_mutate_silently() -> None:
    question = vnext_question("CES.SUPPORT.vNext")
    state = claim_state()
    state.pop("evidence")
    state["evidence_refs"] = ["e1"]
    catalog = {
        "e1": {
            "content": "The public catalogue lists component Q.",
            "provenance": {"source_ref": "synthetic://resolved"},
        }
    }
    request = prepare_provider_request("CES.SUPPORT.vNext", state, question, catalog)
    assert isinstance(request, ValidatedProviderRequest)
    state["claim"]["proposition"] = "mutated after validation"
    question["instructions"] = "mutated after validation"
    payload, bound_question = request.provider_payload()
    assert payload["claim"]["proposition"] == "The fictional entity supplies component Q."
    assert bound_question["instructions"] != "mutated after validation"
    object.__setattr__(request, "_state_json", request._state_json + " ")
    with pytest.raises(LabError, match="integrity check failed"):
        request.provider_payload()


def test_direct_raw_adapter_call_fails_before_fake_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    from types import ModuleType

    observed = {"calls": 0}

    class FakeClient:
        def __init__(self, **_kwargs: object) -> None:
            observed["calls"] += 1

    fake = ModuleType("typesafe_sdk")
    fake.TypeSafeClient = FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "typesafe_sdk", fake)
    evaluator = TypeSafeLabEvaluator(api_key="offline-test-only")
    with pytest.raises(LabError, match="requires ValidatedProviderRequest"):
        evaluator.evaluate(claim_state(), model="fake-model")  # type: ignore[arg-type]
    assert observed["calls"] == 0

    class OverriddenRequest(ValidatedProviderRequest):
        def provider_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return claim_state(), vnext_question("CES.SUPPORT.vNext")

    forged = object.__new__(OverriddenRequest)
    with pytest.raises(LabError, match="requires ValidatedProviderRequest"):
        evaluator.evaluate(forged, model="fake-model")
    assert observed["calls"] == 0


def test_provider_request_constructor_cannot_be_forged_with_boolean_metadata() -> None:
    with pytest.raises(LabError, match="created by the authoritative gate"):
        ValidatedProviderRequest("{}", "{}", "0" * 64, "0" * 64, _seal=True)  # type: ignore[arg-type]


def test_exact_verified_lei_short_circuits_and_has_no_model_provenance() -> None:
    state = {
        "state_contract_version": "entity-alignment.vNext.1",
        "entities": {
            "a": {
                "name": "A",
                "canonical_identifier": {
                    "scheme": "LEI",
                    "authority": "GLEIF",
                    "validation_status": "VERIFIED",
                    "value": "5493001KJTIIGC8Y1R12",
                },
            },
            "b": {
                "name": "A Ltd",
                "canonical_identifier": {
                    "scheme": "LEI",
                    "authority": "GLEIF",
                    "validation_status": "VERIFIED",
                    "value": "5493001KJTIIGC8Y1R12",
                },
            },
        },
        "evidence": [
            {
                "content": "Synthetic identity evidence.",
                "provenance": {"source_ref": "synthetic://identity"},
            }
        ],
    }
    result = prepare_provider_request(
        "ENT.ALIGN.vNext", state, vnext_question("ENT.ALIGN.vNext"), {}
    )
    assert isinstance(result, DeterministicDecisionResult)
    assert result.result == "SAME_LEGAL_ENTITY"
    assert result.rule_id == "entity-alignment.exact-verified-lei.v1"
    assert result.identifier_namespace == "GLEIF:LEI"
    assert "confidence" not in result.to_dict()
    assert "model" not in result.to_dict()
    assert (
        quality_eligible_cases(
            [
                {
                    "case_id": "deterministic",
                    "answerability": {"status": "ANSWERABLE"},
                    "result_source": "DETERMINISTIC_RESULT",
                    "expected_outcome": "SAME_LEGAL_ENTITY",
                    "label_provenance": "synthetic",
                    "raw_judgment": {"status": "ANSWERED"},
                }
            ]
        )
        == []
    )
    state["entities"]["b"]["canonical_identifier"]["value"] = "529900T8BM49AURSDO55"
    different = prepare_provider_request(
        "ENT.ALIGN.vNext", state, vnext_question("ENT.ALIGN.vNext"), {}
    )
    assert isinstance(different, DeterministicDecisionResult)
    assert different.result == "DISTINCT_ENTITY"


def test_unverified_or_different_identifier_does_not_claim_deterministic_identity() -> None:
    question = vnext_question("ENT.ALIGN.vNext")
    state = {
        "state_contract_version": "entity-alignment.vNext.1",
        "entities": {
            "a": {"name": "Same Name"},
            "b": {"name": "Same Name"},
        },
        "evidence": [{"content": "Pair evidence.", "provenance": {"source_ref": "s"}}],
    }
    assert isinstance(
        prepare_provider_request("ENT.ALIGN.vNext", state, question, {}),
        ValidatedProviderRequest,
    )


def test_lei_deterministic_rule_rejects_unicode_lookalikes_and_invalid_references() -> None:
    question = vnext_question("ENT.ALIGN.vNext")
    state = {
        "state_contract_version": "entity-alignment.vNext.1",
        "entities": {
            key: {
                "name": f"Entity {key}",
                "canonical_identifier": {
                    "scheme": "LEI",
                    "authority": "GLEIF",
                    "validation_status": "VERIFIED",
                    "value": "5493001KJTIIGC8Y1R12",
                },
            }
            for key in ("a", "b")
        },
        "evidence": [
            {
                "content": "Synthetic identity evidence.",
                "provenance": {"source_ref": "synthetic://lei"},
            }
        ],
    }
    state["entities"]["b"]["canonical_identifier"]["value"] = chr(0xFF15) + "493001KJTIIGC8Y1R12"
    result = prepare_provider_request("ENT.ALIGN.vNext", state, question, {})
    assert isinstance(result, ValidatedProviderRequest)

    claim = claim_state()
    claim.pop("evidence")
    claim["evidence_refs"] = ["e1", "e1"]
    with pytest.raises(LabError, match="duplicate identifiers"):
        prepare_provider_request(
            "CES.SUPPORT.vNext",
            claim,
            vnext_question("CES.SUPPORT.vNext"),
            {"e1": {"content": "Duplicate fixture passage."}},
        )

    claim["evidence_refs"] = ["e1"]
    with pytest.raises(LabError, match="record must be an object"):
        prepare_provider_request(
            "CES.SUPPORT.vNext",
            claim,
            vnext_question("CES.SUPPORT.vNext"),
            {"e1": "not-an-object"},  # type: ignore[dict-item]
        )

    claim["evidence_refs"] = "e1"
    direct = validate_decision_request("CES.SUPPORT.vNext", {**claim_state(), **claim})
    assert direct.status == "NOT_ANSWERABLE"
    assert "UNRESOLVED_REFERENCE" in direct.reasons
    for malformed_refs in (None, [], ["   "]):
        invalid_state = claim_state()
        invalid_state["evidence_refs"] = malformed_refs
        with pytest.raises(LabError):
            prepare_provider_request(
                "CES.SUPPORT.vNext",
                invalid_state,
                vnext_question("CES.SUPPORT.vNext"),
                {},
            )
    direct_malformed_result = validate_decision_request(
        "CES.SUPPORT.vNext",
        {**claim_state(), "unresolved_evidence_refs": "e1"},
    )
    assert direct_malformed_result.status == "NOT_ANSWERABLE"
    assert "UNRESOLVED_REFERENCE" in direct_malformed_result.reasons
    state["entities"]["a"]["canonical_identifier"] = {
        "scheme": "LEI",
        "authority": "GLEIF",
        "validation_status": "VERIFIED",
        "value": "one",
    }
    state["entities"]["b"]["canonical_identifier"] = {
        "scheme": "LEI",
        "authority": "GLEIF",
        "validation_status": "VERIFIED",
        "value": "two",
    }
    assert isinstance(
        prepare_provider_request("ENT.ALIGN.vNext", state, question, {}),
        ValidatedProviderRequest,
    )


def test_unanswerable_cases_are_excluded_from_model_quality_metrics() -> None:
    cases = [
        {
            "case_id": "a",
            "answerability": {"status": "ANSWERABLE"},
            "expected_outcome": "SUPPORTED",
            "label_provenance": "synthetic",
            "raw_judgment": {"status": "ANSWERED"},
        },
        {
            "case_id": "b",
            "answerability": {"status": "NOT_ANSWERABLE"},
            "expected_outcome": "SUPPORTED",
            "label_provenance": "synthetic",
        },
        {
            "case_id": "c",
            "answerability": {"status": "ANSWERABLE"},
            "expected_outcome": None,
            "label_provenance": "synthetic",
        },
    ]
    assert [case["case_id"] for case in quality_eligible_cases(cases)] == ["a"]


def test_vnext_corpus_has_evidence_bearing_state_and_keeps_labels_outside_state() -> None:
    import json

    document = json.loads(
        (ROOT / "experiments/decision_lab/corpus/vnext/cases.json").read_text(encoding="utf-8")
    )
    assert document["version"] == "vNext.1"
    assert len(document["cases"]) == 14
    cases_by_id = {case["case_id"]: case for case in document["cases"]}
    assert {"CES-N-01", "CES-N-06"} <= cases_by_id.keys()
    for case in document["cases"]:
        assert "expected_outcome" not in case["state"]
        assert "label_provenance" not in case["state"]
        compiled = compile_decision_state(
            {
                "CLAIM_EVIDENCE_SUPPORT": "CES.SUPPORT.vNext",
                "ENTITY_ALIGNMENT": "ENT.ALIGN.vNext",
                "ECONOMIC_RELATIONSHIP": "REL.EXISTENCE.vNext",
            }[case["family"]],
            assemble_state(case["state"], case["evidence_catalog"])[0],
        )
        assert compiled.answerability.status == case["expected_answerability"]


def test_experiment_validity_gate_fails_closed_and_never_authorizes_live_use() -> None:
    missing = validate_experiment_validity({})
    assert missing.live_experiment_eligible is False
    assert missing.live_experiment_authorized is False
    assert set(missing.failed_gates) == set(VALIDITY_GATES)
    all_pass = validate_experiment_validity({"gates": dict.fromkeys(VALIDITY_GATES, True)})
    assert all_pass.live_experiment_eligible is True
    assert all_pass.live_experiment_authorized is False


def test_preregistered_state_ladder_locks_holdout_and_is_not_live_eligible() -> None:
    import json

    preregistration = json.loads(
        (
            ROOT
            / "experiments/decision_lab/experiments/vnext/state-sufficiency-preregistration.json"
        ).read_text(encoding="utf-8")
    )
    development = set(preregistration["development_case_ids"])
    held_out = set(preregistration["held_out_case_ids"])
    assert development and held_out and development.isdisjoint(held_out)
    validity = validate_experiment_validity(preregistration)
    assert validity.status == "INVALID"
    assert validity.failed_gates == ("GOLDEN_PROVENANCE_VALID",)
    assert validity.live_experiment_eligible is False
    assert validity.live_experiment_authorized is False


def test_failure_attribution_requires_an_explicit_basis() -> None:
    attribution = FailureAttribution(FailureClass.MODEL_JUDGMENT_ERROR, AttributionBasis.UNKNOWN)
    assert attribution.basis is AttributionBasis.UNKNOWN


def test_composer_preserves_raw_primitive_uncertainty_and_policy_version() -> None:
    judgment = NormalizedJudgment(
        "CES.SUPPORT.vNext",
        "CHOICE",
        "PARTIAL",
        distribution={"SUPPORTED": 0.2, "PARTIAL": 0.7, "UNRESOLVED": 0.1},
        confidence=0.74,
        evaluator="offline-fixture",
    )
    result = compose_vnext(judgment, policy_version="support.vNext.1")
    assert result["derived_result"] == {"selected_class": "PARTIAL"}
    assert result["raw_judgment"]["distribution"] == judgment.distribution
    assert result["raw_judgment"]["confidence"] == 0.74
    assert result["composition_policy_version"] == "support.vNext.1"
    assert result["canonical_authority"] is False


def test_unanswerable_case_record_cannot_carry_a_provider_judgment() -> None:
    record = DecisionCaseRecord(
        case_id="fixture",
        golden_target=None,
        golden_provenance="synthetic structural case",
        decision_contract_version="decision-contract.vNext.1",
        question_version="vNext.1",
        state_contract_version="claim-evidence.vNext.1",
        state_compiler_version="decision-state-compiler.vNext.1",
        answerability_status="NOT_ANSWERABLE",
        answerability_reasons=("MISSING_REQUIRED_INFORMATION",),
        primitive="CHOICE",
        requested_model="not-submitted",
        sdk_version="not-submitted",
        composition_policy_version="support.vNext.1",
        raw_judgment=None,
        composed_result=None,
        metrics={},
        failure_attribution=None,
    )
    assert record.validate() == ()
    invalid = DecisionCaseRecord(
        **{**record.__dict__, "raw_judgment": NormalizedJudgment("q", "CHOICE", "YES")}
    )
    assert invalid.validate() == ("UNANSWERABLE_CASE_HAS_PROVIDER_RESULT",)


def test_historical_v01_live_path_is_refused_before_provider_or_key_lookup(tmp_path: Path) -> None:
    definition = ROOT / "experiments/decision_lab/experiments/v0.1/claim-wording-ab.json"
    with pytest.raises(LabError, match="INVALID_DECISION_CONTRACT"):
        _run_live(definition, tmp_path / "result.json")


def test_typesafe_adapter_rejects_unregistered_contract_before_sdk_import() -> None:
    evaluator = TypeSafeLabEvaluator(api_key="offline-test-fixture")
    with pytest.raises(LabError, match="requires ValidatedProviderRequest"):
        evaluator.evaluate(
            {"candidate": {"id": "only-an-id"}},
            model="jev-1.13.0",
        )


def test_historical_pilot_entrypoints_are_replay_only() -> None:
    with pytest.raises(LabError, match="immutable historical evidence"):
        run_historical_smoke()
    with pytest.raises(LabError, match="immutable historical evidence"):
        run_historical_experiment()


def test_vnext_modules_have_no_provider_or_canonical_writer_imports() -> None:
    paths = [
        ROOT / "experiments/decision_lab/contracts_vnext.py",
        ROOT / "experiments/decision_lab/answerability_vnext.py",
        ROOT / "experiments/decision_lab/compiler_vnext.py",
        ROOT / "experiments/decision_lab/validity_vnext.py",
    ]
    forbidden = {"cognition", "typesafe", "evidence", "faxt", "relationships"}
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported |= {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not (imported & forbidden)


def test_historical_p0_jev_03_evidence_files_remain_present_and_bounded() -> None:
    report = (ROOT / "docs/research/p0-jev-03/empirical-report.md").read_text(encoding="utf-8")
    artifact = ROOT / "docs/research/p0-jev-03/claim-wording-ab-result.json"
    assert artifact.is_file()
    assert "JEV_CLAIM_EVIDENCE_ACCURACY=NOT_ESTABLISHED" in report
