"""Presentation-boundary contracts for the P0-HFX-01 subscriber surface."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"


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
        if tag == "aside" and attrs.get("aria-label") == "AXENT cognitive navigator"
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
