"""Premises the organization pins on a map on its own website, placed anywhere in the world."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from application.first_observation.contracts import RunLedger
from application.first_observation.site import map_coordinates, read_page
from pipeline.geo.nominatim import NominatimReverseGeocoder

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def test_map_links_and_embeds_carry_their_point() -> None:
    assert map_coordinates("https://www.google.com/maps/place/X/@43.5269,-5.6721,17z") == (
        43.5269,
        -5.6721,
    )
    assert map_coordinates("https://www.google.com/maps/embed?pb=!1m18!2d-73.5673!3d45.5017") == (
        45.5017,
        -73.5673,
    )
    assert map_coordinates("https://www.openstreetmap.org/?mlat=37.7749&mlon=-122.4194") == (
        37.7749,
        -122.4194,
    )
    assert map_coordinates("https://www.google.com/search?q=40.1,-3.2") is None  # not a map
    assert map_coordinates("https://maps.app.goo.gl/abc") is None  # short link: not resolved


def test_a_page_keeps_the_points_it_publishes() -> None:
    html = (
        "<html><body><iframe src='https://www.google.com/maps/embed?pb=!2d11.582!3d48.1351'></iframe>"
        '<script type="application/ld+json">{"@type":"Place","geo":{"@type":"GeoCoordinates",'
        '"latitude":40.4168,"longitude":-3.7038}}</script></body></html>'
    )
    page = read_page(
        url="https://x.example/",
        html=html,
        observed_at=NOW,
        content_fingerprint="x",
        artifact_ref=None,
    )
    assert page.signals["coordinates"] == [
        [48.1351, 11.582, "MAP_LINK"],
        [40.4168, -3.7038, "SCHEMA_GEO"],
    ]


def test_reverse_geocoding_is_cached_and_polite(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetch(url: str) -> bytes:
        calls.append(url)
        return json.dumps(
            {
                "address": {
                    "country_code": "ca",
                    "ISO3166-2-lvl4": "CA-QC",
                    "state": "Quebec",
                    "city": "Montreal",
                }
            }
        ).encode()

    geocoder = NominatimReverseGeocoder(tmp_path / "geo.sqlite3", fetch=fetch, min_interval_s=0)
    first = geocoder.place(45.5017, -73.5673)
    again = geocoder.place(45.50171, -73.56729)  # same ~100 m cell
    assert first == again and first is not None and first.country_code == "CA"
    assert first.region_code == "CA-QC" and "OpenStreetMap" in first.attribution
    assert len(calls) == 1


def test_the_service_turns_pinned_points_into_declared_premises() -> None:
    from types import SimpleNamespace

    from application.first_observation.service import FirstObservationService
    from pipeline.geo.nominatim import Place

    class Geo:
        def place(self, latitude: float, longitude: float) -> Place:
            return Place("US", "US-CA", "California", "San Francisco")

    page = read_page(
        url="https://acme.example/contact",
        html="<html><body><a href='https://maps.google.com/?q=37.7749,-122.4194'>Map</a></body></html>",
        observed_at=NOW, content_fingerprint="x", artifact_ref=None,
    )  # fmt: skip
    service = SimpleNamespace(_geocoder=Geo())
    ledger = RunLedger()
    ((code, discovery),) = FirstObservationService._mapped_premises(service, [page], ledger)  # type: ignore[arg-type]
    assert code.code == "US/US-CA"
    assert discovery.code == "PREMISES_PINNED_ON_MAP" and discovery.epistemic_state == "DECLARED"
    assert discovery.statement == "San Francisco, California, US"
    assert "LOCATION:MAP_POINT:US" in ledger.decisions
