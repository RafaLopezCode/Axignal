"""A home country needs two independent signals the website itself publishes."""

from __future__ import annotations

from datetime import UTC, datetime

from application.first_observation.country_evidence import country_evidence
from application.first_observation.site import read_page
from application.world_demand.live import _without_duplicates

NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)


def _page(html: str, url: str):  # type: ignore[no-untyped-def]
    return read_page(
        url=url, html=html, observed_at=NOW, content_fingerprint="x", artifact_ref=None
    )


def test_domain_and_phone_point_to_spain() -> None:
    page = _page(
        "<html lang='es'><body><p>Llámanos: +34 912 345 678</p></body></html>", "https://pyme.es/"
    )
    evidence = country_evidence([page])
    assert evidence is not None and evidence.scope.code == "EU/ES"
    assert {s.kind for s in evidence.signals} == {"DOMAIN", "PHONE_PREFIX"}


def test_a_com_site_with_language_region_and_tax_id() -> None:
    page = _page(
        "<html lang='es-ES'><body><p>Grupo Ejemplo S.L. CIF: B12345678</p></body></html>",
        "https://grupo-ejemplo.com/",
    )
    evidence = country_evidence([page])
    assert evidence is not None and evidence.country == "ES"


def test_one_signal_is_not_enough_and_conflicts_guess_nothing() -> None:
    assert (
        country_evidence(
            [_page("<html lang='es'><body><p>Hola</p></body></html>", "https://a.es/")]
        )
        is None
    )
    mixed = _page(
        "<html lang='pt-PT'><body><p>+351 210 000 000</p><p>+34 910 000 000</p></body></html>",
        "https://b.es/",
    )
    assert country_evidence([mixed]) is None  # Portugal and Spain both supported


def test_the_same_call_in_two_sources_is_shown_once_from_the_national_platform() -> None:
    placsp = {"buyer": "Ayuntamiento de Alhama", "deadline": "2026-11-05", "source": "es-placsp",
              "title": "Suministro de energía eléctrica a las dependencias municipales"}  # fmt: skip
    dash = f" {chr(0x2013)} "  # TED separates country and category with en dashes
    ted = {"buyer": "Ayuntamiento de Alhama", "deadline": "2026-11-05+01:00", "source": "ted-search-v3",
           "title": f"España{dash}Electricidad{dash}Suministro de energía eléctrica a las dependencias municipales"}  # fmt: skip
    other = {"buyer": "Ayuntamiento de Alhama", "deadline": "2026-11-05", "source": "es-placsp",
             "title": "Mantenimiento de alumbrado público"}  # fmt: skip
    kept = _without_duplicates([ted, placsp, other])
    assert [c["source"] for c in kept] == ["es-placsp", "es-placsp"]
