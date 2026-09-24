"""Deterministic guardrails for the accepted AXIGLAND graph architecture."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".opencode/skills/axignal-graph-design"
REFERENCES = (
    "economic-cartography.md",
    "semantic-lod.md",
    "node-grammar.md",
    "edge-grammar.md",
    "epistemic-grammar.md",
    "temporal-grammar.md",
    "pathx-grammar.md",
    "corporate-structure.md",
    "focus-and-recenter.md",
    "progressive-materialization.md",
    "labels.md",
    "accessibility.md",
    "performance-budgets.md",
    "renderer-boundary.md",
    "representation-anomalies.md",
    "evidence-explainability.md",
    "visual-validation.md",
)


def test_adr_0009_is_accepted_and_axignal_owns_the_boundary() -> None:
    adr = (ROOT / "docs/adr/ADR-0009-axigland-graph-architecture.md").read_text(encoding="utf-8")
    assert "**Status:** **ACCEPTED.**" in adr
    assert "HYBRID" in adr
    assert "AXIGNAL owns semantic LOD" in adr
    assert "No renderer types may exist above the renderer" in adr
    assert "initial implementation choice" in adr
    assert "no production" in adr.casefold()


def test_graph_design_skill_and_all_required_references_exist() -> None:
    entrypoint = SKILL / "SKILL.md"
    assert entrypoint.is_file()
    skill_text = entrypoint.read_text(encoding="utf-8")
    assert "name: axignal-graph-design" in skill_text
    for reference in REFERENCES:
        assert (SKILL / "references" / reference).is_file()
        assert reference in skill_text


def test_skill_preserves_economic_and_epistemic_separation() -> None:
    text = " ".join(
        " ".join(path.read_text(encoding="utf-8").split()) for path in SKILL.rglob("*.md")
    )
    for invariant in (
        "Sigma + Graphology is only",
        "Neither is AXIGLAND",
        "Graphology may be an in-memory structure/algorithm substrate behind the adapter, but it is not a canonical store or semantic authority",
        "semantic LOD",
        "renderer contract",
        "POTENTIAL != OBSERVED",
        "PATHX is an explainable economic path composed of relationships",
        "UNKNOWN != FALSE",
        "REQUEST REVIEW seam",
        "Review does not grant graph editing or canonical truth authority",
        "canonical",
        "source lineage",
    ):
        assert invariant.casefold() in text.casefold()
    assert "customer edits to graph truth" in text


def test_production_dependencies_exclude_graph_engines_and_cosmos() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["dependencies"] == []
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8").casefold()
    assert "sigma.js" not in lock
    assert "graphology" not in lock
    assert "@cosmograph/cosmos" not in lock
    assert "cosmos.gl" not in lock

    harness_dir = ROOT / "experiments/graph-engine-bakeoff"
    harness = json.loads((harness_dir / "package.json").read_text(encoding="utf-8"))
    assert harness["private"] is True
    assert "research only; not production dependencies" in harness["description"].casefold()
    assert "@cosmograph/cosmos" not in harness["dependencies"]
    assert "@cosmograph/cosmos" not in (harness_dir / "package-lock.json").read_text(
        encoding="utf-8"
    )


def test_renderer_imports_do_not_leak_into_canonical_runtime_layers() -> None:
    forbidden = ("sigma", "graphology", "cosmograph", "cosmos.gl")
    roots = (ROOT / "domain", ROOT / "cognition", ROOT / "pipeline")
    for root in roots:
        for source in root.rglob("*.py"):
            source_text = source.read_text(encoding="utf-8").casefold()
            assert not any(token in source_text for token in forbidden), source


def test_adr_index_and_design_governance_record_acceptance() -> None:
    index = (ROOT / "docs/adr/README.md").read_text(encoding="utf-8")
    governance = (ROOT / "docs/design/DESIGN_GOVERNANCE.md").read_text(encoding="utf-8")
    assert "AXIGLAND Graph Architecture (**ACCEPTED**)" in index
    assert "**accepted** ADR" in governance
    assert "Sigma +" in governance
    assert "renderer contract" in governance
