"""FR-15 Accessible Non-Graph Projection contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"


def test_non_graph_projection_has_semantic_focus_relationship_time_and_evidence_structure() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "function renderAccessibleProjection(focus)" in script
    assert "section.setAttribute('aria-labelledby', 'semantic-projection-title')" in script
    assert "const pathNav = document.createElement('nav')" in script
    assert "const pathList = document.createElement('ol')" in script
    assert "const relationshipList = document.createElement('ul')" in script
    assert "const stateList = document.createElement('dl')" in script
    assert "const timeList = document.createElement('dl')" in script
    assert "evidenceButton.setAttribute('aria-expanded', 'false')" in script
    assert "evidenceDetail.tabIndex = -1" in script
    assert "renderAccessibleProjection(node)" in script


def test_non_graph_navigation_is_keyboard_focus_preserving_and_canvas_independent() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "function navigateNonGraph(key)" in script
    assert "navigate(key, { recenter: false })" in script
    assert "$('#semantic-projection-title')?.focus({ preventScroll: true })" in script
    assert "button.addEventListener('click', () => navigateNonGraph(key))" in script
    assert "open.addEventListener('click', () => navigateNonGraph(target.key))" in script

    section = script.split("function renderAccessibleProjection(focus)", 1)[1].split(
        "function renderBottomTabVisibility()", 1
    )[0]
    assert "spatialEdges(" not in section
    assert "focusCamera(" not in section


def test_epistemic_and_relationship_states_are_textual_not_color_only() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    english = (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8")
    spanish = (SUBSCRIBER / "locale-es.js").read_text(encoding="utf-8")

    assert "function epistemicText(value)" in script
    assert "presentation.text('accessible.relationState')" in script
    assert "epistemicText(edge.epistemicState)" in script
    assert "fact.epistemicLabel ?? epistemicText(focus.source.epistemicState)" in script
    assert "'epistemic.potential': 'Potential'" in english
    assert "'epistemic.historical': 'Historical'" in english
    assert "'epistemic.potential': 'Potencial'" in spanish
    assert "'epistemic.historical': 'Histórico'" in spanish


def test_evidence_action_fails_closed_without_leaking_internal_projection_status() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "const evidenceAvailable = Boolean(evidenceStatus)" in script
    assert "!presentation.isImplementationValue(evidenceStatus)" in script
    assert "presentation.text('accessible.evidenceUnavailable')" in script
    assert "presentation.text('accessible.evidenceAvailable')" in script
    assert "UNKNOWN_UNSUPPORTED" not in script


def test_zoom_reflow_keeps_semantic_projection_available_at_narrow_equivalents() -> None:
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert "@media (max-width: 680px)" in css
    assert ".center > .bottom { display: flex; max-height: 45vh; min-height: 210px; }" in css
    assert ".center > .bottom .conn { display: none; }" in css
    assert ".semantic-definition," in css
    assert ".semantic-relation-list li {" in css
    assert "grid-template-columns: 1fr;" in css
    assert "overflow-wrap: anywhere;" in css
