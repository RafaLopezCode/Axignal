"""Tests for the isolated P0-SOURCE-01 benchmark harness."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "experiments"
    / "source-acquisition-bakeoff"
    / "run_bakeoff.py"
)
SPEC = importlib.util.spec_from_file_location("source_bakeoff", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
source_bakeoff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = source_bakeoff
SPEC.loader.exec_module(source_bakeoff)


def test_corpus_covers_twelve_required_workload_classes() -> None:
    corpus = source_bakeoff.fixture_data()
    assert [row["id"] for row in corpus] == [f"W{number}" for number in range(1, 13)]
    assert len({row["class"] for row in corpus}) == 12


def test_candidate_evidence_has_the_required_field_set() -> None:
    evidence_path = MODULE_PATH.parent / "candidate-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    required = {
        "project",
        "canonical_repository",
        "current_version_or_commit",
        "last_meaningful_activity",
        "license",
        "commercial_use_status",
        "copyleft_implications",
        "self_hostable",
        "language",
        "maintenance_signal",
        "security_signal",
        "js_rendering",
        "raw_http",
        "browser_mode",
        "pdf_support",
        "structured_extraction",
        "search_support",
        "crawl_support",
        "targeted_single_resource_fetch",
        "proxy_support",
        "robots_support",
        "retry_model",
        "rate_limit_control",
        "state_persistence",
        "provenance_preservation",
        "raw_artifact_access",
        "source_metadata",
        "extensibility",
        "vendor_dependency",
        "model_dependency",
        "estimated_operational_complexity",
        "axignal_fit_hypothesis",
        "eligibility",
        "benchmark_status",
    }
    assert len(evidence["candidates"]) >= 7
    assert all(required <= candidate.keys() for candidate in evidence["candidates"])


def test_observation_never_contains_canonical_truth_fields() -> None:
    field_names = set(source_bakeoff.SourceObservation.__dataclass_fields__)
    assert "faxt" not in field_names
    assert "canonical_truth" not in field_names
    assert {"source_uri", "retrieved_at", "provenance", "failure_state"} <= field_names


def test_fixture_adapter_rejects_non_fixture_hosts() -> None:
    try:
        source_bakeoff.OfflineFixtureAdapter("https://example.org", Path.cwd())
    except ValueError as error:
        assert "loopback" in str(error)
    else:
        raise AssertionError("non-loopback fixture host should be rejected")


def test_run_has_explicit_failure_raw_artifacts_and_iterative_provenance() -> None:
    result = source_bakeoff.run(iterations=1)
    assert result["run_metadata"]["external_network_used"] is False
    assert result["measurement_summary"]["requests"] == 14
    assert result["measurement_summary"]["explicit_failures"] == 1
    assert result["measurement_summary"]["raw_artifacts_written"] == 13
    assert result["measurement_summary"]["reuse_refetch_hashes_match"] is True
    assert result["information_gain_loop"]["PROVENANCE_CHAIN_PRESERVED"] is True
    assert result["information_gain_loop"]["STRUCTURED_GAP"]["basis_observation"]
    observation = result["observations"][0]
    assert observation["response_metadata"]["status"] == 200
    assert observation["response_metadata"]["final_uri"] == observation["source_uri"]
    assert observation["response_metadata"]["redirect_chain"] == [observation["source_uri"]]
    assert observation["acquisition_config"]["max_response_bytes"] > 0
