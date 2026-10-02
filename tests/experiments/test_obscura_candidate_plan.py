from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "experiments" / "source-acquisition-bakeoff" / "obscura-candidate.json"
SPEC = ROOT / "specs" / "034-p0-obscura-browser-provider-bakeoff" / "spec.md"
QUICKSTART = ROOT / "specs" / "034-p0-obscura-browser-provider-bakeoff" / "quickstart.md"


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_obscura_candidate_is_reproducibly_pinned() -> None:
    manifest = _manifest()
    candidate = manifest["candidate"]
    assert isinstance(candidate, dict)
    assert candidate["release"] == "v0.2.3"
    assert candidate["platform"] == "linux-x86_64"
    assert candidate["sha256"] == (
        "1534d1e6ddaf3d080ec4091eb41d0a4d8cc042a48b607d3c410fc13b482a9eec"
    )
    assert manifest["status"] == "PLANNED_NOT_EXECUTED"


def test_obscura_plan_forbids_evasion_and_truth_authority() -> None:
    manifest = _manifest()
    policy = manifest["policy"]
    assert isinstance(policy, dict)
    assert policy == {
        "stealth": False,
        "anti_bot_bypass": False,
        "captcha_bypass": False,
        "authenticated_scraping": False,
        "public_allow_private_network": False,
        "provider_is_truth_authority": False,
    }


def test_obscura_adoption_gate_keeps_chromium_fallback() -> None:
    manifest = _manifest()
    gate = manifest["decision_gate"]
    assert isinstance(gate, dict)
    assert gate["useful_observation_recovery_ratio_min"] >= 0.95
    assert gate["provenance_completeness_ratio_min"] == 1.0
    assert gate["security_regressions_max"] == 0
    assert gate["target_aggregate_resource_ratio_max"] <= 0.60
    assert gate["chromium_fallback_required"] is True


def test_obscura_docs_do_not_authorize_production_or_stealth() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    quickstart = QUICKSTART.read_text(encoding="utf-8")
    assert "does not add Obscura to production" in spec
    assert "Obscura stealth mode is forbidden" in spec
    assert "--stealth" in quickstart
    assert "Never use latest" in quickstart
