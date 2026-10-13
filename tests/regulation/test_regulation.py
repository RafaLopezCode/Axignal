"""Regulation: official journals, where a rule applies, a precise prefilter, a judgment."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from application.regulation import RegulationItem, applies_in, regulation_discoveries
from cognition.jobs.model import JobKind
from pipeline.regulation import sources
from pipeline.regulation.sqlite_store import RegulationIngestor, SqliteRegulationIndex
from tools.runtime.regulation_context import RegulationContextRunner

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)

BOE_DAY = {"data": {"sumario": {"diario": [{"seccion": [
    {"codigo": "1", "nombre": "I. Disposiciones generales", "departamento": [{
        "nombre": "MINISTERIO DEL INTERIOR",
        "epigrafe": [{"item": {"identificador": "BOE-A-2026-1",
                               "titulo": "Orden por la que se regula la seguridad privada en eventos",
                               "url_html": "https://www.boe.es/a1"}}]}]},
    {"codigo": "2A", "nombre": "II. Autoridades", "departamento": {
        "nombre": "X", "epigrafe": {"item": {"identificador": "BOE-A-2026-2",
                                             "titulo": "Nombramiento", "url_html": "u"}}}},
    {"codigo": "3", "nombre": "III. Otras disposiciones", "departamento": {
        "nombre": "MINISTERIO DE TRABAJO", "epigrafe": {"item": [
            {"identificador": "BOE-A-2026-3",
             "titulo": "Resolución por la que se registra el Convenio colectivo estatal de las "
                       "empresas de seguridad privada", "url_html": "https://www.boe.es/a3"},
            {"identificador": "BOE-A-2026-4",
             "titulo": "Resolución de la Dirección General de Seguridad Jurídica y Fe Pública, "
                       "en el recurso interpuesto contra la nota", "url_html": "u4"}]}}},
]}]}}}  # fmt: skip


def _fetch(url: str, accept: str) -> bytes:
    if "boe.es" in url:
        return json.dumps(BOE_DAY).encode()
    if "federalregister" in url:
        return json.dumps({"results": [{
            "document_number": "2026-1", "title": "Private Security Guard Licensing Standards",
            "publication_date": "2026-10-01", "html_url": "https://fr/1", "type": "Rule",
            "agencies": [{"name": "Labor Department"}]}], "next_page_url": None}).encode()  # fmt: skip
    if "sparql" in url:
        return json.dumps({"results": {"bindings": [{
            "celex": {"value": "32026R0001"}, "date": {"value": "2026-09-20"},
            "title": {"value": "Regulation on private security services in the Union"}}]}}).encode()  # fmt: skip
    if "legislation.gov.uk" in url:
        return (b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>The Private Security '
                b'Industry (Licences) Regulations 2026</title><id>http://www.legislation.gov.uk/uksi/'
                b'2026/1</id><published>2026-10-02T00:00:00Z</published><link rel="alternate" '
                b'href="https://www.legislation.gov.uk/uksi/2026/1"/></entry></feed>')  # fmt: skip
    raise AssertionError(url)


def test_journals_are_read_with_where_they_apply() -> None:
    boe = sources.read_boe(date(2026, 10, 9), _fetch)
    assert [i.item_id for i in boe] == ["BOE-A-2026-1", "BOE-A-2026-3", "BOE-A-2026-4"]
    assert boe[0].scope == "EU/ES" and boe[0].issuer == "MINISTERIO DEL INTERIOR"
    eu = sources.read_eur_lex(date(2026, 9, 1), _fetch)
    assert eu[0].scope == "EU" and eu[0].kind == "REGULATION" and len(eu) == 6  # per language
    assert sources.read_federal_register(date(2026, 9, 1), _fetch)[0].scope == "US"
    assert sources.read_legislation_gov_uk(_fetch)[0].scope == "GB"


def test_an_eu_act_applies_in_every_member_state_only() -> None:
    assert applies_in("EU", "EU/ES") and applies_in("EU/ES", "EU/ES/ES3")
    assert not applies_in("EU", "US") and not applies_in("EU/ES", "EU/FR")


def test_candidates_need_the_activity_not_one_shared_word(tmp_path: Path) -> None:
    index = SqliteRegulationIndex(tmp_path / "r.sqlite3")
    ingestor = RegulationIngestor(index, fetch=_fetch, clock=lambda: NOW)
    assert ingestor.run() > 0
    phrases = ("seguridad privada", "private security")
    keywords = ("seguridad", "privada", "security", "vigilantes")
    found = index.candidates("EU/ES", phrases, keywords=keywords, since=date(2026, 8, 1),
                             language="es")  # fmt: skip
    titles = [str(f["title"]) for f in found]
    assert any("Convenio colectivo" in t for t in titles)
    assert any("eventos" in t for t in titles)
    assert not any("Fe Pública" in t for t in titles)  # an individual appeal, never
    eu = [f for f in found if f["source"] == "EUR_LEX"]
    assert len(eu) == 1 and eu[0]["language"] in {"es", "en"}
    us = index.candidates("US", phrases, keywords=keywords, since=date(2026, 8, 1), language="en")
    assert [f["source"] for f in us] == ["FEDERAL_REGISTER"]


def test_the_judgment_decides_what_is_shown_once_per_activity_country_day(
    tmp_path: Path,
) -> None:
    index = SqliteRegulationIndex(tmp_path / "r.sqlite3")
    index.upsert([
        RegulationItem("BOE", "A1", "Convenio colectivo estatal de las empresas de seguridad privada",
                       date(2026, 10, 1), "EU/ES", "MINISTERIO DE TRABAJO", "https://boe/1", "es"),
        RegulationItem("BOE", "A2", "Ayudas a vigilantes de seguridad privada jubilados en Cuenca",
                       date(2026, 10, 2), "EU/ES", "X", "https://boe/2", "es"),
    ])  # fmt: skip
    calls: list[Any] = []

    def complete(job: Any) -> Any:
        assert job.kind is JobKind.SEMANTIC_DECISION
        calls.append(job)
        lines = str(job.context["user"]).splitlines()[2:]
        keep = [i for i, line in enumerate(lines) if "Convenio" in line]
        return SimpleNamespace(payload={"answer": {"relevant": keep}})

    runner = RegulationContextRunner(complete, "m", index, tmp_path / "c.sqlite3",
                                     clock=lambda: NOW)  # fmt: skip
    runner.request("security-guarding", "EU/ES", "es")
    runner.request("security-guarding", "EU/ES", "es")
    assert runner.run() == 1 and len(calls) == 1
    result = runner.latest("security-guarding", "EU/ES")
    found = regulation_discoveries(result or {}, capability_id="security-guarding",
                                   sector="Security", country="EU/ES", observed_at="x")  # fmt: skip
    assert [d["statement"] for d in found] == [
        "Convenio colectivo estatal de las empresas de seguridad privada"
    ]
    assert found[0]["kind"] == "CONTEXT_SIGNAL" and found[0]["code"] == "REGULATION"
    assert found[0]["epistemicState"] == "POTENTIAL"
    assert "Not legal advice" in str(found[0]["detail"]["limitation"])  # type: ignore[index]


def test_a_failing_journal_waits_an_hour_instead_of_retrying_every_tick(tmp_path: Path) -> None:
    from datetime import timedelta

    index = SqliteRegulationIndex(tmp_path / "r.sqlite3")
    now = [NOW]
    calls: list[str] = []

    def failing_eu(url: str, accept: str) -> bytes:
        if "eur-lex" in url or "publications.europa.eu" in url:
            calls.append(url)
            raise TimeoutError("down")
        return _fetch(url, accept)

    ingestor = RegulationIngestor(index, fetch=failing_eu, clock=lambda: now[0])
    ingestor.run()
    first = len(calls)
    assert first and index.last_error("EUR_LEX") == "TimeoutError"
    now[0] += timedelta(minutes=10)
    ingestor.run()
    assert len(calls) == first  # not on the next tick
    now[0] += timedelta(hours=1)
    ingestor.run()
    assert len(calls) > first  # retried after the wait


def test_section_labels_are_not_sector_headlines() -> None:
    from application.context.sector import context_discoveries

    result = {"relevant": [{"title": "CONSTRUCCIÓN", "url": "https://a"},
                           {"title": "La construcción crece un 4% en octubre", "url": "https://b"}]}  # fmt: skip
    found = context_discoveries(result, capability_id="x", country="ES", observed_at="2026-10-13")
    assert [d["statement"] for d in found] == ["La construcción crece un 4% en octubre"]
