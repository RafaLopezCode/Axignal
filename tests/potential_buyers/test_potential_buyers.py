"""Potential buyers: every public route, each signal kept apart, never a score (ADR-0099)."""

from __future__ import annotations

import json
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from application.first_observation.families import family_of
from application.potential_buyers import (
    customer_names,
    excluded_names,
    group_signals,
    no_buyer_signals,
    peer_signals,
    potential_buyers,
    similar_signals,
    view_signals,
)
from pipeline.potential_buyers.wikidata import WikidataBuyerLookups

NOW = datetime(2026, 10, 14, 9, tzinfo=UTC)


def _d(
    kind: str, code: str, statement: str, state: str = "OBSERVED", **detail: Any
) -> dict[str, Any]:
    return {"kind": kind, "code": code, "statement": statement, "epistemicState": state,
            "sourceUrl": f"https://src/{code}", "excerpt": None, "observedAt": "2026-10-13",
            "detail": detail}  # fmt: skip


OWN = [
    _d("IDENTITY_HINT", "LEGAL_NAME_DECLARED", "Acme Ingeniería S.L.", "DECLARED"),
    _d("RELATIONSHIP", "CLIENT_DECLARED", "Iberdrola", "DECLARED", role="CLIENT"),
    _d("RELATIONSHIP", "CLIENT_DECLARED", "Repsol", "DECLARED", role="CLIENT"),
    _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "Ayuntamiento de Bilbao", "OBSERVED"),
    _d("RELATIONSHIP", "GROUP_SUBSIDIARIES", "2", subsidiaries=[{"name": "Acme Portugal Lda"}]),
    _d("COMPETITION", "WINS_IN_SAME_CODES", "Rival SA", "POTENTIAL",
       buyers=["Ayuntamiento de Getafe", "Ayuntamiento de Bilbao"]),
    _d("DEMAND", "RECURRING_PUBLIC_BUYER", "Ayuntamiento de Getafe", "POTENTIAL", contracts=4,
       topWinners=["Rival SA"]),
    _d("DEMAND", "POTENTIAL_PRIVATE_CUSTOMER", "Naturgy SA", "POTENTIAL",
       sector="D35", sectorLabel="Electricity and gas"),
]  # fmt: skip


def test_customers_and_exclusions_come_from_the_observation_itself() -> None:
    assert customer_names(OWN) == ["Iberdrola", "Repsol", "Ayuntamiento de Bilbao"]
    excluded = excluded_names(OWN, ["Acme"])
    for name in ("acme", "iberdrola", "repsol", "ayuntamiento de bilbao", "acme portugal lda"):
        assert name in excluded


