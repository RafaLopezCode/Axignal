"""Subscriber attention locators (spec 052).

A locator is what a subscriber typed to direct AXIGNAL's attention: a name, a
public website/domain, a verified-identifier string, or a name plus a website.
Parsing only classifies those signals. It never resolves, admits or trusts them.
"""

from __future__ import annotations

import ipaddress
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlsplit

from domain.identity import identity_name_key

MAX_LOCATOR = 2048
_LEI = re.compile(r"^(?:LEI[:\s]*)?([A-Z0-9]{18}[0-9]{2})$")
# Internal references are never accepted as attention: a subscriber cannot point a
# Focus at an Organization, Focus or Xeed by its AXIGNAL identifier.
_INTERNAL = re.compile(r"^(org|organization|focus|xeed|pending|tenant|principal)[:_]", re.I)
_PRIVATE_SUFFIXES = (".localhost", ".local", ".internal", ".invalid", ".test", ".example")
_DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class LocatorError(ValueError):
    """Invalid attention locator; ``code`` is a stable reason, never the input."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class LeiIdentifier:
    """ISO 17442 Legal Entity Identifier, checksum-verified (ISO 7064 MOD 97-10)."""

    value: str
    scheme: str = "LEI"
    authority: str = "GLEIF"


@dataclass(frozen=True, slots=True)
class AttentionLocator:
    """Classified signals. At least one is present; none is an identity decision."""

    name: str | None = None
    domain: str | None = None
    identifier: LeiIdentifier | None = None

    @property
    def name_key(self) -> str | None:
        return None if self.name is None else identity_name_key(self.name)


def _lei(token: str) -> LeiIdentifier | None:
    match = _LEI.fullmatch(token.strip().upper())
    if match is None:
        return None
    value = match.group(1)
    digits = "".join(str(int(char, 36)) for char in value)
    return LeiIdentifier(value) if int(digits) % 97 == 1 else None


def public_domain(value: str) -> str:
    """Normalized public registrable host of a website; raises LocatorError otherwise.

    One leading ``www.`` is removed so the bare and www forms of the same website
    share one binding key. Nothing else is rewritten.
    """

    text = value.strip()
    parsed = urlsplit(text if "://" in text else "https://" + text)
    if parsed.scheme not in ("http", "https"):
        raise LocatorError("UNSUPPORTED_URL_SCHEME")
    if parsed.username or parsed.password:
        raise LocatorError("CREDENTIALS_IN_URL")
    try:
        host = (parsed.hostname or "").rstrip(".")
        if parsed.port not in (None, 80, 443):
            raise LocatorError("NON_STANDARD_PORT")
    except ValueError as exc:
        raise LocatorError("INVALID_URL") from exc
    try:
        host = host.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise LocatorError("INVALID_HOSTNAME") from exc
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise LocatorError("PUBLIC_HOSTNAME_REQUIRED")
    labels = host.split(".")
    if (
        len(labels) < 2
        or len(host) > 253
        or host == "localhost"
        or host.endswith(_PRIVATE_SUFFIXES)
        or not all(_DOMAIN_LABEL.fullmatch(label) for label in labels)
        or labels[-1].isdigit()
    ):
        raise LocatorError("PUBLIC_HOSTNAME_REQUIRED")
    return host[4:] if host.startswith("www.") and len(labels) > 2 else host


def _looks_like_web(token: str) -> bool:
    lowered = token.lower()
    if "://" in lowered or lowered.startswith("www."):
        return True
    # "axignal.com" is a website; "S.L", "S.A." or "Inc." are parts of a name.
    host = lowered.split("/", 1)[0]
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    return bool(re.fullmatch(r"[a-z]{2,63}|xn--[a-z0-9-]{1,59}", tld)) and not host.endswith(".")


def parse_locator(raw: str) -> AttentionLocator:
    """Classify a subscriber locator into name / website / LEI signals."""

    if not isinstance(raw, str):
        raise LocatorError("INVALID_LOCATOR")
    text = unicodedata.normalize("NFC", raw).strip()
    if not text or len(text) > MAX_LOCATOR:
        raise LocatorError("INVALID_LOCATOR")
    if any(unicodedata.category(char) in ("Cc", "Cf") and char not in "\n\t" for char in text):
        raise LocatorError("CONTROL_CHARACTERS")
    tokens = text.split()
    if any("@" in token and "://" not in token for token in tokens):
        # An email address is not an Organization signal and never an authority.
        raise LocatorError("EMAIL_NOT_ACCEPTED")
    web = [token for token in tokens if _looks_like_web(token)]
    if len(web) > 1:
        raise LocatorError("MULTIPLE_WEBSITES")
    domain = public_domain(web[0]) if web else None
    rest = " ".join(token for token in tokens if token not in web).strip()
    identifier = _lei(rest) if rest else None
    if identifier is None and rest and _LEI.fullmatch(rest.upper()):
        # LEI-shaped but the ISO 7064 check fails: a typo, never a name to search.
        raise LocatorError("INVALID_LEI_CHECKSUM")
    if rest and _INTERNAL.match(rest):
        raise LocatorError("INTERNAL_IDENTIFIER_NOT_ACCEPTED")
    if identifier is not None:
        return AttentionLocator(domain=domain, identifier=identifier)
    if rest and len(identity_name_key(rest)) < 2:
        raise LocatorError("NAME_TOO_SHORT")
    return AttentionLocator(name=rest or None, domain=domain)
