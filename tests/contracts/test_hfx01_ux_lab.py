"""Isolation contracts for the deterministic synthetic UX laboratory."""

from __future__ import annotations

from pathlib import Path

from tests.support.hfx01_ux_lab import SCENARIOS, build_scenario

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_scenario_suite_is_explicit_and_has_documented_scale() -> None:
    assert SCENARIOS == (
        "SYNTHETIC_SPARSE",
        "SYNTHETIC_NOMINAL",
        "SYNTHETIC_DENSE",
        "SYNTHETIC_EDGE_CASES",
    )
    assert [build_scenario(name)["uxLab"]["scenarioObjectCount"] for name in SCENARIOS] == [
        3,
        9,
        17,
        12,
    ]


def test_scenarios_are_deterministic_and_mark_every_contract_fixture() -> None:
    for name in SCENARIOS:
        first = build_scenario(name)
        second = build_scenario(name)
        assert first == second
        assert first["realityLevel"] == "SYNTHETIC_PRESENTATION_LAB"
        assert "NOT CANONICAL" in first["uxLab"]["disclosure"]
        assert first["uxLab"]["fixtureClass"] == "CANONICAL_CONTRACT_BACKED_SYNTHETIC"
        assert first["organization"]["syntheticFixture"] is True
        assert first["organization"]["fixtureClass"] == "CANONICAL_CONTRACT_BACKED_SYNTHETIC"
        assert all(node["syntheticFixture"] is True for node in first["nodes"])
        assert all(
            node["fixtureClass"] == "CANONICAL_CONTRACT_BACKED_SYNTHETIC" for node in first["nodes"]
        )
        assert "evidence_refs" not in first["nodes"][0]
        assert "evidenceRefs" not in first["nodes"][0]


def test_presentation_relationships_never_enter_the_canonical_projection_shape() -> None:
    sparse = build_scenario("SYNTHETIC_SPARSE")
    dense = build_scenario("SYNTHETIC_DENSE")

    assert "relationships" not in sparse
    assert "relationships" not in dense
    assert sparse["uxLab"]["edges"] == []
    assert len(dense["uxLab"]["edges"]) == 24
    assert all(edge["syntheticFixture"] is True for edge in dense["uxLab"]["edges"])
    assert all(
        edge["source"] in {dense["organization"]["id"], *(node["id"] for node in dense["nodes"])}
        and edge["target"]
        in {dense["organization"]["id"], *(node["id"] for node in dense["nodes"])}
        for edge in dense["uxLab"]["edges"]
    )
    assert all(reference["meaning"] == "XeedFaxtReference" for reference in dense["memberships"])


def test_presentation_only_states_are_explicit_and_do_not_claim_authority() -> None:
    nominal = build_scenario("SYNTHETIC_NOMINAL")
    edge_cases = build_scenario("SYNTHETIC_EDGE_CASES")

    assert nominal["uxLab"]["presentationOnlyFixtures"] == [
        "relationship edges",
        "timeline",
        "AXENT transcript",
        "sidebar contexts",
    ]
    assert nominal["uxLab"]["timeline"]
    assert all(item["syntheticFixture"] is True for item in nominal["uxLab"]["timeline"])
    assert all(item["syntheticFixture"] is True for item in nominal["uxLab"]["contexts"])
    assert len(nominal["uxLab"]["contexts"]) == 101
    assert nominal["uxLab"]["contexts"][0]["label"] == "Asterion focus"
    assert all(item["syntheticFixture"] is True for item in nominal["uxLab"]["moves"])
    assert all(item["syntheticFixture"] is True for item in nominal["uxLab"]["messages"])
    assert nominal["uxLab"]["composerEnabled"] is True
    assert "No model or provider was called" in nominal["uxLab"]["fixtureReply"]
    assert edge_cases["uxLab"]["accountLabel"] is None
    assert any("精密部品" in node["objectOrValue"] for node in edge_cases["nodes"])
    assert any("تصنيع" in node["objectOrValue"] for node in edge_cases["nodes"])
    assert edge_cases["uxLab"]["initialHistory"][-1] == edge_cases["uxLab"]["initialFocus"]


def test_invalid_scenario_name_fails_closed_without_sparse_fallback() -> None:
    try:
        build_scenario("SYNTHETIC_UNLISTED")
    except ValueError as error:
        assert str(error) == "unsupported synthetic UX scenario"
    else:
        raise AssertionError("unlisted scenarios must not select a fallback")


