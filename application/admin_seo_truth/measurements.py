"""Governed AO-24 bridge for Chrome UX Report field metrics."""

from __future__ import annotations

from datetime import UTC, datetime, time
from decimal import Decimal

from application.admin_measurements import MeasurementRegistryService
from domain.admin_measurements import (
    MeasurementDefinition,
    MeasurementInstrumentAuthority,
    MeasurementObservation,
    MeasurementState,
    MeasurementUnit,
)
from domain.admin_seo_truth import CruxMetricName, CruxSnapshot

CRUX_SOURCE_FAMILY = "CHROME_UX_REPORT"
CRUX_INSTRUMENT_ID = "instrument:crux-field-data"
CRUX_INSTRUMENT_VERSION = "crux-query-record-v1"
CRUX_DEFINITION_EFFECTIVE_AT = datetime(2026, 10, 7, tzinfo=UTC)

_CRUX_MEASURES: tuple[tuple[CruxMetricName, str, str, MeasurementUnit], ...] = (
    (CruxMetricName.LCP, "lcp", "LCP p75", MeasurementUnit.DURATION_MS),
    (CruxMetricName.INP, "inp", "INP p75", MeasurementUnit.DURATION_MS),
    (CruxMetricName.CLS, "cls", "CLS p75", MeasurementUnit.SCALAR),
    (CruxMetricName.FCP, "fcp", "FCP p75", MeasurementUnit.DURATION_MS),
    (CruxMetricName.TTFB, "ttfb", "TTFB p75", MeasurementUnit.DURATION_MS),
)


def crux_authority() -> MeasurementInstrumentAuthority:
    return MeasurementInstrumentAuthority(
        integration_id="crux-axignal-own-origin",
        source_family=CRUX_SOURCE_FAMILY,
        instrument_id=CRUX_INSTRUMENT_ID,
    )


def crux_measurement_definitions() -> tuple[MeasurementDefinition, ...]:
    common_limits = (
        "CrUX is aggregated Chrome field data over an eligible rolling population.",
        "CrUX absence means insufficient eligible field data, not zero latency or perfect performance.",
        "Origin-level field data does not identify which route caused a regression.",
        "CRUX_PRIVATE_OPERATING_METRIC != AXIGLAND_PUBLIC_OBSERVATION.",
    )
    return tuple(
        MeasurementDefinition(
            measure_id=f"measure:crux-{short}-p75",
            version=1,
            label=label,
            question_served="How do eligible real Chrome users experience AXIGNAL's public origin?",
            decision_served="Prioritize public web performance investigation using field evidence.",
            formula_or_coding_rule=(
                f"Chrome UX Report queryRecord origin-level percentile; metric={metric.value}; p75."
            ),
            unit=unit,
            source_family=CRUX_SOURCE_FAMILY,
            instrument_id=CRUX_INSTRUMENT_ID,
            instrument_version=CRUX_INSTRUMENT_VERSION,
            subject_scope="AXIGNAL_PUBLIC_ORIGIN",
            default_window="P28D_ROLLING",
            freshness_seconds=604800,
            minimum_sample_size=1,
            uncertainty_policy=(
                "One sample means one aggregate CrUX record. Google eligibility/privacy thresholds "
                "determine availability and the underlying user population size is not reported."
            ),
            compatibility_key=f"measure:crux-{short}-p75:v1",
            interpretation_limits=common_limits,
            evaluation_cases=(
                "same origin, form factor and instrument version across adjacent collection periods",
                "missing CrUX record must remain insufficient rather than zero",
                "form factors must not be combined as if they were independent samples",
            ),
            effective_at=CRUX_DEFINITION_EFFECTIVE_AT,
        )
        for metric, short, label, unit in _CRUX_MEASURES
    )


def _decimal(value: float) -> str:
    return format(Decimal(str(value)).normalize(), "f")


def record_crux_measurements(
    *,
    registry: MeasurementRegistryService,
    snapshot: CruxSnapshot,
    now: datetime,
) -> tuple[str, ...]:
    if snapshot.instrument_version != CRUX_INSTRUMENT_VERSION:
        raise ValueError("unsupported CrUX instrument version")

    authority = crux_authority()
    definitions = crux_measurement_definitions()
    for definition in definitions:
        registry.register_instrument_definition(
            authority=authority,
            operation_id=f"crux-definition:{definition.measure_id}",
            reason="SEO Production Truth canonical CrUX instrument definition",
            definition=definition,
            now=now,
        )

    metrics = {metric.name: metric.p75 for metric in snapshot.metrics}
    definition_by_name = {
        metric: (short, definition)
        for (metric, short, _, _), definition in zip(_CRUX_MEASURES, definitions, strict=True)
    }
    window_start = datetime.combine(snapshot.collection_start, time.min, tzinfo=UTC)
    window_end = datetime.combine(snapshot.collection_end, time.max, tzinfo=UTC)
    suffix = snapshot.form_factor.value.lower()
    window_key = snapshot.collection_end.strftime("%Y%m%d")
    observation_ids: list[str] = []

    for metric_name, value in metrics.items():
        short, definition = definition_by_name[metric_name]
        observation = MeasurementObservation(
            observation_id=f"obs:crux:{short}:{suffix}:{window_key}",
            measure_id=definition.measure_id,
            definition_version=1,
            subject_ref=f"web-origin:axignal-com:{suffix}",
            instrument_id=CRUX_INSTRUMENT_ID,
            instrument_version=CRUX_INSTRUMENT_VERSION,
            compatibility_key=definition.compatibility_key,
            state=MeasurementState.MEASURED,
            observed_at=snapshot.observed_at,
            window_start=window_start,
            window_end=window_end,
            sample_size=1,
            informative_sample_size=1,
            value=_decimal(value),
            currency=None,
            uncertainty=(
                "One aggregate CrUX record; underlying eligible Chrome user population size is not exposed."
            ),
            source_refs=(snapshot.source_ref,),
        )
        registry.record_instrument_observation(
            authority=authority,
            operation_id=f"crux-observation:{short}:{suffix}:{window_key}",
            reason="Imported observed Chrome UX Report field percentile",
            observation=observation,
            now=now,
        )
        observation_ids.append(observation.observation_id)
    return tuple(observation_ids)
