from dataclasses import fields
from pathlib import Path

from application.admin_observability import AdminProjectionRuntime
from domain.admin_observability import AdminEventEnvelope, AdminProjectionSnapshot

ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs" / "adr" / "ADR-0058-admin-observability-projection-runtime.md"
ARCH = ROOT / "docs" / "architecture" / "AXIGNAL_ADMIN_OBSERVABILITY_ARCHITECTURE_V0.1.md"
CONTRACTS = (
    ROOT / "specs" / "004-p0-admin-observability" / "contracts" / "observability-contracts.md"
)
TASKS = ROOT / "specs" / "004-p0-admin-observability" / "tasks.md"


def test_admin_event_envelope_is_metadata_first_without_generic_raw_payload() -> None:
    names = {item.name for item in fields(AdminEventEnvelope)}
    forbidden = {"payload", "body", "content", "prompt", "response", "credential", "token"}
    assert names.isdisjoint(forbidden)
    assert {"record_id", "owning_domain", "recorded_at", "provenance_refs"} <= names


def test_projection_snapshot_is_versioned_temporal_and_lineage_bearing() -> None:
    names = {item.name for item in fields(AdminProjectionSnapshot)}
    required = {
        "projection_id",
        "schema_version",
        "scope",
        "as_of",
        "generated_at",
        "completeness",
        "source_record_ids",
        "fingerprint",
    }
    assert required <= names


def test_ao03_runtime_remains_projection_not_domain_authority() -> None:
    source = (ROOT / "application" / "admin_observability" / "runtime.py").read_text(
        encoding="utf-8"
    )
    assert "EvidenceAdmission" not in source
    assert "FAXT" not in source
    assert "canonical_write" not in source.lower()
    assert AdminProjectionRuntime is not None


def test_ao03_documentation_closes_t011_without_claiming_full_admin_runtime() -> None:
    adr = ADR.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")
    contracts = CONTRACTS.read_text(encoding="utf-8")
    tasks = TASKS.read_text(encoding="utf-8")

    assert "**Status:** Accepted" in adr
    assert "supersedes_record_id" in adr
    assert "later `as_of`" in adr
    assert "PARTIALLY_IMPLEMENTED (AO-03 substrate)" in architecture
    assert "PARTIALLY_IMPLEMENTED BY AO-03" in contracts
    assert "- [x] T011" in tasks
    assert "purpose-specific metric/read models remain AO-04" in tasks
