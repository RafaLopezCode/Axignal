"""Ensure agent autonomy governance rejects missing or weakened handoff authority."""

from __future__ import annotations

import hashlib
from pathlib import Path

from tools.governance.checks import check_spec_consistency

CONTRACT = "AGENT_AUTONOMY_AND_DELEGATION_CONTRACT.md"


def test_agent_autonomy_contract_is_binding_in_governance(tmp_path: Path) -> None:
    master = tmp_path / "docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md"
    master.parent.mkdir(parents=True)
    master.write_text("master fixture\n", encoding="utf-8")
    master.with_name(master.name + ".sha256").write_text(
        hashlib.sha256(master.read_bytes().replace(b"\r\n", b"\n")).hexdigest(), encoding="utf-8"
    )

    constitution = tmp_path / ".specify/memory/constitution.md"
    constitution.parent.mkdir(parents=True)
    constitution.write_text(
        "MASTER PRODUCT MODEL\nAXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md\n"
        "One Canonical AXIGLAND\nEpistemic Neutrality\nModel Provider Abstraction\n"
        "CLAIM\nUNKNOWN != FALSE\nIMPLEMENTATION\nFAIL CLOSED\n" + CONTRACT,
        encoding="utf-8",
    )
    contract = tmp_path / "docs/governance" / CONTRACT
    contract.parent.mkdir(parents=True)
    contract.write_text(
        "FRONTIER_AGENT GUIDED_AGENT Authority ceiling VERIFIED E2E",
        encoding="utf-8",
    )
    for rel in ("AGENTS.md", "CLAUDE.md", "docs/governance/README.md"):
        entry = tmp_path / rel
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(CONTRACT, encoding="utf-8")

    assert check_spec_consistency(tmp_path) == []

    contract.write_text("FRONTIER_AGENT Authority ceiling VERIFIED E2E", encoding="utf-8")
    assert any("GUIDED_AGENT" in item for item in check_spec_consistency(tmp_path))

    contract.write_text(
        "FRONTIER_AGENT GUIDED_AGENT Authority ceiling VERIFIED E2E",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text("no contract here", encoding="utf-8")
    assert any("CLAUDE.md" in item for item in check_spec_consistency(tmp_path))
