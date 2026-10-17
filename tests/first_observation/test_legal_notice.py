"""The legal name a legal notice states in its text (spec 089, Organization from minute 0).

Measured on 14 agencies: 4 declared a legal name as structured data; their notices said it
in plain text. Real wordings from those notices, plus the traps: service providers named
for analytics, hosting or payments are never the organization.
"""

from __future__ import annotations

import pytest

from application.first_observation.legal_notice import legal_names_in_text

CASES = [
    ("En cumplimiento de la LSSI, el titular de este sitio web es DIGILAB TEAM, S.L, con CIF "
     "B12345678 y domicilio en Valencia.", "webpositer", ["B12345678"], ["DIGILAB TEAM, S.L"]),
    ("Le Site Eskimoz.fr est édité par la société Groupe Ydyle, S.A. au capital de 40 000 euros.",
     "eskimoz", [], ["Groupe Ydyle, S.A."]),
    ("Builtvisible.com is the trading name of Builtvisible Limited. We use Google Analytics, a "
     "service provided by Google, Inc. Alternatively write to Builtvisible Ltd.", "builtvisible", [],
     ["Builtvisible Limited"]),
    ("ATREVIA CORPORACIÓN S.L.U. con domicilio en Madrid y GABINETE DE PRENSA INFORPRESS S.L.U.",
     "atrevia", [], ["ATREVIA CORPORACIÓN S.L.U.", "GABINETE DE PRENSA INFORPRESS S.L.U."]),
    ("Impressum: Simon-Kucher & Partners GmbH, Bonn. Handelsregister HRB 1234", "simonkucher", [],
     ["Simon-Kucher & Partners GmbH"]),
    ("Rodríguez y Asociados S.L. es la titular. CIF B11111111", "rodriguez", ["B11111111"],
     ["Rodríguez y Asociados S.L."]),
]  # fmt: skip


@pytest.mark.parametrize(("text", "brand", "ids", "expected"), CASES)
def test_the_legal_name_is_read_from_the_notice(
    text: str, brand: str, ids: list[str], expected: list[str]
) -> None:
    assert legal_names_in_text(text, brand=brand, identifiers=ids) == expected


def test_providers_named_for_operations_are_never_the_organization() -> None:
    text = "Hosting provided by Hostinger International Ltd. Payments by Stripe Payments Europe Limited."
    assert legal_names_in_text(text, brand="acme") == []
