"""Governed source-acquisition runtime adapters."""

from pipeline.source_acquisition.artifact_integrity import ContentAddressedArtifactIntegrityAdapter
from pipeline.source_acquisition.artifacts import ContentAddressedArtifactStore
from pipeline.source_acquisition.http_sensor import HttpSourceSensor
from pipeline.source_acquisition.http_transport import PinnedHttpTransport, RawHttpResponse
from pipeline.source_acquisition.policy import (
    PublicSourcePolicyGate,
    ResolvedTarget,
    SourcePolicyRejected,
)

__all__ = [
    "ContentAddressedArtifactIntegrityAdapter",
    "ContentAddressedArtifactStore",
    "HttpSourceSensor",
    "PinnedHttpTransport",
    "PublicSourcePolicyGate",
    "RawHttpResponse",
    "ResolvedTarget",
    "SourcePolicyRejected",
]
