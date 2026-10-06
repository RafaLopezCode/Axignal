from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from domain.admin_billing.checkout_binding import ApprovedTaxConfiguration
from tools.runtime.subscriber_configuration import SubscriberSettings, load_subscriber_settings
from tools.runtime.subscriber_provisioning import (
    SubscriberBillingConfigurationError,
    build_subscriber_billing_inputs,
)

_ACCOUNT = "acct_1TybkH8feyjV8Pem"


def _settings(api_file: Path, webhook_file: Path, **overrides: str) -> SubscriberSettings:
    values = {
        "AXIGNAL_SUBSCRIBER_ENABLED": "true",
        "AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED": "true",
        "AXIGNAL_EXPERIENCE_ORIGIN": "https://axignal.com",
        "AXIGNAL_LEGAL_OPERATOR_NAME": "Test legal operator",
        "AXIGNAL_LEGAL_TAX_ID": "TEST-TAX-ID",
        "AXIGNAL_LEGAL_ADDRESS": "Test address",
        "AXIGNAL_LEGAL_CONTACT": "legal@example.invalid",
        "AXIGNAL_LEGAL_TERMS_VERSION": "test-terms-v1",
        "AXIGNAL_STRIPE_LIVE_ENABLED": "true",
        "AXIGNAL_STRIPE_API_VERSION": "2025-09-30.clover",
        "AXIGNAL_STRIPE_ACCOUNT_ID": _ACCOUNT,
        "AXIGNAL_STRIPE_API_KEY_FILE": str(api_file),
        "AXIGNAL_STRIPE_WEBHOOK_SIGNING_SECRET_FILE": str(webhook_file),
        "AXIGNAL_STRIPE_BASE_PRICE_REF": "price_user_confirmed_base",
        "AXIGNAL_STRIPE_ADDITIONAL_XEED_PRICE_REF": "price_user_confirmed_addon",
    }
    values.update(overrides)
    return load_subscriber_settings(values)


def _secrets(tmp_path: Path) -> tuple[Path, Path]:
    api_file = tmp_path / "stripe-api-key"
    webhook_file = tmp_path / "stripe-webhook-secret"
    api_file.write_text("rk_live_redacted_test_value\n", encoding="ascii")
    webhook_file.write_text("whsec_redacted_test_value\n", encoding="ascii")
    return api_file, webhook_file


def test_absent_secret_file_configuration_is_not_configured(tmp_path: Path) -> None:
    settings = load_subscriber_settings({"AXIGNAL_SUBSCRIBER_ENABLED": "true"})

    assert build_subscriber_billing_inputs(settings, tmp_path) == (None, None)


def test_ready_configuration_builds_live_catalogue_without_mutation_or_tax(tmp_path: Path) -> None:
    api_file, webhook_file = _secrets(tmp_path)
    settings = _settings(api_file, webhook_file)

    runtime, reader = build_subscriber_billing_inputs(settings, tmp_path / "data")

    assert runtime is not None and reader is not None
    assert runtime.account_ref == _ACCOUNT
    assert runtime.live_mode is True and runtime.enabled is True
    assert runtime.api_version == "2025-09-30.clover"
    assert runtime.price_refs == {
        "axignal-subscriber-base": "price_user_confirmed_base",
        "axignal-subscriber-additional-xeed": "price_user_confirmed_addon",
    }
    assert runtime.mutations_enabled is False
    assert runtime.success_url == "https://axignal.com/account?billing=complete"
    assert runtime.cancel_url == "https://axignal.com/account?billing=cancelled"
    assert runtime.checkout_hosts == frozenset({"checkout.stripe.com"})
    assert runtime.invoice_hosts == frozenset({"invoice.stripe.com"})
    assert runtime.database_path == (tmp_path / "data" / "subscriber-billing.sqlite3").resolve()
    catalogue = reader.resolve(runtime.environment_ref)
    assert catalogue is not None and catalogue.tax_configuration is None
    assert catalogue.version == "1"
    assert catalogue.base_offer.terms.unit_amount_minor == 995
    assert catalogue.base_offer.terms.currency == "EUR"
    assert catalogue.base_offer.terms.interval_unit == "month"
    assert catalogue.base_offer.terms.tax_behavior == "exclusive"
    assert catalogue.additional_xeed_offer.terms.unit_amount_minor == 495
    assert catalogue.additional_xeed_offer.terms.tax_behavior == "exclusive"
    assert reader.resolve("stripe-test:unrelated") is None
    assert "rk_live_redacted_test_value" not in repr(runtime)
    assert "whsec_redacted_test_value" not in repr(runtime)
    assert "rk_live_redacted_test_value" not in repr(settings)