def test_signals_combine_per_organization_ordered_by_independent_kinds_never_a_score() -> None:
    signals = [
        *view_signals(OWN),
        *peer_signals([{"name": "Peer Consulting", "clients": [
            _d("RELATIONSHIP", "CLIENT_DECLARED", "Naturgy", "DECLARED"),
            _d("RELATIONSHIP", "CLIENT_DECLARED", "Ayuntamiento de Getafe", "DECLARED"),
            _d("RELATIONSHIP", "PARTNER_DECLARED", "Microsoft", "DECLARED"),
        ]}]),
        *group_signals("Iberdrola", {"readAt": "2026-10-10", "parents": {}, "children": [
            {"name": "Iberdrola Clientes SAU", "lei": "L1", "country": "ES"},
            {"name": "Avangrid Inc", "lei": "L2", "country": "US"},
            {"name": "Repsol", "lei": "L3", "country": "ES"},  # already a customer
        ]}, countries=["ES"]),
        *similar_signals(
            {"Iberdrola": {"industries": ["Q1"], "countries": ["Q29"]}},
            [{"industry": "Q1", "country": "Q29", "industryLabel": "energy industry",
              "countryLabel": "Spain", "readAt": "2026-10-01", "organizations": [
                  {"item": "Q9", "label": "Naturgy", "website": "https://naturgy.com", "lei": None},
                  {"item": "Q8", "label": "Endesa", "website": "https://endesa.com", "lei": "E1"},
              ]}],
        ),
    ]  # fmt: skip
    found = potential_buyers(signals, exclude=excluded_names(OWN, ["Acme"]), observed_at="t")
    names = [d["statement"] for d in found]
    # Getafe: buys from a competitor (award and a peer's website) and is a public buyer.
    assert names[1] == "Ayuntamiento de Getafe"
    getafe = found[1]["detail"]
    assert getafe["signalTypes"] == ["CUSTOMER_OF_COMPETITOR", "PUBLIC_BUYER_OF_CATEGORY"]
    assert {s["via"] for s in getafe["signals"]} >= {"Rival SA", "Peer Consulting"}
    # Naturgy (legal form aside) gathers three kinds: competitor's client, similar, sector.
    naturgy = next(d for d in found if d["statement"].startswith("Naturgy"))
    assert naturgy["detail"]["independentSignals"] == 3
    assert naturgy["detail"]["identifiers"]["wikidata"] == "Q9"
    assert names[0] == naturgy["statement"]  # three kinds of signal agree: first
    # Existing customers, its own group and partners of peers are never candidates.
    for never in (
        "Repsol",
        "Iberdrola",
        "Ayuntamiento de Bilbao",
        "Microsoft",
        "Acme Portugal Lda",
    ):
        assert never not in names
    # Only subsidiaries in the subscriber's countries: a large group elsewhere is noise.
    assert "Iberdrola Clientes SAU" in names and "Avangrid Inc" not in names
    assert all(d["epistemicState"] == "POTENTIAL" and family_of(d) == "demand" for d in found)
    assert all("score" not in d["detail"] for d in found)


def test_no_signal_is_an_unknown_never_no_demand() -> None:
    unknown = no_buyer_signals(has_customers=False, observed_at="t")
    assert unknown["epistemicState"] == "UNKNOWN" and family_of(unknown) == "demand"
    assert "not an absence of demand" in unknown["detail"]["limitation"]


class _Wikidata:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def __call__(self, url: str) -> dict[str, Any]:
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        self.calls.append(q)
        if q["action"] == "wbsearchentities":
            hits = {
                "Iberdrola": [{"id": "Q1", "match": {"text": "Iberdrola"}},
                              {"id": "Q2", "match": {"text": "Iberdrola Tower"}}],
                "Mercury": [{"id": "Q3", "match": {"text": "Mercury"}},
                            {"id": "Q4", "match": {"text": "mercury"}}],
                "Nobody": [{"id": "Q5", "match": {"text": "Nobody"}}],
            }  # fmt: skip
            return {"search": hits.get(q["search"], [])}
        if q["action"] == "query":
            return {"query": {"search": [{"title": "Q20"}, {"title": "Q10"}, {"title": "Q30"}]}}
        claims = {
            "Q1": {"P452": "Q100", "P17": "Q29", "P1278": "LEI1", "P856": "https://iberdrola.com"},
            "Q2": {"P452": "Q100", "P17": "Q29"},
            "Q3": {"P452": "Q100"}, "Q4": {"P1278": "LEI4"}, "Q5": {"P17": "Q29"},
            "Q10": {"P452": "Q100", "P17": "Q29"}, "Q20": {"P452": "Q100", "P17": "Q29"},
            "Q30": {"P452": "Q100", "P17": "Q29", "P576": "+2001-01-01T00:00:00Z"},
        }  # fmt: skip
        entities: dict[str, Any] = {}
        for qid in q["ids"].split("|"):
            built: dict[str, Any] = {}
            for prop, value in claims.get(qid, {}).items():
                data = {"id": value} if str(value).startswith("Q") else value
                built[prop] = [{"rank": "normal", "mainsnak": {"datavalue": {"value": data}}}]
            entities[qid] = {"labels": {"en": {"value": f"Label {qid}"}}, "claims": built}
        return {"entities": entities}


