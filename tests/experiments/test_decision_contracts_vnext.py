from __future__ import annotations

import ast
import hashlib
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
from experiments.decision_lab.validity_vnext import (
    VALIDITY_GATES,
    quality_eligible_cases,
    validate_experiment_validity,
)

ROOT = Path(__file__).resolve().parents[2]


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
                    "a": {"name": "A", "canonical_identifier": {"scheme": "LEI", "value": "x"}},
                    "b": {"name": "A Ltd", "canonical_identifier": {"scheme": "LEI", "value": "x"}},
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
    claim_question = {
        "question_id": "CES.SUPPORT.vNext",
        "version": "vNext.1",
        "family": "CLAIM_EVIDENCE_SUPPORT",
        "primitive": "CHOICE",
        "semantic_target": (
            "Assess the explicit claim proposition against all supplied semantic evidence passages."
        ),
        "criteria": {
            "options": [
                {"id": "SUPPORTED", "meaning": "Supports."},
                {"id": "PARTIAL", "meaning": "Partially supports."},
                {"id": "NOT_SUPPORTED", "meaning": "Does not support."},
                {"id": "NO_EVIDENCE", "meaning": "No evidence."},
                {"id": "CONFLICTING", "meaning": "Conflicts."},
                {"id": "UNRESOLVED", "meaning": "Unresolved."},
            ],
            "mutually_exclusive": True,
            "coverage": "EXHAUSTIVE_WITH_UNRESOLVED",
        },
    }
    assert validate_question_binding("CES.SUPPORT.vNext", claim_question, claim_state()) == []
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
    relationship_question = {
        "question_id": "REL.EXISTENCE.vNext",
        "version": "vNext.1",
        "family": "ECONOMIC_RELATIONSHIP",
        "primitive": "NOUL",
        "semantic_target": (
            "Judge whether the explicit directed or undirected relation proposition between two endpoints is evidenced."
        ),
        "criteria": {
            "proposition": (
                "Judge whether the explicit directed or undirected relation proposition between two endpoints is evidenced."
            ),
            "required_arguments": [
                "relationship.endpoints",
                "relationship.proposition",
                "evidence[*]",
            ],
            "probability_semantics": "Probability of the stated proposition only; not truth or confidence.",
        },
    }
    assert (
        validate_question_binding("REL.EXISTENCE.vNext", relationship_question, relationship_state)
        == []
    )
    relationship_question["criteria"]["required_arguments"] = ["unmodeled.secret"]
    assert "NOUL_ARGUMENT_NOT_IN_STATE_CONTRACT" in validate_question_binding(
        "REL.EXISTENCE.vNext", relationship_question, relationship_state
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
    with pytest.raises(LabError, match="registered V-next DecisionContract"):
        _run_live(definition, tmp_path / "result.json")


def test_typesafe_adapter_rejects_unregistered_contract_before_sdk_import() -> None:
    evaluator = TypeSafeLabEvaluator(api_key="offline-test-fixture")
    with pytest.raises(LabError, match="no registered V-next DecisionContract"):
        evaluator.evaluate(
            {"candidate": {"id": "only-an-id"}},
            [
                {
                    "question_id": "CES.SUPPORT.v1",
                    "primitive": "CHOICE",
                    "instructions": "historical",
                    "criteria": {},
                }
            ],
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
