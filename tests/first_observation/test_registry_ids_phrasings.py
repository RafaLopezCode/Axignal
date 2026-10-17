"""Register numbers stated the way legal notices really state them (spec 094).

Found on the agencies' legal notices (2026-10-18): eskimoz.fr writes "RCS de Paris sous le
numéro 528 338 494" and simon-kucher.com "HRB 3771, AG Bonn"; neither was read, so the open
French register was never asked and a German company carried no register anchor.
"""

from __future__ import annotations

import pytest

from application.first_observation.registry_ids import DE_HR, SIREN, registry_identifiers


@pytest.mark.parametrize(
    "text",
    [
        "Eskimoz, SAS au capital de 100 €, RCS de Paris sous le numéro 528 338 494",
        "immatriculée au registre du commerce et des sociétés de Lyon sous le n° 528 338 494",
        "RCS Paris B 528 338 494",
        "SIREN : 528338494",
        "SIRET 528 338 494 00031",
    ],
)
def test_french_phrasings_read_the_siren(text: str) -> None:
    assert registry_identifiers(text) == [(SIREN, "528338494")]


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("Simon-Kucher & Partners (HRB 3771, AG Bonn) belonging", "HRB 3771 Bonn"),
        ("Registergericht: Amtsgericht München, HRB 123456", "HRB 123456 München"),
        ("Amtsgericht Charlottenburg HRB 98765 B", "HRB 98765 Charlottenburg"),
    ],
)
def test_german_entries_need_their_register_court(text: str, value: str) -> None:
    assert registry_identifiers(text) == [(DE_HR, value)]


@pytest.mark.parametrize(
    "text",
    [
        "RCS Paris 123 456 789",  # fails the SIREN check digit
        "RCS de Paris, tel 01 45 67 89 12",
        "Telefon 0228 9843 0 HRB",  # no number after the section, no court
        "HRB 12345",  # no register court: not unique
    ],
)
def test_numbers_that_are_not_register_entries_are_never_read(text: str) -> None:
    assert registry_identifiers(text) == []
