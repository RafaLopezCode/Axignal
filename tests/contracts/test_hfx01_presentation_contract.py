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
    assert (
        "$('#axent-composer').addEventListener('submit', (event) => event.preventDefault())"
        in script
    )


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
