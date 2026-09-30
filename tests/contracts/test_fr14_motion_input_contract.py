"""FR-14 Motion/Input Contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"
LANDING = ROOT / "apps" / "web" / "landing" / "index.html"
TOKENS = ROOT / "apps" / "web" / "design-system" / "tokens.css"


def test_axigland_wheel_ownership_distinguishes_pan_zoom_and_controls() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")

    assert 'id="field" role="group" tabindex="0"' in html
    assert 'aria-describedby="spatial-status field-hint"' in html
    assert "function normalizedWheelDelta(event)" in script
    assert "WheelEvent.DOM_DELTA_LINE" in script
    assert "function canvasOwnsWheel(event)" in script
    assert "'.canvas-tools, .here, .minimap'" in script
    assert "field.addEventListener('wheel'" in script
    assert "window.addEventListener('wheel'" not in script
    assert "if (!canvasOwnsWheel(event)) return" in script
    assert "if (event.ctrlKey || event.metaKey)" in script
    assert (
        "changeZoom(state.camera.zoom * Math.exp(-dominant * 0.002), screenPoint(event))" in script
    )
    assert "if (event.shiftKey && Math.abs(delta.x) < Math.abs(delta.y))" in script
    assert "panCameraBy(delta.x, delta.y)" in script


def test_axigland_pan_keyboard_and_motion_have_explicit_fallbacks() -> None:
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    tokens = TOKENS.read_text(encoding="utf-8")

    assert "const CAMERA_MOTION_MS = 440" in script
    assert "--ax-motion-focus-duration: 440ms" in tokens
    assert "if (reduceMotion.matches)" in script
    assert "state.camera = target" in script
    assert "const middlePan = event.button === 1 && !onControl" in script
    assert "const directPan = event.button === 0 && !onControl && !onNode" in script
    assert "field.focus({ preventScroll: true })" in script
    assert "const step = KEYBOARD_PAN_STEP * (event.shiftKey ? 2 : 1)" in script
    for key in ("ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home"):
        assert f"event.key === '{key}'" in script
    assert "event.key === '+' || event.key === '='" in script
    assert "event.key === '-' || event.key === '_'" in script
    assert "event.key === '0'" in script
    assert "event.key.toLowerCase() === 'r'" in script
    assert ".field.panning" in css
    assert ".field:focus-visible" in css


def test_landing_chapter_motion_is_directional_hysteretic_and_reduced_motion_safe() -> None:
    html = LANDING.read_text(encoding="utf-8")

    assert "--ax-motion-chapter:620ms" in html
    assert '.scene[data-direction="backward"] .art-next' in html
    assert "scene.dataset.direction=dir<0?'backward':'forward'" in html
    assert "const total=reduced.matches?120:640" in html
    assert "const swapAt=reduced.matches?40:220" in html
    assert "let wheelGestureArmed=true" in html
    assert "function armWheelAfterQuiet()" in html
    assert "},180);" in html
    assert "if(transitioning||!wheelGestureArmed){armWheelAfterQuiet();return}" in html
    assert "if(wheelAccum>=72)" in html
    assert "wheelGestureArmed=false" in html
    assert (
        ".art-next{transform:none!important;opacity:0;transition:opacity 120ms linear!important}"
        in html
    )
    assert ".scene.is-transitioning .art-next{transform:none!important;opacity:1}" in html
    assert "animation:none!important" in html


def test_landing_inputs_converge_on_one_navigation_state_machine() -> None:
    html = LANDING.read_text(encoding="utf-8")

    assert "function next(){ if(chapter<15) goTo(chapter+1,1); }" in html
    assert "function prev(){ if(chapter>1) goTo(chapter-1,-1); }" in html
    assert "sign>0?next():prev()" in html
    assert "['ArrowDown','PageDown','ArrowRight',' ']" in html
    assert "if(Math.abs(dy)>=48) dy<0?next():prev()" in html
    assert "b.onclick=()=>goTo(ch.n,ch.n>chapter?1:-1)" in html
