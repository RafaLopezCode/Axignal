"""QA wrapper: existing AO-24A auth/runtime + controlled EB-04 economic projection."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from application.subscriber_projection import attach_economic_output
from tests.economic_discovery.test_first_vertical_e2e import CORPUS, _run_fixture
from tools.runtime import service as runtime_service

ROOT = Path(__file__).resolve().parents[5]
BASE_RUNTIME = ROOT / "apps" / "web" / "experience" / "qa" / "037-customer-zero" / "run_runtime.py"


def _load_base_runtime():
    spec = importlib.util.spec_from_file_location("eb08_base_run_runtime", BASE_RUNTIME)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load existing Customer Zero QA runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _economic_projection(config) -> dict[str, object]:
    patch = pytest.MonkeyPatch()
    result, *_ = _run_fixture(patch, config.data_dir / "eb08-economic-fixture")
    subject = CORPUS["documents"][0]
    activity = CORPUS["documents"][1]
    base: dict[str, object] = {
        "realityLevel": "CONTROLLED_ECONOMIC_PRODUCT_PROOF",
        "runtimeCodeSha": config.code_sha,
        "lifecycleStatus": "LIVE",
        "context": {"id": "xeed:eb08:arbor", "label": "Arbor Cooling"},
        "organization": {
            "id": str(subject["subject_id"]),
            "name": str(subject["subject_mention"]),
        },
        "nodes": [],
        "temporalHistory": {
            "disposition": "MULTIPLE_OBSERVATIONS",
            "items": [
                {
                    "observationId": "eb08:subject",
                    "sourceRef": str(subject["source_ref"]),
                    "sourceType": str(subject["source_type"]),
                    "observedAt": str(CORPUS["observed_at"]),
                    "currentness": "CURRENT",
                    "normalizedStateChanged": None,
                },
                {
                    "observationId": "eb08:activity",
                    "sourceRef": str(activity["source_ref"]),
                    "sourceType": str(activity["source_type"]),
                    "observedAt": str(CORPUS["observed_at"]),
                    "currentness": "CURRENT",
                    "normalizedStateChanged": True,
                },
            ],
        },
        "memberships": [],
        "today": {"disposition": "EMPTY", "items": []},
        "reloadContinuity": "PERSISTED_RUNTIME_READ_MODEL",
    }
    return attach_economic_output(base, result.human_output)


def main() -> None:
    base = _load_base_runtime()
    original_build_runtime = runtime_service.build_runtime

    def build_runtime_with_economic_projection(config):
        runtime = original_build_runtime(config)
        proof = runtime.first_proof
        if proof is None:
            raise RuntimeError("EB-08 QA requires FirstProofService")
        projection = _economic_projection(config)

        def current_projection(*_args, **_kwargs):
            return projection

        type(proof).current_projection = current_projection
        return runtime

    base.build_runtime = build_runtime_with_economic_projection
    base.main()


if __name__ == "__main__":
    main()
