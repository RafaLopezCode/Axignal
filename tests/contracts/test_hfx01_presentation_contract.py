"""Presentation-boundary contracts for the P0-HFX-01 subscriber surface."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"
PRESENTATION_SCRIPT = SUBSCRIBER / "presentation.js"


class _Elements(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.transcript_depth = 0
        self.transcript_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self.elements.append((tag, attributes))
        if attributes.get("id") == "axent-transcript":
            self.transcript_depth = 1
        elif self.transcript_depth:
            self.transcript_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.transcript_depth:
            self.transcript_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.transcript_depth:
            self.transcript_text += data


def _by_id(elements: _Elements, element_id: str) -> tuple[str, dict[str, str | None]]:
    matches = [item for item in elements.elements if item[1].get("id") == element_id]
    assert len(matches) == 1
    return matches[0]


def test_axent_keeps_golden_master_structure_without_faking_capabilities() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)

    axent = [
        attrs
        for tag, attrs in elements.elements
        if tag == "aside" and attrs.get("aria-label") == "AXENT context guide"
    ]
    assert len(axent) == 1

    moves = [attrs for tag, attrs in elements.elements if attrs.get("class") == "ax-move"]
    assert len(moves) == 6
    assert all("disabled" in attrs for attrs in moves)
    assert all(attrs.get("data-capability") == "UNAVAILABLE" for attrs in moves)

    _, transcript = _by_id(elements, "axent-transcript")
    assert transcript.get("role") == "log"
    assert elements.transcript_text.strip() == ""

    _, composer = _by_id(elements, "axent-composer")
    _, ask_input = _by_id(elements, "axent-input")
    _, ask_button = _by_id(elements, "axent-ask")
    assert composer.get("class") == "ax-ask"
    assert "disabled" in ask_input
    assert "disabled" in ask_button

    subscriber_copy = html.casefold()
    for engineering_phrase in (
        "authorized scope",
        "one authorizedxeed",
        "no model calls",
        "axent reasoning is not implemented",
        "no cross-context retrieval",
    ):
        assert engineering_phrase not in subscriber_copy


def test_axent_context_marker_halo_is_not_clipped_by_text_truncation() -> None:
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    scope_rule = re.search(r"\.ax-scope\s*\{([^}]*)\}", css)
    text_rule = re.search(r"\.ax-scope\s*>\s*span\s*\{([^}]*)\}", css)

    assert scope_rule is not None
    assert "overflow: visible;" in scope_rule.group(1)
    assert text_rule is not None
    assert "overflow: hidden;" in text_rule.group(1)
    assert "text-overflow: ellipsis;" in text_rule.group(1)


def test_active_context_binds_canonical_identity_and_csp_needs_no_inline_style() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)

    assert all("style" not in attrs for _, attrs in elements.elements)
    _, pill = _by_id(elements, "axent-active-context")
    assert pill.get("data-active-xeed-id") == ""
    assert pill.get("data-active-kind") == ""
    assert pill.get("data-active-canonical-id") == ""
    assert "pill.dataset.activeXeedId = state.projection.context.id" in script
    assert "pill.dataset.activeKind = node.kind" in script
    assert "pill.dataset.activeCanonicalId = node.id" in script
    assert 'id="axent-input" type="text"' in html and 'aria-label="Ask AXENT" disabled' in html
    assert "if (!state.uxLab?.composerEnabled) return" in script


def test_presentation_semantics_separate_canonical_values_from_locale_copy() -> None:
    javascript_path = json.dumps(str(PRESENTATION_SCRIPT))
    script = f"""
      const assert = require('node:assert/strict')
      const fs = require('node:fs')
      const vm = require('node:vm')
      const context = {{}}
      vm.runInNewContext(fs.readFileSync({javascript_path}, 'utf8'), context)
      const presentation = context.AXIGNAL_PRESENTATION
      const canonical = {{
        id: 'faxt-demo-a2',
        predicate: 'MAINTAINS_STANDARD',
        objectOrValue: 'ISO 9001',
        epistemicState: 'STALE',
        currentness: 'UNKNOWN',
        subjectKind: 'UNKNOWN_UNSUPPORTED',
        subjectResolution: 'UNKNOWN_UNSUPPORTED',
      }}
      const english = presentation.forLocale('en-GB').describeFact(canonical)
      assert.equal(english.label, 'Maintains a standard · ISO 9001')
      assert.equal(english.predicateKey, 'predicate.maintainsStandard')
      assert.equal(english.epistemicLabel, 'May be out of date')
      assert.equal(english.currentnessLabel, "How current this information is hasn't been verified.")
      assert.equal(english.label.includes('MAINTAINS_STANDARD'), false)
      assert.equal(english.label.includes('UNKNOWN'), false)
      assert.equal(canonical.predicate, 'MAINTAINS_STANDARD')
      assert.equal(canonical.currentness, 'UNKNOWN')
      assert.equal(canonical.subjectKind, 'UNKNOWN_UNSUPPORTED')
      assert.equal(canonical.subjectResolution, 'UNKNOWN_UNSUPPORTED')

      const opaque = presentation.forLocale('en-US').describeFact({{
        predicate: 'UNREGISTERED_DOMAIN_PREDICATE',
        objectOrValue: 'subject_resolution',
        epistemicState: 'UNKNOWN',
        currentness: 'UNKNOWN',
        }})
      assert.equal(opaque.label, 'Information')
      assert.equal(opaque.valueLabel, null)
      assert.equal(opaque.label.includes('UNREGISTERED_DOMAIN_PREDICATE'), false)
      assert.equal(opaque.label.includes('subject_resolution'), false)

      for (const machineValue of ['CANONICAL_FAXT', 'AUTHORIZED_XEED', 'UNKNOWN_UNSUPPORTED', 'subject-demo-a']) {{
        const result = presentation.forLocale('en').describeFact({{
          predicate: 'UNREGISTERED_DOMAIN_PREDICATE',
          objectOrValue: machineValue,
        }})
        assert.equal(result.valueLabel, null)
        assert.equal(result.label, 'Information')
      }}

      const otherIdentity = {{ ...canonical, id: 'faxt-demo-b' }}
      const otherCopy = presentation.forLocale('en').describeFact(otherIdentity)
      assert.notEqual(canonical.id, otherIdentity.id)
      assert.equal(english.label, otherCopy.label)
      assert.equal(presentation.forLocale('es-ES').locale, 'en')
      assert.equal(presentation.forLocale('en-US').describeFact(canonical).label, english.label)
      assert.equal(presentation.forLayoutPreview('es-ES').locale, 'es')
      assert.equal(presentation.resolveLocale('es-MX', ['de-DE'], 'en'), 'en')
      assert.equal(presentation.resolveLocale(null, ['fr-FR', 'de-DE'], 'en'), 'en')
      assert.equal(presentation.resolveLocale('xx-YY', ['fr-FR'], 'ja'), 'en')
      assert.equal(presentation.resolveLocale(null, ['fr-FR'], 'en'), 'en')
      for (const locale of ['en', 'es', 'de', 'ja', 'ar']) {{
        const localized = presentation.forLayoutPreview(locale).describeFact(canonical)
        assert.equal(localized.valueLabel, 'ISO 9001')
        assert.equal(canonical.id, 'faxt-demo-a2')
        assert.equal(canonical.predicate, 'MAINTAINS_STANDARD')
      }}
      assert.equal(presentation.forLayoutPreview('ar').direction, 'rtl')
      assert.equal(presentation.forLayoutPreview('ja').direction, 'ltr')
      assert.deepEqual([...presentation.supportedLocales], ['en'])
      assert.deepEqual([...presentation.layoutPreviewLocales], ['en', 'es', 'de', 'ja', 'ar'])
    """
    subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)


def test_static_subscriber_copy_is_bound_to_presentation_catalog() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    runtime = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    presentation = PRESENTATION_SCRIPT.read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)

    keys = {
        value
        for _, attributes in elements.elements
        for name, value in attributes.items()
        if name
        in {
            "data-copy",
            "data-copy-aria-label",
            "data-copy-title",
            "data-copy-placeholder",
            "data-copy-content",
        }
        and value is not None
    }
    catalog_keys = set(re.findall(r"'([\w.]+)'\s*:", presentation))
    assert keys <= catalog_keys
    runtime_keys = set(re.findall(r"presentation\.text\('([\w.]+)'", runtime))
    assert runtime_keys <= catalog_keys


def test_locale_preference_is_a_synthetic_account_preference_and_stresses_all_surfaces() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    presentation = PRESENTATION_SCRIPT.read_text(encoding="utf-8")
    stylesheet = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)

    _, account = _by_id(elements, "lab-account")
    _, locale_selector = _by_id(elements, "ui-locale")
    assert "hidden" in account
    assert locale_selector.get("aria-describedby") == "locale-preview-note"
    _, preferences = _by_id(elements, "preferences-open")
    assert "hidden" in preferences
    assert preferences.get("aria-controls") == "preferences-view"
    assert preferences.get("class") == "lab-preferences-open"
    assert preferences.get("data-copy-aria-label") == "preferences.label"
    governance = re.search(
        r'<section class="gv-sec" id="governance-section".*?</section>',
        html,
        re.DOTALL,
    )
    assert governance is not None
    assert 'id="preferences-open"' not in governance.group(0)
    account = re.search(r'<div class="lab-account".*?</div>', html, re.DOTALL)
    assert account is not None
    assert 'id="preferences-open"' in account.group(0)
    assert 'class="ax-icon lab-preferences-icon"' in account.group(0)
    assert re.search(r'<section class="preferences-view" id="preferences-view"[^>]*hidden>', html)
    assert '<details class="lab-preferences"' not in html
    assert (
        "$('#preferences-open').addEventListener('click', () => setBottomView('preferences'))"
        in script
    )
    assert "$('.bottom').classList.toggle('preferences-open', showPreferences)" in script
    assert ".bottom.preferences-open" in stylesheet
    assert "'preferences.label': 'Settings'" in presentation
    assert (
        'value="auto"' in html
        and 'value="en"' in html
        and 'value="es"' in html
        and 'value="de"' in html
    )
    assert 'value="ja"' in html and 'value="ar"' in html
    assert (
        "function resolveLocale(userLocale, browserLocales = [], fallbackLocale = 'en')"
        in presentation
    )
    assert "const explicit = supportedLocale(userLocale)" in presentation
    assert "for (const preference of browserPreferences)" in presentation
    assert "return supportedLocale(fallbackLocale) ?? 'en'" in presentation
    assert "navigator.languages" in script
    assert "window.localStorage.getItem(LOCALE_PREFERENCE_KEY)" in script
    assert "window.localStorage.setItem(LOCALE_PREFERENCE_KEY, resolvedLocale)" in script
    assert "window.localStorage.removeItem(LOCALE_PREFERENCE_KEY)" in script
    assert "!window.AXIGNAL_PRESENTATION.isSupportedLocale(storedLocale)" in script
    assert "window.AXIGNAL_PRESENTATION.forLayoutPreview(resolvedLocale)" in script
    assert (
        "window.AXIGNAL_PRESENTATION.resolveLocale(null, browserLocalePreferences, 'en')" in script
    )
    assert "if (persist && state.uxLab && isLoopbackScenario)" in script
    assert "document.documentElement.lang = presentation.locale" in script
    assert "document.documentElement.dir = presentation.direction" in script
    assert "if (state.projection) render()" in script

    stress_keys = {
        "navigation.today",
        "navigation.capabilities",
        "navigation.trail",
        "copy.contextExplanation",
        "navigation.guide",
        "navigation.timeline",
        "navigation.zoomIn",
        "navigation.fieldControls",
    }
    keys = set(re.findall(r"'([\w.]+)'\s*:", presentation))
    assert stress_keys <= keys
    assert "const LOCALE_STRESS_COPY" in presentation
    assert "Automatic uses a complete UI catalog" in presentation
    assert "Vista sintética de maquetación. No es una traducción completa" in presentation
    assert "html[dir='rtl'] .axent" in stylesheet


def test_unknown_and_unsupported_subject_states_stay_in_internal_payload_only() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    visible_template = "\n".join((html, script)).casefold()
    for implementation_copy in (
        "unknown_unsupported",
        "subject kind",
        "subject resolution",
        "canonical faxt",
        "explicitly referenced faxt",
        "authorized scope",
        "current xeed",
        "connections are unavailable",
        "conversation unavailable",
    ):
        assert implementation_copy not in visible_template
    assert "UNKNOWN_UNSUPPORTED" not in html
    assert "UNKNOWN_UNSUPPORTED" not in script


def test_sidebar_uses_quiet_truthful_states_and_golden_master_rail_contract() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    presentation = PRESENTATION_SCRIPT.read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)

    sidebar, _ = _by_id(elements, "sidebar-navigation")
    assert sidebar == "nav"
    assert re.search(
        r'<section class="gv-sec" id="governance-section" tabindex="-1">\s*'
        r'<span class="gv-cap" data-copy="navigation.governance">',
        html,
    )
    _, workspace = _by_id(elements, "workspace-placeholder")
    assert workspace.get("aria-hidden") == "true"
    _, xeed = _by_id(elements, "xeed-current")
    assert xeed.get("type") == "button"
    assert "disabled" in xeed
    assert xeed.get("aria-haspopup") == "listbox"
    assert xeed.get("aria-expanded") == "false"
    assert xeed.get("aria-controls") == "lab-contexts"
    assert 'id="lab-contexts" hidden' in html
    assert "Other Xeeds are not available in this demonstration." in html
    _, xeed_list = _by_id(elements, "lab-context-list")
    assert xeed_list.get("role") == "listbox"
    assert 'id="xeed-organization-label"' not in html
    assert 'data-copy="context.organizationLabel"' not in html
    assert 'data-copy="navigation.createXeed"' in html
    assert "Plant Xeed" in presentation
    assert "state.projection.organization.name" not in script
    assert "aria-selected" in script
    assert "setXeedMenuOpen(true, true)" in script
    assert "event.key === 'Escape'" in script
    assert "button.disabled = index !== 0" in script
    assert "state.projection.context.label" in script
    assert "lab.activeXeedLabel" not in script
    assert ".lab-context:disabled { color: var(--faint); cursor: not-allowed; }" in css
    assert "max-height: 220px;" in css
    assert ".gv-plant:disabled { opacity: 1; }" in css
    assert "border: 1px dashed var(--hair-2);" in css
    assert "font: 400 13px/1.4 var(--sans);" in css
    assert ".gv-rk,\n.gv-plant { font: 400 13px/1.4 var(--sans); }" in css
    assert "letter-spacing: normal;" in css
    assert "text-transform: none;" in css
    assert "min-height: 34px;" in css
    assert "min-height: 58px;" in css

    capabilities = {
        attrs.get("data-capability")
        for _, attrs in elements.elements
        if attrs.get("class", "").startswith("gv-row")
    }
    assert capabilities == {"READ_ONLY", "UNAVAILABLE", "AVAILABLE"}
    assert "Private · current context" not in html
    assert "UNAVAILABLE" not in presentation
    assert "gv-sw" not in html
    assert "No memory setting is shown in this view." in presentation
    assert "No uncertainty setting is shown in this view." in presentation

    _, research = _by_id(elements, "research-depth")
    assert research.get("data-capability") == "AVAILABLE"
    _, today_rail = _by_id(elements, "today-rail")
    _, governance_rail = _by_id(elements, "governance-rail")
    assert today_rail.get("aria-current") == "true"
    assert governance_rail.get("type") == "button"
    assert "#today-rail" in script
    assert "#governance-rail" in script
    assert "#governance-section').focus()" in script
    assert "#today-rail').setAttribute('aria-current'" in script
    assert ".gov.collapsed .gv-rail { display: flex; }" in css
    assert ".gov.collapsed .gv-scroll" in css
    assert ".gov:not(.collapsed) { position: fixed" in css
    assert "matchMedia('(max-width: 900px)')" in script

    assert 'id="xeed-rail"' in html
    assert 'id="create-xeed-rail"' in html
    assert 'class="gv-account"' not in html
    assert 'class="gv-avatarsm"' not in html
    assert 'class="hfx-demo-indicator"' in html
    assert "TEST / DEV" not in html


def test_focus_history_uses_distinct_nonsemantic_breadcrumb_separators() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    assert 'class="trail-path" id="history-list"' in html
    assert 'aria-label="Focus trail"' in html
    assert "separator.className = 'trail-sep'" in script
    assert "separator.textContent = '/'" in script
    assert "separator.setAttribute('aria-hidden', 'true')" in script
    assert "item.title = item.textContent" in script
    assert "visible.length > 3" in script
    assert "visible.slice(1, -1)" in script
    assert "navigation.hiddenStops" in script
    assert "hidden.setAttribute('role', 'note')" in script
    assert "$('.trail').classList.toggle('is-compacted', hiddenCount > 0)" in script
    assert "width: min(300px, calc(100% - 480px));" in css
    assert ".trail.is-compacted .session-only { display: none; }" in css
    assert "min-width: 48px;" in css
    assert "text-overflow: ellipsis;" in css
    assert "@media (max-width: 1000px) {\n  .session-only { display: none; }\n}" in css


def test_hidden_focus_trail_stops_use_locale_aware_copy() -> None:
    presentation = (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8")
    for copy in (
        "{count} earlier stops hidden",
        "{count} pasos anteriores ocultos",
        "{count} frühere Stationen ausgeblendet",
        "前の{count}件を省略",
        "تم إخفاء {count} محطات سابقة",
    ):
        assert copy in presentation


def test_field_controls_reset_view_and_minimap_respects_its_canvas_bounds() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)
    _, reset = _by_id(elements, "field-reload")
    assert reset.get("aria-label") == "Reset field view"
    assert 'href="/assets/icons/lucide/axignal-ui.svg#rotate-ccw"' in html
    assert "state.camera.zoom * 1.3" in script
    assert "state.camera.zoom / 1.3" in script
    assert "function resetFieldView()" in script
    assert "state.history = [organization]" in script
    assert "state.focus = organization" in script
    assert "$('#field-reload').addEventListener('click', resetFieldView)" in script
    assert ".minimap svg {\n  display: block;\n  width: 100%;\n  height: 100%;\n}" in css
    assert 'class="mm-bg"' not in html
    assert 'class="mini-window" id="minimap-window"' in html
    assert "const MINIMAP = { width: 160, height: 96, inset: 8 }" in script
    minimap_rules = re.findall(r"\.minimap\s*\{([^}]*)\}", css)
    assert any("background: #f0ebdf;" in rule for rule in minimap_rules)
    assert any("border: 1px solid var(--hair);" in rule for rule in minimap_rules)
    minimap_window_rules = re.findall(r"\.minimap \.mini-window\s*\{([^}]*)\}", css)
    assert len(minimap_window_rules) == 1
    assert "fill: transparent;" in minimap_window_rules[0]
    assert "stroke: none;" in minimap_window_rules[0]
    assert "pointer-events: none;" in minimap_window_rules[0]


def test_synthetic_field_controls_collapse_bottom_tab_and_expose_only_fixture_connections() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    script = (SUBSCRIBER / "app.js").read_text(encoding="utf-8")
    css = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    presentation = (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)

    _, section = _by_id(elements, "connection-section")
    assert "hidden" in section
    assert section.get("aria-hidden") is None
    _, labels_toggle = _by_id(elements, "labels-toggle")
    assert labels_toggle.get("type") == "button"
    assert labels_toggle.get("aria-controls") == "bottom-panel"
    assert labels_toggle.get("aria-expanded") == "true"
    assert "$('#labels-toggle').addEventListener('click'" in script
    assert "$('.bottom').classList.toggle('collapsed', state.bottomTabCollapsed)" in script
    assert "state.bottomTabCollapsed = !state.bottomTabCollapsed" in script
    assert ".bottom.collapsed .reader" in css
    assert ".field.labels-hidden .anch-lbl" not in css

    assert "edge.syntheticFixture === true" in script
    assert "edge.source === focusId || edge.target === focusId" in script
    assert "button.addEventListener('click', () => navigate(target.key))" in script
    assert "Synthetic links · demo" in presentation
    assert "Enlaces sintéticos · demo" in presentation
    assert "Synthetische Demo-Verbindungen" in presentation
    assert "合成デモの接続" in presentation
    assert "روابط تجريبية اصطناعية" in presentation


def test_branding_uses_authoritative_assets_and_reproducible_derivatives() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    elements = _Elements()
    elements.feed(html)
    image_sources = {attrs.get("src") for tag, attrs in elements.elements if tag == "img"}
    assert "/brand/logo-light.svg" in image_sources
    assert "/brand/isotope.svg" in image_sources
    assert 'href="/brand/favicon.svg"' in html
    assert 'href="/brand/favicon.ico"' in html
    assert "M -46 0 Q 0 -21 46 0" not in html

    manifest_path = SUBSCRIBER / "assets" / "brand" / "brand-assets.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["source_directory"] == "D:\\AXIGNAL\\LOGOS"
    assert manifest["rasterizer"].startswith("Chrome headless Canvas")

    records = {record["output_file"]: record for record in manifest["assets"]}
    assert set(records) == {
        "logo-light.svg",
        "logo-dark.svg",
        "isotope.svg",
        "favicon.svg",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "favicon.ico",
    }
    for filename, record in records.items():
        output = manifest_path.parent / filename
        content = output.read_bytes()
        assert hashlib.sha256(content).hexdigest() == record["output_sha256"]
        assert record["source_sha256"]

    for size in (16, 32):
        png = (manifest_path.parent / f"favicon-{size}x{size}.png").read_bytes()
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        assert int.from_bytes(png[16:20], "big") == size
        assert int.from_bytes(png[20:24], "big") == size

    ico = (manifest_path.parent / "favicon.ico").read_bytes()
    assert ico[:4] == b"\x00\x00\x01\x00"
    assert int.from_bytes(ico[4:6], "little") == 1
    assert ico[22:].startswith(b"\x89PNG\r\n\x1a\n")


def test_subscriber_icons_consume_the_canonical_lucide_grammar() -> None:
    sprite = (SUBSCRIBER / "assets" / "icons" / "lucide" / "axignal-ui.svg").read_text(
        encoding="utf-8"
    )
    license_text = (SUBSCRIBER / "assets" / "icons" / "lucide" / "LICENSE").read_text(
        encoding="utf-8"
    )
    stylesheet = (SUBSCRIBER / "subscriber.css").read_text(encoding="utf-8")
    design_system = (ROOT / "docs" / "design" / "DESIGN_SYSTEM.md").read_text(encoding="utf-8")

    symbols = re.findall(r'<symbol\b[^>]*stroke-width="([^"]+)"', sprite)
    assert len(symbols) == 15
    assert set(symbols) == {"1.5"}
    assert '<symbol id="send"' in sprite
    assert "ISC License" in license_text
    assert "The MIT License (MIT)" in license_text
    assert "## Canonical iconography" in design_system
    assert "normalized 1.5px stroke" in design_system
    assert "ICONOGRAPHY_AUTHORITY_V1" not in design_system
    assert not (ROOT / "docs" / "design" / "ICONOGRAPHY_AUTHORITY_V1.md").exists()

    icon_rules = re.findall(r"([^{}]+)\{([^{}]*)\}", stylesheet)
    for selector, declarations in icon_rules:
        if ".ax-icon" not in selector:
            continue
        sizes = re.findall(r"(?:width|height):\s*([^;]+);", declarations)
        assert all(size.strip() in {"1em", "16px", "20px"} for size in sizes)
