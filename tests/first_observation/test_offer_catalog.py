"""What a client sells, in its own catalog's words (spec 097).

On 20 typical agency clients, 10 were read only as "retail trade". Their catalogs say what
they sell: Velasca shirts and loafers, Claus Porto soaps and candles, mymuesli muesli.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from application.first_observation.offer_catalog import (
    catalog_categories,
    offer_categories,
    product_types,
)
from tests.first_observation import harness
from tests.first_observation.harness import SOLAR_ES, World, build, discoveries, runtime
from tests.first_observation.test_first_observation_e2e import _attend, _pending_id, _view

HOME = "https://shop.example/"


def test_catalog_links_name_categories_never_promotions_counts_or_audiences() -> None:
    links = [
        (HOME + "collections/sunglasses", "Sunglasses"),
        (HOME + "collections/all", "Shop all"),
        (HOME + "collections/sale", "Sale -50%"),
        (HOME + "collections/mujer", "Mujer"),
        (HOME + "collections/gift-card", "Gift card"),
        (HOME + "collections/frames", "Optical frames (49)"),
        ("/product-category/bolsos", ""),  # no text: its slug names it
        ("https://other.example/collections/hats", "Hats"),  # another site
        (HOME + "pages/about", "About"),  # not a catalog path
        (HOME + "collections/sunglasses-2", "SUNGLASSES"),  # the same category twice
    ]
    assert catalog_categories(links, HOME) == ["Sunglasses", "Optical frames", "Bolsos"]


def test_product_types_are_counted_and_season_codes_and_generic_types_dropped() -> None:
    raw = json.dumps({"products": [
        {"product_type": "Soaps"}, {"product_type": "Soaps"}, {"product_type": "Candles"},
        {"product_type": "AW26"}, {"product_type": "food"}, {"product_type": ""},
        {"product_type": "Fragrances"}, {"title": "no type"},
    ]}).encode()  # fmt: skip
    assert product_types(raw) == [("Soaps", 2), ("Candles", 1), ("Fragrances", 1)]
    assert product_types(b"<html>not json") == []


def test_product_types_win_when_they_name_three_or_more() -> None:
    types = [("Soaps", 2), ("Candles", 1), ("Fragrances", 1)]
    assert offer_categories(["Gifts", "Home"], types) == (
        ["Soaps", "Candles", "Fragrances"],
        "PRODUCT_TYPES",
    )
    assert offer_categories(["Big bars", "Small bars"], [("Bars", 3)]) == (
        ["Big bars", "Small bars"],
        "CATALOG_LINKS",
    )
    assert offer_categories([], [("Kondome", 17)]) == (["Kondome"], "PRODUCT_TYPES")
    assert offer_categories(["Only one"], []) is None


def test_a_shopify_client_gets_what_it_sells_from_minute_zero(
    tmp_path: Path, monkeypatch: Any
) -> None:
    home = harness.PAGES[SOLAR_ES].replace(
        "</head>", "<script src='https://cdn.shopify.com/s/files/x.js'></script></head>"
    )
    monkeypatch.setitem(harness.PAGES, SOLAR_ES, home)
    catalog = json.dumps({"products": [{"product_type": t} for t in
                                       ("Paneles solares", "Paneles solares", "Inversores", "Baterías")]})  # fmt: skip
    monkeypatch.setitem(harness.PAGES, SOLAR_ES + "products.json?limit=250", catalog)
    world = World()
    facade = build(tmp_path, world)
    token, _added = _attend(facade, tmp_path, "subject:offer", SOLAR_ES)
    assert runtime(facade).drain() == 1
    view = _view(facade, token, _pending_id(facade, token))
    assert SOLAR_ES + "products.json?limit=250" in world.sites.requests
    (offer,) = discoveries(view, "OFFER")
    assert offer["epistemicState"] == "DECLARED" and offer["detail"]["basis"] == "PRODUCT_TYPES"
    assert offer["detail"]["categories"] == ["Paneles solares", "Inversores", "Baterías"]