def test_lookups_accept_one_exact_organization_and_keep_search_order(tmp_path: Path) -> None:
    fetch = _Wikidata()
    lookups = WikidataBuyerLookups(tmp_path / "b.sqlite3", fetch=fetch, clock=lambda: NOW)
    for name in ("Iberdrola", "Mercury", "Nobody"):
        lookups.request_customer(name)
        assert lookups.customer(name) is None  # reads only use what is stored
    lookups.request_peers("Q100", "Q29")
    assert lookups.run() == 4
    iberdrola = lookups.customer("IBERDROLA")
    assert iberdrola is not None and iberdrola["item"]["item"] == "Q1"  # "Tower" is not exact
    assert iberdrola["item"]["lei"] == "LEI1" and iberdrola["matchedBy"] == "EXACT_LABEL_OR_ALIAS"
    mercury = lookups.customer("Mercury")
    assert mercury is not None and mercury["item"] is None and mercury["ambiguous"] == ["Q3", "Q4"]
    nobody = lookups.customer("Nobody")
    assert nobody is not None and nobody["item"] is None  # no industry nor LEI: not an org
    peers = lookups.peers("Q100", "Q29")
    assert peers is not None
    assert [p["item"] for p in peers["organizations"]] == ["Q20", "Q10"]  # Q30 dissolved
    assert peers["industryLabel"] == "Label Q100" and peers["rights"] == "Wikidata, CC0 1.0"
    assert lookups.run() == 0  # refreshed monthly, not on every read


