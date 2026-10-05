"""Deterministic EB-05 preflight evidence, with live execution left gated."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from experiments.decision_lab.bakeoff_vnext import build_bakeoff_artifact
from experiments.decision_lab.harness_vnext import live_eligibility


def build_eb05_preflight_artifact() -> dict[str, Any]:
    payload = build_bakeoff_artifact()
    payload["experiment_id"] = "EB-05-governed-evaluator-preflight-v1"
    payload["live_provider_eligibility"] = list(live_eligibility())
    payload["batch_vs_singles"] = {
        "status": "LIVE_COMPARISON_BLOCKED",
        "reason_code": "NO_AUTHORIZED_LIVE_EVALUATOR_AND_JEV_CORPUS_GATE_CLOSED",
        "fixture_mechanics": "IMPLEMENTED_TESTED_SEPARATELY_NOT_PROVIDER_EVIDENCE",
    }
    payload["dimension_measurement_basis"] = {
        "dimensions": sorted(
            {str(case["contract_id"]) for case in payload["frozen_input_manifest"]["cases"]}
        ),
        "labels_visible_to_evaluator": False,
        "answerability_precedes_quality_metrics": True,
    }
    payload["authority"] = (
        "EXPERIMENTAL_ONLY; no live calls, no policy promotion, EvidenceAdmission or AXIGLAND writes"
    )
    payload.pop("result_id", None)
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["result_id"] = hashlib.sha256(body.encode()).hexdigest()
    return payload
