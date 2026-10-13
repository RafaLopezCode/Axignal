"""Where the pool looks and which channel each country's rules leave open, versioned.

Conservative and operator-facing, not legal advice: a country is EMAIL only where business
email to an address an organization publishes for contact is permitted on an opt-out basis
with sender identification. Everywhere else the study is kept and nothing is sent (HOLD)
until the operator records a reviewed basis by changing this policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

CHANNEL_POLICY_VERSION = "channel-policy-v1"


class Channel(StrEnum):
    EMAIL = "EMAIL"
    HOLD = "HOLD"


@dataclass(frozen=True, slots=True)
class Market:
    iso: str
    wikidata: str
    channel: Channel
    basis: str


_EMAIL_US = "CAN-SPAM: opt-out, sender identity and postal address"
_EMAIL_CA = "CASL implied consent: address conspicuously published, message relevant to role"
_EMAIL_GB = "PECR: corporate subscribers, opt-out and sender identity"
_EMAIL_FR = "CNIL B2B: message related to the recipient's profession, opt-out"
_EMAIL_AU = "Spam Act inferred consent: address conspicuously published, relevant to role"
_EMAIL_SE = "Swedish Marketing Act: legal persons, opt-out"
_HOLD_EU = "Prior consent required or unclear for business email: kept, not sent"
_HOLD = "Not yet reviewed: kept, not sent"

#: The rotation, in order. Wikidata items are the countries (P17 values).
MARKETS: tuple[Market, ...] = (
    Market("US", "Q30", Channel.EMAIL, _EMAIL_US),
    Market("GB", "Q145", Channel.EMAIL, _EMAIL_GB),
    Market("CA", "Q16", Channel.EMAIL, _EMAIL_CA),
    Market("DE", "Q183", Channel.HOLD, _HOLD_EU),
    Market("FR", "Q142", Channel.EMAIL, _EMAIL_FR),
    Market("ES", "Q29", Channel.HOLD, _HOLD_EU),
    Market("AU", "Q408", Channel.EMAIL, _EMAIL_AU),
    Market("IT", "Q38", Channel.HOLD, _HOLD_EU),
    Market("NL", "Q55", Channel.HOLD, _HOLD),
    Market("SE", "Q34", Channel.EMAIL, _EMAIL_SE),
    Market("PT", "Q45", Channel.HOLD, _HOLD_EU),
    Market("IE", "Q27", Channel.HOLD, _HOLD),
    Market("NZ", "Q664", Channel.EMAIL, "Unsolicited Electronic Messages Act: inferred consent"),
    Market("BE", "Q31", Channel.HOLD, _HOLD),
    Market("AT", "Q40", Channel.HOLD, _HOLD_EU),
    Market("CH", "Q39", Channel.HOLD, _HOLD),
    Market("MX", "Q96", Channel.HOLD, _HOLD),
    Market("BR", "Q155", Channel.HOLD, _HOLD),
    Market("PL", "Q36", Channel.HOLD, _HOLD_EU),
    Market("DK", "Q35", Channel.HOLD, _HOLD_EU),
)


def market(iso: str | None) -> Market | None:
    wanted = (iso or "").upper()
    return next((m for m in MARKETS if m.iso == wanted), None)


def channel_for(iso: str | None) -> tuple[Channel, str]:
    found = market(iso)
    return (found.channel, found.basis) if found is not None else (Channel.HOLD, _HOLD)
