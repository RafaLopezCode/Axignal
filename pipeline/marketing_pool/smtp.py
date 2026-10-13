"""Send one approved message through the operator's own mailbox (SMTP over TLS).

Provider-neutral; the default host is Hostinger's (smtp.hostinger.com:465, implicit TLS).
The password is read from a root-owned secret file at send time, never logged or echoed.
"""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

DEFAULT_HOST = "smtp.hostinger.com"
DEFAULT_PORT = 465


@dataclass(frozen=True, slots=True)
class SmtpSettings:
    host: str
    port: int
    username: str
    password_file: Path
    sender_name: str
    sender_address: str
    reply_to: str | None = None


@dataclass(frozen=True, slots=True)
class OutgoingMessage:
    to: str
    subject: str
    body: str
    language: str
    unsubscribe_url: str
    unsubscribe_mailto: str
    html: str | None = None


class SmtpSender:
    def __init__(self, settings: SmtpSettings) -> None:
        self._settings = settings

    @property
    def sender_address(self) -> str:
        return self._settings.sender_address

    def send(self, message: OutgoingMessage) -> str:
        """Deliver it; returns the Message-ID. Raises on any refusal (nothing is retried)."""
        settings = self._settings
        email = EmailMessage()
        email["From"] = formataddr((settings.sender_name, settings.sender_address))
        email["To"] = message.to
        email["Subject"] = message.subject
        if settings.reply_to:
            email["Reply-To"] = settings.reply_to
        email["Content-Language"] = message.language
        domain = settings.sender_address.rsplit("@", 1)[-1]
        email["Message-ID"] = make_msgid(domain=domain)
        # RFC 8058 one-click unsubscribe, honoured by the runtime's public endpoint.
        email["List-Unsubscribe"] = f"<{message.unsubscribe_url}>, <{message.unsubscribe_mailto}>"
        email["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        email.set_content(message.body)
        if message.html:
            email.add_alternative(message.html, subtype="html")
        password = settings.password_file.read_text(encoding="utf-8").strip()
        context = ssl.create_default_context()
        if settings.port == 465:
            with smtplib.SMTP_SSL(settings.host, settings.port, context=context, timeout=30) as s:
                s.login(settings.username, password)
                s.send_message(email)
        else:
            with smtplib.SMTP(settings.host, settings.port, timeout=30) as s:
                s.starttls(context=context)
                s.login(settings.username, password)
                s.send_message(email)
        return str(email["Message-ID"])
