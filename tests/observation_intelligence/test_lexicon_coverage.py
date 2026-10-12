"""The deterministic lexicon recognizes what real organizations say they do.

The sentences are the self-descriptions published by real websites, observed in the
subscriber audit of 2026-10-12. Before catalog .5 the lexicon had five entries and none of
these organizations had an established activity. A match stays a POTENTIAL hypothesis with
its exact sentence; these tests only fix what is recognized and in which order.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from application.first_observation.activity import MAX_LEXICON_FINDINGS, deterministic_activity
from application.first_observation.site import read_page
from application.observation_intelligence.catalog import CAPABILITY_LEXICON
from application.observation_intelligence.understanding import detect_capabilities
from domain.xignal import XignalEpistemicState

NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)

OBSERVED = {
    "ventilation-systems": "Design, manufacturing and installation of underground ventilation "
    "systems for road, rail, metro tunnels and mining, since 1963.",
    "food-retail": "Empieza tu compra online en Mercadona, encuentra nuestros supermercados más "
    "cercanos o descubre cómo trabajar con nosotros",
    "legal-services": "Garrigues es una firma internacional de servicios legales que asesora a "
    "nivel local y global desde todos los ángulos del derecho de los negocios.",
    "formwork-scaffolding": "International company specialising in the development and "
    "distribution of formwork & scaffolding.",
    "automotive-components": "Gestamp is an international group dedicated to the design, "
    "development and manufacture of metal automotive components.",
    "energy-supply": "Somos tu compañía de luz, gas y placas solares - Holaluz",
}


def _ids(text: str) -> list[str]:
    return [
        h.capability_id
        for h in detect_capabilities(
            text=text, observation_id="o", source_ref="https://example.org/", observed_at=NOW
        )
    ]


@pytest.mark.parametrize(("expected", "sentence"), list(OBSERVED.items()))
def test_real_self_descriptions_are_recognized(expected: str, sentence: str) -> None:
    assert _ids(sentence)[0] == expected


def test_a_match_is_potential_and_cites_its_sentence() -> None:
    (hypothesis, *_) = detect_capabilities(
        text=OBSERVED["legal-services"], observation_id="o", source_ref="https://g.example/",
        observed_at=NOW,
    )  # fmt: skip
    assert hypothesis.state is XignalEpistemicState.POTENTIAL
    assert "servicios legales" in hypothesis.basis[0].excerpt


def test_what_the_page_leads_with_comes_first_and_passing_mentions_are_bounded() -> None:
    html = (
        "<html><head><title>Limpiezas Norte</title><meta name='description' content="
        "'Empresa de limpieza de oficinas en Bilbao.'></head><body><p>Servicios de limpieza, "
        "gestión de residuos, mantenimiento de instalaciones, seguridad privada y "
        "jardinería.</p></body></html>"
    )
    page = read_page(
        url="https://limpiezas.example/", html=html, observed_at=NOW,
        content_fingerprint="sha256:test", artifact_ref=None,
    )  # fmt: skip
    findings = deterministic_activity([page])
    assert findings[0].activity_id == "cleaning-services"
    assert len(findings) <= MAX_LEXICON_FINDINGS


def test_text_with_no_declared_activity_stays_unestablished() -> None:
    assert (
        _ids("Política de privacidad. Aviso legal. Cookies. Contacto. Trabaja con nosotros.") == []
    )


def test_catalog_entries_are_unique_and_route_only_through_valid_codes() -> None:
    ids = [entry.capability_id for entry in CAPABILITY_LEXICON]
    assert len(ids) == len(set(ids))
    for entry in CAPABILITY_LEXICON:
        assert entry.terms and all(term == term.strip() and len(term) >= 4 for term in entry.terms)
        for code in entry.demand_codes:
            if code.scheme == "CPV":
                assert re.fullmatch(r"\d{8}", code.code), (entry.capability_id, code.code)
