"""FR-11 Initial Cognitive Load Reduction contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"


def test_first_view_hides_advanced_controls_without_removing_them() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert '<details class="gv-sec gv-advanced" id="governance-section">' in html
    assert '<details class="gv-sec gv-advanced" id="governance-section" open>' not in html
    assert 'data-copy="navigation.advancedControls"' in html
    assert 'id="research-depth"' in html
    assert 'data-copy="navigation.memory"' in html
    assert 'data-copy="navigation.uncertainty"' in html
    assert 'id="workspace-placeholder"' not in html
    assert '<em class="sr-only" data-copy="context.private">Private view</em>' in html
    assert "advanced.open = true" in script
    assert "advanced.querySelector('summary').focus()" in script
    assert ".gv-advanced[open] .gv-advanced-summary" in css


def test_depth_is_directly_accessible_but_secondary_labels_are_progressive() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert 'id="depth-slider" role="slider" tabindex="0"' in html
    assert 'data-copy="navigation.evidence"' in html
    assert ".lens-stop.on b," in css
    assert ".lens:hover .lens-stop b," in css
    assert ".lens.is-expanded .lens-stop b" in css
    assert "depthLens.addEventListener('focusin'" in (SUBSCRIBER / "app.js").read_text(
        encoding="utf-8"
    )
    assert "opacity: 0;" in css


def test_axent_caps_primary_questions_and_preserves_secondary_actions() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    presentation = (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8")

    assert "const availableMoves = lab.moves.filter((move) => move.available)" in script
    assert "const primaryMoves = availableMoves.slice(0, 2)" in script
    assert "const secondaryMoves = availableMoves.slice(2)" in script
    assert "more.className = 'ax-more-moves'" in script
    assert "presentation.text('navigation.moreQuestions')" in script
    assert "'navigation.moreQuestions': 'More questions'" in presentation
