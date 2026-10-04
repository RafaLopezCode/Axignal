import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "governance" / "AXIGNAL_ADVERSARIAL_EPISTEMIC_REMEDIATION_2026-10-03.md"
ADMIN_ROADMAP = (
    ROOT / "docs" / "governance" / "AXIGNAL_ADMIN_OPERATING_SYSTEM_ROADMAP_2026-10-01.md"
)


def test_adversarial_remediation_has_complete_task_sequence() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    task_ids = re.findall(r"^## (AUD-\d{2})", text, re.MULTILINE)
    assert task_ids == [f"AUD-{index:02d}" for index in range(1, 11)]
    assert (
        "**Revalidated against:** current canonical integration state; exact SHA recorded in results-current-main.json"
        in text
    )
    assert "**Status:** CLOSED — AUD-01..AUD-10 REPAIRED" in text
    assert "AXIGNAL_ADVERSARIAL_REAUDIT_DELTA_2026-10-04.md" in text


def test_ao25_is_unblocked_after_adversarial_remediation_closes() -> None:
    text = ADMIN_ROADMAP.read_text(encoding="utf-8")
    assert "**CURRENT_TASK = AO-25**" in text
    assert "**Status:** READY" in text
    assert "**Depends on:** AO-02, AO-09, AO-24, AUD-01..AUD-10" in text


def test_remediation_preserves_core_negative_semantics() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    required = (
        "Business truths such as supply/capability/relationship require canonical compatible admission",
        "No private evidence is promoted to global AXIGLAND truth",
        "Temporal aging can classify evidence HISTORICAL while reuse and visible read model still claim CURRENT",
        "Future evidence, missing artifact, mismatched effective version or absent approval cannot enable claims/live",
        "Credential-like query parameters can reach CAS metadata, persisted read models and visible sourceRefs",
    )
    for invariant in required:
        assert invariant in text
