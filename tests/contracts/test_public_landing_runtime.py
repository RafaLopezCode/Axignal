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


def test_runtime_preserves_organization_signal_commercial_semantics() -> None:
    serialized = json.dumps(DATA, ensure_ascii=False)
    assert "Start with one organization." in serialized
    assert "Empieza con una organización." in serialized
    assert "€9.95/month includes one organization." in serialized
    assert "9,95 €/mes incluye una organización." in serialized
    assert "AXIGNAL can surface many signals around one organization." in serialized
    assert "AXIGNAL puede hacer emerger muchas señales alrededor de una organización." in serialized
    assert "€4.95/month per additional organization" in serialized
    assert "4,95 €/mes por cada organización adicional" in serialized


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


def test_pricing_is_specific_and_signals_are_not_billable_units() -> None:
    assert "9,95 €" in HTML
    assert "+4,95 €" in HTML
    assert "Signals surfaced around your organizations are not billable units." in HTML
    assert (
        "Las señales que emergen alrededor de tus organizaciones no son unidades facturables."
        in HTML
    )


def test_public_ctas_never_dead_end_or_fake_account_runtime() -> None:
    assert 'id="loginButton"' in HTML
    assert 'id="accessDialog"' in HTML
    assert "function openAccessDialog()" in HTML
    assert "'1:Primary CTA':()=>goTo(15,1)" in HTML
    assert "'1:Secondary CTA':()=>goTo(2,1)" in HTML
    assert "'5:Primary CTA':()=>goTo(15,1)" in HTML
    assert "'7:Primary CTA':openEvidenceDialog" in HTML
    assert 'id="evidenceDialog"' in HTML
    assert "function openEvidenceDialog()" in HTML
    assert "persisted supporting context" in HTML
    assert "does not fabricate a live company evidence trace" in HTML
    assert "'15:Primary CTA':openAccessDialog" in HTML
    assert "'15:Secondary CTA':()=>goTo(7,-1)" in HTML
    assert "placeholder checkout or fake account flow" in HTML


def test_public_landing_has_indexable_metadata_and_real_robots_file() -> None:
    assert '<link rel="canonical" href="https://axignal.com/">' in HTML
    assert '<meta property="og:title"' in HTML
    assert 'width="166" height="42"' in HTML
    robots = (LANDING / "robots.txt").read_text(encoding="utf-8")
    assert robots == "User-agent: *\nAllow: /\n"


