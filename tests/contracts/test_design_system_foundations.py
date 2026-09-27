import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN_SYSTEM = ROOT / "apps" / "web" / "design-system"


def test_visual_tokens_preserve_measured_golden_master_values() -> None:
    tokens = (DESIGN_SYSTEM / "tokens.css").read_text(encoding="utf-8")

    assert "--ax-paper: #f2eee4" in tokens
    assert "--ax-ink: #201e19" in tokens
    assert "--ax-brass: #967a2f" in tokens
    assert "--ax-font-size-body: 15px" in tokens
    assert "--ax-motion-focus-duration: 440ms" in tokens
    assert "cubic-bezier(0.22, 1, 0.36, 1)" in tokens
    assert "--ax-opacity-muted: 0.72" in tokens
    assert "--ax-attention-selected-stroke" in tokens
    assert "--ax-attention-active-ink" in tokens


def test_readable_text_colors_meet_wcag_aa_on_paper_surfaces() -> None:
    tokens = (DESIGN_SYSTEM / "tokens.css").read_text(encoding="utf-8")

    def luminance(token: str) -> float:
        match = re.search(rf"--ax-{re.escape(token)}:\s*(#[0-9a-fA-F]{{6}})", tokens)
        assert match is not None
        channels = [int(match.group(1)[offset : offset + 2], 16) / 255 for offset in (1, 3, 5)]
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    paper = luminance("paper")
    for foreground in ("ink", "ink-subtle", "ink-muted"):
        ratio = (paper + 0.05) / (luminance(foreground) + 0.05)
        assert ratio >= 4.5


def test_global_layer_has_logical_direction_and_reduced_motion_foundations() -> None:
    global_css = (DESIGN_SYSTEM / "global.css").read_text(encoding="utf-8")

    assert "@media (prefers-reduced-motion: reduce)" in global_css
    assert "min-block-size" in global_css
    assert "padding-inline" in global_css
    assert "overflow-wrap: anywhere" in global_css
    assert ":focus-visible" in global_css
    assert ".ax-type-meta" in global_css
    assert "color: var(--ax-ink-muted)" in global_css


def test_primitives_use_semantic_state_and_accessible_native_controls() -> None:
    primitives = (DESIGN_SYSTEM / "primitives.ts").read_text(encoding="utf-8")
    css = (DESIGN_SYSTEM / "global.css").read_text(encoding="utf-8")

    assert "document.createElement('button')" in primitives
    assert "button.disabled = options.disabled ?? false" in primitives
    assert "'unknown'" in primitives
    assert ".ax-status[data-state='unknown']" in css
    assert ".ax-status[data-state='unknown']::before" in css
    assert "background: var(--ax-epistemic-unknown)" in css
    assert "aria-disabled='true'" in css
    assert ".ax-input::placeholder" in css
    assert "color: var(--ax-ink-muted)" in css


def test_reference_fixture_is_marked_and_isolated_from_product_truth() -> None:
    fixture = ROOT / "apps" / "web" / "reference" / "p0-ds-01" / "index.html"
    html = fixture.read_text(encoding="utf-8")

    assert 'data-fixture="TEST_FIXTURE"' in html
    assert "TEST_FIXTURE · P0-DS-01 REFERENCE SPECIMEN" in html
    assert "noindex, nofollow" in html
    assert "canonical evidence" not in html.lower()
