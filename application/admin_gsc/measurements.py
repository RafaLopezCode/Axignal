"""Bridge private GSC outcomes into the governed AO-24 measurement registry."""

from __future__ import annotations

from datetime import UTC, datetime, time
from decimal import Decimal

from application.admin_measurements import MeasurementRegistryService
from domain.admin_gsc import GscSearchRow
from domain.admin_measurements import (
    MeasurementDefinition,
    MeasurementInstrumentAuthority,
    MeasurementObservation,
    MeasurementState,
    MeasurementUnit,
)

GSC_SOURCE_FAMILY = "GOOGLE_SEARCH_CONSOLE"
GSC_INSTRUMENT_ID = "instrument:gsc-search-analytics"
GSC_INSTRUMENT_VERSION = "gsc-search-analytics-v1"
GSC_DEFINITION_EFFECTIVE_AT = datetime(2026, 10, 7, tzinfo=UTC)

_GSC_MEASURES: tuple[tuple[str, str, MeasurementUnit, str], ...] = (
    (
        "measure:gsc-clicks-28d",
        "Search clicks, 28 days",
        MeasurementUnit.COUNT,
        "clicks",
    ),
    (
        "measure:gsc-impressions-28d",
        "Search impressions, 28 days",
        MeasurementUnit.COUNT,
        "impressions",
    ),
    (
        "measure:gsc-ctr-28d",
        "Search CTR, 28 days",
        MeasurementUnit.RATIO,
        "ctr",
    ),
    (
        "measure:gsc-average-position-28d",
        "Search average position, 28 days",
        MeasurementUnit.SCALAR,
        "position",
    ),
)


def gsc_authority() -> MeasurementInstrumentAuthority:
    return MeasurementInstrumentAuthority(
        integration_id="gsc-axignal-own-site",
        source_family=GSC_SOURCE_FAMILY,
        instrument_id=GSC_INSTRUMENT_ID,
    )


def gsc_measurement_definitions() -> tuple[MeasurementDefinition, ...]:
    common_limits = (
        "Search Console measures Google Search exposure for the connected property, not revenue.",
        "Missing rows do not prove zero demand outside the measured property/query dimensions.",
        "Position, CTR and impressions can change because query mix or indexing changed.",
        "GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION.",
    )
    return tuple(
        MeasurementDefinition(
            measure_id=measure_id,
            version=1,
            label=label,
            question_served="How is AXIGNAL's own Google Search visibility changing?",
            decision_served="Decide which public acquisition surfaces deserve investigation.",
            formula_or_coding_rule=(
                "Google Search Console Search Analytics property summary over the declared 28-day "
                f"window; value={field}."
            ),
            unit=unit,
            source_family=GSC_SOURCE_FAMILY,
            instrument_id=GSC_INSTRUMENT_ID,
            instrument_version=GSC_INSTRUMENT_VERSION,
            subject_scope="AXIGNAL_OWN_REGISTERED_WEB_PROPERTY",
            default_window="P28D",
            freshness_seconds=432000,
            minimum_sample_size=1,
            uncertainty_policy=(
                "Coverage is limited to the connected Search Console property and Google's "
                "reported Search Analytics data."
            ),
            compatibility_key=f"{measure_id}:v1",
            interpretation_limits=common_limits,
            evaluation_cases=(
                "same property, same Search Analytics instrument version and adjacent windows",
                "instrument version drift must reject naive historical comparison",
                "missing or unavailable data must remain NOT_MEASURED rather than zero",
            ),
            effective_at=GSC_DEFINITION_EFFECTIVE_AT,
        )
        for measure_id, label, unit, field in _GSC_MEASURES
    )


def _value(row: GscSearchRow, field: str) -> str:
    raw = Decimal(str(getattr(row, field)))
    if field in {"clicks", "impressions"}:
        return str(int(raw))
    return format(raw.normalize(), "f")


def record_gsc_summary_measurements(
    *,
    registry: MeasurementRegistryService,
    summary: GscSearchRow,
    now: datetime,
) -> tuple[str, ...]:
    if summary.dimensions:
        raise ValueError("GSC measurement bridge requires a property summary row")
    if summary.instrument_version != GSC_INSTRUMENT_VERSION:
        raise ValueError("unsupported GSC instrument version")

    authority = gsc_authority()
    for definition in gsc_measurement_definitions():
        registry.register_instrument_definition(
            authority=authority,
            operation_id=f"gsc-definition:{definition.measure_id}",
            reason="AO-13 canonical instrument definition for AXIGNAL private Search Console metrics",
            definition=definition,
            now=now,
        )

    window_start = datetime.combine(summary.window_start, time.min, tzinfo=UTC)
    window_end = datetime.combine(summary.window_end, time.max, tzinfo=UTC)
    sample_size = max(1, int(summary.impressions))
    observation_ids: list[str] = []
    window_key = summary.window_end.strftime("%Y%m%d")
    for measure_id, _, _, field in _GSC_MEASURES:
        observation = MeasurementObservation(
            observation_id=f"obs:gsc:{field}:{window_key}",
            measure_id=measure_id,
            definition_version=1,
            subject_ref="web-property:axignal.com",
            instrument_id=GSC_INSTRUMENT_ID,
            instrument_version=GSC_INSTRUMENT_VERSION,
            compatibility_key=f"{measure_id}:v1",
            state=MeasurementState.MEASURED,
            observed_at=summary.observed_at,
            window_start=window_start,
            window_end=window_end,
            sample_size=sample_size,
            informative_sample_size=sample_size,
            value=_value(summary, field),
            currency=None,
            uncertainty=(
                "Private GSC property summary only; Search Console can omit low-volume query rows "
                "and does not measure non-Google search surfaces."
            ),
            source_refs=(summary.source_ref,),
        )
        registry.record_instrument_observation(
            authority=authority,
            operation_id=f"gsc-observation:{field}:{window_key}",
            reason="AO-13 imported observed Search Console outcome",
            observation=observation,
            now=now,
        )
        observation_ids.append(observation.observation_id)
    return tuple(observation_ids)
