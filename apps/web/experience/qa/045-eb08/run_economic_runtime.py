"""QA wrapper: existing AO-24A auth/runtime + controlled EB-04 economic projection."""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import pytest

from application.subscriber_projection import attach_economic_output
from domain.identity import OrganizationId
from domain.organizations.model import Organization
from tests.economic_discovery.test_first_vertical_e2e import CORPUS, _run_fixture
from tools.runtime.config import RuntimeConfig
from tools.runtime.organization_attention import (
    CanonicalObservationTarget,
    OrganizationAttention,
    attention_target,
)
from tools.runtime.service import AxignalRuntime

ROOT = Path(__file__).resolve().parents[5]
BASE_RUNTIME = ROOT / "apps" / "web" / "experience" / "qa" / "037-customer-zero" / "run_runtime.py"


def _load_base_runtime() -> ModuleType:
    spec = importlib.util.spec_from_file_location("eb08_base_run_runtime", BASE_RUNTIME)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load existing Customer Zero QA runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _economic_projection(config: RuntimeConfig) -> dict[str, object]:
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
    original_build_runtime = base.build_runtime

    def build_runtime_with_economic_projection(config: RuntimeConfig) -> AxignalRuntime:
        runtime = original_build_runtime(config)
        projection = _economic_projection(config)
        if runtime.organization_attention is None or runtime.first_proof is None:
            raise RuntimeError("EB-08 QA requires FirstProof and OrganizationAttention")

        context = projection.get("context")
        organization_data = projection.get("organization")
        if not isinstance(context, dict) or not isinstance(context.get("id"), str):
            raise RuntimeError("EB-08 QA projection requires a persisted context id")
        if not isinstance(organization_data, dict):
            raise RuntimeError("EB-08 QA projection requires canonical organization identity")
        organization_id = organization_data.get("id")
        organization_name = organization_data.get("name")
        if not isinstance(organization_id, str) or not isinstance(organization_name, str):
            raise RuntimeError("EB-08 QA projection organization identity is invalid")

        context_id = str(context["id"])
        target_uri = attention_target("https://arbor-cooling.example/")
        if runtime.first_proof.store.get(context_id) is None:
            runtime.first_proof.store.append(
                xeed_id=context_id,
                created_at=datetime.now(UTC),
                target_uri=target_uri,
                projection=projection,
            )

        target = CanonicalObservationTarget(
            Organization(OrganizationId(organization_id), organization_name),
            target_uri,
            "qa-eb08:controlled-economic-fixture",
        )
        attention = OrganizationAttention(
            runtime.first_proof,
            (*runtime.organization_attention.catalog, target),
        )
        identifier = attention._id(target.target_uri)
        attention._append(
            identifier,
            organization_name,
            target.target_uri,
            "LIVE",
            target,
            context_id,
        )
        # QA-only adoption seam: persist a controlled projection without triggering
        # a new public-source observation. Product runtime code remains unchanged.
        attention.select("admin:ao24a-local-validation", identifier)
        runtime.organization_attention = attention
        return runtime

    base.build_runtime = build_runtime_with_economic_projection
    base.main()


if __name__ == "__main__":
    main()
