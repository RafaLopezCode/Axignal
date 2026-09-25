"""Validation for versioned corpus, grammar and experiment definitions."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from typing import Any

from experiments.decision_lab.models import LabError
from experiments.decision_lab.state import STATE_VARIANTS

LABELS = {
    "DETERMINISTIC_GROUND_TRUTH",
    "EXPERT_ADJUDICATED",
    "HIGH_CONFIDENCE_REFERENCE",
    "AMBIGUOUS_BY_DESIGN",
    "CONTRADICTORY_BY_DESIGN",
    "NO_EXPECTED_SINGLE_ANSWER",
}
AUTHORITIES = {
    "SYNTHETIC_CONSTRUCTION",
    "EXPERT_ADJUDICATION",
    "HIGH_CONFIDENCE_REFERENCE",
    "EXPLICIT_DESIGN",
}
FAMILIES = {"CLAIM_EVIDENCE_SUPPORT", "ENTITY_ALIGNMENT", "ECONOMIC_RELATIONSHIP"}
SUPPORTED_EXPERIMENT_TYPES = {
    "QUESTION_WORDING",
    "STATE_ABLATION",
    "ATOMIC_DECOMPOSITION",
    "MODEL_COMPARISON",
    "REPEATABILITY",
}
INDEPENDENT_VARIABLES = {
    "QUESTION_WORDING": "question_version",
    "STATE_ABLATION": "state_variant",
    "ATOMIC_DECOMPOSITION": "question_strategy",
    "MODEL_COMPARISON": "requested_model",
    "REPEATABILITY": "repetition_count",
}
CONTROLLED_DIMENSIONS = {
    "QUESTION_WORDING": {
        "case_ids",
        "state_variant",
        "primitive",
        "semantic_target",
        "requested_model",
        "repetitions",
        "policy_version",
        "budget",
    },
    "STATE_ABLATION": {
        "case_ids",
        "question_versions",
        "requested_model",
        "repetitions",
        "policy_version",
        "budget",
    },
    "ATOMIC_DECOMPOSITION": {
        "case_ids",
        "state_variant",
        "requested_model",
        "repetitions",
        "policy_version",
        "budget",
    },
    "MODEL_COMPARISON": {
        "case_ids",
        "question_versions",
        "state_variant",
        "repetitions",
        "policy_version",
        "budget",
    },
    "REPEATABILITY": {
        "case_ids",
        "question_versions",
        "state_variant",
        "requested_model",
        "policy_version",
        "budget",
    },
}


def validate_corpus(document: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if document.get("version") != "0.1.0" or not isinstance(document.get("cases"), list):
        raise LabError("corpus must declare version 0.1.0 and a cases list")
    cases = document["cases"]
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, Mapping):
            raise LabError("case must be an object")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise LabError("case IDs must be non-empty and unique")
        ids.add(case_id)
        if case.get("decision_family") not in FAMILIES:
            raise LabError(f"unsupported family for {case_id}")
        status = case.get("label_status")
        authority = str(case.get("label_authority", "")).upper()
        if status not in LABELS or authority not in AUTHORITIES:
            raise LabError(f"invalid label authority for {case_id}")
        if not case.get("label_provenance"):
            raise LabError(f"label provenance missing for {case_id}")
        if (
            status
            in {"AMBIGUOUS_BY_DESIGN", "CONTRADICTORY_BY_DESIGN", "NO_EXPECTED_SINGLE_ANSWER"}
            and case.get("expected_outcome") is not None
        ):
            raise LabError(f"non-single-answer case has an expected outcome: {case_id}")
        if (
            status
            in {"DETERMINISTIC_GROUND_TRUTH", "EXPERT_ADJUDICATED", "HIGH_CONFIDENCE_REFERENCE"}
            and case.get("expected_outcome") is None
        ):
            raise LabError(f"single-answer label status requires an expected outcome: {case_id}")
        if not isinstance(case.get("evidence"), list) or not isinstance(case.get("state"), Mapping):
            raise LabError(f"case evidence and state must be explicit: {case_id}")
        state_evidence_ids = case["state"].get("evidence_ids", [])
        if not isinstance(state_evidence_ids, list):
            raise LabError(f"state evidence_ids must be a list: {case_id}")
        evidence_ids = {
            item.get("evidence_id") for item in case["evidence"] if isinstance(item, Mapping)
        }
        if not set(state_evidence_ids) <= evidence_ids:
            raise LabError(f"state references missing evidence records: {case_id}")
    return list(cases)


def validate_grammar(
    document: Mapping[str, Any], lock: Mapping[str, Any] | None = None
) -> list[Mapping[str, Any]]:
    if document.get("version") != "0.1.0" or not isinstance(document.get("questions"), list):
        raise LabError("grammar must declare version 0.1.0 and a questions list")
    identities: set[tuple[str, str]] = set()
    for question in document["questions"]:
        if not isinstance(question, Mapping):
            raise LabError("question must be an object")
        identity = (str(question.get("question_id", "")), str(question.get("question_version", "")))
        if not all(identity) or identity in identities:
            raise LabError("question ID/version pairs must be non-empty and unique")
        identities.add(identity)
        if question.get("family") not in FAMILIES or question.get("primitive") not in {
            "CHOICE",
            "SCORE",
            "NOUL",
        }:
            raise LabError(f"invalid question family or primitive: {identity[0]}")
        for field in (
            "instructions",
            "semantic_meaning",
            "known_exclusions",
            "experimental_status",
        ):
            if not question.get(field):
                raise LabError(f"question {identity[0]} missing {field}")
        if lock is not None:
            locked = lock.get("questions", {})
            key = f"{identity[0]}@{identity[1]}"
            canonical = json.dumps(
                question, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if not isinstance(locked, Mapping) or locked.get(key) != digest:
                raise LabError(f"question version content changed or is not locked: {key}")
    return list(document["questions"])


def validate_experiment(
    document: Mapping[str, Any], grammar: Mapping[str, Mapping[str, Any]] | None = None
) -> None:
    required = (
        "version",
        "experiment_id",
        "hypothesis",
        "experiment_type",
        "independent_variable",
        "controlled_dimensions",
        "policy_version",
        "evaluation_criteria",
        "case_ids",
        "variants",
        "requested_model",
        "budget",
        "stop_conditions",
    )
    missing = [field for field in required if field not in document]
    if missing:
        raise LabError(f"experiment is missing required fields: {', '.join(missing)}")
    budget = document["budget"]
    if not isinstance(budget, Mapping) or any(
        not isinstance(budget.get(key), int) or budget[key] < 0
        for key in (
            "max_requests",
            "max_questions",
            "max_state_bytes",
            "max_request_bytes",
            "max_total_request_bytes",
        )
    ):
        raise LabError("experiment budget must contain non-negative integer limits")
    if not isinstance(document.get("variants"), list) or not document["variants"]:
        raise LabError("experiment requires one or more controlled variants")
    if not isinstance(document.get("case_ids"), list) or not document["case_ids"]:
        raise LabError("experiment requires a non-empty case set")
    requested_model = document.get("requested_model")
    if not isinstance(requested_model, str) or not re.fullmatch(
        r"jev-\d+\.\d+\.\d+", requested_model
    ):
        raise LabError("experiment must pin an immutable Jev model version")
    if budget.get("max_concurrency") != 1 or budget.get("max_retries") != 0:
        raise LabError("V0.1 live experiments require sequential single-attempt calls")
    if (
        not isinstance(document.get("repetitions", 1), int)
        or isinstance(document.get("repetitions", 1), bool)
        or document.get("repetitions", 1) < 1
    ):
        raise LabError("experiment repetitions must be a positive integer")
    if not isinstance(document.get("stop_conditions"), list) or not document["stop_conditions"]:
        raise LabError("experiment requires explicit stop conditions")
    experiment_type = document.get("experiment_type")
    if experiment_type not in SUPPORTED_EXPERIMENT_TYPES:
        raise LabError(f"unsupported experiment type: {experiment_type}")
    if document.get("independent_variable") != INDEPENDENT_VARIABLES[experiment_type]:
        raise LabError("independent variable does not match experiment type")
    dimensions = document.get("controlled_dimensions")
    if not isinstance(dimensions, list) or not CONTROLLED_DIMENSIONS[experiment_type] <= set(
        dimensions
    ):
        raise LabError("experiment does not declare all required controlled dimensions")
    if not isinstance(document.get("policy_version"), str) or not document["policy_version"]:
        raise LabError("experiment must pin its experimental policy version")
    criteria = document.get("evaluation_criteria")
    if not isinstance(criteria, Mapping):
        raise LabError("experiment requires predeclared evaluation criteria")
    min_answered = criteria.get("minimum_answered_cases")
    invalidations = criteria.get("invalidation_conditions")
    if (
        criteria.get("primary_metric") != "exact_outcome_accuracy"
        or criteria.get("direction") not in {"HIGHER_IS_BETTER", "LOWER_IS_BETTER"}
        or not isinstance(min_answered, int)
        or isinstance(min_answered, bool)
        or min_answered < 1
        or criteria.get("critical_regression_policy") != "BLOCK"
        or not isinstance(invalidations, list)
        or not {"OPERATIONAL_FAILURE", "CRITICAL_REGRESSION", "INCOMPATIBLE_OUTPUT_SEMANTICS"}
        <= set(invalidations)
    ):
        raise LabError("predeclared outcome criteria are incomplete or unsupported")
    minimum_effect = criteria.get("minimum_effect")
    if minimum_effect is not None and (
        not isinstance(minimum_effect, (int, float))
        or isinstance(minimum_effect, bool)
        or not math.isfinite(minimum_effect)
        or minimum_effect <= 0
    ):
        raise LabError("minimum_effect must be positive or null")
    if minimum_effect is None and not criteria.get("no_threshold_reason"):
        raise LabError("null effect threshold requires a predeclared reason")

    for variant in document["variants"]:
        if (
            not isinstance(variant, Mapping)
            or not isinstance(variant.get("variant_id"), str)
            or not isinstance(variant.get("question_ids"), list)
            or not variant["question_ids"]
        ):
            raise LabError("experiment variants require an ID and question IDs")
        if variant.get("state_variant") not in STATE_VARIANTS:
            raise LabError(f"unknown state variant: {variant.get('state_variant')}")
        for forbidden_override in ("budget", "repetitions", "policy_version"):
            if forbidden_override in variant:
                raise LabError(f"variant may not override controlled {forbidden_override}")
        if (
            experiment_type != "MODEL_COMPARISON"
            and variant.get("requested_model", requested_model) != requested_model
        ):
            raise LabError("requested model drift outside MODEL_COMPARISON")

    variants = document["variants"]
    question_sets = [tuple(variant["question_ids"]) for variant in variants]
    state_variants = [variant["state_variant"] for variant in variants]
    model_ids = [variant.get("requested_model", requested_model) for variant in variants]
    if experiment_type == "QUESTION_WORDING":
        if len(variants) != 2 or any(len(ids) != 1 for ids in question_sets):
            raise LabError("QUESTION_WORDING requires exactly two single-question variants")
        targets = {variant.get("semantic_target_id") for variant in variants}
        if len(targets) != 1 or None in targets:
            raise LabError("QUESTION_WORDING variants must declare one identical semantic target")
        if len(set(state_variants)) != 1 or len(set(model_ids)) != 1:
            raise LabError("QUESTION_WORDING variants changed a controlled state or model")
        if question_sets[0] == question_sets[1]:
            raise LabError("QUESTION_WORDING requires distinct question versions")
        if grammar is not None:
            questions = [grammar.get(ids[0]) for ids in question_sets]
            if any(question is None for question in questions):
                raise LabError("QUESTION_WORDING references an unknown question")
            first, second = questions
            if (
                first.get("primitive") != second.get("primitive")
                or first.get("family") != second.get("family")
                or first.get("criteria") != second.get("criteria")
                or first.get("question_version") == second.get("question_version")
                or first.get("question_id", "").rsplit(".", 1)[0]
                != second.get("question_id", "").rsplit(".", 1)[0]
            ):
                raise LabError(
                    "QUESTION_WORDING variants drifted primitive, family, options, target ID, or version"
                )
    elif experiment_type == "STATE_ABLATION":
        if len(set(question_sets)) != 1 or len(set(model_ids)) != 1:
            raise LabError("STATE_ABLATION must keep exact question versions and model fixed")
        if len(set(state_variants)) != len(state_variants):
            raise LabError("STATE_ABLATION requires distinct state variants")
    elif experiment_type == "ATOMIC_DECOMPOSITION":
        if len(variants) != 2 or len(set(state_variants)) != 1 or len(set(model_ids)) != 1:
            raise LabError("ATOMIC_DECOMPOSITION must keep state and model identical")
        by_strategy = {
            variant.get("question_strategy"): set(variant["question_ids"]) for variant in variants
        }
        if set(by_strategy) != {"COMPOUND", "ATOMIC"}:
            raise LabError("ATOMIC_DECOMPOSITION requires COMPOUND and ATOMIC strategies")
        if by_strategy["COMPOUND"] != {"REL.COMPOUND.v1"} or by_strategy["ATOMIC"] != {
            "REL.PRESENCE.v1",
            "REL.TYPE.v1",
            "REL.TIME.v1",
            "REL.CONTRADICTION.v1",
        }:
            raise LabError("relationship decomposition question set is unsupported")
    elif experiment_type == "MODEL_COMPARISON":
        if len(set(question_sets)) != 1 or len(set(state_variants)) != 1:
            raise LabError("MODEL_COMPARISON must keep grammar and state identical")
        if len(set(model_ids)) != len(model_ids):
            raise LabError("MODEL_COMPARISON requires distinct pinned models")
        if any(not re.fullmatch(r"jev-\d+\.\d+\.\d+", model) for model in model_ids):
            raise LabError("each model-comparison variant must pin a versioned model")
    elif experiment_type == "REPEATABILITY":
        if len(variants) != 1 or document.get("repetitions", 1) <= 1:
            raise LabError("REPEATABILITY requires one semantic variant and repetitions > 1")

    if grammar is not None:
        for ids in question_sets:
            if any(question_id not in grammar for question_id in ids):
                raise LabError("experiment references unknown question")


def validate_controlled_state_fingerprints(
    definition: Mapping[str, Any],
    case_states: Mapping[str, Mapping[str, Mapping[str, str]]],
) -> None:
    """Assert state equality/change according to the experiment's declared type."""
    kind = definition["experiment_type"]
    variants = definition["variants"]
    if kind == "STATE_ABLATION":
        changed = False
        for case_id, by_variant in case_states.items():
            fingerprints = [by_variant[item["variant_id"]]["fingerprint"] for item in variants]
            source_has_ablatable_fields = any(
                by_variant[item["variant_id"]]["has_ablatable_fields"] for item in variants
            )
            if len(set(fingerprints)) > 1 and source_has_ablatable_fields:
                changed = True
            if source_has_ablatable_fields and len(set(fingerprints)) == 1:
                raise LabError(f"STATE_ABLATION did not change state fields for case {case_id}")
        if not changed:
            raise LabError("STATE_ABLATION did not change any selected case state")
        return
    if kind in {"QUESTION_WORDING", "ATOMIC_DECOMPOSITION", "MODEL_COMPARISON", "REPEATABILITY"}:
        for case_id, by_variant in case_states.items():
            fingerprints = {
                by_variant[variant["variant_id"]]["fingerprint"] for variant in variants
            }
            if len(fingerprints) != 1:
                raise LabError(f"controlled state fingerprint drift for case {case_id}")
