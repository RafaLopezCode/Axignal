"""The representation audit states what it saw on the site, where, and why it matters."""

from __future__ import annotations

from datetime import UTC, datetime

from application.first_observation.representation_audit import (
    SiteExtras,
    Status,
    audit_representation,
    crawler_access,
    parse_sitemap,
)
from application.first_observation.site import RobotsReading, read_page

NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)

GOOD = (
    """<html lang="es"><head><title>Ventilación de túneles · Apex Ingeniería</title>
<meta name="description" content="Diseño, fabricación e instalación de sistemas de ventilación para túneles, metro y minería desde 1963.">
<meta name="viewport" content="width=device-width"><link rel="canonical" href="https://apex.example/">
<meta property="og:title" content="Apex"><meta property="og:description" content="Ventilación">
<meta property="og:image" content="https://apex.example/og.png">
<script type="application/ld+json">{"@type":"Organization","name":"Apex","url":"https://apex.example/",
"logo":"https://apex.example/l.png","sameAs":["https://www.linkedin.com/company/apex","https://es.wikipedia.org/wiki/Apex"],
"address":{"@type":"PostalAddress","addressCountry":"ES"},"telephone":"+34 900 000 000"}</script>
<script type="application/ld+json">{"@type":"Service","name":"Ventilación de túneles"}</script>
</head><body><h1>Ventilación de túneles</h1><img src="a.png" alt="Ventilador">
"""
    + "".join(
        f"<p>Proyecto {i}: ventilación industrial para túneles y minería.</p>" for i in range(60)
    )
    + """</body></html>"""
)

BAD = """<html><head><title>Inicio</title><script type="application/ld+json">{broken</script></head>
<body><h1>Uno</h1><h1>Dos</h1><img src="a.png"><img src="b.png"></body></html>"""


def _page(html: str, url: str = "https://apex.example/"):  # type: ignore[no-untyped-def]
    return read_page(
        url=url, html=html, observed_at=NOW, content_fingerprint="sha256:x", artifact_ref=None
    )


def _by_id(audit):  # type: ignore[no-untyped-def]
    return {c.check_id: c for c in audit.checks}


def test_a_well_declared_site_passes_with_evidence_and_no_score() -> None:
    robots = RobotsReading(
        "User-agent: *\nAllow: /\nSitemap: https://apex.example/sitemap.xml\n", NOW
    )
    audit = audit_representation(
        [_page(GOOD)], robots, SiteExtras("https://apex.example/sitemap.xml", 40, "2026-10-01", True),
        activity_found=True,
    )  # fmt: skip
    checks = _by_id(audit)
    for check_id in (
        "SEARCH_CRAWLERS_ALLOWED", "AI_CRAWLERS_ALLOWED", "ORGANIZATION_DECLARED",
        "ORGANIZATION_COMPLETE", "ENTITY_PROFILES_LINKED", "OFFER_DECLARED", "ONE_H1_PER_PAGE",
        "MOBILE_VIEWPORT", "SOCIAL_PREVIEW_TAGS", "SITEMAP_READABLE", "LLMS_TXT_PUBLISHED",
        "HOMEPAGE_TEXT_DEPTH", "STRUCTURED_DATA_PARSES",
    ):  # fmt: skip
        assert checks[check_id].status is Status.PASS, check_id
    assert "score" not in str(audit.to_wire()).lower()


def test_a_poorly_declared_site_gets_ordered_attention_items() -> None:
    robots = RobotsReading("User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n", NOW)
    audit = audit_representation(
        [_page(BAD)], robots, SiteExtras(llms_txt=False), activity_found=True
    )
    checks = _by_id(audit)
    assert checks["AI_CRAWLERS_ALLOWED"].status is Status.ATTENTION
    assert checks["AI_CRAWLERS_ALLOWED"].value["blocked"] == ["GPTBot"]  # type: ignore[index]
    assert checks["SEARCH_CRAWLERS_ALLOWED"].status is Status.PASS
    assert checks["ONE_H1_PER_PAGE"].status is Status.ATTENTION
    assert checks["STRUCTURED_DATA_PARSES"].value == 1
    assert checks["IMAGES_DESCRIBED"].value == {"images": 2, "withoutAlt": 2}
    assert checks["HOMEPAGE_CANONICAL_SAME_SITE"].status is Status.ATTENTION
    impacts = [c.impact.value for c in audit.attention()]
    assert impacts == sorted(impacts, key=["HIGH", "MEDIUM", "LOW"].index)


def test_what_was_not_read_is_unknown_never_a_failure() -> None:
    audit = audit_representation([_page(GOOD)], None, SiteExtras(), activity_found=False)
    checks = _by_id(audit)
    assert checks["AI_CRAWLERS_ALLOWED"].status is Status.UNKNOWN
    assert checks["LLMS_TXT_PUBLISHED"].status is Status.UNKNOWN
    assert checks["SITEMAP_DECLARED"].status is Status.UNKNOWN


def test_crawler_access_and_sitemap_parsing() -> None:
    assert crawler_access(RobotsReading(None, NOW), "https://a.example/")["ClaudeBot"] == "ALLOWED"
    body = b"""<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://a.example/</loc><lastmod>2026-09-01</lastmod></url>
    <url><loc>https://a.example/b</loc><lastmod>2026-10-02</lastmod></url></urlset>"""
    assert parse_sitemap(body) == (2, "2026-10-02")
