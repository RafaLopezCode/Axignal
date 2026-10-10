"""Fail-closed local composition of subscriber Stripe billing inputs.

This module reads an explicitly whitelisted pair of deployment-managed secret
files. It never sources shell files, expands values, performs provider calls, or
derives tax authority from Stripe credentials or the offer catalogue.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from application.admin_billing.subscriber_checkout import OfferCatalogueReader
from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    ApprovedRecurringOffer,
    ApprovedTaxConfiguration,
    RecurringTerms,
)
from domain.admin_billing.commercial_prices import (
    DEFAULT_CURRENCY,
    EUR_MONTHLY_ADDITIONAL_MINOR,
    EUR_MONTHLY_BASE_MINOR,
)
from tools.runtime.subscriber_checkout import StripeSubscriberRuntimeSettings
from tools.runtime.subscriber_configuration import SubscriberSettings

_ACCOUNT_REF = "acct_1TybkH8feyjV8Pem"
_ENVIRONMENT_REF = f"stripe-live:{_ACCOUNT_REF}"
_CATALOGUE_REF = "axignal-subscriber-live-v1"
_CATALOGUE_VERSION = "1"
_BASE_OFFER_REF = "axignal-subscriber-base"
_ADDITIONAL_OFFER_REF = "axignal-subscriber-additional-xeed"
_MAX_SECRET_BYTES = 8192


class SubscriberBillingConfigurationError(ValueError):
    """Safe configuration failure that never includes values or file paths."""


@dataclass(frozen=True, slots=True)
class ConfiguredOfferCatalogueReader:
    """Immutable single-environment catalogue composed from deployment config."""

    catalogue: ApprovedOfferCatalogue
    environment_ref: str

    def resolve(self, environment_ref: str) -> ApprovedOfferCatalogue | None:
        if environment_ref != self.environment_ref:
            return None
        return self.catalogue


def build_subscriber_billing_inputs(
    settings: SubscriberSettings,
    data_dir: Path,
    *,
    approved_tax_configuration: ApprovedTaxConfiguration | None = None,
) -> tuple[StripeSubscriberRuntimeSettings | None, OfferCatalogueReader | None]:
    """Build typed live Stripe inputs without contacting Stripe.

    Missing both secret-file settings, or both declared files before secret
    provisioning, means NOT_CONFIGURED and returns ``(None, None)``. Partial
    credentials, invalid file references, or incomplete live catalogue
    settings fail closed with a redacted exception. Mutations require both
    explicitly enabled contracting/legal settings and a typed, current tax
    registration configuration for this exact live environment.
    """
    values = settings.values
    api_file = values.get("AXIGNAL_STRIPE_API_KEY_FILE", "").strip()
    webhook_file = values.get("AXIGNAL_STRIPE_WEBHOOK_SIGNING_SECRET_FILE", "").strip()
    if not api_file and not webhook_file:
        return None, None
    if not api_file or not webhook_file:
        raise SubscriberBillingConfigurationError("Stripe credentials are incomplete")

    api_path = _canonical_secret_path(api_file, key="Stripe API key")
    webhook_path = _canonical_secret_path(webhook_file, key="Stripe webhook secret")
    if not api_path.exists() and not webhook_path.exists():
        return None, None
    if not api_path.exists() or not webhook_path.exists():
        raise SubscriberBillingConfigurationError("Stripe credentials are incomplete")
    api_key = _read_secret_file(api_path, key="Stripe API key")
    webhook_secret = _read_secret_file(webhook_path, key="Stripe webhook secret")
    if not (api_key.startswith("sk_live_") or api_key.startswith("rk_live_")):
        raise SubscriberBillingConfigurationError("Stripe API key is not a live key")
    if not webhook_secret.startswith("whsec_"):
        raise SubscriberBillingConfigurationError("Stripe webhook secret is invalid")

    if values.get("AXIGNAL_STRIPE_LIVE_ENABLED", "") != "true":
        raise SubscriberBillingConfigurationError("live Stripe enablement must be explicit")
    if values.get("AXIGNAL_STRIPE_ACCOUNT_ID", "") != _ACCOUNT_REF:
        raise SubscriberBillingConfigurationError("Stripe account configuration is not approved")
    api_version = values.get("AXIGNAL_STRIPE_API_VERSION", "").strip()
    if (
        not api_version
        or not api_version.isascii()
        or len(api_version) > 40
        or any(ord(char) < 33 or ord(char) > 126 for char in api_version)
    ):
        raise SubscriberBillingConfigurationError("Stripe API version is required")

    base_price = values.get("AXIGNAL_STRIPE_BASE_PRICE_REF", "").strip()
    addon_price = values.get("AXIGNAL_STRIPE_ADDITIONAL_XEED_PRICE_REF", "").strip()
    if not _is_price_ref(base_price) or not _is_price_ref(addon_price) or base_price == addon_price:
        raise SubscriberBillingConfigurationError(
            "both distinct Stripe Price references are required"
        )

    if approved_tax_configuration is not None:
        if not isinstance(approved_tax_configuration, ApprovedTaxConfiguration):
            raise SubscriberBillingConfigurationError(
                "tax authority must be a reviewed typed value"
            )
        if approved_tax_configuration.environment_ref != _ENVIRONMENT_REF:
            raise SubscriberBillingConfigurationError("tax authority environment does not match")
    tax_current = approved_tax_configuration is not None and approved_tax_configuration.is_current(
        _ENVIRONMENT_REF, datetime.now(UTC)
    )

    origin = _validated_origin(settings.origin)
    catalogue = ApprovedOfferCatalogue(
        catalogue_ref=_CATALOGUE_REF,
        version=_CATALOGUE_VERSION,
        base_offer=ApprovedRecurringOffer(
            _BASE_OFFER_REF,
            RecurringTerms(
                "month", 1, DEFAULT_CURRENCY, EUR_MONTHLY_BASE_MINOR, tax_behavior="exclusive"
            ),
        ),
        additional_xeed_offer=ApprovedRecurringOffer(
            _ADDITIONAL_OFFER_REF,
            RecurringTerms(
                "month", 1, DEFAULT_CURRENCY, EUR_MONTHLY_ADDITIONAL_MINOR, tax_behavior="exclusive"
            ),
        ),
        tax_configuration=approved_tax_configuration,
    )
    checkout_hosts = frozenset({"checkout.stripe.com"})
    invoice_hosts = frozenset({"invoice.stripe.com"})
    runtime_settings = StripeSubscriberRuntimeSettings(
        environment_ref=_ENVIRONMENT_REF,
        account_ref=_ACCOUNT_REF,
        live_mode=True,
        api_version=api_version,
        base_offer_ref=_BASE_OFFER_REF,
        additional_offer_ref=_ADDITIONAL_OFFER_REF,
        price_refs={_BASE_OFFER_REF: base_price, _ADDITIONAL_OFFER_REF: addon_price},
        success_url=f"{origin}/account?billing=complete",
        cancel_url=f"{origin}/account?billing=cancelled",
        checkout_hosts=checkout_hosts,
        invoice_hosts=invoice_hosts,
        database_path=Path(data_dir).expanduser().resolve() / "subscriber-billing.sqlite3",
        enabled=True,
        mutations_enabled=settings.contracting_enabled and tax_current,
        api_key=api_key,
        webhook_signing_secret=webhook_secret,
    )
    return runtime_settings, ConfiguredOfferCatalogueReader(catalogue, _ENVIRONMENT_REF)


def _canonical_secret_path(raw_path: str, *, key: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise SubscriberBillingConfigurationError(f"{key} file reference is invalid")
    try:
        canonical = candidate.resolve(strict=False)
        if candidate.is_symlink():
            raise SubscriberBillingConfigurationError(f"{key} file reference is invalid")
    except (OSError, RuntimeError):
        raise SubscriberBillingConfigurationError(f"{key} file reference is invalid") from None
    return canonical


def _read_secret_file(path: Path, *, key: str) -> str:
    try:
        canonical = path.resolve(strict=True)
        if path.is_symlink() or not canonical.is_file():
            raise SubscriberBillingConfigurationError(f"{key} file reference is invalid")
        with canonical.open("rb") as stream:
            payload = stream.read(_MAX_SECRET_BYTES + 1)
    except (OSError, RuntimeError):
        raise SubscriberBillingConfigurationError(f"{key} file is unavailable") from None
    if len(payload) > _MAX_SECRET_BYTES:
        raise SubscriberBillingConfigurationError(f"{key} file is too large")
    try:
        value = payload.decode("ascii").strip()
    except UnicodeDecodeError:
        raise SubscriberBillingConfigurationError(f"{key} file is malformed") from None
    if not value or any(char.isspace() for char in value):
        raise SubscriberBillingConfigurationError(f"{key} file is empty or malformed")
    return value


def _is_price_ref(value: str) -> bool:
    return (
        value.startswith("price_")
        and 6 < len(value) <= 200
        and value.isascii()
        and all(char.isalnum() or char in "_-" for char in value)
    )


def _validated_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise SubscriberBillingConfigurationError("subscriber origin is invalid") from None
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or parsed.scheme != "https"
        or local
        or (not local and port not in {None, 443})
    ):
        raise SubscriberBillingConfigurationError("subscriber origin is invalid")
    return value.rstrip("/")


__all__ = [
    "ConfiguredOfferCatalogueReader",
    "SubscriberBillingConfigurationError",
    "build_subscriber_billing_inputs",
]
