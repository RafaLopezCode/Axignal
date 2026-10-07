"""AO-13 server-side Google Search Console sync for AXIGNAL's own property."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from application.admin_gsc import GscIngestionService
from application.admin_gsc.measurements import (
    GSC_INSTRUMENT_VERSION,
    record_gsc_summary_measurements,
)
from application.admin_measurements import MeasurementRegistryService
from domain.admin_gsc import GscDimension, GscSearchRow
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_gsc import SqliteAdminGscStore
from pipeline.admin_measurements import SqliteMeasurementRegistryStore


@dataclass(frozen=True, slots=True)
class GoogleOAuthRefreshCredentials:
    client_id: str
    client_secret: str
    refresh_token: str

    @classmethod
    def from_file(cls, path: Path) -> GoogleOAuthRefreshCredentials:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("GSC OAuth secret must be a JSON object")
        values = tuple(
            str(raw.get(key, "")).strip() for key in ("client_id", "client_secret", "refresh_token")
        )
        if not all(values):
            raise ValueError("GSC OAuth secret requires client_id, client_secret and refresh_token")
        return cls(*values)


class GoogleSearchConsoleClient:
    token_url = "https://oauth2.googleapis.com/token"
    api_base = "https://searchconsole.googleapis.com/webmasters/v3"

    def __init__(
        self, credentials: GoogleOAuthRefreshCredentials, *, timeout_seconds: int = 30
    ) -> None:
        self._credentials = credentials
        self._timeout = timeout_seconds

    def _json_request(
        self,
        request: Request,
        *,
        failure_prefix: str,
    ) -> dict[str, Any]:
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"{failure_prefix}: HTTP_{exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"{failure_prefix}: TRANSPORT_FAILURE") from exc
        if not isinstance(payload, dict):
            raise RuntimeError(f"{failure_prefix}: INVALID_RESPONSE")
        return payload

    def access_token(self) -> str:
        body = urlencode(
            {
                "client_id": self._credentials.client_id,
                "client_secret": self._credentials.client_secret,
                "refresh_token": self._credentials.refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode()
        payload = self._json_request(
            Request(
                self.token_url,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            ),
            failure_prefix="GSC_OAUTH_FAILED",
        )
        token = str(payload.get("access_token", "")).strip()
        if not token:
            raise RuntimeError("GSC_OAUTH_FAILED: ACCESS_TOKEN_MISSING")
        return token

    def query(
        self,
        *,
        property_ref: str,
        start_date: date,
        end_date: date,
        dimensions: tuple[GscDimension, ...],
        row_limit: int = 25000,
    ) -> tuple[dict[str, Any], ...]:
        if not property_ref.startswith(("sc-domain:", "https://", "http://")):
            raise ValueError("invalid Search Console property reference")
        token = self.access_token()
        start_row = 0
        rows: list[dict[str, Any]] = []
        while True:
            body = json.dumps(
                {
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "dimensions": [item.value for item in dimensions],
                    "type": "web",
                    "dataState": "final",
                    "rowLimit": row_limit,
                    "startRow": start_row,
                },
                separators=(",", ":"),
            ).encode()
            endpoint = f"{self.api_base}/sites/{quote(property_ref, safe='')}/searchAnalytics/query"
            payload = self._json_request(
                Request(
                    endpoint,
                    data=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                ),
                failure_prefix="GSC_QUERY_FAILED",
            )
            page = payload.get("rows", [])
            if not isinstance(page, list):
                raise RuntimeError("GSC_QUERY_FAILED: INVALID_ROWS")
            rows.extend(item for item in page if isinstance(item, dict))
            if len(page) < row_limit:
                break
            start_row += len(page)
            if start_row >= 100000:
                raise RuntimeError("GSC_QUERY_FAILED: SAFETY_ROW_LIMIT")
        return tuple(rows)


def _source_ref(
    property_ref: str, start_date: date, end_date: date, dimensions: tuple[GscDimension, ...]
) -> str:
    dim = "-".join(item.value.lower() for item in dimensions) or "summary"
    prop = property_ref.removeprefix("sc-domain:").replace("https://", "").replace("http://", "")
    prop = prop.strip("/").replace(".", "-")
    return f"gsc:{prop}:{start_date.isoformat()}:{end_date.isoformat()}:{dim}"


def _row(
    *,
    property_ref: str,
    start_date: date,
    end_date: date,
    dimensions: tuple[GscDimension, ...],
    raw: dict[str, Any],
    observed_at: datetime,
) -> GscSearchRow:
    keys = raw.get("keys", [])
    if not isinstance(keys, list) or len(keys) != len(dimensions):
        if dimensions:
            raise RuntimeError("GSC_QUERY_FAILED: DIMENSION_KEY_MISMATCH")
        keys = []
    return GscSearchRow(
        property_ref=property_ref,
        window_start=start_date,
        window_end=end_date,
        dimensions=tuple(
            (dimension.value, str(value)) for dimension, value in zip(dimensions, keys, strict=True)
        ),
        clicks=float(raw.get("clicks", 0)),
        impressions=float(raw.get("impressions", 0)),
        ctr=float(raw.get("ctr", 0)),
        position=float(raw.get("position", 0)),
        observed_at=observed_at,
        source_ref=_source_ref(property_ref, start_date, end_date, dimensions),
        instrument_version=GSC_INSTRUMENT_VERSION,
    )


def _query_rows(
    client: GoogleSearchConsoleClient,
    *,
    property_ref: str,
    start_date: date,
    end_date: date,
    dimensions: tuple[GscDimension, ...],
    observed_at: datetime,
) -> tuple[GscSearchRow, ...]:
    raw_rows = client.query(
        property_ref=property_ref,
        start_date=start_date,
        end_date=end_date,
        dimensions=dimensions,
    )
    return tuple(
        _row(
            property_ref=property_ref,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            raw=item,
            observed_at=observed_at,
        )
        for item in raw_rows
    )


def run_sync(*, now: datetime | None = None) -> dict[str, object]:
    enabled = os.getenv("AXIGNAL_GSC_ENABLED", "").strip().lower() in {"1", "true", "yes"}
    if not enabled:
        return {"state": "DISABLED"}
    data_dir_raw = os.getenv("AXIGNAL_DATA_DIR", "").strip()
    secret_path_raw = os.getenv("AXIGNAL_GSC_OAUTH_SECRET_FILE", "").strip()
    property_ref = os.getenv("AXIGNAL_GSC_PROPERTY", "sc-domain:axignal.com").strip()
    if not data_dir_raw or not secret_path_raw or not property_ref:
        return {"state": "NOT_CONFIGURED"}
    data_dir = Path(data_dir_raw).expanduser().resolve()
    secret_path = Path(secret_path_raw).expanduser().resolve()
    if not secret_path.is_file():
        return {"state": "NOT_CONFIGURED"}

    wall_clock = now or datetime.now(UTC)
    current = datetime.combine(wall_clock.date(), datetime.min.time(), tzinfo=UTC)
    # Search Console final data commonly trails wall clock. Use an explicit safety lag.
    end_date = current.date() - timedelta(days=3)
    start_date = end_date - timedelta(days=27)
    credentials = GoogleOAuthRefreshCredentials.from_file(secret_path)
    client = GoogleSearchConsoleClient(credentials)
    dimensions = (
        (),
        (GscDimension.QUERY,),
        (GscDimension.PAGE,),
        (GscDimension.COUNTRY,),
        (GscDimension.DEVICE,),
        (GscDimension.SEARCH_APPEARANCE,),
    )
    rows = tuple(
        row
        for dimension_set in dimensions
        for row in _query_rows(
            client,
            property_ref=property_ref,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimension_set,
            observed_at=current,
        )
    )
    if not rows or rows[0].dimensions:
        raise RuntimeError("GSC_QUERY_FAILED: SUMMARY_MISSING")

    store = SqliteAdminGscStore(data_dir / "admin-gsc.sqlite3")
    source_ref = _source_ref(property_ref, start_date, end_date, ())
    sync_id = f"gsc-sync:{property_ref.replace(':', '-').replace('.', '-')}-{end_date:%Y%m%d}"
    inserted = GscIngestionService(store).ingest(
        sync_id=sync_id,
        property_ref=property_ref,
        rows=rows,
        window_start=start_date,
        window_end=end_date,
        observed_at=current,
        source_ref=source_ref,
    )
    registry = MeasurementRegistryService(
        SqliteMeasurementRegistryStore(data_dir / "admin-measurements.sqlite3"),
        SqliteAdminGovernanceAuditStore(data_dir / "admin-governance-audit.sqlite3"),
    )
    observation_ids = record_gsc_summary_measurements(
        registry=registry,
        summary=rows[0],
        now=current,
    )
    return {
        "state": "COMPLETED",
        "property": property_ref,
        "window": [start_date.isoformat(), end_date.isoformat()],
        "rows": len(rows),
        "insertedRows": inserted,
        "measurementObservations": list(observation_ids),
    }


def main() -> None:
    try:
        result = run_sync()
    except Exception as exc:
        print(json.dumps({"state": "FAILED", "error": type(exc).__name__}, sort_keys=True))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))
    if result["state"] == "NOT_CONFIGURED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
