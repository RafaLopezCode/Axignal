"""Revenue a third-party page reports (spec 104): same sentence, amount, scale and currency."""

from __future__ import annotations

import pytest

from application.web_research.money import reported_revenue

CASES = [
    (
        "Goiko facturó 120,5 millones de euros en 2025, un 10% más.",
        "goiko",
        (120_500_000.0, "EUR", 2025),
    ),
    (
        "En 2024 la facturación de Holded alcanzó los 45 millones de euros.",
        "holded",
        (45_000_000.0, "EUR", 2024),
    ),
    ("Huel reported revenue of £214m for the year to 2025.", "huel", (214_000_000.0, "GBP", 2025)),
    ("Bombas revenue topped $300 million in 2023.", "bombas", (300_000_000.0, "USD", 2023)),
    (
        "mymuesli erzielte 2024 einen Umsatz von 60 Mio. Euro.",
        "mymuesli",
        (60_000_000.0, "EUR", 2024),
    ),
    (
        "Aigle a réalisé un chiffre d'affaires de 250 millions d'euros en 2024.",
        "aigle",
        (250_000_000.0, "EUR", 2024),
    ),
    (
        "Velasca ha registrato un fatturato di 1,2 milioni di euro nel 2024",
        "velasca",
        (1_200_000.0, "EUR", 2024),
    ),
    ("Zitrón cerró 2025 con unas ventas de 95,3 M€.", "zitron", (95_300_000.0, "EUR", 2025)),
]


@pytest.mark.parametrize(("text", "needle", "expected"), CASES)
def test_a_reported_figure_is_read_with_its_scale_currency_and_year(
    text: str, needle: str, expected: tuple[float, str, int]
) -> None:
    found = reported_revenue(text, [needle], current_year=2026)
    assert found is not None and (found.value, found.currency, found.year) == expected


@pytest.mark.parametrize("text", [
    "El mercado de la moda factura 1.200 millones de euros; Ecoalf crece.",  # the market's
    "Ecoalf crece. El sector textil facturó 1.200 millones de euros en 2024.",  # another sentence
    "Ecoalf abre 12 tiendas en 2026 con 300 empleados.",  # no revenue, no currency
    "Ecoalf factura 45 millones.",  # no currency: not guessed
    # Found in the 20-client panel (2026-10-19): a target, a lifetime total, a profit.
    "Ecoalf aspira a duplicar su facturación, hasta alcanzar alrededor de los 750 millones de euros, al término de su plan 2025-2030.",
    "Ecoalf's revenue has grown 22%, it's reached more than $2 billion in lifetime sales.",
    "Ecoalf revenue rose 15% while its pre-tax profit reached £20m in 2025.",
    "Ecoalf, valued at €400m after raising funding, grew its revenue.",
    "CEO took Ecoalf's sales from just over £20m when he joined in 2017.",  # years old
    "Ecoalf revenue reached €45m.",  # no year: not its revenue today
])  # fmt: skip
def test_figures_that_are_not_its_revenue_are_left_out(text: str) -> None:
    assert reported_revenue(text, ["ecoalf"], current_year=2026) is None


def test_a_name_with_symbols_is_matched_word_for_word() -> None:
    found = reported_revenue(
        "Bloom & Wild's revenue reached £120m in 2025.", ["bloom wild"], current_year=2026
    )
    assert found is not None and found.value == 120_000_000.0
