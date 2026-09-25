"""Validation for versioned corpus, grammar and experiment definitions."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from typing import Any

from experiments.decision_lab.models import LabError

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


def validate_experiment(document: Mapping[str, Any]) -> None:
    required = (
        "experiment_id",
        "hypothesis",
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
            "max_input_tokens_estimate",
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
    if (
        not isinstance(budget.get("max_cost_usd"), (int, float))
        or not math.isfinite(budget["max_cost_usd"])
        or budget["max_cost_usd"] < 0
    ):
        raise LabError("experiment cost budget must be finite and non-negative")
    if budget.get("max_concurrency") != 1 or budget.get("max_retries") != 0:
        raise LabError("V0.1 live experiments require sequential single-attempt calls")
    if not isinstance(document.get("repetitions", 1), int) or document.get("repetitions", 1) < 1:
        raise LabError("experiment repetitions must be a positive integer")
    if not isinstance(document.get("stop_conditions"), list) or not document["stop_conditions"]:
        raise LabError("experiment requires explicit stop conditions")
    for variant in document["variants"]:
        if (
            not isinstance(variant, Mapping)
            or not isinstance(variant.get("variant_id"), str)
            or not isinstance(variant.get("question_ids"), list)
            or not variant["question_ids"]
        ):
            raise LabError("experiment variants require an ID and question IDs")
