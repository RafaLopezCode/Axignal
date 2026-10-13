"""Business opportunities from awards: recurrent buyers, partners, and the history behind."""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

from application.first_observation.registry_ids import registry_identifiers
from application.observation_intelligence.contracts import TaxonomyCode
from application.world_demand.awards import AwardRecord
from application.world_demand.opportunities import ute_members
from application.world_demand.relations import public_award_discoveries
from pipeline.observation_intelligence.placsp_archive import PlacspAwardsBackfill, months_back
from pipeline.world_demand.sqlite_store import SqliteWorldDemandIndex

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
CAPS = [{"capabilityId": "security-guarding", "demandCodes": [["CPV", "79710000"]]}]
FIXTURE = (
    Path(__file__).parents[1] / "observation_intelligence" / "fixtures" / "placsp-feed-sample.atom"
)


def _award(record: str, lot: str, buyer: str, winner: str, tax: str | None, *, day: int = 1,
           place: str = "EU/ES/ES3", amount: float = 10000.0, offers: int = 2) -> AwardRecord:  # fmt: skip
    return AwardRecord(
        source_id="es-placsp", record_id=record, lot=lot, title=f"Vigilancia {record}",
        buyer_name=buyer, winner_name=winner, winner_id=tax, amount=amount, currency="EUR",
        awarded_on=date(2026, 9, day), offers_received=offers,
        demand_codes=(TaxonomyCode("CPV", "79710000"),), places=(TaxonomyCode("GEO", place),),
        source_url=f"https://contrataciondelestado.es/{record}/{lot}",
    )  # fmt: skip


def _index(tmp_path: Path) -> SqliteWorldDemandIndex:
    index = SqliteWorldDemandIndex(tmp_path / "wd.sqlite3")
    index.upsert_awards([
        # Its own awards: one alone, one lot shared with a partner.
        _award("r1", "1", "Ayuntamiento A", "Segur SL", "B00000000"),
        _award("r2", "1", "Ayuntamiento A", "Segur SL", "B00000000"),
        _award("r2", "1", "Ayuntamiento A", "Aliado SA", "A11111111"),
        # A recurrent buyer in its area that never awarded it.
        _award("r3", "1", "Ministerio B", "Rival SL", "B22222222", amount=50000.0),
        _award("r4", "1", "Ministerio B", "Otro SL", "B33333333", amount=70000.0, offers=4),
        _award("r5", "1", "Ministerio B", "Rival SL", "B22222222", amount=20000.0),
        # Buys often too, but outside its area: ranked after the in-area buyer.
        _award("r6", "1", "Cabildo C", "Rival SL", "B22222222", place="EU/ES/ES7", amount=9e6),
        _award("r7", "1", "Cabildo C", "Rival SL", "B22222222", place="EU/ES/ES7", amount=9e6),
        _award("r8", "1", "Cabildo C", "Rival SL", "B22222222", place="EU/ES/ES7", amount=9e6),
        # A one-off buyer is not recurrent.
        _award("r9", "1", "Diputación D", "Rival SL", "B22222222"),
        # A joint venture whose name lists it.
        _award("r10", "1", "Puerto E", "UTE SEGUR - VIGILA NORTE", "U44444444"),
    ])  # fmt: skip
    return index


def _view() -> dict[str, object]:
    return {
        "observedAt": NOW.isoformat(),
        "target": {"name": "Segur"},
        "discoveries": [
            {"kind": "IDENTITY_HINT", "code": "IDENTIFIER_DECLARED:ES_CIF",
             "statement": "ES_CIF B00000000"},
            {"kind": "IDENTITY_HINT", "code": "LEGAL_NAME_DECLARED", "statement": "Segur SL"},
        ],
    }  # fmt: skip


