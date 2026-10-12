"""Corporate group discoveries: parents, subsidiaries and the countries the group is in.

Registry data (GLEIF Level 2): that a subsidiary is registered in a country is OBSERVED
in the registry. The group belongs to this organization OBSERVED-ly only when its LEI is
the verified registry identity; an LEI the website merely declares keeps the attribution
POTENTIAL. Countries of subsidiaries are where the group has entities, not its market.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

MAX_LISTED = 50


def group_discoveries(
    group: Mapping[str, object], *, verified: bool, observed_at: str
) -> list[dict[str, object]]:
    state = "OBSERVED" if verified else "POTENTIAL"
    basis = {
        "lei": group.get("lei"),
        "attributedBy": "VERIFIED_LEI" if verified else "LEI_DECLARED_ON_WEBSITE",
        "readAt": group.get("readAt"),
        "rights": group.get("rights"),
    }
    out: list[dict[str, object]] = []
    parents = group.get("parents")
    if isinstance(parents, Mapping):
        for level in ("ultimate-parent", "direct-parent"):
            parent = parents.get(level)
            if isinstance(parent, Mapping) and parent.get("name"):
                if level == "direct-parent" and parents.get("ultimate-parent") == parent:
                    continue  # the same entity, said once
                out.append({
                    "kind": "RELATIONSHIP", "code": "GROUP_PARENT", "statement": str(parent["name"]),
                    "epistemicState": state, "sourceUrl": f"https://search.gleif.org/#/record/{parent.get('lei')}",
                    "excerpt": None, "observedAt": observed_at,
                    "detail": {"role": "ULTIMATE_PARENT" if level == "ultimate-parent" else "DIRECT_PARENT",
                               "parentLei": parent.get("lei"), "country": parent.get("country"),
                               "city": parent.get("city"), **basis},
                })  # fmt: skip
    children = [c for c in group.get("children") or [] if isinstance(c, Mapping)]  # type: ignore[attr-defined]
    total = group.get("childrenTotal")
    if children:
        countries = Counter(str(c.get("country")) for c in children if c.get("country"))
        out.append({
            "kind": "RELATIONSHIP", "code": "GROUP_SUBSIDIARIES",
            "statement": f"{total if isinstance(total, int) else len(children)}",
            "epistemicState": state, "sourceUrl": f"https://search.gleif.org/#/record/{group.get('lei')}",
            "excerpt": None, "observedAt": observed_at,
            "detail": {"role": "SUBSIDIARIES", "total": total, "listed": len(children),
                       "countries": dict(countries.most_common()),
                       "subsidiaries": [dict(c) for c in children[:MAX_LISTED]], **basis},
        })  # fmt: skip
        out.append({
            "kind": "DECLARED_LOCATION", "code": "GROUP_ENTITIES_IN_COUNTRIES",
            "statement": ", ".join(code for code, _n in countries.most_common()),
            "epistemicState": state, "sourceUrl": None, "excerpt": None, "observedAt": observed_at,
            "detail": {"countries": dict(countries.most_common()), "limitation":
                       "Countries where group entities are registered; not its whole market or reach.",
                       **basis},
        })  # fmt: skip
    return out
