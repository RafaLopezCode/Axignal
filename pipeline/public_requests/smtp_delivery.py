"""Provider-neutral TLS SMTP transport; authority is supplied by composition."""

from __future__ import annotations

import smtplib
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from email.message import EmailMessage

from application.public_requests.service import PublicRequest, RequestReceipt


@dataclass(frozen=True)
class SmtpContactDelivery:
    host: str
    port: int
    sender: str
    contact_recipient: str
    privacy_recipient: str
    username: str
    authorize_password: Callable[[], str]

    def send(self, request: PublicRequest, *, receipt: RequestReceipt) -> None:
        # Authorize AO-18 before reading a credential or opening any connection.
        password = self.authorize_password()
        recipient = self.contact_recipient if request.kind == "CONTACT" else self.privacy_recipient
        if not all((self.host, self.username, self.sender, recipient, password)):
            raise PermissionError("delivery unavailable")
        for value in (self.sender, recipient, request.email, request.subject):
            if "\r" in value or "\n" in value:
                raise ValueError("invalid header")
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Reply-To"] = request.email
        message["Subject"] = f"{request.kind} {receipt.request_id}: {request.subject}"
        message["Message-ID"] = f"<{receipt.request_id}@{self.sender.rsplit('@', 1)[-1]}>"
        message.set_content(
            f"Request: {receipt.request_id}\nCreated: {receipt.created_at}\n"
            f"Category: {request.category}\nLocale: {request.locale}\n"
            f"Name: {request.name}\n\n{request.message}"
        )
        with smtplib.SMTP_SSL(
            self.host, self.port, timeout=10, context=ssl.create_default_context()
        ) as client:
            client.login(self.username, password)
            refused = client.send_message(message)
            if refused:
                raise RuntimeError("delivery rejected")
