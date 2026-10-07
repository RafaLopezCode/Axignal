from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

import tools.runtime.seo_truth_sync as seo_truth_sync
from application.admin_measurements import project_measurement_registry
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_seo_truth import CruxFormFactor
from pipeline.admin_measurements import SqliteMeasurementRegistryStore
from pipeline.admin_seo_truth import SqliteSeoTruthStore
from tools.runtime.seo_truth_sync import run_sync

NOW = datetime(2026, 10, 7, 13, 30, tzinfo=UTC)


def _grant() -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("session:founder"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, crux: bool = True) -> None:
    oauth = tmp_path / "gsc-oauth.json"
    oauth.write_text(
        '{"client_id":"fixture-client","client_secret":"fixture-secret",'
        '"refresh_token":"fixture-refresh"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("AXIGNAL_SEO_TRUTH_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AXIGNAL_GSC_OAUTH_SECRET_FILE", str(oauth))
    monkeypatch.setenv("AXIGNAL_GSC_PROPERTY", "sc-domain:axignal.com")
    monkeypatch.setenv("AXIGNAL_PUBLIC_ORIGIN", "https://axignal.com")
    monkeypatch.setenv("AXIGNAL_SEO_SITEMAP_URL", "https://axignal.com/sitemap.xml")
    monkeypatch.setenv("AXIGNAL_SEO_INSPECTION_LIMIT", "750")
    if crux:
        key = tmp_path / "crux-api-key"
        key.write_text("fixture-key", encoding="utf-8")
        monkeypatch.setenv("AXIGNAL_CRUX_API_KEY_FILE", str(key))
    else:
        monkeypatch.delenv("AXIGNAL_CRUX_API_KEY_FILE", raising=False)


def _inspection_payload(url: str) -> dict[str, object]:
    return {
        "indexStatusResult": {
            "verdict": "NEUTRAL",
            "coverageState": "URL is unknown to Google",
            "robotsTxtState": "ROBOTS_TXT_STATE_UNSPECIFIED",
            "indexingState": "INDEXING_STATE_UNSPECIFIED",
            "pageFetchState": "PAGE_FETCH_STATE_UNSPECIFIED",
            "crawledAs": "CRAWLING_USER_AGENT_UNSPECIFIED",
            "referringUrls": [],
            "userCanonical": url,
        }
    }


def _crux_record(form_factor: CruxFormFactor) -> dict[str, object]:
    del form_factor
    return {
        "collectionPeriod": {
            "firstDate": {"year": 2026, "month": 9, "day": 7},
            "lastDate": {"year": 2026, "month": 10, "day": 4},
        },
        "metrics": {
            "largest_contentful_paint": {"percentiles": {"p75": 2100}},
            "interaction_to_next_paint": {"percentiles": {"p75": 180}},
            "cumulative_layout_shift": {"percentiles": {"p75": "0.08"}},
            "first_contentful_paint": {"percentiles": {"p75": 1400}},
            "experimental_time_to_first_byte": {"percentiles": {"p75": 650}},
        },
    }


def test_direct_google_seo_truth_is_private_replay_safe_and_governed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(tmp_path, monkeypatch)
    urls = (
        "https://axignal.com/es/knowledge",
        "https://axignal.com/en/knowledge",
        "https://axignal.com/es/knowledge/observar-una-organizacion-desde-fuera",
    )
    monkeypatch.setattr(seo_truth_sync, "_fetch_sitemap_urls", lambda _: urls)

    class FakeGscClient:
        def __init__(self, credentials: object) -> None:
            self.credentials = credentials

        def list_sitemaps(self, *, property_ref: str) -> tuple[dict[str, object], ...]:
            assert property_ref == "sc-domain:axignal.com"
            return (
                {
                    "path": "https://axignal.com/sitemap.xml",
                    "isPending": False,
                    "warnings": "0",
                    "errors": "0",
                    "lastSubmitted": "2026-10-07T13:19:13.318Z",
                    "lastDownloaded": "2026-10-07T11:11:05.191Z",
                    "contents": [{"type": "web", "submitted": "528", "indexed": "0"}],
                },
            )

        def inspect_url(
            self, *, property_ref: str, inspection_url: str, language_code: str = "en-US"
        ) -> dict[str, object]:
            assert property_ref == "sc-domain:axignal.com"
            assert language_code == "en-US"
            return _inspection_payload(inspection_url)

    class FakeCruxClient:
        @classmethod
        def from_file(cls, path: Path) -> FakeCruxClient:
            assert path.read_text(encoding="utf-8") == "fixture-key"
            return cls()

        def query(self, *, origin: str, form_factor: CruxFormFactor) -> dict[str, object] | None:
            assert origin == "https://axignal.com"
            return _crux_record(form_factor)

    monkeypatch.setattr(seo_truth_sync, "GoogleSearchConsoleClient", FakeGscClient)
    monkeypatch.setattr(seo_truth_sync, "ChromeUxReportClient", FakeCruxClient)

    first = run_sync(now=NOW)
    assert first["state"] == "COMPLETED"
    assert first["sitemapUrls"] == 3
    assert first["gscSitemap"] == {
        "state": "OBSERVED",
        "pending": False,
        "warnings": 0,
        "errors": 0,
        "submitted": 528,
        "indexed": 0,
    }
    assert first["newInspections"] == 3
    assert first["inspectedToday"] == 3
    assert first["remainingToday"] == 0
    assert first["coverage"] == {"URL is unknown to Google": 3}
    assert first["cruxState"] == "MEASURED"
    assert first["cruxSnapshots"] == 3
    assert len(first["cruxMeasurementObservations"]) == 15

    second = run_sync(now=NOW)
    assert second["newInspections"] == 0
    assert second["replaySkipped"] == 3
    assert second["inspectedToday"] == 3

    store = SqliteSeoTruthStore(tmp_path / "admin-seo-truth.sqlite3")
    assert len(store.inspections()) == 3
    assert len(store.sitemap_snapshots()) == 1
    assert len(store.crux_snapshots()) == 3

    measurements = SqliteMeasurementRegistryStore(tmp_path / "admin-measurements.sqlite3")
    assert len(measurements.definitions()) == 5
    assert len(measurements.observations()) == 15
    projection = project_measurement_registry(
        store=measurements,
        grant=_grant(),
        generated_at=NOW,
    )
    crux_readouts = [
        item
        for item in projection.readouts
        if item.observation.measure_id.startswith("measure:crux-")
    ]
    assert len(crux_readouts) == 15
    assert all(item.observation.state.value == "MEASURED" for item in crux_readouts)


def test_crux_no_data_is_insufficient_not_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(tmp_path, monkeypatch)
    urls = ("https://axignal.com/es/knowledge",)
    monkeypatch.setattr(seo_truth_sync, "_fetch_sitemap_urls", lambda _: urls)

    class FakeGscClient:
        def __init__(self, credentials: object) -> None:
            del credentials

        def list_sitemaps(self, **kwargs: object) -> tuple[dict[str, object], ...]:
            del kwargs
            return ()

        def inspect_url(self, **kwargs: object) -> dict[str, object]:
            return _inspection_payload(str(kwargs["inspection_url"]))

    class NoDataCrux:
        @classmethod
        def from_file(cls, path: Path) -> NoDataCrux:
            del path
            return cls()

        def query(self, **kwargs: object) -> None:
            del kwargs
            return None

    monkeypatch.setattr(seo_truth_sync, "GoogleSearchConsoleClient", FakeGscClient)
    monkeypatch.setattr(seo_truth_sync, "ChromeUxReportClient", NoDataCrux)

    result = run_sync(now=NOW)
    assert result["cruxState"] == "INSUFFICIENT_DATA"
    assert result["cruxSnapshots"] == 0
    assert result["cruxMeasurementObservations"] == []
    measurements = SqliteMeasurementRegistryStore(tmp_path / "admin-measurements.sqlite3")
    assert measurements.observations() == ()


def test_seo_truth_fails_closed_without_server_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AXIGNAL_SEO_TRUTH_ENABLED", raising=False)
    assert run_sync(now=NOW) == {"state": "DISABLED"}

    monkeypatch.setenv("AXIGNAL_SEO_TRUTH_ENABLED", "true")
    monkeypatch.delenv("AXIGNAL_DATA_DIR", raising=False)
    monkeypatch.delenv("AXIGNAL_GSC_OAUTH_SECRET_FILE", raising=False)
    assert run_sync(now=NOW) == {"state": "NOT_CONFIGURED"}


def test_sitemap_origin_guard_rejects_noncanonical_hosts() -> None:
    with pytest.raises(RuntimeError, match="URL_OUTSIDE_CANONICAL_ORIGIN"):
        seo_truth_sync._ensure_origin(
            ("https://www.axignal.com/es/knowledge",),
            "https://axignal.com",
        )


def test_production_seo_truth_runner_is_hardened_and_secret_files_are_read_only() -> None:
    root = Path(__file__).resolve().parents[2]
    runner = (root / "deploy" / "production" / "run-seo-truth-sync.sh").read_text(encoding="utf-8")
    service = (root / "deploy" / "production" / "axignal-seo-truth-sync.service").read_text(
        encoding="utf-8"
    )
    timer = (root / "deploy" / "production" / "axignal-seo-truth-sync.timer").read_text(
        encoding="utf-8"
    )

    runner_mode = subprocess.check_output(
        ["git", "ls-files", "--stage", "--", "deploy/production/run-seo-truth-sync.sh"],
        cwd=root,
        text=True,
    ).split(maxsplit=1)[0]
    assert runner_mode == "100755"
    assert "AXIGNAL_GSC_OAUTH_SECRET_FILE=/run/secrets/gsc_oauth.json" in runner
    assert "AXIGNAL_CRUX_API_KEY_FILE=/run/secrets/crux_api_key" in runner
    assert "dst=/run/secrets/gsc_oauth.json,readonly" in runner
    assert "dst=/run/secrets/crux_api_key,readonly" in runner
    assert "AXIGNAL_SEO_INSPECTION_LIMIT=30" in runner
    assert "--read-only" in runner
    assert "--cap-drop ALL" in runner
    assert "ConditionPathExists=/etc/axignal/secrets/gsc_oauth.json" in service
    assert "OnCalendar=*-*-* *:17:00 UTC" in timer
    assert "fixture-key" not in runner
