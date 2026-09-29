"""Contracts for the public AXIGNAL landing runtime."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANDING = ROOT / "apps" / "web" / "landing"
HTML = (LANDING / "index.html").read_text(encoding="utf-8")
DATA = json.loads((LANDING / "storyboard-data.json").read_text(encoding="utf-8"))


def test_public_landing_is_a_fifteen_chapter_runtime_not_a_review_fixture() -> None:
    assert len(DATA) == 15
    assert [chapter["n"] for chapter in DATA] == list(range(1, 16))
    assert "Storyboard V2 Review" not in HTML
    assert "Observe the economic world from the outside" in HTML
    assert 'data-jump="14"' in HTML
    assert 'data-jump="15"' in HTML


def test_runtime_preserves_xeed_xignal_commercial_semantics() -> None:
    serialized = json.dumps(DATA, ensure_ascii=False)
    assert "Start with one Xeed." in serialized
    assert "Empieza con una Xeed." in serialized
    assert "€9.95/month includes one Xeed." in serialized
    assert "9,95 €/mes incluye una Xeed." in serialized
    assert "One Xeed can produce many Xignals." in serialized
    assert "Una Xeed puede producir muchos Xignals." in serialized
    assert "€4.95/month per additional Xeed" in serialized
    assert "4,95 €/mes por cada Xeed adicional" in serialized


def test_six_locales_are_present_for_every_chapter() -> None:
    for chapter in DATA:
        for locale in ("en", "es", "fr", "de", "it", "pt"):
            assert locale in chapter, f"chapter {chapter['n']} missing {locale}"
            assert chapter[locale], f"chapter {chapter['n']} has empty {locale}"


def test_every_runtime_artwork_reference_exists_and_is_governance_sized() -> None:
    refs: set[str] = set()
    for chapter in DATA:
        refs.add(chapter["image"])
        refs.update(chapter.get("responsiveImages", {}).values())
    assert len(refs) == 17
    for ref in refs:
        path = LANDING / ref
        assert path.is_file(), ref
        assert path.stat().st_size <= 2 * 1024 * 1024, ref


def test_runtime_uses_canonical_typography_and_brand_assets() -> None:
    assert "--ax-font-display:'Fraunces'" in HTML
    assert "--ax-font-body:'Inter'" in HTML
    assert "--ax-font-mono:'IBM Plex Mono'" in HTML
    assert "./assets/brand/logo-dark.svg" in HTML
    assert (LANDING / "assets" / "brand" / "logo-dark.svg").is_file()
    assert (LANDING / "assets" / "favicon.svg").is_file()


def test_accessible_navigation_and_reduced_motion_are_structural_contracts() -> None:
    assert 'aria-label="Primary"' in HTML
    assert 'aria-haspopup="listbox"' in HTML
    assert "prefers-reduced-motion:reduce" in HTML
    assert "addEventListener('wheel',onWheel,{passive:false})" in HTML
    assert "addEventListener('touchstart'" in HTML
    assert "addEventListener('keydown'" in HTML
    assert "aria-current" in HTML


def test_pricing_is_specific_and_xignals_are_not_billable_units() -> None:
    assert "9,95 €" in HTML
    assert "+4,95 €" in HTML
    assert "The Xignals that germinate from your Xeeds are not billable units." in HTML
    assert "Los Xignals que germinan de tus Xeeds no son unidades facturables." in HTML
