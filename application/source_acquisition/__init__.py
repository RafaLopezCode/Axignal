"""Governed source-acquisition contracts and Brain bridge."""

from application.source_acquisition.contracts import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
    SourceTargetRule,
)
from application.source_acquisition.runtime import (
    SourceIngestionResult,
    ingest_source_observation,
    source_observation_id,
    to_governed_observation,
)

__all__ = [
    "DispatchDisposition",
    "SourceDispatchPolicy",
    "SourceIngestionResult",
    "SourceObservation",
    "SourceRequest",
    "SourceTargetRule",
    "ingest_source_observation",
    "source_observation_id",
    "to_governed_observation",
]
