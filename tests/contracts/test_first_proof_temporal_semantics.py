"""First Proof shares the normalized, tri-state temporal authority with subscriber runtime."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from application.economic_discovery.observation_memory import ObservedField
from tests.contracts.test_fr30_production_first_proof import NOW, _install_source, _service


def test_first_proof_does_not_confuse_empty_observations_with_no_economic_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    _install_source(monkeypatch, service)
    first_map = service.plant(label="AXIGNAL proof", target_uri="https://axignal.com/")
    org = str(first_map["organization"]["id"])
    xeed = str(first_map["context"]["id"])
    (original,) = service.observation_memory.for_subject(org)

    def history(first, second):
        previous = replace(
            original,
            record=replace(
                original.record,
                observation_id="obs:before",
                observed_at=NOW,
            ),
            fields=first,
        )
        current = replace(
            original,
            record=replace(
                original.record,
                observation_id="obs:after",
                observed_at=NOW + timedelta(hours=1),
            ),
            fields=second,
        )
        monkeypatch.setattr(
            type(service), "_authorized_history", lambda self, **_: (previous, current)
        )
        return service._temporal_history_payload(
            subject_id=org, xeed_id=xeed, as_of=NOW + timedelta(hours=2)
        )["items"]

    assert [row["normalizedStateChanged"] for row in history((), ())] == [None, None]
    economic = (ObservedField("capability", "website-design"),)
    changed = (ObservedField("capability", "SEO"),)
    assert [row["normalizedStateChanged"] for row in history(economic, economic)] == [None, False]
    assert [row["normalizedStateChanged"] for row in history(economic, changed)] == [None, True]
    assert [row["normalizedStateChanged"] for row in history(economic, ())] == [None, None]