def test_public_header_exposes_governed_knowledge_surface() -> None:
    assert 'href="../knowledge/" data-label="knowledge"' in HTML
    assert "knowledge:'Knowledge'" in HTML
    knowledge = (LANDING.parent / "knowledge" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="/knowledge/">' in knowledge
    assert "CANONICAL KNOWLEDGE" in knowledge
    assert "EDITORIAL INTELLIGENCE" in knowledge
    assert "DISCOVERY SURFACES" in knowledge
    assert "No doorway pages." in knowledge


def test_global_pagination_does_not_hijack_interactive_controls() -> None:
    assert "function isInteractiveTarget(target)" in HTML
    assert "if(isInteractiveTarget(e.target)||!localeList.hidden||!chapterMenu.hidden" in HTML
    assert (
        "if(accessDialog.open||evidenceDialog.open||footerSheet.open||isInteractiveTarget(e.target)) return;"
        in HTML
    )
    assert "isScrollableCopyTarget(e.target)" in HTML
    assert "touchY=(isInteractiveTarget(e.target)||isScrollableCopyTarget(e.target))" in HTML


def test_fr28_landing_promise_matches_demonstrated_runtime_boundaries() -> None:
    by_id = {chapter["id"]: chapter for chapter in DATA}
    serialized = json.dumps(DATA, ensure_ascii=False)

    dri = by_id["DIGITAL_REPRESENTATION"]["en"]
    assert "When those surfaces are measured" in dri["Body"]
    assert "without pretending to see the whole Internet" in dri["Body"]
    assert "Representation is not reality" in dri["Value line"]
    assert (
        "AXIGNAL independently observes how an organization appears across search" not in serialized
    )

    axent = by_id["AXENT"]["en"]
    assert "challenge your interpretation" in axent["Body"]
    assert "cannot turn a user statement into truth" in axent["Body"]
    assert axent["Value line"] == "Friendly to you. Loyal to the evidence."

    use_cases = by_id["USE_CASES"]["en"]
    assert "Leadership, sales and business development" in use_cases["Body"]
    assert "SEO, GEO, AEO and AIO agencies" in use_cases["Body"]
    assert "when those surfaces are actually observed" in use_cases["Body"]
    assert (
        use_cases["Value line"]
        == "Your role changes the question. It does not change the evidence."
    )

    start = by_id["START"]["en"]["Body"]
    assert "a signal surfaces" in start
    assert "follow the evidence" in start
    assert "decide whether the change matters to you" in start


def test_fr28_landing_preserves_signal_not_conclusion_and_condition_bound_dri() -> None:
    by_id = {chapter["id"]: chapter for chapter in DATA}
    evidence = by_id["EVIDENCE"]
    signal_terms = {
        "en": "signal",
        "es": "señal",
        "fr": "signal",
        "de": "Signal",
        "it": "segnale",
        "pt": "sinal",
    }
    for locale, signal_term in signal_terms.items():
        assert signal_term in evidence[locale]["Headline"]
        assert "Xignal" not in evidence[locale]["Headline"]

    dri = by_id["DIGITAL_REPRESENTATION"]
    for locale in ("en", "es", "fr", "de", "it", "pt"):
        body = dri[locale]["Body"]
        assert body.strip()
        assert dri[locale]["Value line"].strip()

    serialized = json.dumps(DATA, ensure_ascii=False)
    assert "guaranteed opportunity" not in serialized.lower()
    assert "predict who will buy" not in serialized.lower()
    assert "whole Internet" in serialized


def test_mobile_header_is_a_real_navigation_surface_not_a_shrunk_desktop_header() -> None:
    assert 'id="mobileMenuToggle"' in HTML
    assert 'aria-controls="mobileMenu"' in HTML
    assert 'id="mobileMenu" hidden' in HTML
    assert 'class="mobile-menu-nav"' in HTML
    assert 'class="login mobile-login"' in HTML
    assert 'data-mobile-locale="es"' in HTML
    assert ".main-nav,.header-actions{display:none}" in HTML
    assert ".mobile-menu-toggle{display:inline-flex" in HTML
    assert "function openMobileMenu()" in HTML
    assert "function closeMobileMenu(" in HTML
    assert "mobileMenuToggle.onclick=toggleMobileMenu" in HTML
    assert "document.querySelector('.mobile-login').onclick" in HTML


def test_mobile_storyboard_uses_dynamic_viewport_and_safe_copy_floor() -> None:
    assert "height:100dvh" in HTML
    assert "min-height:100svh" in HTML
    assert "env(safe-area-inset-bottom)" in HTML
    assert "max-height:calc(100dvh - 154px)" in HTML
    assert "overscroll-behavior:contain" in HTML


def test_logo_is_a_real_home_control() -> None:
    assert 'id="brandHome" href="./"' in HTML
    assert "$('brandHome').addEventListener('click'" in HTML
    assert "if(chapter!==1)" in HTML
    assert "chapter=1;" in HTML
    assert "renderStable();" in HTML


def test_mobile_home_supports_explicit_pull_down_reload() -> None:
    assert "if(chapter===1&&innerWidth<=900&&dy>=96){location.reload();return}" in HTML


def test_collapsed_footer_opens_legal_bottom_sheet() -> None:
    assert 'id="footerTab"' in HTML
    assert 'id="footerSheet"' in HTML
    assert 'class="footer-sheet"' in HTML
    assert "footerTab.onclick=openFooterSheet" in HTML
    assert "footerSheet.showModal()" in HTML
    assert 'href="./legal/privacidad-rgpd/"' in HTML
    assert 'href="./legal/cookies/"' in HTML
    assert 'href="./legal/terminos/"' in HTML
    assert 'href="./legal/accesibilidad/"' in HTML


def test_public_legal_surfaces_exist_and_do_not_invent_controller_identity() -> None:
    legal = LANDING / "legal"
    required = {
        "index.html",
        "aviso-legal/index.html",
        "privacidad-rgpd/index.html",
        "cookies/index.html",
        "terminos/index.html",
        "accesibilidad/index.html",
    }
    for relative in required:
        assert (legal / relative).is_file(), relative

    privacy = (legal / "privacidad-rgpd" / "index.html").read_text(encoding="utf-8")
    notice = (legal / "aviso-legal" / "index.html").read_text(encoding="utf-8")
    cookies = (legal / "cookies" / "index.html").read_text(encoding="utf-8")

    assert "RGPD / GDPR" in privacy
    assert "identidad y datos de contacto del responsable" in privacy
    assert "finalidades y base jurídica" in privacy
    assert "transferencias internacionales" in privacy
    assert "derechos de acceso, rectificación, supresión" in privacy
    assert "Agencia Española de Protección de Datos" in privacy
    assert "PENDIENTE DE CONFIRMACIÓN" in notice
    assert "NIF/CIF" in notice
    assert "axignal.storyboard.locale" in cookies
    assert "no instala cookies publicitarias ni de analítica" in cookies


def test_public_knowledge_uses_production_root_routes() -> None:
    knowledge = (LANDING.parent / "knowledge" / "index.html").read_text(encoding="utf-8")
    assert "../landing/" not in knowledge
    assert 'href="/"' in knowledge
    assert 'src="/assets/brand/logo-dark.svg"' in knowledge
    assert 'href="/?c=4"' in knowledge
    assert 'href="/?c=7"' in knowledge
    assert 'href="/?c=14"' in knowledge


def test_public_interaction_states_do_not_leak_browser_teal() -> None:
    legal_css = (LANDING / "legal" / "legal.css").read_text(encoding="utf-8")
    knowledge = (LANDING.parent / "knowledge" / "index.html").read_text(encoding="utf-8")

    for surface in (HTML, legal_css, knowledge):
        lowered = surface.lower()
        assert "-webkit-tap-highlight-color:transparent" in lowered
        assert "#2f6b62" not in lowered
        assert "teal" not in lowered
        assert "cyan" not in lowered
        assert "a:visited{color:inherit}" in lowered

    assert "a:focus-visible,button:focus-visible{outline:1.5px solid var(--ax-brass)" in HTML
    assert "a:active,button:active{opacity:.78}" in HTML
    assert "a:focus-visible{outline:1.5px solid var(--brass)" in legal_css
    assert "a:active{opacity:.78}" in legal_css
