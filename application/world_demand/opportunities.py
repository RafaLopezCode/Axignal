"""Business opportunities read from public contract awards: who buys, who partners.

Two derived readings, both POTENTIAL unless an official publication names this
organization:

* Recurrent public buyers: bodies that award, again and again, contracts under the
  classification codes of what this organization does, and have not awarded it one in
  the awards held. Each is shown with the dimensions behind it (contracts, amount,
  recency, how many offers they usually receive, how many different winners, whether
  it buys in the organization's area), ordered by a stated deterministic policy — never
  a probability of winning, never a lead.
* Partners in public contracts: companies awarded the same contract lot together with
  this organization, or in a temporary joint venture (UTE) whose name contains it. A
  joint award by its tax identifier is OBSERVED; a joint venture read from a name only
  stays POTENTIAL.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from statistics import median

from application.observation_intelligence.contracts import TaxonomyCode
from application.world_demand.awards import AwardRecord, normalized_name

BUYER_POLICY = "recurrent-buyers-v1: in-area first, then contracts, then amount"
MAX_BUYERS = 8
MIN_BUYER_CONTRACTS = 2
MAX_PARTNERS = 8
_UTE = re.compile(r"\b(?:u\.?\s?t\.?\s?e\.?|union temporal de empresas)\b", re.IGNORECASE)
_SPLIT = re.compile(r"\s*(?:,|/|\s-\s|\s\u2013\s|\by\b|\band\b|&|\+)\s*", re.IGNORECASE)


def _wire(award: AwardRecord) -> dict[str, object]:
    return {
        "title": award.title,
        "buyer": award.buyer_name,
        "winner": award.winner_name,
        "amount": award.amount,
        "currency": award.currency,
        "awardedOn": None if award.awarded_on is None else award.awarded_on.isoformat(),
        "offersReceived": award.offers_received,
        "url": award.source_url,
    }


def _in_area(award: AwardRecord, scopes: Sequence[TaxonomyCode]) -> bool:
    return any(place.within(scope) for place in award.places for scope in scopes)


def recurrent_buyers(
    matched: Iterable[AwardRecord],
    *,
    own_buyers: set[str],
    scopes: Sequence[TaxonomyCode],
    observed_at: str,
    coverage: Mapping[str, object],
) -> list[dict[str, object]]:
    by_buyer: dict[str, list[AwardRecord]] = defaultdict(list)
    for award in matched:
        if award.buyer_name and award.buyer_name not in own_buyers:
            by_buyer[award.buyer_name].append(award)
    rows = []
    for buyer, awards in by_buyer.items():
        if len(awards) < MIN_BUYER_CONTRACTS:
            continue
        in_area = sum(_in_area(a, scopes) for a in awards)
        amount = round(sum(a.amount or 0 for a in awards), 2)
        rows.append((in_area > 0, len(awards), amount, buyer, awards, in_area))
    rows.sort(key=lambda r: (not r[0], -r[1], -r[2], r[3]))
    out: list[dict[str, object]] = []
    for _area, count, amount, buyer, awards, in_area in rows[:MAX_BUYERS]:
        offers = [a.offers_received for a in awards if a.offers_received]
        winners: dict[str, int] = defaultdict(int)
        for a in awards:
            winners[a.winner_name] += 1
        dated = sorted((a for a in awards if a.awarded_on), key=lambda a: a.awarded_on or "")
        out.append(
            {
                "kind": "DEMAND",
                "code": "RECURRING_PUBLIC_BUYER",
                "statement": buyer,
                "epistemicState": "POTENTIAL",
                "sourceUrl": awards[0].source_url,
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "buyer": buyer,
                    "contracts": count,
                    "amount": amount,
                    "currency": next((a.currency for a in awards if a.currency), None),
                    "lastAwardedOn": None
                    if not dated
                    else (dated[-1].awarded_on.isoformat() if dated[-1].awarded_on else None),
                    "medianOffers": None if not offers else median(offers),
                    "distinctWinners": len(winners),
                    "topWinners": [w for w, _n in sorted(winners.items(), key=lambda x: -x[1])][:3],
                    "contractsInArea": in_area,
                    "awards": [_wire(a) for a in dated[-5:][::-1]],
                    "policy": BUYER_POLICY,
                    "basis": "Awards contracts under the classification codes of this "
                    "organization's activity and has not awarded it one in the awards held. "
                    "A buyer that could need what it offers: not a lead, not a probability.",
                    **coverage,
                },
            }
        )
    return out


def ute_members(name: str) -> list[str]:
    """Member names a joint venture's own name lists ("UTE ACME - BETA"), best effort."""
    if not _UTE.search(name):
        return []
    rest = _UTE.sub(" ", name)
    rest = re.sub(r"\(.*?\)", " ", rest)
    parts = [p.strip(" .-") for p in _SPLIT.split(rest)]
    return [p for p in parts if len(normalized_name(p)) >= 3]


def contract_partners(
    own_awards: Sequence[AwardRecord],
    lot_awards: Sequence[AwardRecord],
    ute_awards: Sequence[AwardRecord],
    *,
    own_ids: set[str],
    own_names: set[str],
    observed_at: str,
) -> list[dict[str, object]]:
    partners: dict[str, dict[str, object]] = {}

    def add(name: str, award: AwardRecord, state: str, how: str, partner_id: str | None) -> None:
        key = partner_id or normalized_name(name)
        if not key or key in own_ids or normalized_name(name) in own_names:
            return
        entry = partners.setdefault(
            key,
            {"name": name, "id": partner_id, "state": state, "how": how, "awards": []},
        )
        if state == "OBSERVED":
            entry["state"], entry["how"] = state, how
        awards = entry["awards"]
        assert isinstance(awards, list)
        if len(awards) < 5:
            awards.append(_wire(award))

    lots = {(a.source_id, a.record_id, a.lot) for a in own_awards}
    for award in lot_awards:
        if (award.source_id, award.record_id, award.lot) in lots:
            by_id = bool(award.winner_id) and any(a.winner_id in own_ids for a in own_awards)
            add(award.winner_name, award, "OBSERVED" if by_id else "POTENTIAL",
                "SAME_LOT_JOINT_AWARD", award.winner_id)  # fmt: skip
    for award in ute_awards:
        members = ute_members(award.winner_name)
        if not any(normalized_name(m) in own_names for m in members):
            continue
        for member in members:
            add(member, award, "POTENTIAL", "JOINT_VENTURE_NAME", None)
    out: list[dict[str, object]] = []
    ranked = sorted(partners.values(), key=lambda p: (p["state"] != "OBSERVED", -len(p["awards"])))  # type: ignore[arg-type]
    for partner in ranked[:MAX_PARTNERS]:
        awards = partner["awards"]
        assert isinstance(awards, list)
        out.append(
            {
                "kind": "RELATIONSHIP",
                "code": "PUBLIC_CONTRACT_PARTNER",
                "statement": partner["name"],
                "epistemicState": partner["state"],
                "sourceUrl": awards[0]["url"] if awards else None,
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "role": "PARTNER",
                    "partnerId": partner["id"],
                    "how": partner["how"],
                    "contracts": len(awards),
                    "awards": awards,
                    "basis": "Awarded a public contract together with this organization "
                    "(same lot or joint venture). A past joint award, not a current alliance.",
                },
            }
        )
    return out