def test_browser_lab_is_loopback_gated_and_absent_from_default_mode() -> None:
    script = (REPOSITORY_ROOT / "apps/web/subscriber/app.js").read_text(encoding="utf-8")
    server = (REPOSITORY_ROOT / "tests/support/hfx01_server.py").read_text(encoding="utf-8")

    assert "scenario && window.location.hostname !== '127.0.0.1'" in script
    assert "window.location.hostname !== '127.0.0.1'" in script
    assert "projection.uxLab" in script
    assert 'scenario = parse_qs(request.query).get("scenario", [None])[0]' in server
    assert "else:\n                self._serve_projection()" in server


def test_label_decluttering_preserves_world_positions_and_prefers_attention() -> None:
    script = (REPOSITORY_ROOT / "apps/web/subscriber/app.js").read_text(encoding="utf-8")
    stylesheet = (REPOSITORY_ROOT / "apps/web/subscriber/subscriber.css").read_text(
        encoding="utf-8"
    )

    assert "function layoutLabels()" in script
    assert "function segmentIntersectsRectangle(start, end, rect)" in script
    assert "const OVERVIEW_LABEL_ZOOM = 0.78" in script
    assert "state.camera.zoom < OVERVIEW_LABEL_ZOOM && priority > 1" in script
    assert "label.dataset.layoutVisibility = 'semantic-zoom-hidden'" in script
    assert "querySelectorAll('.canvas-tools, .minimap, .here, .zone')" in script
    assert "labelPriority(first.node, connectedToFocus)" in script
    assert "if (node.key === state.focus) return 0" in script
    assert "if (node.kind === 'ORGANIZATION') return 1" in script
    assert "if (connectedToFocus.has(node.id)) return 2" in script
    assert "label.dataset.layoutVisibility = 'attention-decluttered'" in script
    assert "label.dataset.layoutVisibility = 'visible-edge-overlap'" in script
    assert "label.dataset.layoutVisibility = 'priority-visible'" in script
    assert "element.dataset.worldX = String(node.x)" in script
    assert "element.dataset.worldY = String(node.y)" in script
    assert "element.title = node.label" in script
    assert "side-above" in stylesheet
    assert "left: calc(50% + 15px)" in stylesheet
    assert "right: calc(50% + 15px)" in stylesheet
    assert "top: calc(50% + 15px)" in stylesheet
    assert "bottom: calc(50% + 15px)" in stylesheet
    assert ".anch-lbl.is-decluttered { visibility: hidden; }" in stylesheet
    assert ".lab-edge.is-attenuated { opacity: .09; }" in stylesheet
    assert ".lab-edge.is-attention { opacity: .68; }" in stylesheet
    assert "SYNTHETIC_NOMINAL" not in script
    assert "SYNTHETIC_DENSE" not in script


def test_minimap_fits_visible_graph_and_uses_the_same_bounds_for_navigation() -> None:
    script = (REPOSITORY_ROOT / "apps/web/subscriber/app.js").read_text(encoding="utf-8")

    assert "function minimapBounds(nodes = state.worldNodes)" in script
    assert "const MINIMAP = { width: 160, height: 96, inset: 5 }" in script
    assert "function minimapPoint(x, y, bounds)" in script
    assert "const mapBounds = minimapBounds(state.worldNodes)" in script
    assert "const point = (node) => minimapPoint(node.x, node.y, bounds)" in script
    assert "const rect = $('#minimap svg').getBoundingClientRect()" in script
    assert "const bounds = minimapBounds()" in script
    assert "cameraTopLeft = minimapPoint(xLeft, yTop, bounds)" in script


def test_test_instrumentation_does_not_add_product_overlay_or_change_layout_bounds() -> None:
    html = (REPOSITORY_ROOT / "apps/web/subscriber/index.html").read_text(encoding="utf-8")
    script = (REPOSITORY_ROOT / "apps/web/subscriber/app.js").read_text(encoding="utf-8")
    stylesheet = (REPOSITORY_ROOT / "apps/web/subscriber/subscriber.css").read_text(
        encoding="utf-8"
    )

    assert 'id="lab-toolbar"' not in html
    assert 'id="lab-scenario"' not in html
    assert "#lab-scenario" not in script
    assert ".lab-toolbar" not in stylesheet
