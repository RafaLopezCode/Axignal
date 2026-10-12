"""Corporate group from GLEIF relationship data, worldwide."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.organization_group import group_discoveries
from pipeline.entity_resolution.gleif_group import API, GleifGroupReader

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
LEI = "9598008X362A8R6PTW48"


def _record(lei: str, name: str, country: str) -> dict[str, object]:
    return {"id": lei, "attributes": {"entity": {"legalName": {"name": name}, "status": "ACTIVE",
            "legalAddress": {"country": country, "city": "X"}}}}  # fmt: skip


def _fetch(calls: list[str]):  # type: ignore[no-untyped-def]
    def fetch(url: str) -> tuple[int, bytes]:
        calls.append(url)
        if url.endswith("/direct-parent") or url.endswith("/ultimate-parent"):
            return 404, b""
        children = [_record("98450055CCCC7E3A7810", "ZITRON AUSTRALIA PTY LTD", "AU"),
                    _record("724500HBL3SPO28GQ063", "Zitron Nederland B.V.", "NL")]  # fmt: skip
        return 200, json.dumps({"data": children, "meta": {"pagination": {"total": 2}}}).encode()

    return fetch


def test_a_group_is_read_once_and_cached_for_a_week(tmp_path: Path) -> None:
    calls: list[str] = []
    clock = [NOW]
    reader = GleifGroupReader(tmp_path / "g.sqlite3", fetch=_fetch(calls), clock=lambda: clock[0])
    group = reader.group(LEI)
    assert group["childrenTotal"] == 2 and group["parents"] == {}
    reader.group(LEI)
    assert len(calls) == 3  # parent, ultimate parent, children: once
    clock[0] = NOW + timedelta(days=8)
    reader.group(LEI)
    assert len(calls) == 6 and all(url.startswith(API) for url in calls)


def test_a_verified_lei_gives_an_observed_group_and_its_countries(tmp_path: Path) -> None:
    group = GleifGroupReader(tmp_path / "g.sqlite3", fetch=_fetch([])).group(LEI)
    found = group_discoveries(group, verified=True, observed_at=NOW.isoformat())
    subsidiaries = next(d for d in found if d["code"] == "GROUP_SUBSIDIARIES")
    countries = next(d for d in found if d["code"] == "GROUP_ENTITIES_IN_COUNTRIES")
    assert subsidiaries["epistemicState"] == "OBSERVED" and subsidiaries["statement"] == "2"
    assert countries["statement"] == "AU, NL"
    declared = group_discoveries(group, verified=False, observed_at=NOW.isoformat())
    assert {d["epistemicState"] for d in declared} == {"POTENTIAL"}


def test_a_parent_is_said_once_when_direct_and_ultimate_are_the_same() -> None:
    parent = {"lei": "W38RGI023J3WT1HWRP32", "name": "Siemens AG", "country": "DE"}
    group = {
        "lei": "X",
        "parents": {"direct-parent": parent, "ultimate-parent": parent},
        "children": [],
    }
    (only,) = group_discoveries(group, verified=True, observed_at=NOW.isoformat())
    assert only["code"] == "GROUP_PARENT" and only["detail"]["role"] == "ULTIMATE_PARENT"  # type: ignore[index]
