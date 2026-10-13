"""Job boards: found on its own site, read on the source thread, never storing a person."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from application.activity import board_of, country_of_location, function_of, job_board_discoveries
from application.first_observation.site import read_page
from pipeline.activity.job_boards import JobBoards, parse

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def test_boards_are_recognized_from_links_and_embeds() -> None:
    assert board_of("https://boards.greenhouse.io/acme") == ("GREENHOUSE", "acme")
    assert board_of("https://boards.greenhouse.io/embed/job_board?for=acme") == (
        "GREENHOUSE",
        "acme",
    )
    assert board_of("https://jobs.lever.co/octoenergy/123") == ("LEVER", "octoenergy")
    assert board_of("https://jobs.ashbyhq.com/alan") == ("ASHBY", "alan")
    assert board_of("https://jungvonmatt.jobs.personio.de/job/1") == ("PERSONIO", "jungvonmatt")
    assert board_of("https://bunq.recruitee.com/o/x") == ("RECRUITEE", "bunq")
    assert board_of("https://boards.greenhouse.io/embed/js") is None
    assert board_of("https://example.com/careers") is None
    html = ("<html><body><a href='https://jobs.ashbyhq.com/alan'>Jobs</a>"
            "<script src='https://boards.greenhouse.io/embed/job_board/js?for=alan'></script></body></html>")  # fmt: skip
    page = read_page(url="https://alan.example/", html=html, observed_at=NOW,
                     content_fingerprint="f", artifact_ref=None)  # fmt: skip
    assert page.signals["jobBoards"] == ["ASHBY:alan", "GREENHOUSE:alan"]


def test_a_recruiters_name_in_the_department_field_is_never_kept() -> None:
    xml = (b"<workzag-jobs><position><name>Art Director</name><office>Hamburg</office>"
           b"<department>Anna Example</department></position><position><name>Developer</name>"
           b"<office>Berlin</office><department>Engineering</department></position></workzag-jobs>")  # fmt: skip
    jobs = parse("PERSONIO", xml)
    assert [j["department"] for j in jobs] == ["OTHER", "Engineering"]
    assert "Anna" not in json.dumps(jobs)
    assert function_of("Sales \U0001f1eb\U0001f1f7") == "Sales \U0001f1eb\U0001f1f7"


def test_openings_are_activity_and_hiring_countries_are_market_evidence(tmp_path: Path) -> None:
    body = json.dumps({"jobs": [
        {"title": "Backend engineer", "location": "Paris", "department": "Engineering",
         "address": {"postalAddress": {"addressCountry": "France"}}},
        {"title": "Account executive", "location": "Madrid, Spain", "department": "Sales"},
        {"title": "Nurse", "location": "San Francisco, CA", "department": "Medical Team"},
    ]}).encode()  # fmt: skip
    boards = JobBoards(tmp_path / "j.sqlite3", fetch=lambda url: body, clock=lambda: NOW)
    boards.request("ASHBY:alan")
    boards.request("TEAMTAILOR:x")  # no public API: ignored, never fetched
    assert boards.latest("ASHBY:alan") is None
    assert boards.run() == 1
    activity, markets = job_board_discoveries(boards.latest("ASHBY:alan"), source_page=None)
    assert activity["code"] == "OPEN_POSITIONS" and activity["statement"] == "3"
    assert activity["epistemicState"] == "DECLARED"
    assert activity["detail"]["countries"] == {"FR": 1, "ES": 1, "US": 1}
    assert markets["code"] == "HIRING_IN_COUNTRIES" and markets["statement"] == "ES, FR, US"
    assert boards.run() == 0  # every three days, not on every tick
    assert country_of_location("Remote - Germany") == "DE"
    assert country_of_location("Anywhere") is None