def test_runtime_derives_buyers_from_portfolio_peers_customers_and_groups(tmp_path: Path) -> None:
    from tools.runtime.first_observation import FirstObservationRuntime

    capabilities = [{"demandCodes": [["CPV", "72260000"]]}]
    peer_proof = {"target": {"name": "Peer Consulting"}, "capabilities": capabilities,
                  "discoveries": [_d("RELATIONSHIP", "CLIENT_DECLARED", "Endesa", "DECLARED")]}  # fmt: skip
    other_proof = {"target": {"name": "Bakery"}, "capabilities": [{"demandCodes": [["CPV", "15810000"]]}],
                   "discoveries": [_d("RELATIONSHIP", "CLIENT_DECLARED", "Hotel Sol", "DECLARED")]}  # fmt: skip
    proofs = {"peer": peer_proof, "bakery": other_proof}
    store = SimpleNamespace(
        observed_targets=lambda tenant: frozenset({"self", "peer", "bakery"}),
        proof=lambda tenant, ref: proofs.get(ref),
    )
    buyers = SimpleNamespace(
        request_customer=lambda name, languages=(): None,
        customer=lambda name: {"item": {"item": "Q1", "industries": ["Q100"], "countries": ["Q29"],
                                        "lei": "LEI1"}} if name == "Iberdrola" else None,
        request_peers=lambda industry, country: None,
        peers=lambda industry, country: {"industry": industry, "country": country,
                                         "organizations": [{"item": "Q8", "label": "Endesa"}]},
        request_sector=lambda sector, nace, country: None, sector=lambda sector, country: None,
        industry_nace=lambda qid: [],
    )  # fmt: skip
    groups = SimpleNamespace(group=lambda lei: {"children": [{"name": "Iberdrola Clientes SAU",
                                                              "country": "ES", "lei": "L9"}]})  # fmt: skip
    fake = SimpleNamespace(store=store, _buyers=buyers, _groups=groups, _item_facts=lambda v: None)
    view = {"observedAt": "2026-10-14", "target": {"name": "Acme"},
            "discoveries": [_d("RELATIONSHIP", "CLIENT_DECLARED", "Iberdrola", "DECLARED")]}  # fmt: skip
    proof = {"capabilities": capabilities, "attentionScopes": [{"jurisdiction": "EU/ES"}]}
    out = FirstObservationRuntime._with_potential_buyers(fake, view, proof, "t1", "self")  # type: ignore[arg-type]
    found = {d["statement"]: d for d in out["discoveries"] if d["code"] == "POTENTIAL_BUYER"}
    assert set(found) == {"Endesa", "Iberdrola Clientes SAU"}  # the bakery's client is not
    assert found["Endesa"]["detail"]["signalTypes"] == [
        "CUSTOMER_OF_COMPETITOR",
        "SIMILAR_TO_CUSTOMERS",
    ]
    # Nothing to derive from: the unknown says why, and nothing is invented.
    bare = FirstObservationRuntime._with_potential_buyers(
        SimpleNamespace(store=store, _buyers=None, _groups=None, _item_facts=lambda v: None),
        {"observedAt": "t", "discoveries": [_d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED", "x")]},
        {},
        "t1",
        "self",
    )  # type: ignore[arg-type]
    assert [d["code"] for d in bare["discoveries"]] == [
        "PUBLIC_WEBSITE_OBSERVED",
        "NO_BUYER_SIGNALS",
    ]
    json.dumps(out)  # the view stays serializable


def test_peers_share_a_specific_activity_and_badges_are_never_customers() -> None:
    from application.potential_buyers import same_activity

    assert same_activity(["72260000", "79341000"], ["72262000"])  # software development
    assert not same_activity(["72000000"], ["72000000"])  # a broad division is not a peer
    assert not same_activity(["72413000"], ["72260000"])  # web design vs software
    stored = [_d("RELATIONSHIP", "CLIENT_DECLARED", "Google Partner", "DECLARED"),
              _d("RELATIONSHIP", "CLIENT_DECLARED", "Visit our Facebook page", "DECLARED"),
              _d("RELATIONSHIP", "CLIENT_DECLARED", "HP", "DECLARED")]  # fmt: skip
    assert customer_names(stored) == ["HP"]  # observations stored before v1.1 too
    assert [s.candidate for s in peer_signals([{"name": "P", "clients": stored}])] == ["HP"]


def test_buying_sectors_and_their_nace_codes_come_from_the_input_output_table() -> None:
    from application.value_chain import buying_sectors, nace_codes

    assert nace_codes("C10-12") == ["10", "11", "12"]
    assert nace_codes("F") == ["F", "41", "42", "43"]
    sectors = [code for code, _share in buying_sectors("C10-12")]
    assert sectors and "C10-12" not in sectors  # never its own sector: those compete
    assert not {"HOUSEHOLDS", "GOVERNMENT", "O", "P", "Q86"} & set(sectors)


def test_sector_route_needs_no_customer_and_alternates_sectors(tmp_path: Path) -> None:
    from tools.runtime.first_observation import FirstObservationRuntime, _countries_of

    assert _countries_of([], {"attentionScopes": [{"jurisdiction": "US/US-NY"},
                                                  {"jurisdiction": "EU/ES"}]}) == ["US", "ES"]  # fmt: skip
    requested: list[tuple[str, tuple[str, ...], str]] = []

    def sector(code: str, country: str) -> dict[str, Any]:
        return {"sector": code, "country": country, "countryLabel": "Germany", "readAt": "t",
                "organizations": [{"item": f"Q{code}{i}", "label": f"{code} org {i}",
                                   "website": f"https://{i}.example"} for i in range(3)]}  # fmt: skip

    buyers = SimpleNamespace(
        request_customer=lambda name, languages=(): None, customer=lambda name: None,
        request_peers=lambda i, c: None, peers=lambda i, c: None,
        request_sector=lambda code, nace, country: requested.append((code, tuple(nace), country)),
        sector=sector, industry_nace=lambda qid: ["10.1"] if qid == "Q540912" else [],
    )  # fmt: skip
    store = SimpleNamespace(observed_targets=lambda tenant: frozenset(), proof=lambda t, r: None)
    facts = {"facts": {"industry": {"value": "Q540912"}, "country": {"value": "Q183"}}}
    fake = SimpleNamespace(store=store, _buyers=buyers, _groups=None, _item_facts=lambda v: facts)
    view = {"observedAt": "t", "target": {"name": "Ritter"},
            "discoveries": [_d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED", "ritter")]}  # fmt: skip
    out = FirstObservationRuntime._with_potential_buyers(fake, view, {}, "t1", "self")  # type: ignore[arg-type]
    # Industry from Wikidata (food, NACE 10.1) and its home country (Q183) are enough.
    assert requested and all(country == "Q183" for _c, _n, country in requested)
    found = [d for d in out["discoveries"] if d["code"] == "POTENTIAL_BUYER"]
    assert found and all(
        d["detail"]["signalTypes"] == ["SECTOR_BUYS_FROM_ITS_SECTOR"] for d in found
    )
    first_sectors = [d["detail"]["signals"][0]["via"] for d in found[:2]]
    assert first_sectors[0] != first_sectors[1]  # sectors alternate, none fills the list
    assert "Eurostat" in found[0]["detail"]["signals"][0]["basis"]
    assert not [d for d in out["discoveries"] if d["code"] == "NO_BUYER_SIGNALS"]


def test_sector_lookup_maps_nace_to_industries_and_keeps_actionable_organizations(
    tmp_path: Path,
) -> None:
    def claim(value: Any) -> list[dict[str, Any]]:
        data = {"id": value} if str(value).startswith("Q") else value
        return [{"rank": "normal", "mainsnak": {"datavalue": {"value": data}}}]

    items = {
        "Q10": {"P4496": "10"}, "Q101": {"P4496": "10.1"}, "Q46": {"P4496": "46"},
        "Q183": {},
        "Q1": {"P452": "Q10", "P17": "Q183", "P856": "https://small.example"},
        "Q2": {"P452": "Q101", "P17": "Q183", "P856": "https://big.example"},
        "Q3": {"P452": "Q10", "P17": "Q183"},  # no website, no LEI: not actionable
    }  # fmt: skip
    links = {"Q1": 2, "Q2": 30}

    def fetch(url: str) -> dict[str, Any]:
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        if q["action"] == "query" and q["srsearch"] == "haswbstatement:P4496":
            return {"query": {"search": [{"title": t} for t in ("Q10", "Q101", "Q46")]}}
        if q["action"] == "query" and q["srsearch"].startswith("haswbstatement:P297"):
            return {"query": {"search": [{"title": "Q183"}]}}
        if q["action"] == "query":
            assert "P452=Q10|P452=Q101" in q["srsearch"] and "P17=Q183" in q["srsearch"]
            return {"query": {"search": [{"title": t} for t in ("Q1", "Q2", "Q3")]}}
        return {"entities": {
            qid: {"labels": {"en": {"value": f"Label {qid}"}},
                  "sitelinks": {f"w{i}": {} for i in range(links.get(qid, 0))},
                  "claims": {p: claim(v) for p, v in items.get(qid, {}).items()}}
            for qid in q["ids"].split("|")
        }}  # fmt: skip

    lookups = WikidataBuyerLookups(tmp_path / "b.sqlite3", fetch=fetch, clock=lambda: NOW)
    assert lookups.industry_nace("Q101") == []  # no map yet: it is requested, not fetched
    lookups.request_sector("C10-12", ["10", "11", "12"], "de")
    lookups.run()
    assert lookups.industry_nace("Q101") == ["10.1"]
    reading = lookups.sector("C10-12", "DE")
    assert reading is not None and reading["industries"] == ["Q10", "Q101"]  # exact code first
    assert [o["item"] for o in reading["organizations"]] == ["Q2", "Q1"]  # most documented first
    assert reading["countryLabel"] == "Label Q183"
