"""FR-12 Subscriber Terminology and Locale Coherence contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIBER = ROOT / "apps" / "web" / "subscriber"
PRESENTATION = SUBSCRIBER / "presentation.js"
SPANISH = SUBSCRIBER / "locale-es.js"


def _catalog_keys(text: str) -> set[str]:
    return set(re.findall(r"'([\w.]+)'\s*:", text))


def test_spanish_complete_catalog_matches_english_contract() -> None:
    presentation = PRESENTATION.read_text(encoding="utf-8")
    english_section = presentation.split("// A deliberately partial", 1)[0]
    english_keys = _catalog_keys(english_section)
    spanish_keys = _catalog_keys(SPANISH.read_text(encoding="utf-8"))

    assert english_keys == spanish_keys
    assert len(english_keys) >= 160
    assert "es: SPANISH_COPY" in presentation
    assert "const SUPPORTED_LOCALES = Object.freeze(Object.keys(COMPLETE_COPY))" in presentation


def test_subscriber_chrome_preserves_product_words_and_hides_internal_ontology() -> None:
    english = PRESENTATION.read_text(encoding="utf-8")
    spanish = SPANISH.read_text(encoding="utf-8")
    visible_catalogs = "\n".join((english.split("// A deliberately partial", 1)[0], spanish))

    for product_word in ("AXIGNAL", "AXIGLAND", "Xeed", "AXENT"):
        assert product_word in visible_catalogs

    for internal_word in ("FAXT", "INXIGHT", "PATHX", "EvidenceAdmission"):
        assert internal_word not in visible_catalogs

    for english_control in (
        "Advanced controls",
        "More questions",
        "Why does this matter?",
        "Compare regions",
        "Current view",
        "Ask a question in this synthetic scenario",
    ):
        assert english_control not in spanish


def test_locale_selector_distinguishes_complete_languages_from_layout_previews() -> None:
    html = (SUBSCRIBER / "index.html").read_text(encoding="utf-8")
    presentation = PRESENTATION.read_text(encoding="utf-8")

    assert '<script src="/locale-es.js" defer></script>' in html
    assert '<option value="es" data-copy="locale.es">Español</option>' in html
    assert "Deutsch · layout preview" in html
    assert "日本語 · layout preview" in html
    assert "العربية · layout preview" in html
    assert "English and Spanish are complete interface languages" in presentation
    assert "new Set([...SUPPORTED_LOCALES, ...Object.keys(LOCALE_STRESS_COPY)])" in presentation


def test_agency_audience_is_preserved_without_redefining_subscriber_chrome() -> None:
    landing = (ROOT / "docs" / "product" / "AXIGNAL_PUBLIC_LANDING_PAGE_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    subscriber = "\n".join(
        (
            (SUBSCRIBER / "presentation.js").read_text(encoding="utf-8"),
            (SUBSCRIBER / "locale-es.js").read_text(encoding="utf-8"),
        )
    )

    assert "SEO, GEO, AEO and AIO agencies are a first-class acquisition audience" in landing
    assert "SEO/GEO" not in subscriber
    assert "AEO" not in subscriber
