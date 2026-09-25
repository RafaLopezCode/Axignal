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
from experiments.decision_lab.judgments import compose_support, normalize_judgment
from experiments.decision_lab.metrics import classification_metrics
from experiments.decision_lab.models import LabError, NormalizedJudgment
from experiments.decision_lab.report import render_report
from experiments.decision_lab.state import compile_state
from experiments.decision_lab.validation import (
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


def validate() -> tuple[int, int, int]:
    corpus = validate_corpus(_load(ROOT / "corpus/v0.1/cases.json"))
    grammar = validate_grammar(
        _load(ROOT / "grammar/v0.1/grammar.json"),
        _load(ROOT / "grammar/v0.1/question-lock.json"),
    )
    grammar_by_id = {question["question_id"]: question for question in grammar}
    definitions = sorted((ROOT / "experiments/v0.1").glob("*.json"))
    for path in definitions:
        definition = _load(path)
        validate_experiment(definition)
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
        states = [case["state"] for case in corpus if case["case_id"] in definition["case_ids"]]
        estimate_budget(definition, states, grammar_by_id)
    return len(corpus), len(grammar), len(definitions)


def _run_live(experiment_path: Path, output: Path) -> None:
    validate()
    definition = _load(experiment_path)
    validate_experiment(definition)
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise LabError("TYPESAFE_API_KEY is unavailable; no request was made")
    cases = {
        case["case_id"]: case for case in validate_corpus(_load(ROOT / "corpus/v0.1/cases.json"))
    }
    grammar = {
        q["question_id"]: q
        for q in validate_grammar(
            _load(ROOT / "grammar/v0.1/grammar.json"),
            _load(ROOT / "grammar/v0.1/question-lock.json"),
        )
    }
    selected = [cases[case_id] for case_id in definition["case_ids"]]
    plan = estimate_budget(definition, [case["state"] for case in selected], grammar)
    if (
        definition["budget"].get("max_concurrency") != 1
        or definition["budget"].get("max_retries") != 0
    ):
        raise LabError("live lab requires sequential, zero-retry budget")

    from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator

    repo_root = ROOT.parents[1].resolve()
    if output.resolve().is_relative_to(repo_root):
        raise LabError("experiment result output must be outside the repository")
    evaluator = TypeSafeLabEvaluator()
    records: list[dict[str, Any]] = []
    for case in selected:
        for variant in definition["variants"]:
            for _ in range(int(definition.get("repetitions", 1))):
                questions = [grammar[qid] for qid in variant["question_ids"]]
                state_payload = dict(case["state"])
                if variant.get("state_variant") == "without_temporal_provenance":
                    state_payload.pop("temporal_context", None)
                    state_payload.pop("provenance", None)
                compiled = compile_state(state_payload)
                judgments, failure, safe_meta = evaluator.evaluate(compiled.payload, questions)
                compositions = [
                    {
                        "question_id": item.question_id,
                        "composition": compose_support(item),
                    }
                    for item in judgments
                ]
                records.append(
                    {
                        "case_id": case["case_id"],
                        "variant_id": variant["variant_id"],
                        "repetition": _ + 1,
                        "expected_outcome": case["expected_outcome"],
                        "label_status": case["label_status"],
                        "state_fingerprint": compiled.fingerprint,
                        "judgments": [item.to_dict() for item in judgments],
                        "compositions": compositions,
                        "failure": failure.category if failure else None,
                        "metadata": safe_meta,
                    }
                )
    usage_rows = [row.get("metadata", {}).get("usage", {}) for row in records]
    usage_fields = ("input_tokens", "output_tokens", "total_tokens")
    usage_complete = bool(usage_rows) and all(
        all(isinstance(usage.get(key), int) for key in usage_fields) for usage in usage_rows
    )
    actual_usage = (
        {key: sum(usage[key] for usage in usage_rows) for key in usage_fields}
        if usage_complete
        else None
    )
    metrics_by_variant: dict[str, Any] = {}
    for variant in definition["variants"]:
        if len(variant["question_ids"]) != 1:
            metrics_by_variant[variant["variant_id"]] = {
                "status": "NOT_APPLICABLE_TO_COMPOSED_MULTI_QUESTION_OUTPUT"
            }
            continue
        qid = variant["question_ids"][0]
        if grammar[qid]["primitive"] != "CHOICE":
            metrics_by_variant[variant["variant_id"]] = {
                "status": "NO_SINGLE_CLASS_LABEL_FOR_PRIMITIVE"
            }
            continue
        variant_rows = [
            row
            for row in records
            if row["variant_id"] == variant["variant_id"]
            and row["label_status"] == "DETERMINISTIC_GROUND_TRUTH"
            and row["expected_outcome"] is not None
        ]
        answered = [
            (row["expected_outcome"], row["judgments"][0]["value"])
            for row in variant_rows
            if row["judgments"] and row["judgments"][0]["status"] == "ANSWERED"
        ]
        metrics_by_variant[variant["variant_id"]] = {
            "classification": classification_metrics(
                [str(item[0]) for item in answered], [str(item[1]) for item in answered]
            ),
            "n_expected": len(variant_rows),
            "n_answered": len(answered),
            "missing_or_failed": len(variant_rows) - len(answered),
        }
    result = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "experiment_id": definition["experiment_id"],
        "experiment_definition": definition,
        "data_mode": "LIVE_PROVIDER",
        "evaluator": "typesafe-sdk",
        "records": records,
        "metrics_by_variant": metrics_by_variant,
        "result": "INCONCLUSIVE",
        "budget_preflight": plan,
        "reproducibility_manifest": {
            "git_revision": subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
            ).stdout.strip()
            or "UNKNOWN",
            "corpus_version": "0.1.0",
            "grammar_version": "0.1.0",
            "state_contract_version": "0.1.0",
            "state_compiler_version": "0.1.0",
            "policy_version": "support.v0.1",
            "requested_model": definition["requested_model"],
            "lab_version": LAB_VERSION,
            "typesafe_sdk_version": "0.7.1",
        },
        "actual_usage": actual_usage,
        "actual_usage_status": "COMPLETE" if usage_complete else "UNKNOWN_OR_INCOMPLETE",
        "actual_cost_estimate_usd": (
            actual_usage["input_tokens"] * 0.042 / 1_000_000 if usage_complete else None
        ),
        "cost_status": "PUBLIC_PRICE_ESTIMATE_ONLY" if usage_complete else "UNKNOWN",
        "actual_invoice_cost": "UNKNOWN",
        "actual_cost_estimate_source": "https://docs.typesafe.ai/models (reviewed 2026-09-25)",
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
    result["result_id"] = manifest_digest(result)
    write_result(output, result)


def _run_result_replay(source_path: Path, output: Path) -> None:
    if output.resolve().is_relative_to(ROOT.parents[1].resolve()):
        raise LabError("experiment result output must be outside the repository")
    source = read_result(source_path)
    source_records = source.get("records", [])
    if not isinstance(source_records, list):
        raise LabError("result records are malformed")
    records: list[dict[str, Any]] = []
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
        records.append(
            {
                "case_id": row.get("case_id"),
                "variant_id": row.get("variant_id"),
                "repetition": row.get("repetition", 1),
                "state_fingerprint": row.get("state_fingerprint"),
                "judgments": [item.to_dict() for item in judgments],
                "compositions": compositions,
                "failure": row.get("failure"),
                "metadata": row.get("metadata", {}),
            }
        )
    replay: dict[str, Any] = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "result_id": "",
        "data_mode": "RECORDED_RESULT_REPLAY_NO_PROVIDER_CALL",
        "source_result_id": source.get("result_id"),
        "experiment_id": source.get("experiment_id"),
        "records": records,
        "limitations": ["Recorded re-composition only; no model quality inference."],
    }
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
