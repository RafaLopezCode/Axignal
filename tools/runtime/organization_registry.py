"""Explicit root composition of the governed registry provider; unavailable by default."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path

from application.organization_admission.service import (
    RegistryIdentitySource,
    UnavailableRegistrySource,
)
from pipeline.entity_resolution.gleif_registry import RIGHTS, GLEIFRegistryIdentitySource
from pipeline.source_acquisition import ContentAddressedArtifactStore
from pipeline.source_acquisition.http_sensor import HttpSourceSensor
from pipeline.source_acquisition.http_transport import PinnedHttpTransport
from pipeline.source_acquisition.policy import PublicSourcePolicyGate


def build_registry_source(values: Mapping[str, str], root: Path) -> RegistryIdentitySource:
    if (
        values.get("AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER") != "gleif"
        or values.get("AXIGNAL_ORGANIZATION_REGISTRY_RIGHTS") != RIGHTS
    ):
        return UnavailableRegistrySource()
    try:
        artifacts = ContentAddressedArtifactStore(root / "artifacts")
        return GLEIFRegistryIdentitySource(
            artifacts=artifacts,
            database=root / "gleif-registry.sqlite3",
            sensor=HttpSourceSensor(
                policy_gate=PublicSourcePolicyGate(),
                transport=PinnedHttpTransport(),
                artifacts=artifacts,
            ),
        )
    except (OSError, sqlite3.Error):
        return UnavailableRegistrySource()
