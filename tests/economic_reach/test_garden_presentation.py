"""Spec 060: the garden summary carries what a person needs to read a place: its name,
its source, its words and when it was observed. Labels never decide reach."""

from __future__ import annotations

from application.economic_reach.places import _PLACES, place_label
from application.economic_reach.summary import garden_summary
from tests.economic_reach.harness import model, page


def test_every_gazetteer_jurisdiction_has_a_human_name_and_nothing_else_is_named() -> None:
    assert all(place_label(code.code) for code in _PLACES.values())
    assert place_label("EU/ES/ES3/ES30") == "Comunidad de Madrid"
    assert place_label("EU/XX/UNKNOWN") is None  # unknown stays unknown, never guessed


def test_garden_places_carry_name_source_excerpt_and_observation_time() -> None:
    m = model(
        "org:salon",
        (
            page(
                "org:salon",
                "https://salon.example.com/",
                "Peluquería en nuestro salón en Madrid. Cortes y color con cita previa.",
            ),
        ),
        {"hair": ("peluqueria", "cortes")},
    )
    (hair,) = garden_summary(m)["capabilities"]  # type: ignore[misc]
    (place,) = hair["operating"]
    assert place["label"] == "Comunidad de Madrid"
    assert place["source"] == "https://salon.example.com/"
    assert "Madrid" in place["excerpt"]
    assert place["observedAt"].startswith("20")
