"""Relationships and competition from published public contract awards (PLACSP)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from application.observation_intelligence.contracts import TaxonomyCode
from application.world_demand.awards import AwardRecord, normalized_name, normalized_tax_id
from application.world_demand.relations import public_award_discoveries
from pipeline.observation_intelligence.placsp import parse_feed_awards
from pipeline.world_demand.sqlite_store import SqliteWorldDemandIndex

FIXTURE = (
    Path(__file__).parents[1] / "observation_intelligence" / "fixtures" / "placsp-feed-sample.atom"
)
NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
VENT = [{"capabilityId": "ventilation-systems", "demandCodes": [["CPV", "42520000"]]}]


def test_the_real_feed_publishes_the_winner_its_tax_id_amount_and_offers() -> None:
    (award,) = parse_feed_awards(FIXTURE.read_bytes())
    assert award.winner_id == "A28063485" and award.amount == 42214.92
    assert award.offers_received == 1 and award.awarded_on == date(2026, 10, 6)
    assert award.source_url.startswith("https://") and award.buyer_name


def test_names_and_tax_ids_normalize_for_matching() -> None:
    assert normalized_name("Talleres Zitrón, S.A.") == normalized_name("TALLERES ZITRON SA")
    assert normalized_tax_id("ES-A28063485") == "A28063485"


def _award(lot: str, winner: str, tax: str | None, code: str, amount: float) -> AwardRecord:
    return AwardRecord(
        source_id="es-placsp", record_id=f"r-{lot}", lot=lot, title=f"Ventilación {lot}",
        buyer_name="Metro de Madrid" if lot != "3" else "ADIF", winner_name=winner, winner_id=tax,
        amount=amount, currency="EUR", awarded_on=date(2026, 9, int(lot) + 1), offers_received=3,
        demand_codes=(TaxonomyCode("CPV", code),), places=(TaxonomyCode("GEO", "EU/ES/ES3"),),
        source_url=f"https://contrataciondelestado.es/{lot}",
    )  # fmt: skip


def _index(tmp_path: Path) -> SqliteWorldDemandIndex:
    index = SqliteWorldDemandIndex(tmp_path / "wd.sqlite3")
    index.upsert_awards([
        _award("1", "Talleres Zitrón SA", "A33000000", "42520000", 100000.0),
        _award("2", "Talleres Zitrón SA", "A33000000", "42520000", 50000.0),
        _award("3", "Ventiladores Rivales SL", "B11111111", "42521000", 80000.0),
        _award("4", "Obras Generales SA", "A22222222", "45000000", 999999.0),
    ])  # fmt: skip
    return index


def _view(*hints: tuple[str, str]) -> dict[str, object]:
    return {"discoveries": [{"kind": "IDENTITY_HINT", "code": c, "statement": s} for c, s in hints]}


def test_contracts_won_by_tax_id_are_observed_and_competitors_stay_potential(
    tmp_path: Path,
) -> None:
    found = public_award_discoveries(
        _view(("IDENTIFIER_DECLARED:VAT", "VAT ESA33000000")),
        {"capabilities": VENT}, _index(tmp_path), now=NOW,
    )  # fmt: skip
    (won,) = [d for d in found if d["kind"] == "RELATIONSHIP"]
    assert won["epistemicState"] == "OBSERVED" and won["statement"] == "Metro de Madrid"
    assert won["detail"]["contracts"] == 2 and won["detail"]["amount"] == 150000.0  # type: ignore[index]
    competitors = [d["statement"] for d in found if d["kind"] == "COMPETITION"]
    assert competitors == ["Ventiladores Rivales SL"]  # itself excluded, other trades excluded
    assert all(d["epistemicState"] == "POTENTIAL" for d in found if d["kind"] == "COMPETITION")
    assert won["detail"]["coverageSince"] == "2026-09-02"  # type: ignore[index]


def test_a_legal_name_match_stays_potential(tmp_path: Path) -> None:
    found = public_award_discoveries(
        _view(("LEGAL_NAME_DECLARED", "TALLERES ZITRON, S.A.")), {"capabilities": VENT},
        _index(tmp_path), now=NOW,
    )  # fmt: skip
    (won,) = [d for d in found if d["kind"] == "RELATIONSHIP"]
    assert won["epistemicState"] == "POTENTIAL" and won["detail"]["matchedBy"] == "LEGAL_NAME"  # type: ignore[index]


def test_no_award_found_is_an_unknown_with_its_coverage(tmp_path: Path) -> None:
    found = public_award_discoveries(
        _view(("LEGAL_NAME_DECLARED", "Empresa Sin Contratos SL")), {"capabilities": []},
        _index(tmp_path), now=NOW,
    )  # fmt: skip
    (unknown,) = found
    assert unknown["code"] == "NO_PUBLIC_AWARDS_FOUND" and unknown["epistemicState"] == "UNKNOWN"
    assert unknown["detail"]["awardsInIndex"] == 4  # type: ignore[index]
