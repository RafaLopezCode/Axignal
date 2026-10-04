from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows" / "ci.yml"

CRITICAL_COLLECTION = (
    "tests/contracts/test_evidence_admission.py",
    "tests/contracts/test_observed_vs_potential.py",
    "tests/subscriber_projection/test_explainable_xignal.py",
    "tests/subscriber_projection/test_evidence_narrative.py",
    "tests/economic_discovery/test_observation_reuse.py",
    "tests/economic_discovery/test_temporal_currentness.py",
    "tests/semantic_extraction/test_semantic_claim_candidates.py",
    "tests/contracts/test_ao22_verifactu_sif_decision.py",
    "tests/pipeline/test_evidence_ledger.py",
)

REQUIRED_NEGATIVE_NODE_FRAGMENTS = (
    "test_claim_admission_rejects_proposition_not_equal_to_extracted_claim",
    "test_direct_observed_relationship_construction_is_blocked",
    "test_private_evidence_from_different_owner_is_rejected_before_material_resolution",
    "test_120_day_current_snapshot_is_historical_for_current_reuse",
    "test_ungrounded_claim_fails_closed",
    "test_future_evidence_cannot_enable_as_of_projection",
    "test_same_evidence_id_with_changed_immutable_content_fails_closed",
)


def test_ci_executes_the_entire_pytest_testpath_without_directory_filters() -> None:
    text = CI.read_text(encoding="utf-8")
    pytest_runs = re.findall(r"^\s*run:\s*(uv run pytest[^\r\n]*)$", text, flags=re.MULTILINE)

    assert pytest_runs == ["uv run pytest"]
    assert "pytest tests/" not in text
    assert 'testpaths = ["tests"]' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_critical_authority_negative_cases_are_collectable_by_pytest() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            *CRITICAL_COLLECTION,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    collected = completed.stdout

    for fragment in REQUIRED_NEGATIVE_NODE_FRAGMENTS:
        assert fragment in collected


def test_ci_full_suite_covers_every_top_level_test_family() -> None:
    # An unfiltered pytest invocation honors pyproject testpaths=["tests"], so every
    # current or future test family below tests/ participates in the single CI exit code.
    families = {
        path.name
        for path in (ROOT / "tests").iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }
    assert {
        "contracts",
        "economic_discovery",
        "pipeline",
        "semantic_extraction",
        "source_acquisition",
        "source_representation",
        "subscriber_projection",
        "xeed_germination",
    }.issubset(families)
