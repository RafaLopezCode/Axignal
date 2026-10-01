from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "docs" / "product" / "AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md"
ADMIN = ROOT / "docs" / "product" / "AXIGNAL_ADMIN_PRODUCT_SPEC.md"
ADR = ROOT / "docs" / "adr" / "ADR-0055-admin-private-business-operations-separation.md"
ARCH = ROOT / "docs" / "architecture" / "AXIGNAL_ADMIN_OBSERVABILITY_ARCHITECTURE_V0.1.md"
P0_SPEC = ROOT / "specs" / "004-p0-admin-observability" / "spec.md"
CONTRACTS = (
    ROOT / "specs" / "004-p0-admin-observability" / "contracts" / "observability-contracts.md"
)


def test_master_authorizes_only_axignal_internal_business_operations() -> None:
    text = MASTER.read_text(encoding="utf-8")
    assert "## 2.1A" in text
    assert "operaciones internas de AXIGNAL" in text
    assert "AXIGNAL_INTERNAL_CRM_STATE != AXIGLAND_ECONOMIC_TRUTH" in text
    assert "COMMERCIAL_RELATIONSHIP_WITH_AXIGNAL != OBSERVED_ECONOMIC_RELATIONSHIP" in text
    assert "tampoco autoriza un CRM" in text
    assert "capacidad subscriber-facing" in text


def test_adr_0055_preserves_no_crm_product_boundary() -> None:
    text = ADR.read_text(encoding="utf-8")
    assert "**Status:** Accepted" in text
    assert "ADR-0008 remains fully authoritative for subscriber-facing product/core scope" in text
    assert "Admin presence alone confers no evidence authority" in text
    assert "Internal CRM means **AXIGNAL's CRM for operating AXIGNAL**" in text


def test_admin_v02_contains_new_operating_scope_without_runtime_claim() -> None:
    text = ADMIN.read_text(encoding="utf-8")
    assert "version: 0.2" in text
    assert "status: ACCEPTED_GOVERNED_SPECIFICATION" in text
    assert "implementation_status: PRE_IMPLEMENTATION" in text
    for required in (
        "AXIGNAL's own internal CRM",
        "private GSC/web analytics",
        "Stripe/billing",
        "finance/accounting",
        "fiscal/VeriFactu",
        "Frontier Advisor workbench",
    ):
        assert required in text
    assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in text
    assert "TAX_STATE != AXIGLAND_TRUTH" in text


def test_p0_admin_observability_is_amended_not_discarded() -> None:
    admin = ADMIN.read_text(encoding="utf-8")
    arch = ARCH.read_text(encoding="utf-8")
    spec = P0_SPEC.read_text(encoding="utf-8")
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "**RETAINED:** versioned observability contracts" in admin
    assert "**AMENDED:** Customer Operations may now include AXIGNAL's own CRM" in admin
    assert "ADR-0055" in arch
    assert "ADR-0055" in spec
    assert "ADR-0055" in contracts
    assert "customer-owned CRM/workflow state" in contracts
