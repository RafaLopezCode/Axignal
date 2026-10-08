"""Content-addressed immutable artifacts for raw acquisition material."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

_PREFIX = "cas:sha256:"


class ContentAddressedArtifactStore:
    def __init__(self, root: str | Path, *, read_only: bool = False) -> None:
        self._root = Path(root)
        self._read_only = read_only
        if read_only:
            return
        self._root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, payload: bytes) -> str:
        if self._read_only:
            raise PermissionError("read-only artifact store")
        digest = hashlib.sha256(payload).hexdigest()
        target = self._root / digest[:2] / digest
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise RuntimeError("content-addressed artifact corruption detected")
            return f"{_PREFIX}{digest}"

        with NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
        return f"{_PREFIX}{digest}"

    def put_json(self, value: dict[str, Any]) -> str:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return self.put_bytes(payload)

    def read(self, reference: str) -> bytes:
        if not reference.startswith(_PREFIX):
            raise ValueError("unsupported content-addressed artifact reference")
        digest = reference.removeprefix(_PREFIX)
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("invalid sha256 artifact reference")
        payload = (self._root / digest[:2] / digest).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise RuntimeError("content-addressed artifact corruption detected")
        return payload

    @staticmethod
    def digest(reference: str) -> str:
        if not reference.startswith(_PREFIX):
            raise ValueError("unsupported content-addressed artifact reference")
        return reference.removeprefix(_PREFIX)
