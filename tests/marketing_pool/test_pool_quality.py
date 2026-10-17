"""Pool quality rules found on the first real dry run (CTO, 2026-10-17: "plantillas perfectas
en los 6 idiomas" and "optimizar al máximo el pool marketing")."""

from __future__ import annotations

import re

from application.marketing_pool.email_template import LABELS, readable
from application.marketing_pool.personas import best_persona
from application.marketing_pool.playbooks import COPY
from application.marketing_pool.prospect import _NOTICE, _READ, accept_draft, salutation


def test_an_activity_the_study_read_is_persona_evidence_on_its_own() -> None:
    # 9 of 20 real agencies were "not a target": their title said neither SEO nor marketing.
    chosen, evidence = best_persona("Welcome to Acme. We build brands.", "SEO_GEO_AGENCY",
                                    ("marketing-advertising",))  # fmt: skip
    assert chosen is not None and chosen.id == "DIGITAL_MARKETING_AGENCY"
    assert "activity:marketing-advertising" in evidence
    assert best_persona("Welcome to Acme. We build brands.", None, ("metal-fabrication",)) == (
        None,
        (),
    )


def test_a_card_is_never_a_raw_finding_code() -> None:
    cards = [
        {"statement": "ORGANIZATION_DECLARED"},
        {"statement": "x", "text": "Its site declares no organization data"},
    ]
    assert [c["text"] for c in readable(cards)] == ["Its site declares no organization data"]


def _draft(subject: str, cards: list[dict[str, object]]) -> dict[str, object] | None:
    from application.marketing_pool.prospect import Finding

    selected = [Finding("presence", "GENERATIVE_VISIBILITY", "AI_NOT_NAMED", "0/2", "OBSERVED", None),
                Finding("value", "ACTIVITY", "seo", "SEO services", "POTENTIAL", None)]  # fmt: skip
    body = "We measured how AI assistants describe your agency, from the outside. " * 4
    return accept_draft(
        {"subject": subject, "body": body, "findings_used": [1, 2], "cards": cards}, selected
    )


def test_a_draft_needs_two_readable_cards_and_a_clean_subject() -> None:
    two = [
        {"index": 1, "text": "AI assistants did not name it"},
        {"index": 2, "text": "It offers SEO"},
    ]
    assert _draft("How AI assistants describe your agency", two) is not None
    assert _draft("How AI assistants describe your agency", two[:1]) is None
    assert _draft("Free audit inside!", two) is None
    assert _draft("Your AI visibility 🚀", two) is None


def _spanish_and_portuguese() -> list[str]:
    texts = [LABELS["es"][k] for k in LABELS["es"]] + [LABELS["pt"][k] for k in LABELS["pt"]]
    texts += [values[i] for seg in COPY.values() for values in seg.values() for i in (0, 5)]
    texts += [_NOTICE["es"], _NOTICE["pt"], _READ["es"], _READ["pt"]]
    texts += [salutation(lang, "SEO_GEO_AGENCY", "Acme") for lang in ("es", "pt")]
    return texts


def test_spanish_and_portuguese_copy_is_formal_and_region_neutral() -> None:
    # The pool writes in Spanish to Spain and Latin America, in Portuguese to Portugal and Brazil.
    informal = re.compile(r"\b(tú|tu|tus|ti|te|vosotros|vuestr\w*|os|podríais|vos|vós|você|vocês|teu|tua)\b",
                          re.IGNORECASE)  # fmt: skip
    assert [t for t in _spanish_and_portuguese() if informal.search(t)] == []


def test_every_language_has_every_label() -> None:
    assert set(LABELS) == {"es", "en", "fr", "de", "it", "pt"}
    keys = set(LABELS["en"])
    assert all(set(labels) == keys for labels in LABELS.values())
    assert all(len(values) == 6 for seg in COPY.values() for values in seg.values())


def test_the_registry_class_hint_speaks_for_every_persona_listed_under_it() -> None:
    # A digital marketing agency, found as an SEO agency (both under advertising_agency).
    text = "Growth for local brands: performance marketing"
    chosen, evidence = best_persona(text, "SEO_GEO_AGENCY")
    assert chosen is not None and chosen.id == "DIGITAL_MARKETING_AGENCY"
    assert evidence == ("performance marketing",)
    assert best_persona(text, None) == (None, ())  # without the registry class: two words
