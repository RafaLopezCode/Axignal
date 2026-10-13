"""Economic magnitudes as discoveries, each with its source, date and attribution.

A figure read from a secondary, community-edited source (Wikidata) is shown as what that
source states, with its reference year; it is not an official account. Attribution to this
organization is OBSERVED only through its verified LEI; through an LEI its website merely
declares, it stays POTENTIAL. A magnitude without a reference year says so.
"""

from __future__ import annotations

from collections.abc import Mapping

ORDER = (
    "revenue",
    "netProfit",
    "employees",
    "marketCapitalization",
    "inception",
    "stockExchange",
    "industry",
)


def economic_discoveries(
    facts: Mapping[str, object], *, verified: bool, observed_at: str
) -> list[dict[str, object]]:
    item = facts.get("item")
    values = facts.get("facts")
    if not item or not isinstance(values, Mapping):
        return []
    out: list[dict[str, object]] = []
    for name in ORDER:
        fact = values.get(name)
        if not isinstance(fact, Mapping) or fact.get("value") is None:
            continue
        out.append(
            {
                "kind": "ECONOMIC_FACT",
                "code": f"WIKIDATA:{name}",
                "statement": str(fact.get("valueLabel") or fact.get("value")),
                "epistemicState": "OBSERVED" if verified else "POTENTIAL",
                "sourceUrl": f"https://www.wikidata.org/wiki/{item}",
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "fact": name,
                    "value": fact.get("value"),
                    "unit": fact.get("unitLabel") or fact.get("unit"),
                    "year": fact.get("year"),
                    "source": "Wikidata",
                    "sourceKind": "SECONDARY_COMMUNITY_EDITED",
                    "item": item,
                    "alsoCarryingLei": facts.get("alsoCarryingLei"),
                    "attributedBy": "VERIFIED_LEI" if verified else "LEI_DECLARED_ON_WEBSITE",
                    "rights": facts.get("rights"),
                    "readAt": facts.get("readAt"),
                    "limitation": "What Wikidata states, with its reference year; not an official "
                    "account and possibly outdated.",
                },
            }
        )
    return out


#: Legal-form and filler words ignored when comparing a register's name with the site's.
_FORMS = frozenset(
    [
        "sa",
        "sas",
        "sasu",
        "sarl",
        "eurl",
        "sca",
        "snc",
        "se",
        "sl",
        "slu",
        "ag",
        "gmbh",
        "kg",
        "ug",
        "ohg",
        "spa",
        "srl",
        "bv",
        "nv",
        "ab",
        "as",
        "asa",
        "oy",
        "oyj",
        "aps",
        "ltd",
        "limited",
        "plc",
        "llp",
        "lp",
        "llc",
        "inc",
        "incorporated",
        "corp",
        "corporation",
        "co",
        "company",
        "the",
        "group",
        "holding",
        "holdings",
    ]
)


def _tokens(name: str) -> list[str]:
    import re
    import unicodedata

    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().casefold()
    return [t for t in re.findall(r"[a-z0-9]+", folded) if t not in _FORMS]


def same_organization_name(register_name: str | None, declared: list[str]) -> bool:
    """The register's name and a name the organization declares are the same name."""
    theirs = _tokens(register_name or "")
    if not theirs:
        return False
    for name in declared:
        ours = _tokens(name)
        if ours and (ours == theirs or (set(ours) <= set(theirs) and ours[0] == theirs[0])
                     or (set(theirs) <= set(ours) and ours[0] == theirs[0])):  # fmt: skip
            return True
    return False


REGISTER_ORDER = (
    "revenue", "netProfit", "assets", "employees", "employeesBand", "sizeCategory",
    "accountsType", "inception", "establishments", "activity", "status",
)  # fmt: skip


def register_discoveries(
    record: Mapping[str, object], *, attributed: bool, via: str, observed_at: str
) -> list[dict[str, object]]:
    """Facts an official business register holds for the identifier the organization uses.

    OBSERVED when the identifier comes from the organization itself (its website or its
    verified LEI) and the register's name is the name it declares; otherwise POTENTIAL.
    """
    values = record.get("facts")
    if not isinstance(values, Mapping):
        return []
    out: list[dict[str, object]] = []
    for name in REGISTER_ORDER:
        fact = values.get(name)
        if not isinstance(fact, Mapping) or fact.get("value") is None:
            continue
        out.append(
            {
                "kind": "ECONOMIC_FACT",
                "code": f"REGISTER:{record.get('scheme')}:{name}",
                "statement": str(fact.get("label") or fact.get("value")),
                "epistemicState": "OBSERVED" if attributed else "POTENTIAL",
                "sourceUrl": record.get("url"),
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "fact": name,
                    "value": fact.get("value"),
                    "unit": fact.get("unit"),
                    "year": fact.get("year"),
                    "period": fact.get("period"),
                    "filing": fact.get("filing"),
                    "label": fact.get("label"),
                    "source": record.get("register"),
                    "sourceKind": "OFFICIAL_REGISTER",
                    "registerName": record.get("name"),
                    "identifier": f"{record.get('scheme')} {record.get('id')}",
                    "attributedBy": via if attributed else f"{via}_NAME_NOT_CONFIRMED",
                    "rights": record.get("rights"),
                    "readAt": record.get("readAt"),
                    "limitation": "As the official register states it for this identifier, "
                    "with its reference period; registers lag the present.",
                },
            }
        )
    return out


def registered_activity(discoveries: list[object]) -> list[object]:
    """When the website does not establish what it does but the official register does,
    the register's activity classification answers the value family (with its source).

    It keeps the register fact's state (OBSERVED only when attributed) and replaces the
    ACTIVITY_NOT_ESTABLISHED unknown; a website reading, when present, always prevails.
    """
    held = [d for d in discoveries if isinstance(d, Mapping)]
    if any(d.get("kind") == "ACTIVITY" for d in held):
        return discoveries
    fact = next(
        (
            d for d in held
            if d.get("kind") == "ECONOMIC_FACT"
            and isinstance(d.get("detail"), Mapping)
            and d["detail"].get("fact") == "activity"
            and d["detail"].get("sourceKind") == "OFFICIAL_REGISTER"
        ),
        None,
    )  # fmt: skip
    if fact is None:
        return discoveries
    detail = fact["detail"]
    activity = {
        "kind": "ACTIVITY",
        "code": "REGISTERED_ACTIVITY",
        "statement": str(detail.get("label") or detail.get("value")),
        "epistemicState": fact.get("epistemicState"),
        "sourceUrl": fact.get("sourceUrl"),
        "excerpt": f"{detail.get('source')}: {detail.get('value')}",
        "observedAt": fact.get("observedAt"),
        "detail": {
            "classification": detail.get("value"),
            "source": detail.get("source"),
            "identifier": detail.get("identifier"),
            "method": "OFFICIAL_REGISTER",
            "limitation": "The classification the organization registered; it may not "
            "reflect everything it offers today.",
        },
    }
    kept = [
        d for d in discoveries
        if not (isinstance(d, Mapping) and d.get("code") == "ACTIVITY_NOT_ESTABLISHED")
    ]  # fmt: skip
    return [*kept, activity]
