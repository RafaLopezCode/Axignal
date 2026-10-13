"""Playbooks: each segment's letter opens with its own evidenced hook and its own CTA."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from application.marketing_pool.personas import best_persona, persona
from application.marketing_pool.playbooks import PLAYBOOKS, hooks, playbook_for
from application.marketing_pool.policy import market
from application.marketing_pool.prospect import accept_draft, findings
from pipeline.marketing_pool.discovery import OverpassDiscovery
from pipeline.marketing_pool.sqlite_store import Candidate, SqliteMarketingPool
from tools.runtime.marketing_pool import MarketingPoolRunner, Operator

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def _d(kind: str, code: str, statement: str, state: str = "OBSERVED", **detail: Any) -> dict:
    return {"kind": kind, "code": code, "statement": statement, "epistemicState": state,
            "sourceUrl": f"https://source/{code}", "observedAt": "2026-10-01", "detail": detail}  # fmt: skip


CONSTRUCTION_VIEW = {
    "state": "FIRST_PROOF_READY",
    "observedAt": NOW.isoformat(),
    "discoveries": [
        _d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED", "Obras Norte — constructora"),
        _d("ACTIVITY", "building-construction", "Constructora: obra civil y edificación"),
        _d("INXIGHT", "demand:LOCAL_BUYERS_NEVER_AWARDED", "3 public bodies...", "POTENTIAL",
           family="demand", values={"buyers": 3, "contracts": 14, "where": "AREA"}),
        _d("DEMAND", "RECURRING_PUBLIC_BUYER", "Ayuntamiento A", "POTENTIAL", contractsInArea=6),
        _d("COMPETITION", "WINS_IN_SAME_CODES", "Rival Obras SA", "POTENTIAL"),
        _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "Diputación B", contracts=2),
        _d("ECONOMIC_FACT", "REGISTER:ES:inception", "1998", fact="inception", value="1998"),
    ],
}  # fmt: skip


def test_every_persona_has_a_playbook_and_the_new_ones_are_discoverable() -> None:
    assert {p.segment for p in PLAYBOOKS} == {"AGENCY", "CONSTRUCTION", "PRIVATE_SCHOOL",
                                             "CONSULTANCY"}  # fmt: skip
    for persona_id in ("SEO_GEO_AGENCY", "DIGITAL_MARKETING_AGENCY", "REPUTATION_PR_AGENCY",
                       "CONSTRUCTION", "PRIVATE_SCHOOL", "B2B_CONSULTANCY"):  # fmt: skip
        assert playbook_for(persona_id) is not None
    school = persona("PRIVATE_SCHOOL")
    assert school is not None
    queries: list[str] = []

    def fetch(request: Any, timeout: float) -> bytes:
        queries.append(request.data.decode())
        return json.dumps({"elements": []}).encode()

    OverpassDiscovery(fetch).find(school, market("ES"))
    assert "operator%3Atype" in queries[0] and "language_school" in queries[0]
    chosen, _w = best_persona("Colegio privado bilingüe. Admisiones abiertas", None)
    assert chosen is not None and chosen.id == "PRIVATE_SCHOOL"


def test_the_hook_comes_first_and_must_be_cited() -> None:
    playbook = playbook_for("CONSTRUCTION")
    assert playbook is not None
    opening = hooks(CONSTRUCTION_VIEW, playbook)
    assert [h["code"] for h in opening] == [
        "demand:LOCAL_BUYERS_NEVER_AWARDED", "RECURRING_PUBLIC_BUYER"
    ]  # fmt: skip
    selected = findings(CONSTRUCTION_VIEW, playbook.families, first=opening[:1])
    assert selected[0].kind == "INXIGHT" and selected[0].value["buyers"] == 3  # type: ignore[index]
    body = "Tres organismos de su zona contratan obra como la suya. " * 6
    assert accept_draft({"subject": "Tres organismos cerca", "body": body,
                         "findings_used": [2, 3]}, selected, require_first=True) is None  # fmt: skip
    assert accept_draft({"subject": "Tres organismos cerca", "body": body,
                         "findings_used": [1, 2]}, selected, require_first=True)  # fmt: skip


class _Sender:
    sender_address = "hola@axignal.com"

    def send(self, message: Any) -> str:
        return "<id>"


def _runner(
    tmp_path: Path, view: dict, clock: list[datetime], seen: list[Any]
) -> MarketingPoolRunner:
    def complete(job: Any) -> Any:
        seen.append(job)
        body = ("Tres organismos públicos de su zona contratan obra como la suya y ninguno le ha "
                "adjudicado nada.\n\nPara una constructora, ser conocida por quien adjudica "
                "cerca es la mitad del trabajo.\n\nAXIGNAL lo vigila cada día.")  # fmt: skip
        return SimpleNamespace(payload={"answer": {"subject": "Tres organismos de su zona",
                                                   "body": body, "findings_used": [1, 2]}})  # fmt: skip

    return MarketingPoolRunner(
        SqliteMarketingPool(tmp_path / "pool.sqlite3"), (),
        study=lambda *_: "QUEUED",
        study_result=lambda ref: (view, {"emails": ["info@obrasnorte.es"], "language": "es"}),
        complete=complete, model="m",
        operator=Operator("Rafael López", "Calle 1, Toledo", "https://axignal.com", "CEO"),
        sender=_Sender(), clock=lambda: clock[0],
    )  # fmt: skip


def test_a_construction_letter_opens_with_its_hook_and_its_own_cta(tmp_path: Path) -> None:
    seen: list[Any] = []
    runner = _runner(tmp_path, CONSTRUCTION_VIEW, [NOW], seen)
    runner.store.add([Candidate("Obras Norte", "https://obrasnorte.es", "US", "CONSTRUCTION",
                                "OSM", "osm:1")], now=NOW)  # fmt: skip
    runner.start_studies()
    runner.collect()
    prospect = runner.store.get("obrasnorte.es")
    assert prospect is not None and prospect["state"] == "DRAFTED"
    assert prospect["detail"]["segment"] == "CONSTRUCTION"
    assert prospect["detail"]["hook"]["code"] == "demand:LOCAL_BUYERS_NEVER_AWARDED"
    brief = str(seen[0].context["user"])
    assert "Segment: CONSTRUCTION" in brief and "HOOK (finding [1])" in brief
    html = runner.html(prospect) or ""
    assert "Ver compradores y licitaciones abiertas" in html
    assert "Quién compra tu obra cerca de ti" in html
    assert "#demand" in html and "border-left:3px solid" in html
    assert "A la atención del responsable de licitaciones de Obras Norte" in html


def test_without_a_hook_it_waits_then_is_not_written(tmp_path: Path) -> None:
    bare = {**CONSTRUCTION_VIEW, "discoveries": [
        d for d in CONSTRUCTION_VIEW["discoveries"]
        if d["kind"] not in {"INXIGHT", "DEMAND"}
    ]}  # fmt: skip
    clock, seen = [NOW], []
    runner = _runner(tmp_path, bare, clock, seen)
    runner.store.add([Candidate("Obras Norte", "https://obrasnorte.es", "US", "CONSTRUCTION",
                                "OSM", "osm:1")], now=NOW)  # fmt: skip
    runner.start_studies()
    assert runner.collect() == 0 and runner.store.get("obrasnorte.es")["state"] == "STUDYING"
    clock[0] = NOW + timedelta(days=4)
    runner.collect()
    prospect = runner.store.get("obrasnorte.es")
    assert prospect["state"] == "NOT_QUALIFIED" and prospect["reason"] == "NO_SEGMENT_HOOK"
    assert seen == []  # no model call for a letter that would be generic


def test_cards_speak_the_letters_language_and_never_carry_links() -> None:
    playbook = playbook_for("CONSTRUCTION")
    assert playbook is not None
    selected = findings(CONSTRUCTION_VIEW, playbook.families,
                        first=hooks(CONSTRUCTION_VIEW, playbook)[:1])  # fmt: skip
    body = "Tres organismos de su zona contratan obra como la suya. " * 6
    draft = accept_draft({
        "subject": "Tres organismos cerca", "body": body, "findings_used": [1, 2],
        "cards": [{"index": 1, "text": "3 organismos de su zona contratan su obra"},
                  {"index": 2, "text": "Vea https://x.com"}, {"index": 9, "text": "invented"}],
    }, selected, require_first=True)  # fmt: skip
    assert draft is not None
    used = draft["findingsUsed"]
    assert isinstance(used, list)
    assert used[0]["text"] == "3 organismos de su zona contratan su obra"
    assert "text" not in used[1]  # a card with a link is dropped: the original statement shows
