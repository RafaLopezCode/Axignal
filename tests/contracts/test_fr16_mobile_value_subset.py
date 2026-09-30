"""FR-16 Mobile Value Subset contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"


def test_mobile_product_is_reader_first_not_shrunken_canvas() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert 'class="mobile-header"' in html
    assert 'class="mobile-nav"' in html
    assert 'id="mobile-today"' in html
    assert 'id="mobile-evidence"' in html
    assert 'id="mobile-timeline"' in html
    assert 'id="mobile-axent"' in html

    final_mobile = css.rsplit("@media (max-width: 680px)", 2)[-2]
    assert ".stage2," in final_mobile
    assert "display: none !important;" in final_mobile
    assert ".gov {" in final_mobile
    assert "display: none !important;" in final_mobile
    assert ".center > .bottom" in final_mobile
    assert "grid-template-rows: auto minmax(0, 1fr) auto;" in final_mobile


def test_mobile_core_value_path_has_xignal_why_evidence_and_timeline() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    english = (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8")
    spanish = (SUBSCRIBER / "locale-es.js").read_text(encoding="utf-8")

    assert "function whyTextForSource(source)" in script
    assert "why.className = 'mobile-why'" in script
    assert "function renderMobileTimeline(node)" in script
    assert "renderMobileTimeline(node)" in script
    assert "function openTodayEvidence(key)" in script
    assert "state.mobileSurface = 'evidence'" in script
    assert "$('.semantic-evidence-action')" in script
    assert "const desktopOpenLabel = presentation.text('today.openMap')" in script
    assert (
        "mobileViewport.matches ? presentation.text('mobile.openXignal') : desktopOpenLabel"
        in script
    )

    for key in (
        "mobile.openXignal",
        "mobile.why",
        "mobile.timelineTitle",
        "mobile.timelineUnavailable",
        "mobile.openAxent",
        "mobile.closeAxent",
    ):
        assert f"'{key}'" in english
        assert f"'{key}'" in spanish


def test_mobile_navigation_does_not_depend_on_canvas_pan_or_camera_precision() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")

    assert "if (recenter && !mobileViewport.matches) focusCamera(key)" in script
    assert "function focusMobileSection(surface)" in script
    assert "target?.scrollIntoView({ block: 'start' })" in script
    assert "$('#reader').scrollTop = 0" in script
    assert "$('#bottom-title')?.focus({ preventScroll: true })" in script
    assert "$('#mobile-timeline-section')" in script


def test_mobile_axent_is_context_preserving_sheet_with_keyboard_exit() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert 'id="axent-panel"' in html
    assert 'id="mobile-scrim"' in html
    assert 'id="mobile-axent-close"' in html
    assert "state.mobileReturnSurface = state.mobileSurface" in script
    assert "state.mobileSurface = state.mobileReturnSurface || 'reader'" in script
    assert "panel.setAttribute('role', 'dialog')" in script
    assert "panel.setAttribute('aria-modal', 'true')" in script
    assert "panel.setAttribute('aria-hidden', 'true')" in script
    assert "event.key === 'Escape'" in script
    assert "event.key !== 'Tab'" in script
    assert "document.activeElement === first" in script
    assert "document.activeElement === last" in script
    assert ".app2.mobile-axent-open .axent" in css
    assert "pointer-events: none;" in css
    assert "pointer-events: auto;" in css


def test_mobile_targets_are_touch_sized_and_reflow_without_horizontal_dependency() -> None:
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")

    assert ".today-primary," in css
    assert "min-height: 44px;" in css
    assert ".semantic-evidence-action" in css
    assert ".mobile-nav button {" in css
    assert "min-height: 50px;" in css
    assert "@media (max-width: 380px)" in css
    assert ".today-actions {" in css
    assert "grid-template-columns: 1fr;" in css
