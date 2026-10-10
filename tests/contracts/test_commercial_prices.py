"""Fixed-currency pricing never invents an exchange rate or billing authority."""

import pytest

from domain.admin_billing.commercial_prices import (
    EUR_APPROVED_OFFER,
    EUR_ONLY_PRICE_BOOK,
    CommercialPriceBook,
    FixedCurrencyOffer,
)


def _offer(
    currency: str,
    *,
    base: int = 1000,
    additional: int = 500,
    approval: str = "approved-commercial-pricing-v1",
) -> FixedCurrencyOffer:
    return FixedCurrencyOffer(
        currency=currency,
        base_minor=base,
        additional_minor=additional,
        approval_ref=approval,
        stripe_base_price_ref=f"price_{currency}_base_approved",
        stripe_additional_price_ref=f"price_{currency}_addon_approved",
    )


def test_eur_master_is_the_only_published_reference() -> None:
    assert EUR_ONLY_PRICE_BOOK.exact_offer("EUR") is EUR_APPROVED_OFFER
    assert EUR_ONLY_PRICE_BOOK.exact_offer("USD") is None
    assert EUR_ONLY_PRICE_BOOK.exact_offer("GBP") is None
    assert EUR_ONLY_PRICE_BOOK.suggested_currency("US") == "EUR"
    assert EUR_ONLY_PRICE_BOOK.suggested_currency("GB") == "EUR"
    assert EUR_APPROVED_OFFER.quote_minor(1) == 995
    assert EUR_APPROVED_OFFER.quote_minor(2) == 1490
    assert EUR_APPROVED_OFFER.quote_minor(100) == 50000


def test_fixed_foreign_prices_are_not_fx_conversions() -> None:
    book = CommercialPriceBook(
        "reviewed-v1", (EUR_APPROVED_OFFER, _offer("USD", base=1249), _offer("GBP", base=899))
    )
    assert book.suggested_currency("US") == "USD"
    assert book.suggested_currency("GB") == "GBP"
    assert book.suggested_currency("FR") == "EUR"
    assert book.exact_offer("USD").quote_minor(2) == 1749  # type: ignore[union-attr]
    assert book.exact_offer("GBP").quote_minor(2) == 1399  # type: ignore[union-attr]
    assert book.exact_offer("JPY") is None


@pytest.mark.parametrize("count", [0, -1, 101, 1.5, True, "2", None])
def test_invalid_quantity_never_generates_a_quote(count: object) -> None:
    with pytest.raises(ValueError):
        EUR_APPROVED_OFFER.quote_minor(count)  # type: ignore[arg-type]


@pytest.mark.parametrize("currency", ["usd", "JPY", "EURO", ""])
def test_invalid_currency_rejected(currency: str) -> None:
    with pytest.raises(ValueError):
        _offer(currency)


def test_unapproved_or_partial_foreign_offers_are_never_available() -> None:
    for offer in (
        FixedCurrencyOffer("USD", 1000, 500, "reviewed-but-unbound"),
        FixedCurrencyOffer("GBP", 1000, 500, "reviewed-but-unbound"),
    ):
        with pytest.raises(ValueError, match="Stripe Price"):
            CommercialPriceBook("foreign", (EUR_APPROVED_OFFER, offer))
    with pytest.raises(ValueError):
        FixedCurrencyOffer("USD", 1000, 500, "reviewed", stripe_base_price_ref="price_only")
    with pytest.raises(ValueError):
        CommercialPriceBook("duplicates", (EUR_APPROVED_OFFER, EUR_APPROVED_OFFER))
    with pytest.raises(ValueError):
        CommercialPriceBook("missing-eur", (_offer("USD"),))
    with pytest.raises(ValueError):
        CommercialPriceBook("changed-eur", (_offer("EUR", base=999),))


def test_no_cross_currency_arithmetic_or_implicit_fallback() -> None:
    book = CommercialPriceBook("approved", (EUR_APPROVED_OFFER, _offer("USD")))
    assert book.exact_offer("GBP") is None
    assert book.suggested_currency("GB") == "EUR"
    assert book.exact_offer("USD") is not book.exact_offer("EUR")


def test_cross_currency_price_ref_reuse_fails() -> None:
    first = _offer("USD")
    second = FixedCurrencyOffer(
        "GBP",
        900,
        400,
        "reviewed",
        stripe_base_price_ref=first.stripe_base_price_ref,
        stripe_additional_price_ref="price_GBP_distinct",
    )
    with pytest.raises(ValueError, match="shared"):
        CommercialPriceBook("invalid", (EUR_APPROVED_OFFER, first, second))
