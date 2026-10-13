"""Identity corroboration: independent public anchors that agree on who the organization is.

Admission of identity is a registry decision (ADR-0087: only REGISTRY admits) and stays
untouched: the IDENTITY_NOT_VERIFIED unknown remains until a registry admits it. What a
subscriber can still be told, with sources, is that independent anchors point to the same
legal entity: the Wikidata item whose official website is this site, the LEI it states,
and the official register that names the entity under the identifier the site or that
item gives. A corroboration is POTENTIAL: an agreement of sources, not an admission.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

#: Corroboration needs at least this many independent anchors.
MIN_ANCHORS = 2


def _detail(d: Mapping[str, Any]) -> Mapping[str, Any]:
    detail = d.get("detail")
    return detail if isinstance(detail, Mapping) else {}


def identity_corroboration(discoveries: Sequence[object]) -> list[dict[str, object]]:
    held = [d for d in discoveries if isinstance(d, Mapping)]
    anchors: list[dict[str, object]] = []
    legal_name: str | None = None
    notoriety = next((d for d in held if d.get("code") == "WIKIPEDIA_NOTORIETY"), None)
    if notoriety is not None and _detail(notoriety).get("item"):
        anchors.append({
            "anchor": "WIKIDATA_OFFICIAL_WEBSITE",
            "value": _detail(notoriety)["item"],
            "source": notoriety.get("sourceUrl"),
            "basis": "Its official website in Wikidata is this website.",
        })  # fmt: skip
    register = next(
        (d for d in held if str(d.get("code") or "").startswith("REGISTER:")
         and _detail(d).get("sourceKind") == "OFFICIAL_REGISTER"),
        None,
    )  # fmt: skip
    if register is not None:
        detail = _detail(register)
        legal_name = str(detail.get("registerName") or "") or None
        anchors.append({
            "anchor": "OFFICIAL_REGISTER",
            "value": detail.get("identifier"),
            "source": register.get("sourceUrl"),
            "basis": f"{detail.get('source')} records this identifier"
            + (f" for {legal_name}" if legal_name else "")
            + f" (route: {detail.get('attributedBy')}).",
        })  # fmt: skip
    lei = next(
        (str(d.get("statement", "")).split(" ", 1)[-1] for d in held
         if d.get("code") == "IDENTIFIER_DECLARED:LEI"),
        None,
    )  # fmt: skip
    group = next((d for d in held if str(d.get("code") or "").startswith("GROUP_")), None)
    if lei or group is not None:
        anchors.append({
            "anchor": "LEI",
            "value": lei or _detail(group or {}).get("lei"),
            "source": None if group is None else group.get("sourceUrl"),
            "basis": "A Legal Entity Identifier links it to GLEIF's global register.",
        })  # fmt: skip
    if len(anchors) < MIN_ANCHORS:
        return []
    return [
        {
            "kind": "IDENTITY_HINT",
            "code": "IDENTITY_CORROBORATED",
            "statement": legal_name or str(anchors[0]["value"]),
            "epistemicState": "POTENTIAL",
            "sourceUrl": anchors[0]["source"],
            "excerpt": None,
            "observedAt": None,
            "detail": {
                "anchors": anchors,
                "count": len(anchors),
                "admitted": False,
                "limitation": "Independent public sources agree on which legal entity this is; "
                "a registry has not admitted the identity yet (only a registry admits).",
            },
        }
    ]
