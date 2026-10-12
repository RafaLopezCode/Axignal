"""The service holder's identity (LSSI art. 10) comes only from the operator's configuration."""

from __future__ import annotations

from tools.runtime.subscriber_configuration import load_subscriber_settings
from tools.runtime.subscriber_http import SubscriberHttpFacade, is_subscriber_path

LEGAL = {
    "AXIGNAL_SUBSCRIBER_ENABLED": "true",
    "AXIGNAL_LEGAL_OPERATOR_NAME": "Persona Titular Ejemplo",
    "AXIGNAL_LEGAL_OPERATOR_KIND": "Autónomo",
    "AXIGNAL_LEGAL_TAX_ID": "00000000T",
    "AXIGNAL_LEGAL_ADDRESS": "Calle Ejemplo 1, 00000 Ciudad (Provincia)",
    "AXIGNAL_LEGAL_CONTACT": "titular@example.com",
    "AXIGNAL_LEGAL_TERMS_VERSION": "2026-10-12",
}


def _facade(values: dict[str, str]) -> SubscriberHttpFacade:
    return SubscriberHttpFacade(
        settings=load_subscriber_settings(values),
        identity=None,  # type: ignore[arg-type]
        workflow=None,  # type: ignore[arg-type]
        outputs=None,  # type: ignore[arg-type]
    )


def test_a_complete_configuration_is_published_as_configured() -> None:
    response = _facade(LEGAL).handle("GET", "/subscriber/legal/operator", {})
    assert response.status == 200
    assert response.body == {
        "state": "PUBLISHED",
        "name": "Persona Titular Ejemplo",
        "kind": "Autónomo",
        "taxId": "00000000T",
        "address": "Calle Ejemplo 1, 00000 Ciudad (Provincia)",
        "contact": "titular@example.com",
        "termsVersion": "2026-10-12",
    }
    assert is_subscriber_path("/subscriber/legal/operator")


def test_an_incomplete_configuration_publishes_nothing_invented() -> None:
    partial = {k: v for k, v in LEGAL.items() if k != "AXIGNAL_LEGAL_TAX_ID"}
    response = _facade(partial).handle("GET", "/subscriber/legal/operator", {})
    assert response.body == {"state": "NOT_PUBLISHED"}
