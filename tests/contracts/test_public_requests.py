"""Private pre-auth requests do not grant tenancy, consent or economic authority."""

import json
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from application.public_requests.service import PublicRequestService, validate_request
from pipeline.public_requests.sqlite_store import SqlitePublicRequestStore

NOW = datetime(2026, 10, 8, tzinfo=UTC)


def payload(**changes: object) -> dict[str, object]:
    return {
        "requestRef": "isolated-request-0001",
        "category": "contact",
        "name": "Test Visitor",
        "email": "visitor@example.invalid",
        "subject": "Product question",
        "message": "Please explain the availability of this service.",
        "locale": "en",
        **changes,
    }


@pytest.mark.parametrize("kind,category", [("CONTACT", "contact"), ("PRIVACY_RIGHTS", "erasure")])
def test_persist_before_unavailable_delivery(tmp_path: Path, kind: str, category: str) -> None:
    store = SqlitePublicRequestStore(tmp_path / "requests.sqlite3")
    request = validate_request(payload(category=category), kind=kind)  # type: ignore[arg-type]
    receipt = PublicRequestService(store).submit(request, now=NOW)
    assert receipt.public()["stored"] is True
    assert receipt.delivery_status == "UNAVAILABLE"
    assert "email" not in receipt.public() and "message" not in receipt.public()
    with sqlite3.connect(store.path) as db:
        row = db.execute("SELECT content, delivery FROM public_requests").fetchone()
    assert "visitor@example.invalid" in row[0]
    assert row[1] == "UNAVAILABLE"


def test_delivery_receipt_and_idempotent_retry(tmp_path: Path) -> None:
    calls: list[str] = []

    class ControlledDelivery:
        def send(self, request, *, receipt):  # type: ignore[no-untyped-def]
            with sqlite3.connect(tmp_path / "requests.sqlite3") as db:
                assert db.execute("SELECT delivery FROM public_requests").fetchone()[0] == "PENDING"
            calls.append(receipt.request_id)

    service = PublicRequestService(
        SqlitePublicRequestStore(tmp_path / "requests.sqlite3"), ControlledDelivery()
    )
    request = validate_request(payload(), kind="CONTACT")
    first = service.submit(request, now=NOW)
    assert first.delivery_status == "DELIVERED"
    assert service.submit(request, now=NOW) == first
    assert calls == [first.request_id]
    with pytest.raises(ValueError, match="REQUEST_REF_CONFLICT"):
        service.submit(
            validate_request(
                payload(message="A different request with the same reference."), kind="CONTACT"
            ),
            now=NOW,
        )