@pytest.mark.parametrize(
    ("api_key", "webhook_secret"),
    [
        ("", "whsec_not_empty"),
        ("sk_test_not_live", "whsec_not_empty"),
        ("rk_live_not_empty", ""),
        ("rk_live_not_empty", "not-a-webhook-secret"),
    ],
)
def test_empty_or_non_live_secret_material_fails_safely(
    tmp_path: Path, api_key: str, webhook_secret: str
) -> None:
    api_file = tmp_path / "api"
    webhook_file = tmp_path / "webhook"
    api_file.write_text(api_key, encoding="ascii")
    webhook_file.write_text(webhook_secret, encoding="ascii")

    with pytest.raises(SubscriberBillingConfigurationError) as caught:
        build_subscriber_billing_inputs(_settings(api_file, webhook_file), tmp_path)

    assert not api_key or api_key not in str(caught.value)
    assert not webhook_secret or webhook_secret not in str(caught.value)
    assert str(api_file) not in str(caught.value)


def test_partial_credentials_and_traversal_fail_closed(tmp_path: Path) -> None:
    api_file, webhook_file = _secrets(tmp_path)
    partial = _settings(api_file, webhook_file, AXIGNAL_STRIPE_WEBHOOK_SIGNING_SECRET_FILE="")
    traversal = _settings(
        api_file,
        webhook_file,
        AXIGNAL_STRIPE_API_KEY_FILE=str(tmp_path / ".." / "outside"),
    )

    for settings in (partial, traversal):
        with pytest.raises(SubscriberBillingConfigurationError):
            build_subscriber_billing_inputs(settings, tmp_path)


def test_both_unprovisioned_secret_placeholders_are_not_configured(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path / "not-provisioned-api-key",
        tmp_path / "not-provisioned-webhook-secret",
    )

    assert build_subscriber_billing_inputs(settings, tmp_path) == (None, None)


def test_only_one_unprovisioned_secret_file_fails_safely(tmp_path: Path) -> None:
    api_file, webhook_file = _secrets(tmp_path)
    webhook_file.unlink()

    with pytest.raises(SubscriberBillingConfigurationError):
        build_subscriber_billing_inputs(_settings(api_file, webhook_file), tmp_path)


@pytest.mark.parametrize(
    "override",
    [
        {"AXIGNAL_STRIPE_LIVE_ENABLED": "false"},
        {"AXIGNAL_STRIPE_ACCOUNT_ID": "acct_wrong"},
        {"AXIGNAL_STRIPE_API_VERSION": ""},
        {"AXIGNAL_STRIPE_BASE_PRICE_REF": ""},
        {"AXIGNAL_STRIPE_ADDITIONAL_XEED_PRICE_REF": "price_user_confirmed_base"},
    ],
)
def test_live_account_version_and_distinct_catalogue_refs_are_mandatory(
    tmp_path: Path, override: dict[str, str]
) -> None:
    api_file, webhook_file = _secrets(tmp_path)
    settings = _settings(api_file, webhook_file, **override)

    with pytest.raises(SubscriberBillingConfigurationError):
        build_subscriber_billing_inputs(settings, tmp_path)


def test_only_typed_tax_authority_can_be_injected_for_live_environment(tmp_path: Path) -> None:
    api_file, webhook_file = _secrets(tmp_path)
    settings = _settings(api_file, webhook_file)
    tax = ApprovedTaxConfiguration(
        configuration_ref="reviewed-tax-configuration",
        environment_ref=f"stripe-live:{_ACCOUNT}",
        active_registration_refs=("registration:verified-by-host-authority",),
        automatic_tax_enabled=True,
        verified_at=datetime.now(UTC) - timedelta(minutes=1),
        valid_until=datetime.now(UTC) + timedelta(hours=1),
    )

    runtime, reader = build_subscriber_billing_inputs(
        settings, tmp_path, approved_tax_configuration=tax
    )

    assert runtime is not None and runtime.mutations_enabled
    assert reader is not None
    catalogue = reader.resolve(f"stripe-live:{_ACCOUNT}")
    assert catalogue is not None and catalogue.tax_configuration is tax
    with pytest.raises(SubscriberBillingConfigurationError):
        build_subscriber_billing_inputs(
            settings,
            tmp_path,
            approved_tax_configuration=ApprovedTaxConfiguration(
                configuration_ref="other-environment",
                environment_ref="stripe-test",
                active_registration_refs=("registration:test",),
                automatic_tax_enabled=True,
                verified_at=datetime.now(UTC),
            ),
        )
