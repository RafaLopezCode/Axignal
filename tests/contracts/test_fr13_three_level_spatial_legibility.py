"""FR-13 Three-Level Spatial Legibility contract."""

from pathlib import Path

from tests.support.hfx01_ux_lab import build_scenario

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"


def test_dense_spatial_fixture_has_real_label_and_edge_pressure() -> None:
    payload = build_scenario("SYNTHETIC_DENSE")
    lab = payload["uxLab"]

    assert lab["scenarioObjectCount"] == 17
    assert len(lab["edges"]) == 24
    assert all(edge["syntheticFixture"] is True for edge in lab["edges"])


def test_semantic_zoom_has_three_deterministic_scales_and_edge_budgets() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "WORLD_MAX: 0.84" in script
    assert "RELATION_PROOF_MIN: 1.55" in script
    assert "WORLD_TARGET: 0.72" in script
    assert "NEIGHBORHOOD_TARGET: 1.22" in script
    assert "const NEIGHBORHOOD_EDGE_BUDGET = 6" in script
    assert "const RELATION_PROOF_EDGE_BUDGET = 12" in script
    assert "if (zoom < SPATIAL_ZOOM.WORLD_MAX) return 'WORLD'" in script
    assert "if (zoom < SPATIAL_ZOOM.RELATION_PROOF_MIN) return 'NEIGHBORHOOD'" in script
    assert "return 'RELATION_PROOF'" in script
    assert "if (level === 'WORLD') return []" in script
    assert (
        "if (level === 'NEIGHBORHOOD') return attention.slice(0, NEIGHBORHOOD_EDGE_BUDGET)"
        in script
    )
    assert "const oneHopContext = edges.filter" in script
    assert "[...attention, ...oneHopContext].slice(0, RELATION_PROOF_EDGE_BUDGET)" in script
    assert "const zoom = Math.min(fitZoom, SPATIAL_ZOOM.WORLD_TARGET)" in script
    assert "const zoom = SPATIAL_ZOOM.NEIGHBORHOOD_TARGET" in script


def test_scale_controls_label_authority_without_inventing_clusters() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "(level === 'WORLD' && priority > 1)" in script
    assert "(level === 'NEIGHBORHOOD' && priority > 2)" in script
    assert "if (node.key === state.focus) return 0" in script
    assert "if (node.kind === 'ORGANIZATION') return 1" in script
    assert "if (connectedToFocus.has(node.id)) return 2" in script
    assert "cluster" not in script.casefold()
    assert "aggregate" not in script.casefold()


def test_spatial_scale_is_visible_and_announced_accessibly() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert 'id="spatial-status" role="status" aria-live="polite"' in html
    assert 'aria-describedby="spatial-status"' in html
    assert "field.dataset.spatialLevel = level.toLowerCase().replace('_', '-')" in script
    assert "function updateSpatialStatus(level = spatialLevel())" in script
    assert "'spatial.fieldAccessibleName'" in script
    assert ".anch:focus .anch-lbl" in css
    assert "visibility: visible !important;" in css
    assert ".anch:focus {" in css
    assert "opacity: 1;" in css


def test_non_graph_connection_list_remains_independent_of_visual_edge_budget() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "function renderConnections(focus)" in script
    assert "const edges = (state.uxLab.edges ?? []).filter((edge) =>" in script
    render_connections = script.split("function renderConnections(focus)", 1)[1].split(
        "function renderBottomTabVisibility()", 1
    )[0]
    assert "spatialEdges(" not in render_connections
    assert "button.addEventListener('click', () => navigate(target.key))" in render_connections