def test_recurrent_buyers_never_include_its_clients_and_in_area_comes_first(
    tmp_path: Path,
) -> None:
    proof = {"capabilities": CAPS, "attentionScopes": [{"jurisdiction": "EU/ES/ES3"}]}
    found = public_award_discoveries(_view(), proof, _index(tmp_path), now=NOW)
    buyers = [d for d in found if d["code"] == "RECURRING_PUBLIC_BUYER"]
    assert [b["statement"] for b in buyers] == ["Ministerio B", "Cabildo C"]
    first = buyers[0]["detail"]
    assert isinstance(first, dict)
    assert first["contracts"] == 3 and first["distinctWinners"] == 2
    assert first["medianOffers"] == 2 and first["contractsInArea"] == 3
    assert all(b["epistemicState"] == "POTENTIAL" for b in buyers)
    clients = [d["statement"] for d in found if d["code"] == "PUBLIC_CONTRACTS_WON"]
    assert clients == ["Ayuntamiento A"]


def test_partners_by_shared_lot_are_observed_and_by_joint_venture_name_potential(
    tmp_path: Path,
) -> None:
    proof = {"capabilities": CAPS, "attentionScopes": [{"jurisdiction": "EU/ES"}]}
    found = public_award_discoveries(_view(), proof, _index(tmp_path), now=NOW)
    partners = {d["statement"]: d for d in found if d["code"] == "PUBLIC_CONTRACT_PARTNER"}
    assert partners["Aliado SA"]["epistemicState"] == "OBSERVED"
    assert partners["VIGILA NORTE"]["epistemicState"] == "POTENTIAL"
    assert "Segur SL" not in partners and "SEGUR" not in partners


def test_joint_venture_members_are_read_from_its_name() -> None:
    assert ute_members("UTE ACME SERVICIOS - BETA LIMPIEZAS") == [
        "ACME SERVICIOS",
        "BETA LIMPIEZAS",
    ]
    assert ute_members("U.T.E. Gamma, Delta y Omega") == ["Gamma", "Delta", "Omega"]
    assert ute_members("Acme Servicios SL") == []


def test_spanish_cif_needs_its_control_character() -> None:
    assert registry_identifiers("CIF º B15726177") == [("ES_CIF", "B15726177")]
    assert registry_identifiers("C.I.F.: A-28430882") == [("ES_CIF", "A28430882")]
    assert registry_identifiers("CIF A28430883") == []


def test_the_awards_history_is_backfilled_month_by_month_once(tmp_path: Path) -> None:
    index = SqliteWorldDemandIndex(tmp_path / "wd.sqlite3")
    fetched: list[str] = []

    def download(url: str, target: Path) -> None:
        fetched.append(url)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as bundle:
            bundle.writestr("licitaciones_1.atom", FIXTURE.read_bytes())
            bundle.writestr("readme.txt", "ignored")
        target.write_bytes(buffer.getvalue())

    backfill = PlacspAwardsBackfill(index.upsert_awards, tmp_path / "wd.sqlite3",
                                    tmp_path / "tmp", months=2, download=download,
                                    clock=lambda: NOW)  # fmt: skip
    assert months_back(NOW.date(), 2) == ["202609", "202608"]
    assert backfill.run_one() == 1 and fetched[0].endswith("_202609.zip")
    assert backfill.run_one() == 1 and backfill.run_one() is None
    assert [m for m, *_ in backfill.status()] == ["202609", "202608"]
    since, held = index.awards_coverage("EU/ES")
    assert since == date(2026, 8, 1) and held == 1
    assert not any((tmp_path / "tmp").iterdir())  # the archive is never kept


def test_a_failed_month_is_recorded_and_retried_later(tmp_path: Path) -> None:
    index = SqliteWorldDemandIndex(tmp_path / "wd.sqlite3")

    def failing(url: str, target: Path) -> None:
        raise TimeoutError

    backfill = PlacspAwardsBackfill(index.upsert_awards, tmp_path / "wd.sqlite3",
                                    tmp_path / "tmp", months=1, download=failing,
                                    clock=lambda: NOW)  # fmt: skip
    assert backfill.run_one() == 0
    assert backfill.status()[0][1:] == ("FAILED", 0, "TimeoutError")
    assert backfill.pending() == []  # not again before a day has passed
