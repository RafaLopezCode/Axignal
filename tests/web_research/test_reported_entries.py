"""Countries a page reports an organization has entered (spec 107): same sentence, verb, country."""

from __future__ import annotations

import pytest

from application.web_research.expansion import reported_entries

CASES = [
    ("Bloom & Wild entra en Francia tras comprar Bergamotte.", "bloom wild", "GB", ("FR",)),
    ("Goiko abre su primer restaurante en Italia.", "goiko", "ES", ("IT",)),
    ("Huel launched in the United States and Canada in 2018.", "huel", "GB", ("US", "CA")),
    ("Sézane ouvre une boutique à Londres, au Royaume-Uni.", "sezane", "FR", ("GB",)),
    ("mymuesli eröffnet einen Laden in der Schweiz.", "mymuesli", "DE", ("CH",)),
]


@pytest.mark.parametrize(("text", "needle", "home", "expected"), CASES)
def test_an_entry_is_read_in_any_of_the_languages(
    text: str, needle: str, home: str, expected: tuple[str, ...]
) -> None:
    found = reported_entries(text, [needle], home=home)
    assert found is not None and found.countries == expected


@pytest.mark.parametrize("text", [
    "Ecoalf prevé abrir en Japón el próximo año.",  # a plan
    "Ecoalf aims to enter Germany.",  # a target
    "Ecoalf abre una tienda en Madrid, España.",  # its home country
    "La moda española triunfa en México; Ecoalf crece.",  # another sentence's subject
    "Ecoalf está presente en Italia desde hace años.",  # no entry verb
])  # fmt: skip
def test_what_is_not_an_entry_is_left_out(text: str) -> None:
    assert reported_entries(text, ["ecoalf"], home="ES") is None
