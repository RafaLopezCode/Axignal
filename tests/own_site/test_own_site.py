"""Own-site signals: technology, logo walls, credentials, hiring and reviews — any country."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from application.first_observation.site import PageReading, read_page
from application.own_site import own_site_discoveries

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
ORG = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Acme Ingeniería",
    "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4,7", "reviewCount": "212"},
}
JOB = {"@context": "https://schema.org", "@type": "JobPosting", "title": "Project engineer",
       "datePosted": "2026-10-01"}  # fmt: skip
PRODUCT = {"@type": "Product", "name": "Widget",
           "aggregateRating": {"@type": "AggregateRating", "ratingValue": "2", "reviewCount": "3"}}  # fmt: skip


def _page(body: str, head: str = "", url: str = "https://acme.example/") -> PageReading:
    html = f"<html lang='es'><head><title>Acme</title>{head}</head><body>{body}</body></html>"
    return read_page(
        url=url, html=html, observed_at=NOW, content_fingerprint="f", artifact_ref=None
    )


HOME = _page(
    head=(
        '<meta name="generator" content="WordPress 6.6.2">'
        '<script src="https://www.googletagmanager.com/gtag/js?id=G-1"></script>'
        '<script src="//js.hs-scripts.com/123.js"></script>'
        '<link rel="preconnect" href="https://js.stripe.com">'
        '<script src="https://acme.example/wp-content/app.js"></script>'
        f'<script type="application/ld+json">{json.dumps([ORG, JOB, PRODUCT])}</script>'
    ),
    body=(
        "<h2>Nuestros clientes</h2>"
        '<img alt="Logo Iberdrola" src="a.png"><img alt="Ferrovial" src="b.png">'
        '<img alt="logo" src="c.png"><img alt="Logo de Repsol" src="d.png">'
        '<img alt="Acme Ingeniería" src="e.png"><img alt="ACS" src="f.png">'
        "<h2>Partners tecnológicos</h2>"
        '<img alt="Autodesk"><img alt="Siemens"><img alt="Google Partner">'
        "<h2>Nuestro equipo</h2><img alt="
        '"María en obra"><img alt="Oficina"><img alt="Reunión"><img alt="Taller">'
        "<p>Empresa certificada ISO 9001:2015 e ISO 14001. También ISO 9001.</p>"
        '<a href="/trabaja-con-nosotros">Trabaja con nosotros</a>'
        '<a href="https://boards.greenhouse.io/acme">Ofertas</a>'
        '<a href="https://es.trustpilot.com/review/acme.example">Opiniones</a>'
    ),
)


def _by(code: str) -> list[dict[str, object]]:
    found = own_site_discoveries([HOME], ["Acme Ingeniería"])
    return [d.to_wire() for d in found if d.code == code]


def test_technology_suppliers_are_observed_from_loaded_code_not_own_host() -> None:
    tech = {str(d["statement"]): d for d in _by("TECHNOLOGY_SUPPLIER_OBSERVED")}
    assert {"Google Tag Manager", "HubSpot", "Stripe", "WordPress"} <= set(tech)
    assert all(d["epistemicState"] == "OBSERVED" for d in tech.values())
    assert tech["Stripe"]["detail"]["category"] == "PAYMENTS"  # type: ignore[index]
    assert "contract" in str(tech["HubSpot"]["detail"]["limitation"])  # type: ignore[index]
    assert "acme.example" not in HOME.signals["resourceHosts"]  # type: ignore[operator]


def test_logo_walls_name_declared_clients_and_partners_never_itself_or_generic() -> None:
    clients = [d["statement"] for d in _by("CLIENT_DECLARED")]
    assert clients == ["Iberdrola", "Ferrovial", "Repsol", "ACS"]
    partners = [d["statement"] for d in _by("PARTNER_DECLARED")]
    assert partners == ["Autodesk", "Siemens", "Google Partner"]
    assert all(d["epistemicState"] == "DECLARED" for d in _by("CLIENT_DECLARED"))
    # Team photos are not a client wall, whatever their number.
    assert "Oficina" not in clients


def test_credentials_are_claims_deduplicated() -> None:
    claims = [d["statement"] for d in _by("CERTIFICATION_CLAIMED")]
    assert claims[:2] == ["ISO 9001:2015", "ISO 14001"]
    assert "Google Partner" in claims
    assert len([c for c in claims if str(c).startswith("ISO 9001")]) <= 2


def test_hiring_signals_and_reviews_are_its_own_voice() -> None:
    jobs = _by("JOB_POSTINGS_PUBLISHED")[0]
    assert jobs["statement"] == "1" and jobs["detail"]["titles"] == ["Project engineer"]  # type: ignore[index]
    channel = _by("HIRING_CHANNEL_PUBLISHED")[0]
    assert channel["detail"]["hiringVendors"] == ["Greenhouse"]  # type: ignore[index]
    assert str(channel["detail"]["careersPage"]).endswith("/trabaja-con-nosotros")  # type: ignore[index]
    assert [d["statement"] for d in _by("REVIEW_PROFILE_LINKED")] == ["Trustpilot"]
    rating = _by("RATING_SELF_PUBLISHED")[0]
    assert rating["statement"] == "4.7/5.0"  # the organization's rating, not its product's
    assert "not an independent" in str(rating["detail"]["limitation"])  # type: ignore[index]


def test_a_plain_page_yields_nothing_and_pages_from_earlier_readers_are_safe() -> None:
    assert own_site_discoveries([_page("<p>Hola</p>")]) == []
    assert own_site_discoveries([HOME.metadata_only()]) == []
    assert own_site_discoveries([]) == []


def test_certification_walls_are_credentials_and_customer_experience_is_no_client_wall() -> None:
    page = _page(
        "<h2>Nuestras Certificaciones</h2>"
        '<img alt="Applus ISO 27001 System Certification"><img alt="Aenor Accesibilidad TIC">'
        '<img alt="inicio"><img alt="Applus SOC2 System Certification">'
        "<h2>La mejor alarma en experiencia cliente</h2>"
        '<img alt="Trustpilot"><img alt="Google"><img alt="Cinco estrellas">'
        '<img alt="Icono angulo izquierda"><img alt="Mejor Proyecto Experiencia de cliente 2025">'
    )
    found = [d.to_wire() for d in own_site_discoveries([page])]
    assert not [d for d in found if d["kind"] == "RELATIONSHIP"]
    claims = [d["statement"] for d in found if d["kind"] == "CREDENTIAL"]
    assert claims == ["ISO 27001", "Aenor Accesibilidad TIC", "SOC2"]  # page order


def test_badges_awards_and_social_links_under_a_clients_heading_are_not_clients() -> None:
    from application.own_site import logo_walls

    # Golden set 2026-10-14: an agency's "trusted by" wall of badges, a footer of social links.
    badges = _page(
        "<h2>Trusted by</h2>"
        '<img alt="Google Partner"><img alt="BBB A+ rating"><img alt="Inc. 5000 honoree, 10 years">'
        '<img alt="Meta Business Partner"><img alt="DesignRush review"><img alt="Brooklinen">'
        "<h2>Our customers</h2>"
        '<img alt="Visit our Facebook page"><img alt="View our Instagram profile">'
        '<img alt="Visit our LinkedIn page"><img alt="Outils adaptés au RGPD">'
    )
    assert not logo_walls([badges])
    mixed = _page(
        "<h2>Our customers</h2>"
        '<img alt="HP"><img alt="Amazon"><img alt="Scotiabank"><img alt="Kempinski">'
        '<img alt="Best of 2025 award">'
    )
    assert [d.statement for d in logo_walls([mixed])] == ["HP", "Amazon", "Scotiabank", "Kempinski"]


def test_decorative_images_marked_with_empty_alt_are_described() -> None:
    page = _page(
        '<img src="logo.svg" alt=""><img src="x.png" role="presentation">'
        '<img src="y.png" aria-hidden="true"><img src="z.png" alt="Team at work"><img src="w.png">'
    )
    assert page.signals["images"] == 5
    assert page.signals["imagesWithoutAlt"] == 1  # only the one with no alt attribute at all
