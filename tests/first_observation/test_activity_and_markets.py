"""Activity and Markets from the client's own website (spec 096).

Measured on 20 typical agency clients (2026-10-18): Activity had data for 5 of 20 (only a
hiring channel) and Markets for 10 of 20. Their own sites declare both: a news feed (what
they publish and how often) and versions per country (where they say they sell).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from application.first_observation.publications import cadence, own_feed, parse_feed
from application.first_observation.site_markets import versions_for_countries
from tests.first_observation import harness
from tests.first_observation.harness import SOLAR_ES, World, build, discoveries, runtime
from tests.first_observation.test_first_observation_e2e import _attend, _pending_id, _view

NOW = datetime(2026, 10, 18, tzinfo=UTC)
RSS = (
    "<?xml version='1.0'?><rss version='2.0'><channel><title>Blog</title>"
    "<item><title>Nueva planta de autoconsumo en Getafe</title><link>/blog/getafe</link>"
    "<pubDate>Mon, 13 Oct 2026 10:00:00 +0200</pubDate></item>"
    "<item><title>Ayudas 2026</title><link>https://solaria-norte.example.com/blog/ayudas</link>"
    "<pubDate>Thu, 10 Sep 2026 09:00:00 GMT</pubDate></item>"
    "<item><title>Old news</title><link>/blog/old</link>"
    "<pubDate>Tue, 01 Oct 2024 09:00:00 GMT</pubDate></item>"
    "</channel></rss>"
)
ATOM = (
    "<feed xmlns='http://www.w3.org/2005/Atom'><entry><title>Launch</title>"
    "<link href='https://brand.example/news/launch'/><updated>2026-10-01T08:00:00Z</updated>"
    "</entry></feed>"
)


def test_rss_and_atom_items_are_read_newest_first_with_dates_only() -> None:
    items = parse_feed(RSS.encode(), SOLAR_ES)
    assert [i["title"] for i in items] == [
        "Nueva planta de autoconsumo en Getafe",
        "Ayudas 2026",
        "Old news",
    ]
    assert items[0]["url"] == SOLAR_ES + "blog/getafe" and set(items[0]) == {
        "title",
        "url",
        "publishedAt",
    }
    assert parse_feed(ATOM.encode(), "https://brand.example/")[0]["title"] == "Launch"
    assert parse_feed(b"<html>not a feed", SOLAR_ES) == []


def test_pace_counts_recent_publications_and_a_quiet_channel_says_when() -> None:
    pace = cadence(parse_feed(RSS.encode(), SOLAR_ES), NOW)
    assert (pace["last30Days"], pace["last90Days"], pace["last365Days"]) == (1, 2, 2)
    assert str(pace["lastPublishedAt"]).startswith("2026-10-13")
    quiet = cadence([{"publishedAt": "2024-01-01T00:00:00+00:00"}], NOW)
    assert quiet["last365Days"] == 0 and quiet["lastPublishedAt"] == "2024-01-01T00:00:00+00:00"


def test_only_its_own_feed_counts_never_comments_or_another_host() -> None:
    assert (
        own_feed(["/feed/", "/comments/feed/"], "https://www.brand.com/")
        == "https://www.brand.com/feed/"
    )
    assert (
        own_feed(["https://blog.brand.com/rss"], "https://brand.com/")
        == "https://blog.brand.com/rss"
    )
    assert own_feed(["https://feeds.other.com/brand"], "https://brand.com/") is None


@pytest.mark.parametrize(
    ("hreflang", "hosts", "links", "expected"),
    [
        (["es-es", "fr-fr", "en-gb", "x-default"], [], [], {"ES", "FR", "GB"}),
        (["en", "es", "es-419"], [], [], set()),  # languages name no country
        (
            [],
            [],
            ["https://brand.com/de-de/shop", "/it_it/", "https://other.com/fr-fr/"],
            {"DE", "IT"},
        ),
        ([], ["brand.fr", "www.brand.de", "brand.co", "other.de"], [], {"FR", "DE"}),
        (["en-uk"], [], [], {"GB"}),
    ],
)
def test_country_versions_come_from_tags_paths_and_brand_domains(
    hreflang: list[str], hosts: list[str], links: list[str], expected: set[str]
) -> None:
    assert set(versions_for_countries("https://www.brand.com/", hreflang, hosts, links)) == expected


def test_a_client_site_gives_activity_and_markets_from_minute_zero(
    tmp_path: Path, monkeypatch: Any
) -> None:
    home = harness.PAGES[SOLAR_ES].replace(
        "</head>",
        "<link rel='alternate' type='application/rss+xml' href='/feed/'>"
        "<link rel='alternate' hreflang='es-es' href='https://solaria-norte.example.com/'>"
        "<link rel='alternate' hreflang='pt-pt' href='https://solaria-norte.example.com/pt-pt/'>"
        "</head>",
    )
    monkeypatch.setitem(harness.PAGES, SOLAR_ES, home)
    monkeypatch.setitem(harness.PAGES, SOLAR_ES + "feed/", RSS)
    world = World()
    facade = build(tmp_path, world)
    token, _added = _attend(facade, tmp_path, "subject:activity-markets", SOLAR_ES)
    assert runtime(facade).drain() == 1
    view = _view(facade, token, _pending_id(facade, token))
    assert SOLAR_ES + "feed/" in world.sites.requests  # one more request, within the budget
    (pace,) = [
        d for d in discoveries(view, "OPERATING_SIGNAL") if d["code"] == "PUBLISHING_CADENCE"
    ]
    assert pace["epistemicState"] == "OBSERVED" and pace["detail"]["feed"] == SOLAR_ES + "feed/"
    own = [d for d in discoveries(view, "MENTION") if d["code"] == "OWN_PUBLICATION"]
    assert own and own[0]["statement"] == "Nueva planta de autoconsumo en Getafe"
    (versions,) = [
        d
        for d in discoveries(view, "DECLARED_SERVICE_AREA")
        if d["code"] == "SITE_VERSIONS_FOR_COUNTRIES"
    ]
    assert (
        set(versions["detail"]["countries"]) == {"ES", "PT"}
        and versions["epistemicState"] == "DECLARED"
    )


def test_platform_conventions_guess_one_feed_when_none_is_declared() -> None:
    from application.first_observation.publications import conventional_feed
    from application.first_observation.site import read_page

    shop = read_page(
        url="https://brand.com/", observed_at=NOW, content_fingerprint="x", artifact_ref=None,
        html="<html><head><script src='https://cdn.shopify.com/s/x.js'></script></head>"
        "<body><a href='/blogs/journal'>Journal</a></body></html>",
    )  # fmt: skip
    assert shop.signals["platform"] == "SHOPIFY"
    links = [u for u, _t in shop.links]
    assert conventional_feed("SHOPIFY", shop.url, links) == "https://brand.com/blogs/journal.atom"
    assert conventional_feed("SHOPIFY", shop.url, []) == "https://brand.com/blogs/news.atom"
    wp = read_page(
        url="https://site.es/", observed_at=NOW, content_fingerprint="x", artifact_ref=None,
        html="<html><head><link rel='stylesheet' href='/wp-content/themes/a.css'></head></html>",
    )  # fmt: skip
    assert conventional_feed(wp.signals["platform"], wp.url, []) == "https://site.es/feed/"
    assert conventional_feed(None, "https://plain.com/", []) is None
