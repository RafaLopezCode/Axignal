import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "governance" / "AXIGNAL_ADMIN_OPERATING_SYSTEM_ROADMAP_2026-10-01.md"


def test_admin_operating_system_roadmap_has_complete_task_sequence() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    task_ids = re.findall(r"^## (AO-\d{2})", text, re.MULTILINE)
    assert task_ids == [f"AO-{index:02d}" for index in range(32)]
    assert "**CURRENT_TASK = AO-09**" in text


def test_admin_operating_system_roadmap_preserves_authority_boundaries() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    required = (
        "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH",
        "AXIGNAL_INTERNAL_CRM_STATE != AXIGLAND_ECONOMIC_TRUTH",
        "COMMERCIAL_RELATIONSHIP_WITH_AXIGNAL != OBSERVED_ECONOMIC_RELATIONSHIP",
        "GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION",
        "STRIPE_STATE != AXIGLAND_TRUTH",
        "ACCOUNTING_STATE != AXIGLAND_TRUTH",
        "TAX_STATE != AXIGLAND_TRUTH",
        "PRODUCT_MCP != ADMIN_MCP",
    )
    for invariant in required:
        assert invariant in text


def test_roadmap_keeps_business_hypotheses_unvalidated_until_real_evidence() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    assert "FR-27 remains READY, not DONE" in text
    assert "€9.95/month" in text
    assert "€4.95/month" in text
    assert "€995/month" in text
    assert "FR-27 can only move READY→DONE from qualifying empirical evidence" in text


def test_roadmap_has_explicit_compliance_and_deep_reaudit_gates() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    assert "## AO-22 — VeriFactu / SIF Compliance Architecture Decision" in text
    assert (
        "No production invoice path claims VeriFactu compliance without verified evidence." in text
    )
    assert "## AO-31 — Deep Frontier Re-Audit Package" in text
    assert "without target score, pass/fail outcome or requested verdict" in text
