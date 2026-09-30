from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"


def test_today_ui_is_insight_first_and_limited_to_three_items() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    presentation = (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8")

    assert ".slice(0, 3)" in script
    assert "for (const faxt of state.projection.nodes)" not in script
    assert "presentation.countDetails(state.projection.nodes.length)" not in script
    assert "presentation.text('today.heading')" in script
    assert "presentation.text('today.why')" in script
    assert "presentation.text('today.showHow')" in script
    assert "presentation.text('today.openMap')" in script

    for copy in (
        "What deserves your attention now",
        "Why it matters",
        "Show how AXIGNAL knows",
        "View in map",
        "Nothing material is ready yet. AXIGNAL is still observing.",
    ):
        assert copy in presentation


def test_today_primary_evidence_action_and_map_deep_link_preserve_context() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "function openTodayEvidence(key)" in script
    assert "navigate(key, { recenter: false })" in script
    assert "state.depth = 3" in script
    assert "renderDepth()" in script
    assert "$('#depth-slider').focus({ preventScroll: true })" in script
    assert "open.addEventListener('click', () => navigate(item.key, { recenter: false }))" in script


def test_today_fixture_adapter_does_not_claim_unobserved_change() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    presentation = (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8")

    assert "today.currentObservation" in script
    assert "Current observation" in presentation
    assert "changed today" not in script.casefold()
    assert "new today" not in script.casefold()


def test_today_has_empty_partial_and_responsive_product_states() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    stylesheet = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert "presentation.text('today.partial')" in script
    assert "presentation.text('today.empty')" in script
    assert ".today-empty" in stylesheet
    assert ".today-primary" in stylesheet
    assert ".today-secondary" in stylesheet
    assert "@media (max-width: 1000px)" in stylesheet
    assert ".reader .today-ideas { grid-template-columns: 1fr; }" in stylesheet
