"""Identity corroboration: agreeing public anchors, never an admission."""

from __future__ import annotations

from application.organization_identity import identity_corroboration

NOTORIETY = {"kind": "MENTION", "code": "WIKIPEDIA_NOTORIETY", "sourceUrl": "https://www.wikidata.org/wiki/Q1",
             "detail": {"item": "Q1"}}  # fmt: skip
REGISTER = {"kind": "ECONOMIC_FACT", "code": "REGISTER:SIREN:employees", "sourceUrl": "https://insee.example/1",
            "detail": {"sourceKind": "OFFICIAL_REGISTER", "registerName": "ACME SAS", "identifier": "SIREN 1",
                       "source": "INSEE", "attributedBy": "OFFICIAL_WEBSITE_IN_WIKIDATA"}}  # fmt: skip


def test_two_independent_anchors_corroborate_without_admitting() -> None:
    (found,) = identity_corroboration([NOTORIETY, REGISTER])
    assert found["code"] == "IDENTITY_CORROBORATED" and found["statement"] == "ACME SAS"
    assert found["epistemicState"] == "POTENTIAL" and found["detail"]["admitted"] is False
    assert [a["anchor"] for a in found["detail"]["anchors"]] == [
        "WIKIDATA_OFFICIAL_WEBSITE",
        "OFFICIAL_REGISTER",
    ]


def test_one_anchor_is_not_a_corroboration() -> None:
    assert identity_corroboration([NOTORIETY]) == []
    assert identity_corroboration([REGISTER]) == []
