"""Explicit operator-only runner for the bounded P0-JEV-03 live pilot."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from experiments.decision_lab.artifacts import read_result
from experiments.decision_lab.cli import (
    ROOT,
    _compile_variant_states,
    _load,
    _run_live,
    _run_result_replay,
)
from experiments.decision_lab.experiment import estimate_budget, manifest_digest
from experiments.decision_lab.judgments import compose_support
from experiments.decision_lab.models import LabError
from experiments.decision_lab.pricing import load_pricing_policy
from experiments.decision_lab.state import apply_state_variant, compile_state
from experiments.decision_lab.validation import (
    validate_corpus,
    validate_experiment,
    validate_grammar,
)

REPO_ROOT = ROOT.parents[1].resolve()
RESEARCH_DIR = REPO_ROOT / "docs/research/p0-jev-03"
SMOKE_RESULT = RESEARCH_DIR / "smoke-result.json"
SMOKE_REPLAY = RESEARCH_DIR / "smoke-replay-validated.json"
SMOKE_GATE = RESEARCH_DIR / "smoke-gate.json"
EXPERIMENT_RESULT = RESEARCH_DIR / "claim-wording-ab-result.json"
EXPERIMENT_REPLAY = RESEARCH_DIR / "replay-result.json"
SMOKE_CASE_ID = "CES-01-clear-positive"
SMOKE_QUESTION_ID = "CES.SUPPORT.v1"
PINNED_MODEL = "jev-1.13.0"
EXPECTED_SDK_VERSION = "0.7.1"


def _load_local_api_key() -> str:
    """Read the one named secret into memory without exposing it to output/files."""
    existing = os.environ.get("TYPESAFE_API_KEY")
    if existing and existing.strip():
        return existing

    env_path = REPO_ROOT / ".env"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise LabError("local credential file is unavailable") from exc

    matches: list[str] = []
    for line in lines:
        candidate = line.strip()
        if candidate.startswith("export "):
            candidate = candidate[7:].lstrip()
        if not candidate or candidate.startswith("#") or "=" not in candidate:
            continue
        name, value = candidate.split("=", 1)
        if name.strip() != "TYPESAFE_API_KEY":
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if value.strip():
            matches.append(value)
        else:
            matches.append("")
    if len(matches) != 1 or not matches[0].strip():
        raise LabError("local credential configuration is missing or ambiguous")
    return matches[0]


def _sdk_version() -> str:
    try:
        return version("typesafe-sdk")
    except PackageNotFoundError as exc:
        raise LabError("the pinned optional TypeSafe SDK is not installed") from exc


def _source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _grammar() -> dict[str, dict[str, Any]]:
    questions = validate_grammar(
        _load(ROOT / "grammar/v0.1/grammar.json"),
        _load(ROOT / "grammar/v0.1/question-lock.json"),
    )
    return {question["question_id"]: question for question in questions}


def _corpus() -> dict[str, dict[str, Any]]:
    cases = validate_corpus(_load(ROOT / "corpus/v0.1/cases.json"))
    return {case["case_id"]: case for case in cases}


def _verify_local_safety() -> None:
    check = subprocess.run(
        ["git", "check-ignore", "-q", "--", ".env"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", ".env"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if check.returncode != 0 or tracked.returncode == 0 or not (REPO_ROOT / ".env").is_file():
        raise LabError("credential file safety precondition failed")


def _create_only(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    unhashed = dict(payload)
    unhashed.pop("result_id", None)
    value = dict(unhashed)
    value["result_id"] = manifest_digest(unhashed)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)
    return value


def _smoke_budget(case: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
    transformed, state_version = apply_state_variant(dict(case["state"]), "minimal")
    compiled = compile_state(transformed)
    definition = {
        "requested_model": PINNED_MODEL,
        "repetitions": 1,
        "variants": [
            {
                "variant_id": "smoke",
                "question_ids": [SMOKE_QUESTION_ID],
                "state_variant": "minimal",
            }
        ],
        "budget": {
            "max_requests": 1,
            "max_questions": 1,
            "max_state_bytes": 20000,
            "max_concurrency": 1,
            "max_retries": 0,
            "max_request_bytes": 20000,
            "max_total_request_bytes": 20000,
        },
    }
    plan = estimate_budget(
        definition,
        [case["state"]],
        {SMOKE_QUESTION_ID: question},
        {"smoke": [compiled.payload]},
    )
    if (
        state_version != "0.1.0"
        or plan["expected_request_count"] != 1
        or plan["expected_question_count"] != 1
    ):
        raise LabError("smoke budget or state contract is invalid")
    return plan


def run_smoke() -> None:
    if SMOKE_RESULT.exists() or SMOKE_GATE.exists() or SMOKE_REPLAY.exists():
        raise LabError("P0-JEV-03 smoke artifacts already exist; no second smoke is allowed")
    _verify_local_safety()
    sdk = _sdk_version()
    if sdk != EXPECTED_SDK_VERSION:
        raise LabError("installed TypeSafe SDK does not match the approved pin")
    cases, grammar = _corpus(), _grammar()
    if SMOKE_CASE_ID not in cases or SMOKE_QUESTION_ID not in grammar:
        raise LabError("approved smoke assets are unavailable")
    case = cases[SMOKE_CASE_ID]
    question = grammar[SMOKE_QUESTION_ID]
    if question["primitive"] != "CHOICE" or question["family"] != "CLAIM_EVIDENCE_SUPPORT":
        raise LabError("approved smoke question contract changed")
    budget = _smoke_budget(case, question)
    pricing = load_pricing_policy()
    api_key = _load_local_api_key()
    from experiments.decision_lab.providers.typesafe import ADAPTER_VERSION, TypeSafeLabEvaluator

    compiled_payload, state_variant_version = apply_state_variant(dict(case["state"]), "minimal")
    compiled = compile_state(compiled_payload)
    print(
        "PREFLIGHT phase=smoke cases=1 variants=1 questions=1 max_requests=1 "
        f"request_bytes={budget['max_request_bytes']} total_request_bytes={budget['preflight_request_bytes']} "
        "input_token_budget=UNKNOWN max_estimated_cost=UNKNOWN concurrency=1 sdk_retries=0 "
        f"pricing_policy={pricing['policy_version']}"
    )
    evaluator = TypeSafeLabEvaluator(api_key=api_key)
    del api_key
    judgments, failure, metadata = evaluator.evaluate(
        compiled.payload,
        [question],
        model=PINNED_MODEL,
    )
    judgment = judgments[0].to_dict() if len(judgments) == 1 else None
    row = {
        "case_id": SMOKE_CASE_ID,
        "expected_outcome": case["expected_outcome"],
        "label_status": case["label_status"],
        "question_id": SMOKE_QUESTION_ID,
        "question_version": question["question_version"],
        "primitive": question["primitive"],
        "state_contract_version": compiled.contract_version,
        "state_compiler_version": compiled.compiler_version,
        "state_variant_id": "minimal",
        "state_variant_version": state_variant_version,
        "state_fingerprint": compiled.fingerprint,
        "requested_model": PINNED_MODEL,
        "resolved_model": metadata.get("resolved_model"),
        "raw_answer": metadata.get("raw_answers", {}).get(SMOKE_QUESTION_ID),
        "judgments": [judgment] if judgment is not None else [],
        "composition": compose_support(judgments[0]) if len(judgments) == 1 else None,
        "failure_category": failure.category if failure else None,
        "metadata": metadata,
    }
    artifact = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "data_mode": "LIVE_PROVIDER_SMOKE",
        "experiment_id": "p0-jev-03-smoke",
        "experiment_version": "0.1.0",
        "evaluator": "typesafe-sdk",
        "records": [row],
        "request_count": 1,
        "question_count": 1,
        "retry_count": 0,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "reproducibility_manifest": {
            "git_revision": _source_revision(),
            "corpus_version": "0.1.0",
            "grammar_version": "0.1.0",
            "state_contract_version": compiled.contract_version,
            "state_compiler_version": compiled.compiler_version,
            "state_variant_id": "minimal",
            "state_variant_version": state_variant_version,
            "question_id": SMOKE_QUESTION_ID,
            "question_version": question["question_version"],
            "requested_model": PINNED_MODEL,
            "resolved_model": metadata.get("resolved_model"),
            "adapter_version": ADAPTER_VERSION,
            "typesafe_sdk_version": sdk,
            "execution_mode": "LIVE_PROVIDER",
        },
    }
    _create_only(SMOKE_RESULT, artifact)
    print(f"WROTE {SMOKE_RESULT}")


def evaluate_smoke_gate() -> None:
    if SMOKE_GATE.exists() or SMOKE_REPLAY.exists():
        raise LabError("smoke gate artifacts already exist")
    smoke = read_result(SMOKE_RESULT)
    records = smoke.get("records")
    row = records[0] if isinstance(records, list) and len(records) == 1 else {}
    judgments = row.get("judgments", [])
    judgment = judgments[0] if len(judgments) == 1 and isinstance(judgments[0], dict) else {}
    raw = row.get("raw_answer") or {}
    metadata = row.get("metadata") or {}
    usage = metadata.get("usage")
    normalized_usage = judgment.get("usage")
    raw_distribution = raw.get("probabilities")
    normalized_distribution = judgment.get("distribution")
    distribution_match = (
        isinstance(raw_distribution, dict)
        and isinstance(normalized_distribution, dict)
        and set(raw_distribution) == set(normalized_distribution)
        and all(
            isinstance(raw_distribution[key], (int, float))
            and abs(float(raw_distribution[key]) - float(normalized_distribution[key])) <= 1e-12
            for key in raw_distribution
        )
    )
    confidence = raw.get("confidence")
    confidence_match = confidence == judgment.get("confidence")
    question = _grammar().get(SMOKE_QUESTION_ID, {})
    allowed_choices = set(question.get("criteria", {}))
    checks = {
        "one_request_one_question": smoke.get("request_count") == 1
        and smoke.get("question_count") == 1,
        "pinned_assets": row.get("case_id") == SMOKE_CASE_ID
        and row.get("question_id") == SMOKE_QUESTION_ID
        and row.get("question_version") == "v1"
        and row.get("primitive") == "CHOICE",
        "authentication_and_provider_call": row.get("failure_category") is None,
        "requested_model": row.get("requested_model") == PINNED_MODEL,
        "resolved_model": row.get("resolved_model") in {None, PINNED_MODEL},
        "normalization": judgment.get("status") == "ANSWERED"
        and raw.get("choice") == judgment.get("value")
        and judgment.get("value") in allowed_choices,
        "distribution_preserved": distribution_match,
        "confidence_preserved": confidence_match,
        "usage_preserved": usage == normalized_usage,
        "latency_measured": isinstance(metadata.get("latency_seconds"), (int, float))
        and metadata["latency_seconds"] >= 0,
        "sdk_adapter_versions": metadata.get("sdk_version") == EXPECTED_SDK_VERSION
        and bool(smoke.get("reproducibility_manifest", {}).get("adapter_version")),
        "zero_retries": smoke.get("retry_count") == 0,
        "safe_artifact_digest": bool(smoke.get("result_id")),
    }
    passed = all(checks.values())
    if passed:
        _run_result_replay(SMOKE_RESULT, SMOKE_REPLAY, allow_repository_output=True)
        replay = read_result(SMOKE_REPLAY)
        replay_records = replay.get("records", [])
        checks["offline_replay"] = bool(
            replay.get("source_result_id") == smoke.get("result_id")
            and len(replay_records) == 1
            and replay_records[0].get("judgments") == judgments
            and replay_records[0].get("compositions", [{}])[0].get("composition")
            == row.get("composition")
        )
        passed = passed and checks["offline_replay"]
    gate = {
        "artifact_type": "p0-jev-03-smoke-gate",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "smoke_result_id": smoke.get("result_id"),
        "passed": passed,
        "checks": checks,
        "failure_category": row.get("failure_category"),
        "note": "Compatibility gate only; this is not model quality evidence.",
    }
    _create_only(SMOKE_GATE, gate)
    print(f"SMOKE_GATE={'PASS' if passed else 'FAIL'}")


def run_experiment() -> None:
    if EXPERIMENT_RESULT.exists() or EXPERIMENT_REPLAY.exists():
        raise LabError("P0-JEV-03 experiment artifacts already exist; no rerun is allowed")
    gate = json.loads(SMOKE_GATE.read_text(encoding="utf-8"))
    gate_unhashed = dict(gate)
    gate_id = gate_unhashed.pop("result_id", None)
    smoke = read_result(SMOKE_RESULT)
    if (
        gate.get("artifact_type") != "p0-jev-03-smoke-gate"
        or not gate_id
        or manifest_digest(gate_unhashed) != gate_id
        or gate.get("smoke_result_id") != smoke.get("result_id")
        or gate.get("passed") is not True
    ):
        raise LabError("a digest-valid passing smoke gate is required")
    if _sdk_version() != EXPECTED_SDK_VERSION:
        raise LabError("installed TypeSafe SDK does not match the approved pin")
    definition_path = ROOT / "experiments/v0.1/claim-wording-ab.json"
    definition = _load(definition_path)
    grammar = _grammar()
    validate_experiment(definition, grammar)
    cases = _corpus()
    selected = [cases[case_id] for case_id in definition["case_ids"]]
    variant_states, _ = _compile_variant_states(definition, selected)
    budget = estimate_budget(
        definition,
        [case["state"] for case in selected],
        grammar,
        variant_states,
    )
    if (
        definition.get("experiment_id") != "claim-wording-ab"
        or definition.get("version") != "0.1.0"
        or budget["expected_request_count"] != 10
        or budget["expected_question_count"] != 10
        or definition["budget"].get("max_concurrency") != 1
        or definition["budget"].get("max_retries") != 0
    ):
        raise LabError("predeclared experiment or budget contract changed")
    pricing = load_pricing_policy()
    print(
        "PREFLIGHT phase=experiment cases=5 variants=2 questions=10 max_requests=10 "
        f"max_input_token_budget=UNKNOWN request_byte_budget={definition['budget']['max_request_bytes']} "
        f"max_total_request_bytes={definition['budget']['max_total_request_bytes']} "
        "concurrency=1 sdk_retries=0 pricing_policy="
        f"{pricing['policy_version']} max_estimated_cost=UNKNOWN"
    )
    api_key = _load_local_api_key()
    _run_live(definition_path, EXPERIMENT_RESULT, api_key=api_key, allow_repository_output=True)
    del api_key
    print(f"WROTE {EXPERIMENT_RESULT}")


def replay_experiment() -> None:
    if EXPERIMENT_REPLAY.exists():
        raise LabError("replay artifact already exists; no overwrite is allowed")
    _run_result_replay(EXPERIMENT_RESULT, EXPERIMENT_REPLAY, allow_repository_output=True)
    print(f"WROTE {EXPERIMENT_REPLAY}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="p0-jev-03-pilot")
    parser.add_argument("phase", choices=("smoke", "evaluate-smoke", "experiment", "replay"))
    args = parser.parse_args(argv)
    try:
        if args.phase == "smoke":
            run_smoke()
        elif args.phase == "evaluate-smoke":
            evaluate_smoke_gate()
        elif args.phase == "experiment":
            run_experiment()
        else:
            replay_experiment()
        return 0
    except (LabError, OSError, ValueError, KeyError, TypeError) as exc:
        # Never print exception text here: it could include provider data.
        category = type(exc).__name__
        print(f"p0-jev-03-pilot: stopped safely ({category})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
