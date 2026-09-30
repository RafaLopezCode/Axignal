"""CAS integrity adapter for subscriber-safe evidence narratives."""

from __future__ import annotations

from pipeline.source_acquisition.artifacts import ContentAddressedArtifactStore


class ContentAddressedArtifactIntegrityAdapter:
    def __init__(self, store: ContentAddressedArtifactStore) -> None:
        self._store = store

    def verify(self, reference: str) -> bool:
        try:
            self._store.read(reference)
        except (FileNotFoundError, RuntimeError, ValueError):
            return False
        return True
