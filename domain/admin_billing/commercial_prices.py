"""Governed fixed-currency offers; never an FX quote or a Stripe payment authority.

The MASTER approves only EUR. Foreign-currency offers become selectable ONLY
after explicit, versioned commercial approval, real Stripe Price binding and
a separate currency-aware subscriber checkout implementation. This model
does not grant any of those permissions.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_CURRENCY = "EUR"
SUPPORTED_CURRENCIES = frozenset({"EUR", "USD", "GBP"})
EUR_MONTHLY_BASE_MINOR = 995
EUR_MONTHLY_ADDITIONAL_MINOR = 495
MAX_PREVIEW_ORGANIZATIONS = 100


@dataclass(frozen=True, slots=True)
class FixedCurrencyOffer:
    """An explicitly approved fixed price, not a converted estimate."""

    currency: str
    base_minor: int
    additional_minor: int
    approval_ref: str
    stripe_base_price_ref: str | None = None
    stripe_additional_price_ref: str | None = None

    def __post_init__(self) -> None:
        if self.currency not in SUPPORTED_CURRENCIES:
            raise ValueError("unsupported commercial currency")
        if (
            type(self.base_minor) is not int
            or self.base_minor < 1
            or type(self.additional_minor) is not int
            or self.additional_minor < 1
            or self.base_minor > 10_000_000
            or self.additional_minor > 10_000_000
        ):
            raise ValueError("commercial offers require bounded positive integer minor units")
        if not self.approval_ref or len(self.approval_ref) > 160:
            raise ValueError("commercial approval reference required")
        refs = (self.stripe_base_price_ref, self.stripe_additional_price_ref)
        if any(ref is not None for ref in refs):
            if not all(
                isinstance(ref, str) and ref.startswith("price_") and len(ref) < 150 for ref in refs
            ):
                raise ValueError("both Stripe price references must be complete")
            if refs[0] == refs[1]:
                raise ValueError("base and additional Price references must differ")

    def quote_minor(self, organization_count: int) -> int:
        if (
            type(organization_count) is not int
            or not 1 <= organization_count <= MAX_PREVIEW_ORGANIZATIONS
        ):
            raise ValueError("organization count must be a supported positive integer")
        return self.base_minor + self.additional_minor * (organization_count - 1)

    @property
    def stripe_bound(self) -> bool:
        return (
            self.stripe_base_price_ref is not None and self.stripe_additional_price_ref is not None
        )


EUR_APPROVED_OFFER = FixedCurrencyOffer(
    currency="EUR",
    base_minor=EUR_MONTHLY_BASE_MINOR,
    additional_minor=EUR_MONTHLY_ADDITIONAL_MINOR,
    approval_ref="MASTER_PRODUCT_MODEL_V2_SECTION_27",
)


@dataclass(frozen=True, slots=True)
class CommercialPriceBook:
    """Versioned offers. Currency cannot be silently changed inside a subscription."""

    version: str
    offers: tuple[FixedCurrencyOffer, ...]

    def __post_init__(self) -> None:
        if not self.version or len(self.version) > 100 or not self.offers:
            raise ValueError("versioned commercial catalogue required")
        codes = [offer.currency for offer in self.offers]
        if len(set(codes)) != len(codes):
            raise ValueError("duplicate commercial currency")
        euro = next((offer for offer in self.offers if offer.currency == "EUR"), None)
        if euro is None or (
            euro.base_minor != EUR_MONTHLY_BASE_MINOR
            or euro.additional_minor != EUR_MONTHLY_ADDITIONAL_MINOR
        ):
            raise ValueError("EUR MASTER reference offer cannot be weakened")
        for offer in self.offers:
            if offer.currency != DEFAULT_CURRENCY and not offer.stripe_bound:
                raise ValueError("non-EUR offer requires both reviewed Stripe Price references")
        refs = [
            ref
            for offer in self.offers
            for ref in (offer.stripe_base_price_ref, offer.stripe_additional_price_ref)
            if ref is not None
        ]
        if len(set(refs)) != len(refs):
            raise ValueError("Stripe Price references cannot be shared between currencies")

    def exact_offer(self, currency: str) -> FixedCurrencyOffer | None:
        """Fail closed on missing approval, without silently converting EUR to requested currency."""
        return next((offer for offer in self.offers if offer.currency == currency), None)

    def suggested_currency(self, country: str | None) -> str:
        """Country suggests a currency; localization language never establishes billing currency."""
        preferred = {"US": "USD", "GB": "GBP"}.get(country or "", DEFAULT_CURRENCY)
        return preferred if self.exact_offer(preferred) is not None else DEFAULT_CURRENCY


EUR_ONLY_PRICE_BOOK = CommercialPriceBook(version="master-v2-eur", offers=(EUR_APPROVED_OFFER,))