@pytest.mark.parametrize(
    "change",
    [
        {"email": "invalid"},
        {"email": "a@example.invalid\nBcc: leak@example.invalid"},
        {"subject": "Header\r\ninjection"},
        {"message": "short"},
        {"locale": "xx"},
        {"category": "erasure"},
        {"message": "x" * 3001},
        {"requestRef": "short"},
    ],
)
def test_validation(change: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        validate_request(payload(**change), kind="CONTACT")


def test_rate_limit_and_bounded_retention(tmp_path: Path) -> None:
    store = SqlitePublicRequestStore(tmp_path / "requests.sqlite3")
    service = PublicRequestService(store)
    for index in range(3):
        service.submit(
            validate_request(payload(requestRef=f"isolated-request-{index:04}"), kind="CONTACT"),
            now=NOW,
        )
    with pytest.raises(ValueError, match="REQUEST_RATE_LIMITED"):
        service.submit(
            validate_request(payload(requestRef="isolated-request-0004"), kind="CONTACT"), now=NOW
        )
    assert store.purge(now=NOW + timedelta(days=91)) == 3
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT count(*) FROM public_requests").fetchone()[0] == 0


def test_provider_failure_is_safe_and_persisted(tmp_path: Path) -> None:
    class FailedDelivery:
        def send(self, request, *, receipt):  # type: ignore[no-untyped-def]
            raise OSError("sensitive provider details")

    service = PublicRequestService(
        SqlitePublicRequestStore(tmp_path / "requests.sqlite3"), FailedDelivery()
    )
    receipt = service.submit(validate_request(payload(), kind="CONTACT"), now=NOW)
    assert receipt.delivery_status == "FAILED"
    assert "sensitive" not in str(receipt.public())


@pytest.mark.parametrize(
    "category",
    ["access", "rectification", "erasure", "restriction", "objection", "portability", "other"],
)
def test_all_privacy_categories(category: str) -> None:
    assert validate_request(payload(category=category), kind="PRIVACY_RIGHTS").category == category


def test_invalid_delivery_configuration_keeps_valid_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.runtime.public_requests import submit_public_request

    def invalid_configuration(**kwargs: object) -> None:
        raise ValueError("invalid SMTP port")

    monkeypatch.setattr("tools.runtime.public_requests.configured_delivery", invalid_configuration)
    status, receipt = submit_public_request(
        data_dir=tmp_path, environment="development", payload=payload(), kind="CONTACT"
    )
    assert status == 202 and receipt["code"] == "CONTACT_DELIVERY_UNAVAILABLE"
    with sqlite3.connect(tmp_path / "public-requests.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM public_requests").fetchone()[0] == 1


def test_smtp_requires_authority_before_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    from application.public_requests.service import RequestReceipt
    from pipeline.public_requests.smtp_delivery import SmtpContactDelivery

    def deny() -> str:
        raise PermissionError("integration disabled")

    def forbidden_transport(*args: object, **kwargs: object) -> None:
        pytest.fail("transport must not open before AO-18 authorization")

    monkeypatch.setattr("smtplib.SMTP_SSL", forbidden_transport)
    delivery = SmtpContactDelivery(
        "mail.example.invalid",
        465,
        "sender@example.invalid",
        "contact@example.invalid",
        "privacy@example.invalid",
        "fixture",
        deny,
    )
    with pytest.raises(PermissionError):
        delivery.send(
            validate_request(payload(), kind="CONTACT"),
            receipt=RequestReceipt("a" * 32, NOW.isoformat(), "CONTACT", "PENDING"),
        )


def test_configured_transport_uses_tls_plain_text_server_owned_recipient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ssl
    from email.message import EmailMessage

    from application.public_requests.service import RequestReceipt
    from pipeline.public_requests.smtp_delivery import SmtpContactDelivery

    messages: list[EmailMessage] = []

    class ControlledSmtp:
        def __init__(self, host: str, port: int, *, timeout: int, context: ssl.SSLContext):
            assert (host, port, timeout) == ("mail.example.invalid", 465, 10)
            assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def login(self, username: str, password: str) -> None:
            assert (username, password) == ("fixture", "fixture-only")

        def send_message(self, message: EmailMessage) -> dict[str, object]:
            messages.append(message)
            return {}

    monkeypatch.setattr("smtplib.SMTP_SSL", ControlledSmtp)
    delivery = SmtpContactDelivery(
        "mail.example.invalid",
        465,
        "sender@example.invalid",
        "contact@example.invalid",
        "privacy@example.invalid",
        "fixture",
        lambda: "fixture-only",
    )
    request = validate_request(
        payload(category="other", message="<script>alert('test')</script>"), kind="PRIVACY_RIGHTS"
    )
    delivery.send(
        request, receipt=RequestReceipt("b" * 32, NOW.isoformat(), "PRIVACY_RIGHTS", "PENDING")
    )
    assert messages[0]["To"] == "privacy@example.invalid"
    assert messages[0].get_content_type() == "text/plain"
    assert "<script>" in messages[0].get_content()


def test_http_intake_origin_size_validation_receipts_and_rate_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime, make_handler

    origin = "http://127.0.0.1:3810"
    monkeypatch.setenv("AXIGNAL_EXPERIENCE_ORIGIN", origin)
    monkeypatch.delenv("AXIGNAL_CONTACT_SMTP_HOST", raising=False)
    runtime = build_runtime(
        RuntimeConfig(
            "development",
            "127.0.0.1",
            8765,
            "a" * 40,
            tmp_path / "runtime",
            Path(__file__).resolve().parents[2] / "apps" / "web",
        )
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def send(
        path: str, body: object, *, request_origin: str = origin, method: str = "POST"
    ) -> tuple[int, dict]:  # type: ignore[type-arg]
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        try:
            connection.request(
                method,
                path,
                json.dumps(body),
                {"Content-Type": "application/json", "Origin": request_origin},
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    try:
        assert send("/api/contact", payload(), method="PUT")[0] == 405
        assert send("/api/privacy/request", payload(category="access"), method="PATCH")[0] == 405
        assert send("/api/contact", payload(), request_origin="https://attacker.invalid")[0] == 403
        assert send("/api/contact", payload(message="x" * 17000))[0] == 400
        assert send("/api/contact", payload(email="bad"))[0] == 400
        status, contact = send("/api/contact", payload())
        assert status == 202 and contact["code"] == "CONTACT_DELIVERY_UNAVAILABLE"
        assert send("/api/contact", payload())[1] == contact
        status, privacy = send(
            "/api/privacy/request", payload(category="access", requestRef="isolated-privacy-0001")
        )
        assert status == 202 and privacy["code"] == "PRIVACY_DELIVERY_UNAVAILABLE"
        assert "email" not in privacy and "message" not in privacy
        assert send("/api/contact", payload(requestRef="isolated-contact-0002"))[0] == 202
        assert send("/api/contact", payload(requestRef="isolated-contact-0003"))[0] == 429
        assert (
            runtime.health_payload(detailed=True)["persistence"]["observation_memory"]["rows"] == 0
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
