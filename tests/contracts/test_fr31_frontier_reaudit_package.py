"""FR-31 Frontier re-audit evidence-package contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs" / "audit"
ROADMAP = ROOT / "docs" / "governance" / "AXIGNAL_FRONTIER_RECONCILIATION_ROADMAP_2026-09-30.md"
MANIFEST = AUDIT / "FR31_FRONTIER_REAUDIT_MANIFEST.json"
MATRIX = AUDIT / "FR31_FRONTIER_REAUDIT_EVIDENCE_MATRIX.md"
REQUEST = AUDIT / "FR31_FRONTIER_REAUDIT_REQUEST.md"
VALIDATION = AUDIT / "FR31_AUDIT_BASE_VALIDATION_SNAPSHOT.md"


def _roadmap_statuses() -> dict[str, str]:
    text = ROADMAP.read_text(encoding="utf-8-sig")
    statuses: dict[str, str] = {}
    for match in re.finditer(
        r"^## (FR-\d{2})[^\n]*\n(?P<body>.*?)(?=^## FR-|^# 5\.)",
        text,
        re.MULTILINE | re.DOTALL,
    ):
        status = re.search(r"\*\*Status:\*\*\s*([^\r\n]+)", match.group("body"))
        assert status is not None
        statuses[match.group(1)] = status.group(1).strip()
    return statuses


def test_manifest_matches_all_pre_reaudit_roadmap_statuses() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    roadmap = _roadmap_statuses()
    tasks = {item["fr"]: item for item in manifest["tasks"]}

    assert set(tasks) == {f"FR-{number:02d}" for number in range(31)}
    for fr, item in tasks.items():
        assert item["status"] == roadmap[fr]


def test_every_done_task_has_existing_primary_evidence() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for item in manifest["tasks"]:
        if not item["status"].startswith("DONE"):
            continue
        assert len(item["evidence"]) >= 2, item["fr"]
        for relative in item["evidence"]:
            assert (ROOT / relative).is_file(), (item["fr"], relative)


def test_fr27_empirical_gap_remains_explicit_and_not_done() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fr27 = next(item for item in manifest["tasks"] if item["fr"] == "FR-27")
    gaps = {gap["id"]: gap for gap in manifest["explicit_remaining_gaps"]}

    assert fr27["status"].startswith("READY")
    assert not fr27["status"].startswith("DONE")
    assert gaps["FR-27-EMPIRICAL"]["status"] == "PENDING"
    assert gaps["FR-27-WTP"]["status"] == "PENDING"
    assert "real buyer/job" in gaps["FR-27-EMPIRICAL"]["statement"].lower()
    assert "payment" in gaps["FR-27-WTP"]["statement"].lower()


def test_audit_base_and_production_split_are_explicit() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert re.fullmatch(r"[0-9a-f]{40}", manifest["audit_base_sha"])
    assert manifest["audit_base_ci"]["conclusion"] == "success"
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["production"]["runtime_code_sha"])
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["production"]["landing_sha"])
    assert manifest["production"]["landing_sha"] == manifest["audit_base_sha"]
    assert manifest["production"]["write_surface"] == "closed"
    assert manifest["production"]["first_proof_sessions"] >= 1
    assert manifest["production"]["observation_rows"] >= 1
    assert manifest["production"]["learning_event_rows"] >= 1


def test_validation_snapshot_records_clean_audit_base_evidence() -> None:
    text = VALIDATION.read_text(encoding="utf-8")

    assert "d78afb0f1acdfcb660fb1fb28d325b76ff65552d" in text
    assert "689 tests" in text
    assert "architecture-guard --root ." in text
    assert "governance" in text
    assert "cb89cfe391a0ce6ba93bfc5e5b8a942795897769" in text
    assert "first_proof_sessions   1" in text


def test_human_evidence_matrix_exposes_all_tasks_and_gaps() -> None:
    matrix = MATRIX.read_text(encoding="utf-8")
    for number in range(31):
        assert f"| FR-{number:02d} |" in matrix
    for marker in ("FR-27-EMPIRICAL", "FR-27-WTP", "PUBLIC-SUBSCRIBER-AUTH"):
        assert marker in matrix


def test_independent_reaudit_request_does_not_prescribe_a_verdict() -> None:
    request = REQUEST.read_text(encoding="utf-8")

    assert "Do **not** assume that previous findings are fixed" in request
    assert "do not silently convert to PASS" in request
    assert "Do not assign a desired overall verdict" in request
    assert "CONFIRMED" in request
    assert "INFERRED" in request
    assert "UNKNOWN" in request
    forbidden = (
        "AXIGNAL should pass",
        "give AXIGNAL a pass",
        "conclude that AXIGNAL is ready",
        "score AXIGNAL at",
    )
    assert not any(phrase in request for phrase in forbidden)
