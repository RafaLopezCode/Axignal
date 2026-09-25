"""Offline-first command line entry point for P0-JEV-02."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from experiments.decision_lab import __version__ as LAB_VERSION
from experiments.decision_lab.artifacts import read_result, write_result
from experiments.decision_lab.comparison import compare_records
from experiments.decision_lab.experiment import estimate_budget, manifest_digest
from experiments.decision_lab.judgments import (
    compose_relationship_decomposition,
    compose_support,
    normalize_judgment,
)
from experiments.decision_lab.metrics import classification_metrics
from experiments.decision_lab.models import LabError, NormalizedJudgment
from experiments.decision_lab.outcomes import evaluate_experiment_outcome, object_digest
from experiments.decision_lab.pricing import estimate_cost_from_usage, load_pricing_policy
from experiments.decision_lab.report import render_report
from experiments.decision_lab.state import STATE_VARIANTS, apply_state_variant, compile_state
from experiments.decision_lab.validation import (
    validate_controlled_state_fingerprints,
    validate_corpus,
    validate_experiment,
    validate_grammar,
)

ROOT = Path(__file__).parent


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise LabError(f"expected object in {path}")
    return data


def _compile_variant_states(
    definition: dict[str, Any], cases: list[dict[str, Any]]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, dict[str, Any]]]]:
    payloads: dict[str, list[dict[str, Any]]] = {
        variant["variant_id"]: [] for variant in definition["variants"]
    }
    fingerprints: dict[str, dict[str, dict[str, Any]]] = {}
    for case in cases:
        fingerprints[case["case_id"]] = {}
        for variant in definition["variants"]:
            payload, version = apply_state_variant(dict(case["state"]), variant["state_variant"])
            compiled = compile_state(payload)
            payloads[variant["variant_id"]].append(compiled.payload)
            fingerprints[case["case_id"]][variant["variant_id"]] = {
                "fingerprint": compiled.fingerprint,
                "variant_id": variant["state_variant"],
                "variant_version": version,
                "has_ablatable_fields": bool(
                    {"temporal_context", "provenance"} & case["state"].keys()
                ),
            }
    validate_controlled_state_fingerprints(definition, fingerprints)
    return payloads, fingerprints


def _variant_outcome(
    definition: dict[str, Any],
    variant: dict[str, Any],
    judgments: list[NormalizedJudgment],
) -> dict[str, Any]:
    if (
        definition.get("experiment_type") == "ATOMIC_DECOMPOSITION"
        and variant.get("question_strategy") == "ATOMIC"
    ):
        return compose_relationship_decomposition(judgments)
    if len(judgments) != 1:
        return {"status": "UNRESOLVED", "outcome": None}
    composition = compose_support(judgments[0])
    return {
        "status": composition["status"],
        "outcome": composition["outcome"] if isinstance(composition["outcome"], str) else None,
        "raw_composition": composition,
    }


def validate() -> tuple[int, int, int]:
    corpus = validate_corpus(_load(ROOT / "corpus/v0.1/cases.json"))
    grammar = validate_grammar(
        _load(ROOT / "grammar/v0.1/grammar.json"),
        _load(ROOT / "grammar/v0.1/question-lock.json"),
    )
    grammar_by_id = {question["question_id"]: question for question in grammar}
    definitions = sorted(
        path
        for path in (ROOT / "experiments/v0.1").glob("*.json")
        if path.name != "definition-lock.json"
    )
    definition_lock = _load(ROOT / "experiments/v0.1/definition-lock.json").get("definitions", {})
    for path in definitions:
        definition = _load(path)
        definition_key = f"{definition.get('experiment_id')}@{definition.get('version')}"
        if not isinstance(definition_lock, dict) or definition_lock.get(
            definition_key
        ) != manifest_digest(definition):
            raise LabError(f"experiment definition changed or is not locked: {definition_key}")
        validate_experiment(definition, grammar_by_id)
        case_ids = {case["case_id"] for case in corpus}
        question_ids = set(grammar_by_id)
        if not set(definition["case_ids"]) <= case_ids:
            raise LabError(f"experiment references unknown corpus case: {path.name}")
        referenced = {qid for variant in definition["variants"] for qid in variant["question_ids"]}
        if not referenced <= question_ids:
            raise LabError(f"experiment references unknown grammar question: {path.name}")
        if any(grammar_by_id[qid]["family"] != definition["decision_family"] for qid in referenced):
            raise LabError(f"experiment question family does not match definition: {path.name}")
        if any(
            case["decision_family"] != definition["decision_family"]
            for case in corpus
            if case["case_id"] in definition["case_ids"]
        ):
            raise LabError(f"experiment corpus family does not match definition: {path.name}")
        for variant in definition["variants"]:
            if len(variant["question_ids"]) == 1:
                question = grammar_by_id[variant["question_ids"][0]]
                if question["primitive"] == "CHOICE":
                    options = set(question["criteria"])
                    for case in corpus:
                        if (
                            case["case_id"] in definition["case_ids"]
                            and case["expected_outcome"] is not None
                            and case["expected_outcome"] not in options
                        ):
                            raise LabError(
                                f"case label is outside Choice options: {case['case_id']}"
                            )
        selected = [case for case in corpus if case["case_id"] in definition["case_ids"]]
        variant_states, _fingerprints = _compile_variant_states(definition, selected)
        estimate_budget(
            definition,
            [case["state"] for case in selected],
            grammar_by_id,
            variant_states,
        )
    return len(corpus), len(grammar), len(definitions)


def _run_live(
    experiment_path: Path,
    output: Path,
    *,
    api_key: str | None = None,
    allow_repository_output: bool = False,
) -> None:
    validate()
    definition = _load(experiment_path)
    grammar = {
        q["question_id"]: q
        for q in validate_grammar(
            _load(ROOT / "grammar/v0.1/grammar.json"),
            _load(ROOT / "grammar/v0.1/question-lock.json"),
        )
    }
    validate_experiment(definition, grammar)
    if not api_key and not os.environ.get("TYPESAFE_API_KEY"):
        raise LabError("TYPESAFE_API_KEY is unavailable; no request was made")
    cases = {
        case["case_id"]: case for case in validate_corpus(_load(ROOT / "corpus/v0.1/cases.json"))
    }
    selected = [cases[case_id] for case_id in definition["case_ids"]]
    variant_states, state_fingerprints = _compile_variant_states(definition, selected)
    plan = estimate_budget(
        definition,
        [case["state"] for case in selected],
        grammar,
        variant_states,
    )
    if (
        definition["budget"].get("max_concurrency") != 1
        or definition["budget"].get("max_retries") != 0
    ):
        raise LabError("live lab requires sequential, zero-retry budget")

    from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator

    repo_root = ROOT.parents[1].resolve()
    if output.resolve().is_relative_to(repo_root) and not allow_repository_output:
        raise LabError("experiment result output must be outside the repository")
    evaluator = TypeSafeLabEvaluator(api_key=api_key)
    records: list[dict[str, Any]] = []
    for case_index, case in enumerate(selected):
        for variant in definition["variants"]:
            for _ in range(int(definition.get("repetitions", 1))):
                questions = [grammar[qid] for qid in variant["question_ids"]]
                state_payload = variant_states[variant["variant_id"]][case_index]
                compiled = compile_state(state_payload)
                requested_model = variant.get("requested_model", definition["requested_model"])
                judgments, failure, safe_meta = evaluator.evaluate(
                    compiled.payload, questions, model=requested_model
                )
                compositions = [
                    {
                        "question_id": item.question_id,
                        "composition": compose_support(item),
                    }
                    for item in judgments
                ]
                variant_outcome = _variant_outcome(definition, variant, judgments)
                records.append(
                    {
                        "case_id": case["case_id"],
                        "variant_id": variant["variant_id"],
                        "repetition": _ + 1,
                        "expected_outcome": case["expected_outcome"],
                        "label_status": case["label_status"],
                        "state_fingerprint": compiled.fingerprint,
                        "state_variant_id": variant["state_variant"],
                        "state_variant_version": state_fingerprints[case["case_id"]][
                            variant["variant_id"]
                        ]["variant_version"],
                        "state_contract_version": compiled.contract_version,
                        "state_compiler_version": compiled.compiler_version,
                        "policy_version": definition["policy_version"],
                        "requested_model": requested_model,
                        "judgments": [item.to_dict() for item in judgments],
                        "compositions": compositions,
                        "variant_outcome": variant_outcome,
                        "failure": failure.category if failure else None,
                        "metadata": safe_meta,
                    }
                )
    metrics_by_variant: dict[str, Any] = {}
    for variant in definition["variants"]:
        variant_rows = [
            row
            for row in records
            if row["variant_id"] == variant["variant_id"]
            and row["label_status"] == "DETERMINISTIC_GROUND_TRUTH"
            and row["expected_outcome"] is not None
        ]
        answered = [
            (row["expected_outcome"], row["variant_outcome"].get("outcome"), row["case_id"])
            for row in variant_rows
            if row["variant_outcome"].get("status") in {"COMPOSED", "COMPOSED_EXPERIMENTAL"}
            and isinstance(row["variant_outcome"].get("outcome"), str)
        ]
        unique_case_ids = sorted({str(item[2]) for item in answered})
        classification = classification_metrics(
            [str(item[0]) for item in answered], [str(item[1]) for item in answered]
        )
        metrics_by_variant[variant["variant_id"]] = {
            "exact_outcome_accuracy": classification["accuracy"],
            "classification": classification,
            "n_expected": len(variant_rows),
            "n_answered": len(answered),
            "unique_answered_cases": len(unique_case_ids),
            "answered_case_ids": unique_case_ids,
            "missing_or_failed": len(variant_rows) - len(answered),
        }
    critical_case_ids = {
        case["case_id"]
        for case in selected
        if {"near-match", "conflicting-ID", "contradiction"} & set(case["edge_case_tags"])
    }
    critical_regressions: list[str] = []
    if len(definition["variants"]) == 2:
        first_id, second_id = (item["variant_id"] for item in definition["variants"])
        first_records = {
            (row["case_id"], row["repetition"]): row
            for row in records
            if row["variant_id"] == first_id
        }
        second_records = {
            (row["case_id"], row["repetition"]): row
            for row in records
            if row["variant_id"] == second_id
        }
        for identity in first_records.keys() & second_records.keys():
            first, second = first_records[identity], second_records[identity]
            if identity[0] not in critical_case_ids or first["expected_outcome"] is None:
                continue
            if (
                first["variant_outcome"].get("outcome") == first["expected_outcome"]
                and second["variant_outcome"].get("outcome") != second["expected_outcome"]
            ):
                critical_regressions.append(f"{identity[0]}::{identity[1]}")
    outcome = evaluate_experiment_outcome(
        definition,
        metrics_by_variant,
        operational_failures=sum(row["failure"] is not None for row in records),
        critical_regressions=critical_regressions,
        incompatible_output_semantics=any(
            metric.get("exact_outcome_accuracy") is None for metric in metrics_by_variant.values()
        ),
    )
    actual_usage_by_row = [row.get("metadata", {}).get("usage") for row in records]
    usage_fields = ("input_tokens", "output_tokens", "total_tokens")
    usage_complete = bool(actual_usage_by_row) and all(
        isinstance(usage, dict) and all(isinstance(usage.get(key), int) for key in usage_fields)
        for usage in actual_usage_by_row
    )
    actual_usage = (
        {key: sum(usage[key] for usage in actual_usage_by_row) for key in usage_fields}
        if usage_complete
        else None
    )
    pricing_policy = load_pricing_policy()
    cost_rows = [
        estimate_cost_from_usage(
            pricing_policy,
            row.get("metadata", {}).get("usage"),
            model=row["requested_model"],
        )
        for row in records
    ]
    estimated_costs = [item["estimated_cost"] for item in cost_rows]
    cost_known = bool(estimated_costs) and all(
        isinstance(value, (int, float)) for value in estimated_costs
    )
    actual_cost = sum(float(value) for value in estimated_costs) if cost_known else "UNKNOWN"
    resolved_models = sorted(
        {
            judgment["resolved_model"]
            for row in records
            for judgment in row["judgments"]
            if judgment.get("resolved_model")
        }
    )
    definition_digest = manifest_digest(definition)
    criteria_snapshot = dict(definition["evaluation_criteria"])
    result = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "experiment_id": definition["experiment_id"],
        "experiment_definition": definition,
        "data_mode": "LIVE_PROVIDER",
        "evaluator": "typesafe-sdk",
        "records": records,
        "metrics_by_variant": metrics_by_variant,
        "result": outcome["outcome"],
        "result_reasons": outcome["reasons"],
        "critical_regressions": critical_regressions,
        "budget_preflight": plan,
        "predeclared_evaluation_criteria": criteria_snapshot,
        "evaluation_criteria_sha256": object_digest(criteria_snapshot),
        "reproducibility_manifest": {
            "git_revision": subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
            ).stdout.strip()
            or "UNKNOWN",
            "corpus_version": "0.1.0",
            "grammar_version": "0.1.0",
            "experiment_definition_version": definition["version"],
            "experiment_definition_digest": definition_digest,
            "experiment_type": definition["experiment_type"],
            "question_versions_by_variant": {
                variant["variant_id"]: [
                    {"question_id": qid, "question_version": grammar[qid]["question_version"]}
                    for qid in variant["question_ids"]
                ]
                for variant in definition["variants"]
            },
            "state_contract_version": records[0]["state_contract_version"]
            if records
            else "UNKNOWN",
            "state_compiler_version": records[0]["state_compiler_version"]
            if records
            else "UNKNOWN",
            "state_variants_by_variant": {
                variant["variant_id"]: {
                    "state_variant_id": variant["state_variant"],
                    "state_variant_version": STATE_VARIANTS[variant["state_variant"]].version,
                    "state_fingerprints_by_case": {
                        case_id: by_variant[variant["variant_id"]]["fingerprint"]
                        for case_id, by_variant in state_fingerprints.items()
                    },
                }
                for variant in definition["variants"]
            },
            "policy_version": definition["policy_version"],
            "evaluator_adapter_version": "0.2.0",
            "requested_models_by_variant": {
                variant["variant_id"]: variant.get("requested_model", definition["requested_model"])
                for variant in definition["variants"]
            },
            "resolved_models": resolved_models,
            "pricing_policy_version": pricing_policy["policy_version"] if cost_known else None,
            "case_ids": list(definition["case_ids"]),
            "repetitions": definition.get("repetitions", 1),
            "execution_mode": "LIVE_PROVIDER",
            "lab_version": LAB_VERSION,
            "typesafe_sdk_version": "0.7.1",
        },
        "actual_usage": actual_usage,
        "actual_usage_status": "COMPLETE" if usage_complete else "UNKNOWN_OR_INCOMPLETE",
        "actual_cost_estimate": actual_cost,
        "cost_status": "VERSIONED_PUBLIC_PRICE_ESTIMATE" if cost_known else "UNKNOWN",
        "invoice_cost": "UNKNOWN",
        "pricing_policy": pricing_policy if cost_known else None,
        "limitations": ["No canonical authority; exploratory observations only."],
    }
    result["result_id"] = manifest_digest(result)
    write_result(output, result)


def _run_replay(fixture_path: Path, output: Path) -> None:
    fixture = _load(fixture_path)
    if (
        fixture.get("artifact_type") != "decision-lab-fixture"
        or fixture.get("fixture_only") is not True
    ):
        raise LabError("replay input must be explicitly marked as a contract fixture")
    if output.resolve().is_relative_to(ROOT.parents[1].resolve()):
        raise LabError("experiment result output must be outside the repository")
    judgment = normalize_judgment(
        fixture["question_id"],
        fixture["primitive"],
        fixture["answer"],
        evaluator="contract-fixture",
        requested_model=None,
        resolved_model=None,
        usage=None,
    )
    compiled = compile_state({"fixture": "recorded contract response"})
    result: dict[str, Any] = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "result_id": "",
        "data_mode": "RECORDED_FIXTURE_NOT_OBSERVATION",
        "evaluator": "contract-fixture",
        "state_fingerprint": compiled.fingerprint,
        "judgments": [judgment.to_dict()],
        "usage": None,
        "cost": None,
        "outcome": "CONTRACT_REPLAY_ONLY; NO QUALITY CLAIM",
    }
    result.pop("result_id")
    result["result_id"] = manifest_digest(result)
    write_result(output, result)


def _run_result_replay(
    source_path: Path, output: Path, *, allow_repository_output: bool = False
) -> None:
    if output.resolve().is_relative_to(ROOT.parents[1].resolve()) and not allow_repository_output:
        raise LabError("experiment result output must be outside the repository")
    source = read_result(source_path)
    source_records = source.get("records", [])
    if not isinstance(source_records, list):
        raise LabError("result records are malformed")
    records: list[dict[str, Any]] = []
    definition = source.get("experiment_definition", {})
    variants = {variant.get("variant_id"): variant for variant in definition.get("variants", [])}
    if not source_records and isinstance(source.get("judgments"), list):
        judgments = [NormalizedJudgment(**item) for item in source["judgments"]]
        source_records = [
            {"case_id": "recorded-fixture", "judgments": [item.to_dict() for item in judgments]}
        ]
    for row in source_records:
        judgments = [NormalizedJudgment(**item) for item in row.get("judgments", [])]
        compositions = [
            {"question_id": item.question_id, "composition": compose_support(item)}
            for item in judgments
        ]
        variant = variants.get(row.get("variant_id"), {})
        if (
            definition.get("experiment_type") == "ATOMIC_DECOMPOSITION"
            and variant.get("question_strategy") == "ATOMIC"
        ):
            variant_outcome = compose_relationship_decomposition(judgments)
        elif len(judgments) == 1:
            variant_outcome = _variant_outcome(definition, variant, judgments)
        else:
            variant_outcome = {"status": "UNRESOLVED", "outcome": None}
        records.append(
            {
                "case_id": row.get("case_id"),
                "variant_id": row.get("variant_id"),
                "repetition": row.get("repetition", 1),
                "expected_outcome": row.get("expected_outcome"),
                "label_status": row.get("label_status"),
                "state_fingerprint": row.get("state_fingerprint"),
                "judgments": [item.to_dict() for item in judgments],
                "compositions": compositions,
                "variant_outcome": variant_outcome,
                "failure": row.get("failure"),
                "metadata": row.get("metadata", {}),
            }
        )
    metrics_by_variant: dict[str, Any] = {}
    definition = source.get("experiment_definition", {})
    critical_regressions: list[str] = []
    outcome: dict[str, Any] | None = None
    if isinstance(definition, dict) and definition.get("experiment_id"):
        for variant in definition.get("variants", []):
            variant_id = variant.get("variant_id")
            variant_rows = [
                row
                for row in records
                if row.get("variant_id") == variant_id
                and row.get("label_status") == "DETERMINISTIC_GROUND_TRUTH"
                and row.get("expected_outcome") is not None
            ]
            answered = [
                (row["expected_outcome"], row["variant_outcome"].get("outcome"), row["case_id"])
                for row in variant_rows
                if row["variant_outcome"].get("status") in {"COMPOSED", "COMPOSED_EXPERIMENTAL"}
                and isinstance(row["variant_outcome"].get("outcome"), str)
            ]
            classification = classification_metrics(
                [str(item[0]) for item in answered], [str(item[1]) for item in answered]
            )
            metrics_by_variant[str(variant_id)] = {
                "exact_outcome_accuracy": classification["accuracy"],
                "classification": classification,
                "n_expected": len(variant_rows),
                "n_answered": len(answered),
                "unique_answered_cases": len({str(item[2]) for item in answered}),
                "answered_case_ids": sorted({str(item[2]) for item in answered}),
                "missing_or_failed": len(variant_rows) - len(answered),
            }
        corpus = validate_corpus(_load(ROOT / "corpus/v0.1/cases.json"))
        critical_case_ids = {
            case["case_id"]
            for case in corpus
            if {"near-match", "conflicting-ID", "contradiction"} & set(case["edge_case_tags"])
        }
        if len(definition.get("variants", [])) == 2:
            first_id, second_id = (item["variant_id"] for item in definition["variants"])
            first_records = {
                (row["case_id"], row["repetition"]): row
                for row in records
                if row["variant_id"] == first_id
            }
            second_records = {
                (row["case_id"], row["repetition"]): row
                for row in records
                if row["variant_id"] == second_id
            }
            for identity in first_records.keys() & second_records.keys():
                first, second = first_records[identity], second_records[identity]
                if identity[0] not in critical_case_ids or first.get("expected_outcome") is None:
                    continue
                if (
                    first["variant_outcome"].get("outcome") == first["expected_outcome"]
                    and second["variant_outcome"].get("outcome") != second["expected_outcome"]
                ):
                    critical_regressions.append(f"{identity[0]}::{identity[1]}")
        outcome = evaluate_experiment_outcome(
            definition,
            metrics_by_variant,
            operational_failures=sum(row.get("failure") is not None for row in records),
            critical_regressions=critical_regressions,
            incompatible_output_semantics=any(
                metric.get("exact_outcome_accuracy") is None
                for metric in metrics_by_variant.values()
            ),
        )
    replay: dict[str, Any] = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "result_id": "",
        "data_mode": "RECORDED_RESULT_REPLAY_NO_PROVIDER_CALL",
        "source_result_id": source.get("result_id"),
        "experiment_id": source.get("experiment_id"),
        "experiment_definition": definition if definition else None,
        "reproducibility_manifest": source.get("reproducibility_manifest"),
        "predeclared_evaluation_criteria": source.get("predeclared_evaluation_criteria"),
        "evaluation_criteria_sha256": source.get("evaluation_criteria_sha256"),
        "records": records,
        "metrics_by_variant": metrics_by_variant,
        "critical_regressions": critical_regressions,
        "result": outcome["outcome"] if outcome else None,
        "result_reasons": outcome["reasons"] if outcome else [],
        "limitations": ["Recorded re-composition only; no model quality inference."],
    }
    replay.pop("result_id")
    replay["result_id"] = manifest_digest(replay)
    write_result(output, replay)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="decision-lab")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate synthetic corpus, grammar, and experiment plans")
    sub.add_parser("list-cases", help="list the versioned synthetic corpus")
    sub.add_parser("list-grammar", help="list the executable grammar")
    run = sub.add_parser("run", help="run a predeclared experiment; requires --live")
    run.add_argument("--experiment", required=True)
    run.add_argument("--live", action="store_true")
    run.add_argument("--output", type=Path, required=True)
    replay = sub.add_parser("replay", help="replay a fixture or recorded result without a provider")
    replay_source = replay.add_mutually_exclusive_group(required=True)
    replay_source.add_argument("--fixture", type=Path)
    replay_source.add_argument("--result", type=Path)
    replay.add_argument("--output", type=Path, required=True)
    report = sub.add_parser("report", help="render a local result summary")
    report.add_argument("--result", type=Path, required=True)
    compare = sub.add_parser("compare", help="compare result identities descriptively")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            cases, questions, experiments = validate()
            print(
                f"VALID corpus_cases={cases} grammar_questions={questions} experiment_plans={experiments} mode=OFFLINE"
            )
        elif args.command == "list-cases":
            for case in validate_corpus(_load(ROOT / "corpus/v0.1/cases.json")):
                print(f"{case['case_id']}\t{case['decision_family']}\t{case['label_status']}")
        elif args.command == "list-grammar":
            for question in validate_grammar(
                _load(ROOT / "grammar/v0.1/grammar.json"),
                _load(ROOT / "grammar/v0.1/question-lock.json"),
            ):
                print(
                    f"{question['question_id']}\t{question['primitive']}\t{question['experimental_status']}"
                )
        elif args.command == "run":
            if not args.live:
                raise LabError(
                    "provider evaluation is disabled unless --live is explicitly supplied"
                )
            path = ROOT / "experiments/v0.1" / f"{args.experiment}.json"
            _run_live(path, args.output)
            print(f"WROTE {args.output}")
        elif args.command == "replay":
            if args.fixture:
                _run_replay(args.fixture, args.output)
            else:
                _run_result_replay(args.result, args.output)
            print(f"WROTE {args.output}")
        elif args.command == "report":
            result = read_result(args.result)
            print(render_report(result))
        elif args.command == "compare":
            left, right = read_result(args.baseline), read_result(args.candidate)
            corpus = validate_corpus(_load(ROOT / "corpus/v0.1/cases.json"))
            critical = {
                case["case_id"]
                for case in corpus
                if "near-match" in case["edge_case_tags"]
                or "conflicting-ID" in case["edge_case_tags"]
            }
            print(json.dumps(compare_records(left, right, critical), indent=2, sort_keys=True))
        return 0
    except (LabError, OSError, ValueError, KeyError) as exc:
        print(f"decision-lab: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
